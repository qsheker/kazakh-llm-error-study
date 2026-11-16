#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
import urllib.error
import urllib.request
from collections import Counter
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from openpyxl import load_workbook

from kazllm_eval.annotation import EVENT_CATEGORIES, RESPONSE_FLAGS
from kazllm_eval.core import WORD_RE, canonical_json, sha256_file, write_json

ROOT = Path(__file__).resolve().parents[1]
DEFAULT_WORKBOOK = ROOT / "annotations/team_gold/final_test_v2__team_gold.xlsx"
DEFAULT_DRAFT_DIR = ROOT / "annotations/team_gold/ai_drafts"
DEFAULT_PROVENANCE = ROOT / "annotations/team_gold/ai_draft_provenance.json"
DEFAULT_REVIEW_LOG = ROOT / "annotations/team_gold/team_review_log.csv"
ALLOWED_FLAGS = {"yes", "no", "needs_adjudication"}
DRAFT_SCHEMA_VERSION = 6
NORMALIZER_VERSION = 3
FLAG_KEYS = {
    "refusal": "r",
    "off_task": "o",
    "requirement_missing": "m",
    "repetition": "p",
    "fabricated_specificity": "s",
}
DRAFT_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["f", "miss", "e"],
    "properties": {
        "f": {
            "type": "object",
            "additionalProperties": False,
            "required": list(FLAG_KEYS.values()),
            "properties": {
                name: {"type": "string", "enum": ["y", "n", "u"]}
                for name in FLAG_KEYS.values()
            },
        },
        "miss": {"type": "string", "maxLength": 240},
        "e": {
            "type": "array",
            "maxItems": 2,
            "items": {
                "type": "object",
                "additionalProperties": False,
                "required": ["c", "x", "i", "fix", "why"],
                "properties": {
                    "c": {"type": "string", "enum": list(EVENT_CATEGORIES)},
                    "x": {"type": "string", "maxLength": 160},
                    "i": {"type": "integer", "minimum": 0},
                    "fix": {"type": "string", "maxLength": 160},
                    "why": {"type": "string", "maxLength": 160},
                },
            },
        },
    },
}
SYSTEM_INSTRUCTION = """Draft blinded Kazakh-language annotations for human review. Use only the prompt,
response, and reference card; model identity is unknown. Output the compact schema exactly.

Flags f use y=yes, n=no, u=uncertain: r refusal, o off-task, m explicit requirement missing,
p harmful repetition, s unsupported exact rules/prices/schedules/institutions/specifics. In miss, compactly name
all prompt/card requirements absent from the response; otherwise use an empty string. If miss is nonempty, m=y.

Events e are only the two highest-confidence local errors, or fewer. Each has c category, x smallest exact
verbatim response fragment, i zero-based offset, fix different corrected text, and why short rationale.
Categories: grammatical (morphology/syntax), lexical (word/collocation), semantic (contradiction/unsupported
proposition), code_switching (unrequested Russian/English), surface (spelling/punctuation/case/spacing).

Missing content and repetition are response flags, not events. Relevant extra advice is not an error merely
because it was not required. For overlap prefer code_switching, semantic, grammatical, then lexical. Ignore
style preferences and uncertain events. Keep every string very short."""
DRAFT_OPTIONS = {
    "temperature": 0.0,
    "seed": 2417,
    "num_predict": 768,
    "num_ctx": 8192,
    "top_k": 40,
    "top_p": 1.0,
    "repeat_penalty": 1.0,
}


def utc_now() -> str:
    return datetime.now(UTC).isoformat()


def sheet_records(sheet) -> list[dict[str, Any]]:
    rows = sheet.iter_rows(values_only=True)
    headers = [str(value or "").strip() for value in next(rows)]
    return [
        dict(zip(headers, values))
        for values in rows
        if any(value not in (None, "") for value in values)
    ]


