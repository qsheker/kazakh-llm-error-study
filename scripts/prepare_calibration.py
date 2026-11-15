#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import secrets
from collections import Counter
from pathlib import Path

from kazllm_eval.annotation import load_run_records
from kazllm_eval.core import stable_shuffle, write_json


def select_phase(
    records: list[dict],
    used: set[str],
    per_model_task: dict[str, tuple[int, int]],
    seed: int,
) -> list[dict]:
    selected = []
    for model_label, (edu_count, public_count) in per_model_task.items():
        for task_type, count in (("edu", edu_count), ("public", public_count)):
            candidates = [
                record
                for record in records
                if record["model_label"] == model_label
                and record["task_type"] == task_type
                and record["private_response_id"] not in used
            ]
            candidates = stable_shuffle(candidates, seed + len(selected))
            if len(candidates) < count:
                raise ValueError(f"not enough unused {model_label}/{task_type} responses")
            chosen = candidates[:count]
            selected.extend(chosen)
            used.update(record["private_response_id"] for record in chosen)
    return stable_shuffle(selected, seed)


def main() -> int:
    parser = argparse.ArgumentParser(description="Select and blind dev responses for calibration.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--references", type=Path, default=Path("data/dev/references"))
    parser.add_argument(
        "--mapping", type=Path, default=Path("data/blinding/dev_calibration_v2_key.csv")
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    run_dir = args.run_dir.resolve()
    try:
        records = load_run_records(run_dir)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        raise SystemExit(f"calibration run is incomplete or invalid: {exc}") from exc
    if len(records) != 80:
        raise SystemExit(f"calibration run must contain exactly 80 receipts; found {len(records)}")

    model_labels = ["qwen3_8b", "llama31_8b", "gemma3_12b", "kazllm_8b"]
    if Counter(record["model_label"] for record in records) != Counter({label: 20 for label in model_labels}):
        raise SystemExit("calibration run is not balanced at 20 responses per model")

    used: set[str] = set()
    training_targets = {
        "qwen3_8b": (2, 1),
        "llama31_8b": (1, 2),
        "gemma3_12b": (2, 1),
        "kazllm_8b": (1, 2),
    }
    qualification_targets = {
        "qwen3_8b": (2, 3),
        "llama31_8b": (3, 2),
        "gemma3_12b": (2, 3),
        "kazllm_8b": (3, 2),
    }
    phases = {
        "training": select_phase(records, used, training_targets, 241711),
        "qualification": select_phase(records, used, qualification_targets, 241721),
    }

    mapping_path = (root / args.mapping).resolve() if not args.mapping.is_absolute() else args.mapping
    if mapping_path.exists() or args.output.exists():
        raise SystemExit("calibration outputs already exist; preserve them and choose a new output path")

    blind_by_private = {
        record["private_response_id"]: "C-" + secrets.token_hex(8).upper()
        for phase_records in phases.values()
        for record in phase_records
    }
    mapping_path.parent.mkdir(parents=True, exist_ok=True)
    with mapping_path.open("w", encoding="utf-8", newline="") as stream:
        fields = ["phase", "blind_id", "private_response_id", "prompt_id", "model_label", "response_sha256"]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for phase, phase_records in phases.items():
            for record in phase_records:
                writer.writerow(
                    {
                        "phase": phase,
                        "blind_id": blind_by_private[record["private_response_id"]],
                        "private_response_id": record["private_response_id"],
                        "prompt_id": record["prompt_id"],
                        "model_label": record["model_label"],
                        "response_sha256": record["response_sha256"],
                    }
                )

    reference_dir = (root / args.references).resolve() if not args.references.is_absolute() else args.references
    mapping_sha256 = hashlib.sha256(mapping_path.read_bytes()).hexdigest()
    bundle = {
        "run_id": run_dir.name,
        "private_mapping_sha256": mapping_sha256,
        "phases": {},
    }
    for phase, phase_records in phases.items():
        bundle["phases"][phase] = {}
        for rater, seed in (("rater_1", 241731), ("rater_2", 241741)):
            ordered = stable_shuffle(phase_records, seed + (0 if phase == "training" else 1))
            bundle["phases"][phase][rater] = [
                {
                    "blind_id": blind_by_private[record["private_response_id"]],
                    "prompt_id": record["prompt_id"],
                    "task_type": record["task_type"],
                    "prompt_text": record["prompt_text"],
                    "response_text": record["response_text"],
                    "reference_or_constraint_card": (
                        reference_dir / f"{record['prompt_id']}.md"
                    ).read_text(encoding="utf-8"),
                    "word_count_read_only": record["word_count"],
                    "finish_reason_read_only": record["finish_reason"],
                    "response_sha256": record["response_sha256"],
                }
                for record in ordered
            ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    write_json(args.output, bundle)
    summary = {
        phase: {
            "responses": len(phase_records),
            "task_counts": dict(Counter(record["task_type"] for record in phase_records)),
            "model_counts_private": dict(Counter(record["model_label"] for record in phase_records)),
        }
        for phase, phase_records in phases.items()
    }
    print(
        json.dumps(
            {
                "bundle": str(args.output),
                "bundle_sha256": hashlib.sha256(args.output.read_bytes()).hexdigest(),
                "mapping": str(mapping_path),
                "mapping_sha256": mapping_sha256,
                "selection": summary,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
