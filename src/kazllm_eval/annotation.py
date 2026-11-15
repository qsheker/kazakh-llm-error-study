from __future__ import annotations

import csv
import hashlib
import json
import secrets
from pathlib import Path
from typing import Any

import numpy as np
from openpyxl import Workbook, load_workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from .core import read_csv, stable_shuffle, word_tokens

EVENT_CATEGORIES = ("grammatical", "lexical", "semantic", "code_switching", "surface")
YES_NO_UNKNOWN = ("yes", "no", "needs_adjudication")
RESPONSE_FLAGS = ("refusal", "off_task", "requirement_missing", "repetition", "fabricated_specificity")


def load_run_records(run_dir: Path) -> list[dict[str, Any]]:
    manifest = json.loads((run_dir / "manifest.json").read_text(encoding="utf-8"))
    prompt_path = Path(manifest["prompt_path"])
    if not prompt_path.is_absolute():
        prompt_path = run_dir.parents[1] / prompt_path
    prompts = {row["prompt_id"]: row for row in read_csv(prompt_path)}
    records = []
    for receipt_path in sorted((run_dir / "receipts").glob("*.json")):
        receipt = json.loads(receipt_path.read_text(encoding="utf-8"))
        text = receipt["response"]["message"]["content"]
        prompt = prompts[receipt["prompt_id"]]
        records.append(
            {
                "private_response_id": receipt_path.stem,
                "prompt_id": receipt["prompt_id"],
                "task_type": receipt["task_type"],
                "model_label": receipt["model_label"],
                "prompt_text": prompt["prompt_text"],
                "response_text": text,
                "word_count": len(word_tokens(text)),
                "finish_reason": receipt["response"].get("done_reason"),
                "client_latency_ms": receipt.get("client_latency_ms"),
                "prompt_eval_count": receipt["response"].get("prompt_eval_count"),
                "prompt_eval_duration_ns": receipt["response"].get("prompt_eval_duration"),
                "eval_count": receipt["response"].get("eval_count"),
                "eval_duration_ns": receipt["response"].get("eval_duration"),
                "response_sha256": receipt["response_text_sha256"],
            }
        )
    expected = len(manifest["request_order"])
    if len(records) != expected:
        raise ValueError(f"run has {len(records)} receipts; expected {expected}")
    return records


def build_blind_mapping(records: list[dict[str, Any]]) -> list[dict[str, str]]:
    mapping = []
    for record in records:
        mapping.append(
            {
                "blind_id": "B-" + secrets.token_hex(8).upper(),
                "private_response_id": record["private_response_id"],
                "prompt_id": record["prompt_id"],
                "model_label": record["model_label"],
                "response_sha256": record["response_sha256"],
            }
        )
    return mapping


def write_private_mapping(path: Path, mapping: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = ("blind_id", "private_response_id", "prompt_id", "model_label", "response_sha256")
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows(mapping)


def build_blinded_manifest(
    records: list[dict[str, Any]],
    mapping: list[dict[str, str]],
    reference_dir: Path,
) -> dict[str, Any]:
    by_private = {record["private_response_id"]: record for record in records}
    responses = []
    for item in sorted(mapping, key=lambda row: row["blind_id"]):
        record = by_private[item["private_response_id"]]
        card = reference_text(reference_dir, record["prompt_id"])
        responses.append(
            {
                "blind_id": item["blind_id"],
                "prompt_id": record["prompt_id"],
                "task_type": record["task_type"],
                "prompt_text_sha256": hashlib.sha256(
                    record["prompt_text"].encode("utf-8")
                ).hexdigest(),
                "response_text_sha256": record["response_sha256"],
                "reference_card_sha256": hashlib.sha256(card.encode("utf-8")).hexdigest(),
                "word_count_read_only": record["word_count"],
                "finish_reason_read_only": record["finish_reason"],
            }
        )
    return {"responses": responses}


def validate_blinded_manifest(workbook: dict[str, Any], manifest: dict[str, Any]) -> None:
    rows = manifest.get("responses")
    if not isinstance(rows, list):
        raise TypeError("blinded manifest must contain a responses list")
    expected = {str(row.get("blind_id", "")): row for row in rows}
    if not expected or len(expected) != len(rows) or set(expected) != set(workbook["responses"]):
        raise ValueError("workbook blind IDs do not match the blinded manifest")
    for blind_id, row in workbook["responses"].items():
        source = expected[blind_id]
        checks = {
            "prompt_id": str(row.get("prompt_id") or "") == str(source.get("prompt_id") or ""),
            "task_type": str(row.get("task_type") or "") == str(source.get("task_type") or ""),
            "prompt_text": hashlib.sha256(str(row.get("prompt_text") or "").encode("utf-8")).hexdigest()
            == source.get("prompt_text_sha256"),
            "response_text": hashlib.sha256(row["response_text"].encode("utf-8")).hexdigest()
            == source.get("response_text_sha256"),
            "reference_card": hashlib.sha256(
                str(row.get("reference_or_constraint_card") or "").encode("utf-8")
            ).hexdigest()
            == source.get("reference_card_sha256"),
            "word_count": int(row.get("word_count_read_only"))
            == int(source.get("word_count_read_only")),
            "finish_reason": str(row.get("finish_reason_read_only") or "")
            == str(source.get("finish_reason_read_only") or ""),
        }
        failed = [name for name, passed in checks.items() if not passed]
        if failed:
            raise ValueError(f"{blind_id}: read-only fields differ from blinded manifest: {failed}")


def reference_text(reference_dir: Path, prompt_id: str) -> str:
    path = reference_dir / f"{prompt_id}.md"
    return path.read_text(encoding="utf-8") if path.exists() else "REFERENCE CARD PENDING"


def _style_sheet(sheet, widths: dict[str, float]) -> None:
    header_fill = PatternFill("solid", fgColor="17324D")
    for cell in sheet[1]:
        cell.font = Font(bold=True, color="FFFFFF")
        cell.fill = header_fill
        cell.alignment = Alignment(wrap_text=True, vertical="top")
    sheet.freeze_panes = "A2"
    sheet.auto_filter.ref = sheet.dimensions
    for column, width in widths.items():
        sheet.column_dimensions[column].width = width
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical="top")


