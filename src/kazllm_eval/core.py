from __future__ import annotations

import csv
import hashlib
import json
import re
from collections import Counter, defaultdict
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any, Iterable

WORD_RE = re.compile(r"[^\W\d_]+(?:[-'’][^\W\d_]+)*", re.UNICODE)

TEST_COLUMNS = (
    "prompt_id",
    "task_type",
    "domain",
    "task_form",
    "prompt_text",
    "version",
)
TASK_COUNTS = {"educational": 30, "public_information": 30}


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    temporary.replace(path)


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as stream:
        return list(csv.DictReader(stream))


def word_tokens(text: str) -> list[str]:
    return WORD_RE.findall(text)


def normalized_prompt(text: str) -> str:
    return " ".join(token.casefold().replace("ё", "е") for token in word_tokens(text))


def prompt_similarity(left: str, right: str) -> float:
    return SequenceMatcher(None, normalized_prompt(left), normalized_prompt(right)).ratio()


def validate_test_prompts(test_path: Path, dev_path: Path | None = None) -> dict[str, Any]:
    rows = read_csv(test_path)
    errors: list[str] = []
    warnings: list[str] = []
    if not rows:
        return {"valid": False, "errors": ["test CSV is empty"], "warnings": []}

    columns = tuple(rows[0].keys())
    if columns != TEST_COLUMNS:
        errors.append(f"columns must be exactly {TEST_COLUMNS}, got {columns}")
    if len(rows) != 60:
        errors.append(f"expected 60 prompts, got {len(rows)}")

    ids = [row.get("prompt_id", "") for row in rows]
    if len(ids) != len(set(ids)):
        duplicates = sorted(key for key, n in Counter(ids).items() if n > 1)
        errors.append(f"duplicate prompt IDs: {duplicates}")

    texts = [normalized_prompt(row.get("prompt_text", "")) for row in rows]
    if any(not text for text in texts):
        errors.append("every prompt_text must contain at least one word token")
    if len(texts) != len(set(texts)):
        errors.append("test set contains exact duplicate normalized prompts")

    task_counts = Counter(row.get("task_type", "") for row in rows)
    if dict(task_counts) != TASK_COUNTS:
        errors.append(f"task balance must be {TASK_COUNTS}, got {dict(task_counts)}")

    matrices: dict[str, dict[str, Any]] = {}
    by_task: dict[str, list[dict[str, str]]] = defaultdict(list)
    for row in rows:
        by_task[row.get("task_type", "")].append(row)
        if row.get("version") != "2.0":
            errors.append(f"{row.get('prompt_id')}: version must be 2.0")
    for task, expected_count in TASK_COUNTS.items():
        task_rows = by_task.get(task, [])
        domains = Counter(row.get("domain", "") for row in task_rows)
        forms = Counter(row.get("task_form", "") for row in task_rows)
        cells = [(row.get("domain", ""), row.get("task_form", "")) for row in task_rows]
        matrices[task] = {"domains": dict(domains), "forms": dict(forms)}
        if len(domains) != 5 or set(domains.values()) != {6}:
            errors.append(f"{task}: expected five domains with six prompts each, got {dict(domains)}")
        if len(forms) != 6 or set(forms.values()) != {5}:
            errors.append(f"{task}: expected six forms with five prompts each, got {dict(forms)}")
        if len(cells) != expected_count or len(set(cells)) != expected_count:
            errors.append(f"{task}: every domain/form cell must occur exactly once")

    close_pairs: list[dict[str, Any]] = []
    for index, row in enumerate(rows):
        for other in rows[index + 1 :]:
            score = prompt_similarity(row["prompt_text"], other["prompt_text"])
            if score >= 0.72:
                close_pairs.append({"left": row["prompt_id"], "right": other["prompt_id"], "score": score})
    if close_pairs:
        warnings.append(f"{len(close_pairs)} test prompt pair(s) have similarity >= 0.72; review manually")

    dev_matches: list[dict[str, Any]] = []
    if dev_path is not None:
        for test in rows:
            for dev in read_csv(dev_path):
                score = prompt_similarity(test["prompt_text"], dev["prompt_text"])
                if score >= 0.68:
                    dev_matches.append({"test": test["prompt_id"], "dev": dev["prompt_id"], "score": score})
        if dev_matches:
            errors.append(f"{len(dev_matches)} test/dev pair(s) have similarity >= 0.68")

    return {
        "valid": not errors,
        "test_sha256": sha256_file(test_path),
        "rows": len(rows),
        "task_counts": dict(task_counts),
        "matrices": matrices,
        "close_test_pairs": close_pairs,
        "dev_matches": dev_matches,
        "errors": errors,
        "warnings": warnings,
    }


def stable_shuffle(items: Iterable[Any], seed: int) -> list[Any]:
    import random

    result = list(items)
    random.Random(seed).shuffle(result)
    return result
