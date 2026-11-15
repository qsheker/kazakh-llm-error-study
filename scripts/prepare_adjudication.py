#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path

from kazllm_eval.annotation import (
    RESPONSE_FLAGS,
    annotation_agreement,
    load_annotation_workbook,
)
from kazllm_eval.core import write_json


def write_csv(path: Path, headers: list[str], rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as stream:
        writer = csv.DictWriter(stream, fieldnames=headers, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a blinded adjudication package from two immutable originals.")
    parser.add_argument("rater_1", type=Path)
    parser.add_argument("rater_2", type=Path)
    parser.add_argument("--output", type=Path, default=Path("annotations/adjudication"))
    parser.add_argument("--expected-responses", type=int, required=True)
    args = parser.parse_args()
    if args.output.exists() and any(args.output.iterdir()):
        raise SystemExit(f"refused: output directory is not empty: {args.output}")

    left = load_annotation_workbook(args.rater_1, args.expected_responses)
    right = load_annotation_workbook(args.rater_2, args.expected_responses)
    if left["sha256"] == right["sha256"]:
        raise SystemExit("refused: rater workbooks have identical hashes")
    agreement = annotation_agreement(left, right)
    args.output.mkdir(parents=True, exist_ok=True)
    write_json(args.output / "agreement.json", agreement)
    write_json(
        args.output / "manifest.json",
        {"rater_1_sha256": left["sha256"], "rater_2_sha256": right["sha256"], "blinded": True},
    )

    disagreements = []
    log_rows = []
    for blind_id in sorted(left["responses"]):
        for flag in RESPONSE_FLAGS:
            value_1 = left["responses"][blind_id][flag]
            value_2 = right["responses"][blind_id][flag]
            if value_1 != value_2:
                row = {"blind_id": blind_id, "scope": "response", "field": flag, "rater_1": value_1, "rater_2": value_2}
                disagreements.append(row)
                log_rows.append({**row, "final_value": "", "rationale": "", "adjudicator": ""})
    write_csv(
        args.output / "response_disagreements.csv",
        ["blind_id", "scope", "field", "rater_1", "rater_2"],
        disagreements,
    )
    event_headers = [
        "blind_id", "event_id", "category", "exact_fragment", "start_offset_zero_based",
        "end_offset_exclusive", "start_token_one_based", "end_token_one_based",
        "proposed_correction", "rationale", "source", "needs_adjudication",
    ]
    write_csv(args.output / "events_rater_1.csv", event_headers, left["events"])
    write_csv(args.output / "events_rater_2.csv", event_headers, right["events"])
    write_csv(
        args.output / "adjudication_log_template.csv",
        ["blind_id", "scope", "field", "rater_1", "rater_2", "final_value", "rationale", "adjudicator"],
        log_rows,
    )
    print(json.dumps({"output": str(args.output), "agreement": agreement}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