def create_rater_workbook(
    output_path: Path,
    records: list[dict[str, Any]],
    mapping: list[dict[str, str]],
    reference_dir: Path,
    order_seed: int,
) -> str:
    by_private = {record["private_response_id"]: record for record in records}
    blinded = []
    for item in mapping:
        record = by_private[item["private_response_id"]]
        blinded.append({**record, "blind_id": item["blind_id"]})
    blinded = stable_shuffle(blinded, order_seed)

    workbook = Workbook()
    responses = workbook.active
    responses.title = "Responses"
    response_headers = [
        "blind_id",
        "prompt_id",
        "task_type",
        "prompt_text",
        "response_text",
        "reference_or_constraint_card",
        "word_count_read_only",
        "finish_reason_read_only",
        "refusal",
        "off_task",
        "requirement_missing",
        "missing_requirements",
        "repetition",
        "fabricated_specificity",
        "rater_comments",
    ]
    responses.append(response_headers)
    for record in blinded:
        responses.append(
            [
                record["blind_id"],
                record["prompt_id"],
                record["task_type"],
                record["prompt_text"],
                record["response_text"],
                reference_text(reference_dir, record["prompt_id"]),
                record["word_count"],
                record["finish_reason"],
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ]
        )

    validation = DataValidation(type="list", formula1='"yes,no,needs_adjudication"', allow_blank=False)
    responses.add_data_validation(validation)
    for column in ("I", "J", "K", "M", "N"):
        validation.add(f"{column}2:{column}{responses.max_row}")
    _style_sheet(
        responses,
        {"A": 22, "B": 12, "C": 20, "D": 55, "E": 75, "F": 65, "G": 14, "H": 18,
         "I": 18, "J": 18, "K": 20, "L": 40, "M": 18, "N": 22, "O": 40},
    )

    events = workbook.create_sheet("Error events")
    event_headers = [
        "blind_id",
        "event_id",
        "category",
        "exact_fragment",
        "start_offset_zero_based",
        "end_offset_exclusive",
        "start_token_one_based",
        "end_token_one_based",
        "proposed_correction",
        "rationale",
        "source",
        "needs_adjudication",
    ]
    events.append(event_headers)
    for _ in range(max(500, len(records) * 4)):
        events.append([""] * len(event_headers))
    category_validation = DataValidation(
        type="list", formula1='"grammatical,lexical,semantic,code_switching,surface"', allow_blank=True
    )
    yes_no_validation = DataValidation(type="list", formula1='"yes,no"', allow_blank=True)
    events.add_data_validation(category_validation)
    events.add_data_validation(yes_no_validation)
    category_validation.add(f"C2:C{events.max_row}")
    yes_no_validation.add(f"L2:L{events.max_row}")
    _style_sheet(
        events,
        {"A": 22, "B": 18, "C": 20, "D": 45, "E": 20, "F": 20, "G": 20, "H": 20,
         "I": 45, "J": 55, "K": 45, "L": 20},
    )

    instructions = workbook.create_sheet("Instructions")
    instructions.append(["Rule", "Required behavior"])
    rules = [
        ("Independence", "Do not inspect another rater's workbook or automatic detector output."),
        ("Event", "Use the smallest continuous fragment requiring one independent correction."),
        ("Offsets", "Offsets are zero-based and end_offset is exclusive; copied fragment must match exactly."),
        ("Priority", "code_switching > semantic > grammatical > lexical for overlapping interpretations."),
        ("Uncertainty", "Use needs_adjudication rather than forcing certainty."),
        ("Surface", "Spelling, punctuation, capitalization, and spacing use surface and do not enter primary rate."),
        ("Do not rename", "Do not rename sheets or columns. Do not sort the Events sheet by model guesses."),
    ]
    for row in rules:
        instructions.append(row)
    _style_sheet(instructions, {"A": 24, "B": 110})

    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook.save(output_path)
    return hashlib.sha256(output_path.read_bytes()).hexdigest()


