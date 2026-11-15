from __future__ import annotations

import csv
import hashlib
import json
import secrets
from pathlib import Path
from typing import Any

from openpyxl import Workbook
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.worksheet.datavalidation import DataValidation

from .core import read_csv, stable_shuffle, word_tokens

EVENT_CATEGORIES = ("grammatical", "lexical", "semantic", "code_switching", "surface")
YES_NO_UNKNOWN = ("yes", "no", "needs_adjudication")


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