def call_ollama(endpoint: str, payload: dict[str, Any], timeout: int) -> dict[str, Any]:
    request = urllib.request.Request(
        endpoint.rstrip("/") + "/api/chat",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return json.load(response)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
        raise RuntimeError(f"AI draft request failed: {exc}") from exc


def token_range(text: str, start: int, end: int) -> tuple[int, int] | None:
    spans = [(match.start(), match.end()) for match in WORD_RE.finditer(text)]
    overlapping = [
        index
        for index, (left, right) in enumerate(spans, start=1)
        if right > start and left < end
    ]
    if not overlapping:
        return None
    return overlapping[0], overlapping[-1]


def normalize_flag(value: Any, issues: list[str], name: str) -> str:
    aliases = {"y": "yes", "n": "no", "u": "needs_adjudication"}
    normalized = aliases.get(
        str(value or "").strip().lower(), str(value or "").strip().lower()
    )
    if normalized not in ALLOWED_FLAGS:
        issues.append(f"invalid {name}={normalized!r}; set to needs_adjudication")
        return "needs_adjudication"
    return normalized


def find_event_offset(text: str, fragment: str, supplied: Any) -> int | None:
    try:
        start = int(supplied)
    except (TypeError, ValueError):
        start = -1
    if (
        0 <= start <= len(text) - len(fragment)
        and text[start : start + len(fragment)] == fragment
    ):
        return start
    matches = [match.start() for match in re.finditer(re.escape(fragment), text)]
    return matches[0] if len(matches) == 1 else None


def normalize_draft(row: dict[str, Any], raw: dict[str, Any]) -> dict[str, Any]:
    blind_id = str(row["blind_id"])
    response_text = str(row["response_text"])
    issues: list[str] = []
    raw_flags = raw.get("f") if isinstance(raw.get("f"), dict) else {}
    flags = {
        name: normalize_flag(raw_flags.get(FLAG_KEYS[name]), issues, name)
        for name in RESPONSE_FLAGS
    }
    missing = str(raw.get("miss") or "").strip()
    if missing and flags["requirement_missing"] != "yes":
        issues.append(
            "requirement_missing overridden because missing requirements were named: "
            f"{flags['requirement_missing']} -> yes"
        )
        flags["requirement_missing"] = "yes"
    elif not missing and flags["requirement_missing"] == "yes":
        issues.append("requirement_missing=yes without named requirements")
        flags["requirement_missing"] = "needs_adjudication"

    events = []
    raw_events = raw.get("e") if isinstance(raw.get("e"), list) else []
    seen: set[tuple[str, int, int]] = set()
    repetition_evidence = False
    for raw_event in raw_events[:3]:
        if not isinstance(raw_event, dict):
            issues.append("non-object event omitted")
            continue
        category = str(raw_event.get("c") or "").strip()
        fragment = str(raw_event.get("x") or "")
        correction = str(raw_event.get("fix") or "").strip()
        rationale = str(raw_event.get("why") or "").strip()
        source = "AI draft from prompt/response/reference card"
        if (
            category not in EVENT_CATEGORIES
            or not fragment
            or not correction
            or not rationale
        ):
            issues.append("incomplete or invalid event omitted")
            continue
        rationale_lower = rationale.lower()
        repetition_markers = ("repet", "redundan", "қайтал")
        omission_markers = (
            "absent",
            "lack",
            "missing",
            "omit",
            "does not address",
            "does not include",
            "does not mention",
            "not address",
            "not include",
            "not mention",
            "not explicitly required",
            "жоқ",
            "жетісп",
        )
        if any(marker in rationale_lower for marker in repetition_markers):
            repetition_evidence = True
            issues.append("repetition-only event was omitted")
            continue
        if any(marker in rationale_lower for marker in omission_markers):
            issues.append("omission-only event was omitted")
            continue
        if correction == fragment:
            issues.append("event correction equals fragment and was omitted")
            continue
        start = find_event_offset(response_text, fragment, raw_event.get("i"))
        if start is None:
            issues.append(
                f"event fragment not uniquely located and omitted: {fragment[:60]!r}"
            )
            continue
        end = start + len(fragment)
        tokens = token_range(response_text, start, end)
        if tokens is None:
            issues.append(
                f"event contains no word token and was omitted: {fragment[:60]!r}"
            )
            continue
        key = (category, start, end)
        if key in seen:
            continue
        seen.add(key)
        events.append(
            {
                "event_id": f"AI-{len(events) + 1:02d}",
                "category": category,
                "exact_fragment": fragment,
                "start_offset_zero_based": start,
                "end_offset_exclusive": end,
                "start_token_one_based": tokens[0],
                "end_token_one_based": tokens[1],
                "proposed_correction": correction,
                "rationale": rationale,
                "source": source,
                "needs_adjudication": "yes",
            }
        )
    if repetition_evidence and flags["repetition"] != "yes":
        issues.append(
            f"repetition overridden from event rationale: {flags['repetition']} -> yes"
        )
        flags["repetition"] = "yes"
    return {
        "blind_id": blind_id,
        "flags": flags,
        "missing_requirements": missing,
        "comments": "",
        "events": events,
        "validation_issues": issues,
    }


def response_input_hash(row: dict[str, Any]) -> str:
    value = {
        key: str(row.get(key) or "")
        for key in (
            "blind_id",
            "prompt_text",
            "response_text",
            "reference_or_constraint_card",
        )
    }
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def draft_protocol_hash() -> str:
    value = {
        "schema_version": DRAFT_SCHEMA_VERSION,
        "schema": DRAFT_SCHEMA,
        "system_instruction": SYSTEM_INSTRUCTION,
        "options": DRAFT_OPTIONS,
        "think": False,
    }
    return hashlib.sha256(canonical_json(value).encode()).hexdigest()


def draft_request(row: dict[str, Any], model: str) -> dict[str, Any]:
    item = {
        "blind_id": row["blind_id"],
        "prompt_text": row["prompt_text"],
        "response_text": row["response_text"],
        "reference_or_constraint_card": row["reference_or_constraint_card"],
    }
    return {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_INSTRUCTION},
            {"role": "user", "content": json.dumps(item, ensure_ascii=False)},
        ],
        "format": DRAFT_SCHEMA,
        "stream": False,
        "think": False,
        "keep_alive": "30m",
        "options": DRAFT_OPTIONS,
    }


