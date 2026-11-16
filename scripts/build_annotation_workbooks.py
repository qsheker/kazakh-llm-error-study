#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from pathlib import Path

from openpyxl import load_workbook

from kazllm_eval.annotation import (
    build_blind_mapping,
    build_blinded_manifest,
    create_rater_workbook,
    load_run_records,
    validate_blinded_manifest,
    write_private_mapping,
)
from kazllm_eval.core import read_csv, sha256_file, write_json

REVIEW_LOG_FIELDS = (
    "blind_id",
    "assigned_reviewer",
    "review_status",
    "reviewer",
    "ai_assistance",
    "reviewed_utc",
    "notes",
)


def validate_existing_workbook_sources(path: Path, manifest: dict) -> None:
    workbook = load_workbook(path, read_only=True, data_only=True)
    if "Responses" not in workbook.sheetnames:
        raise SystemExit(f"existing workbook has no Responses sheet: {path}")
    rows = workbook["Responses"].iter_rows(values_only=True)
    headers = [str(value or "").strip() for value in next(rows)]
    responses = {}
    for values in rows:
        row = dict(zip(headers, values))
        blind_id = str(row.get("blind_id") or "").strip()
        if blind_id:
            if blind_id in responses:
                raise SystemExit(
                    f"existing workbook has duplicate blind ID: {blind_id}"
                )
            responses[blind_id] = {
                **row,
                "response_text": str(row.get("response_text") or ""),
            }
    try:
        validate_blinded_manifest({"responses": responses}, manifest)
    except (KeyError, TypeError, ValueError) as exc:
        raise SystemExit(
            f"existing workbook is not source-bound to this run: {exc}"
        ) from exc


def load_or_create_mapping(path: Path, records: list[dict]) -> list[dict[str, str]]:
    if not path.exists():
        mapping = build_blind_mapping(records)
        write_private_mapping(path, mapping)
        return mapping
    mapping = read_csv(path)
    by_private = {record["private_response_id"]: record for record in records}
    if len(mapping) != len(records) or len(
        {row.get("blind_id") for row in mapping}
    ) != len(records):
        raise SystemExit(
            "existing private mapping has the wrong size or duplicate blind IDs"
        )
    if {row.get("private_response_id") for row in mapping} != set(by_private):
        raise SystemExit(
            "existing private mapping does not cover the immutable run receipts"
        )
    for row in mapping:
        record = by_private[row["private_response_id"]]
        if any(
            row.get(field) != record[field]
            for field in ("prompt_id", "model_label", "response_sha256")
        ):
            raise SystemExit(
                f"existing private mapping differs from receipt {row['private_response_id']}"
            )
    return mapping


def load_or_create_review_log(
    path: Path,
    mapping: list[dict[str, str]],
    reviewers: list[str],
) -> tuple[list[dict[str, str]], Counter[str]]:
    if not reviewers or len(set(reviewers)) != len(reviewers):
        raise SystemExit("protocol team must contain distinct named reviewers")
    blind_ids = sorted(row["blind_id"] for row in mapping)
    if len(blind_ids) % len(reviewers):
        raise SystemExit(
            "blind IDs cannot be divided equally among the named reviewers"
        )
    if path.exists():
        rows = read_csv(path)
        if not rows or tuple(rows[0]) != REVIEW_LOG_FIELDS:
            raise SystemExit("existing team review log has an unexpected schema")
        if len(rows) != len(blind_ids) or {row["blind_id"] for row in rows} != set(
            blind_ids
        ):
            raise SystemExit(
                "existing team review log does not cover every blind ID exactly once"
            )
        assignments = Counter(row["assigned_reviewer"] for row in rows)
        expected = len(blind_ids) // len(reviewers)
        if set(assignments) != set(reviewers) or set(assignments.values()) != {
            expected
        }:
            raise SystemExit(
                "existing team review assignments are not equally balanced"
            )
        return rows, assignments

    rows = [
        {
            "blind_id": blind_id,
            "assigned_reviewer": reviewers[index % len(reviewers)],
            "review_status": "pending",
            "reviewer": "",
            "ai_assistance": "",
            "reviewed_utc": "",
            "notes": "",
        }
        for index, blind_id in enumerate(blind_ids)
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    with temporary.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=REVIEW_LOG_FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    temporary.replace(path)
    return rows, Counter(row["assigned_reviewer"] for row in rows)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create one blinded joint-team annotation workbook."
    )
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, default=Path("annotations"))
    parser.add_argument("--references", type=Path, default=Path("data/references"))
    parser.add_argument(
        "--mapping", type=Path, default=Path("data/blinding/private_model_key.csv")
    )
    parser.add_argument(
        "--review-log",
        type=Path,
        default=Path("annotations/team_gold/team_review_log.csv"),
    )
    parser.add_argument(
        "--blinded-manifest",
        type=Path,
        help="Public read-only-field integrity manifest (default: OUTPUT/RUN__blinded_manifest.json)",
    )
    args = parser.parse_args()

    records = load_run_records(args.run_dir)
    mapping = load_or_create_mapping(args.mapping, records)
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads((root / "config/protocol.json").read_text(encoding="utf-8"))
    _, assignments = load_or_create_review_log(
        args.review_log, mapping, protocol["team"]
    )
    manifest_path = (
        args.blinded_manifest
        or args.output / f"{args.run_dir.name}__blinded_manifest.json"
    )
    manifest = build_blinded_manifest(records, mapping, args.references)
    write_json(manifest_path, manifest)
    path = args.output / "team_gold" / f"{args.run_dir.name}__team_gold.xlsx"
    if path.exists():
        validate_existing_workbook_sources(path, manifest)
        sha256 = sha256_file(path)
        workbook_status = "preserved_existing"
    else:
        sha256 = create_rater_workbook(
            path,
            records,
            mapping,
            args.references,
            241701,
            workflow="joint_team_ai_assisted",
        )
        workbook_status = "created"
    print(
        json.dumps(
            {
                "annotation_mode": "joint_team_ai_assisted",
                "blinded_manifest": str(manifest_path),
                "workbook": {
                    "path": str(path),
                    "sha256": sha256,
                    "status": workbook_status,
                },
                "review_log": {
                    "path": str(args.review_log),
                    "status": "pending",
                    "assignments": dict(assignments),
                },
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