def _sheet_records(sheet) -> list[dict[str, Any]]:
    rows = sheet.iter_rows(values_only=True)
    headers = [str(value).strip() if value is not None else "" for value in next(rows)]
    if len(headers) != len(set(headers)) or any(not header for header in headers):
        raise ValueError(f"{sheet.title}: headers must be non-empty and unique")
    records = []
    for values in rows:
        if not any(value not in (None, "") for value in values):
            continue
        records.append(dict(zip(headers, values)))
    return records


def load_annotation_workbook(path: Path, expected_responses: int | None = None) -> dict[str, Any]:
    workbook = load_workbook(path, read_only=True, data_only=True)
    required_sheets = {"Responses", "Error events", "Instructions"}
    if not required_sheets.issubset(workbook.sheetnames):
        raise ValueError(f"{path}: missing sheets {sorted(required_sheets - set(workbook.sheetnames))}")

    response_rows = _sheet_records(workbook["Responses"])
    if expected_responses is not None and len(response_rows) != expected_responses:
        raise ValueError(f"{path}: expected {expected_responses} responses, found {len(response_rows)}")
    responses: dict[str, dict[str, Any]] = {}
    for row in response_rows:
        blind_id = str(row.get("blind_id") or "").strip()
        if not blind_id or blind_id in responses:
            raise ValueError(f"{path}: missing or duplicate blind_id {blind_id!r}")
        for flag in RESPONSE_FLAGS:
            value = str(row.get(flag) or "").strip()
            if value not in YES_NO_UNKNOWN:
                raise ValueError(f"{path}: {blind_id} has invalid {flag}={value!r}")
        response_text = str(row.get("response_text") or "")
        if row.get("word_count_read_only") is None:
            raise ValueError(f"{path}: {blind_id} has no read-only word count")
        responses[blind_id] = {**row, "response_text": response_text}

    event_rows = _sheet_records(workbook["Error events"])
    events = []
    event_ids = set()
    for row in event_rows:
        blind_id = str(row.get("blind_id") or "").strip()
        event_id = str(row.get("event_id") or "").strip()
        category = str(row.get("category") or "").strip()
        if not blind_id or blind_id not in responses:
            raise ValueError(f"{path}: event has unknown blind_id {blind_id!r}")
        key = (blind_id, event_id)
        if not event_id or key in event_ids:
            raise ValueError(f"{path}: missing or duplicate event_id for {blind_id}")
        event_ids.add(key)
        if category not in EVENT_CATEGORIES:
            raise ValueError(f"{path}: {blind_id}/{event_id} has invalid category {category!r}")
        try:
            start = int(row["start_offset_zero_based"])
            end = int(row["end_offset_exclusive"])
            start_token = int(row["start_token_one_based"])
            end_token = int(row["end_token_one_based"])
        except (KeyError, TypeError, ValueError) as exc:
            raise ValueError(f"{path}: {blind_id}/{event_id} has invalid offsets or token indices") from exc
        text = responses[blind_id]["response_text"]
        fragment = str(row.get("exact_fragment") or "")
        if start < 0 or end <= start or end > len(text) or text[start:end] != fragment:
            raise ValueError(f"{path}: {blind_id}/{event_id} fragment does not match its offsets")
        if start_token < 1 or end_token < start_token:
            raise ValueError(f"{path}: {blind_id}/{event_id} has invalid token indices")
        if not str(row.get("proposed_correction") or "").strip() or not str(row.get("rationale") or "").strip():
            raise ValueError(f"{path}: {blind_id}/{event_id} lacks correction or rationale")
        needs = str(row.get("needs_adjudication") or "").strip()
        if needs not in {"yes", "no"}:
            raise ValueError(f"{path}: {blind_id}/{event_id} has invalid needs_adjudication={needs!r}")
        events.append(
            {
                **row,
                "blind_id": blind_id,
                "event_id": event_id,
                "category": category,
                "start_offset_zero_based": start,
                "end_offset_exclusive": end,
                "start_token_one_based": start_token,
                "end_token_one_based": end_token,
            }
        )
    return {"responses": responses, "events": events, "sha256": hashlib.sha256(path.read_bytes()).hexdigest()}