def load_or_generate_draft(
    row: dict[str, Any],
    draft_dir: Path,
    endpoint: str,
    model: str,
    model_digest: str,
    timeout: int,
) -> tuple[dict[str, Any], str]:
    blind_id = str(row["blind_id"])
    path = draft_dir / f"{blind_id}.json"
    input_hash = response_input_hash(row)
    protocol_hash = draft_protocol_hash()
    if path.exists():
        saved = json.loads(path.read_text(encoding="utf-8"))
        if (
            saved.get("draft_schema_version") == DRAFT_SCHEMA_VERSION
            and saved.get("input_sha256") == input_hash
            and saved.get("annotator_model") == model
            and saved.get("annotator_model_digest") == model_digest
        ):
            changed = False
            status = "reused"
            saved_protocol_hash = saved.get("draft_protocol_sha256")
            if saved_protocol_hash is None:
                saved["draft_protocol_sha256"] = protocol_hash
                changed = True
                status = "provenance_upgraded"
            elif saved_protocol_hash != protocol_hash:
                raise RuntimeError(f"existing AI draft protocol differs for {blind_id}")
            normalized = normalize_draft(row, saved["raw_output"])
            if (
                saved.get("normalizer_version") != NORMALIZER_VERSION
                or saved.get("draft") != normalized
            ):
                saved["normalizer_version"] = NORMALIZER_VERSION
                saved["draft"] = normalized
                changed = True
                status = "renormalized"
            if changed:
                write_json(path, saved)
            return normalized, status
        raise RuntimeError(f"existing AI draft provenance differs for {blind_id}")

    returned = call_ollama(endpoint, draft_request(row, model), timeout)
    content = returned.get("message", {}).get("content")
    if returned.get("done") is not True or not isinstance(content, str):
        raise RuntimeError(f"incomplete AI draft response for {blind_id}")
    try:
        raw = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"AI draft was not valid JSON for {blind_id}") from exc
    if not isinstance(raw, dict):
        raise TypeError(f"AI draft root must be an object for {blind_id}")
    draft = normalize_draft(row, raw)
    record = {
        "blind_id": blind_id,
        "draft_schema_version": DRAFT_SCHEMA_VERSION,
        "normalizer_version": NORMALIZER_VERSION,
        "input_sha256": input_hash,
        "draft_protocol_sha256": protocol_hash,
        "annotator_model": model,
        "annotator_model_digest": model_digest,
        "created_utc": utc_now(),
        "raw_output": raw,
        "draft": draft,
    }
    write_json(path, record)
    return draft, "received"