def _cohen_kappa(left: np.ndarray, right: np.ndarray) -> float | None:
    observed = float(np.mean(left == right))
    left_positive = float(np.mean(left))
    right_positive = float(np.mean(right))
    expected = left_positive * right_positive + (1 - left_positive) * (1 - right_positive)
    if expected == 1:
        return None
    return (observed - expected) / (1 - expected)


def _interval_alpha(left: np.ndarray, right: np.ndarray) -> float | None:
    observed = float(np.mean(np.square(left - right)))
    pooled = np.concatenate([left, right]).astype(float)
    if len(pooled) < 2:
        return None
    differences = pooled[:, None] - pooled[None, :]
    expected = float(np.square(differences)[np.triu_indices(len(pooled), 1)].mean())
    if expected == 0:
        return 1.0 if observed == 0 else None
    return 1 - observed / expected


def annotation_agreement(left: dict[str, Any], right: dict[str, Any]) -> dict[str, Any]:
    blind_ids = sorted(left["responses"])
    if blind_ids != sorted(right["responses"]):
        raise ValueError("rater workbooks contain different blind_id sets")

    flag_results = {}
    for flag in RESPONSE_FLAGS:
        left_values = np.array([left["responses"][blind_id][flag] == "yes" for blind_id in blind_ids])
        right_values = np.array([right["responses"][blind_id][flag] == "yes" for blind_id in blind_ids])
        flag_results[flag] = {
            "agreement": float(np.mean(left_values == right_values)),
            "cohen_kappa": _cohen_kappa(left_values, right_values),
        }

    def event_sets(workbook: dict[str, Any]) -> tuple[dict[tuple[str, str], int], set[tuple[str, str, int, int]]]:
        counts = {(blind_id, category): 0 for blind_id in blind_ids for category in EVENT_CATEGORIES}
        spans = set()
        for event in workbook["events"]:
            counts[(event["blind_id"], event["category"])] += 1
            spans.add(
                (
                    event["blind_id"],
                    event["category"],
                    event["start_offset_zero_based"],
                    event["end_offset_exclusive"],
                )
            )
        return counts, spans

    left_counts, left_spans = event_sets(left)
    right_counts, right_spans = event_sets(right)
    primary = EVENT_CATEGORIES[:4]
    category_left = np.array([left_counts[(blind_id, category)] > 0 for blind_id in blind_ids for category in primary])
    category_right = np.array([right_counts[(blind_id, category)] > 0 for blind_id in blind_ids for category in primary])
    totals_left = np.array([sum(left_counts[(blind_id, category)] for category in primary) for blind_id in blind_ids])
    totals_right = np.array([sum(right_counts[(blind_id, category)] for category in primary) for blind_id in blind_ids])
    matches = len(left_spans & right_spans)
    span_precision = matches / len(left_spans) if left_spans else None
    span_recall = matches / len(right_spans) if right_spans else None
    span_f1 = (
        2 * matches / (len(left_spans) + len(right_spans))
        if left_spans or right_spans
        else 1.0
    )
    return {
        "responses": len(blind_ids),
        "response_flags": flag_results,
        "category_presence": {
            "agreement": float(np.mean(category_left == category_right)),
            "cohen_kappa": _cohen_kappa(category_left, category_right),
        },
        "total_primary_count": {"krippendorff_alpha_interval": _interval_alpha(totals_left, totals_right)},
        "exact_span_match": {
            "matches": matches,
            "rater_1_spans": len(left_spans),
            "rater_2_spans": len(right_spans),
            "precision": span_precision,
            "recall": span_recall,
            "f1": span_f1,
        },
    }