def apply_drafts(workbook_path: Path, drafts: list[dict[str, Any]]) -> tuple[str, str]:
    before_hash = sha256_file(workbook_path)
    workbook = load_workbook(workbook_path)
    responses = workbook["Responses"]
    response_headers = {
        cell.value: index for index, cell in enumerate(responses[1], start=1)
    }
    response_rows = {
        str(responses.cell(row, 1).value): row
        for row in range(2, responses.max_row + 1)
    }
    if set(response_rows) != {draft["blind_id"] for draft in drafts}:
        raise RuntimeError("AI drafts do not cover exactly the workbook blind IDs")
    for draft in drafts:
        row_index = response_rows[draft["blind_id"]]
        for name, value in draft["flags"].items():
            responses.cell(row_index, response_headers[name]).value = value
        responses.cell(
            row_index, response_headers["missing_requirements"]
        ).value = draft["missing_requirements"]
        comments = ["AI DRAFT; human review required."]
        if draft["comments"]:
            comments.append(draft["comments"])
        if draft["validation_issues"]:
            comments.append(
                "Draft validation issues: " + " | ".join(draft["validation_issues"])
            )
        responses.cell(row_index, response_headers["rater_comments"]).value = " ".join(
            comments
        )

    events = workbook["Error events"]
    event_headers = {cell.value: index for index, cell in enumerate(events[1], start=1)}
    for row in events.iter_rows(min_row=2):
        for cell in row:
            cell.value = None
    event_row = 2
    for draft in drafts:
        for event in draft["events"]:
            values = {"blind_id": draft["blind_id"], **event}
            for name, value in values.items():
                events.cell(event_row, event_headers[name]).value = value
            event_row += 1

    temporary = workbook_path.with_suffix(workbook_path.suffix + ".tmp")
    workbook.save(temporary)
    temporary.replace(workbook_path)
    return before_hash, sha256_file(workbook_path)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create resumable blinded AI annotation drafts."
    )
    parser.add_argument("--workbook", type=Path, default=DEFAULT_WORKBOOK)
    parser.add_argument("--draft-dir", type=Path, default=DEFAULT_DRAFT_DIR)
    parser.add_argument("--provenance", type=Path, default=DEFAULT_PROVENANCE)
    parser.add_argument("--review-log", type=Path, default=DEFAULT_REVIEW_LOG)
    parser.add_argument("--endpoint", default="http://127.0.0.1:11434")
    parser.add_argument("--model", default="qwen3:8b")
    parser.add_argument("--timeout", type=int, default=1800)
    parser.add_argument(
        "--offset",
        type=int,
        default=0,
        help="Skip the first N workbook rows; use with --limit for resumable partitioning.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Generate only the first N drafts for quality control; do not modify the workbook.",
    )
    args = parser.parse_args()
    if args.limit is not None and args.limit <= 0:
        raise SystemExit("--limit must be positive")
    if args.offset < 0 or args.offset >= 240:
        raise SystemExit("--offset must be between 0 and 239")
    if args.offset and args.limit is None:
        raise SystemExit(
            "--offset requires --limit so a partial run cannot modify the workbook"
        )
    if not args.review_log.is_file():
        raise SystemExit(f"review log not found: {args.review_log}")
    review_log_hash_before = sha256_file(args.review_log)

    artifacts = json.loads(
        (ROOT / "config/model_artifacts.json").read_text(encoding="utf-8")
    )
    model_record = artifacts.get("models", {}).get(args.model)
    if not isinstance(model_record, dict) or not model_record.get("digest"):
        raise SystemExit(
            f"annotator model is not in the frozen artifact manifest: {args.model}"
        )
    model_digest = str(model_record["digest"])

    workbook = load_workbook(args.workbook, read_only=True, data_only=True)
    rows = sheet_records(workbook["Responses"])
    if len(rows) != 240:
        raise SystemExit(f"expected 240 blinded responses, found {len(rows)}")
    remaining_rows = rows[args.offset :]
    selected_rows = (
        remaining_rows if args.limit is None else remaining_rows[: args.limit]
    )
    if not selected_rows:
        raise SystemExit("workbook contains no responses")
    args.draft_dir.mkdir(parents=True, exist_ok=True)
    drafts = []
    counters: Counter[str] = Counter()

    def generate(row: dict[str, Any]) -> tuple[dict[str, Any], str]:
        return load_or_generate_draft(
            row,
            args.draft_dir,
            args.endpoint,
            args.model,
            model_digest,
            args.timeout,
        )

    for index, row in enumerate(selected_rows, start=1):
        draft, status = generate(row)
        drafts.append(draft)
        counters[status] += 1
        print(f"{index}/{len(selected_rows)} {row['blind_id']} {status}", flush=True)

    row_order = {str(row["blind_id"]): index for index, row in enumerate(rows)}
    drafts.sort(key=lambda draft: row_order[draft["blind_id"]])

    if args.limit is not None:
        workbook_hash = sha256_file(args.workbook)
        review_log_hash_after = sha256_file(args.review_log)
        if review_log_hash_after != review_log_hash_before:
            raise RuntimeError("review log changed during AI draft quality control")
        selected_ids = [draft["blind_id"] for draft in drafts]
        provenance = {
            "status": "quality_control_sample_only_not_applied",
            "created_utc": utc_now(),
            "annotator_model": args.model,
            "annotator_model_digest": model_digest,
            "draft_protocol_sha256": draft_protocol_hash(),
            "offset": args.offset,
            "draft_count": len(drafts),
            "blind_ids": selected_ids,
            "workbook_sha256_before": workbook_hash,
            "workbook_sha256_after": workbook_hash,
            "review_log_sha256_before": review_log_hash_before,
            "review_log_sha256_after": review_log_hash_after,
            "draft_file_hashes": {
                f"{blind_id}.json": sha256_file(args.draft_dir / f"{blind_id}.json")
                for blind_id in selected_ids
            },
            "generation": dict(counters),
            "workbook_changed": False,
            "review_log_changed": False,
        }
        write_json(args.provenance, provenance)
        print(json.dumps(provenance, ensure_ascii=False, indent=2))
        return 0

    before_hash, after_hash = apply_drafts(args.workbook, drafts)
    review_log_hash_after = sha256_file(args.review_log)
    if review_log_hash_after != review_log_hash_before:
        raise RuntimeError("review log changed while AI drafts were applied")
    provenance = {
        "status": "ai_draft_only_human_review_required",
        "created_utc": utc_now(),
        "annotator_model": args.model,
        "annotator_model_digest": model_digest,
        "draft_protocol_sha256": draft_protocol_hash(),
        "workbook_sha256_before": before_hash,
        "workbook_sha256_after": after_hash,
        "review_log_sha256_before": review_log_hash_before,
        "review_log_sha256_after": review_log_hash_after,
        "draft_count": len(drafts),
        "event_count": sum(len(draft["events"]) for draft in drafts),
        "validation_issue_count": sum(
            len(draft["validation_issues"]) for draft in drafts
        ),
        "draft_file_hashes": {
            path.name: sha256_file(path)
            for path in sorted(args.draft_dir.glob("B-*.json"))
        },
        "generation": dict(counters),
        "review_log_changed": review_log_hash_before != review_log_hash_after,
    }
    write_json(args.provenance, provenance)
    print(json.dumps(provenance, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
