#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from kazllm_eval.annotation import (
    build_blind_mapping,
    build_blinded_manifest,
    create_rater_workbook,
    load_run_records,
    write_private_mapping,
)
from kazllm_eval.core import write_json


def main() -> int:
    parser = argparse.ArgumentParser(description="Create two independently ordered blinded annotation workbooks.")
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--output", type=Path, default=Path("annotations"))
    parser.add_argument("--references", type=Path, default=Path("data/references"))
    parser.add_argument("--mapping", type=Path, default=Path("data/blinding/private_model_key.csv"))
    parser.add_argument(
        "--blinded-manifest",
        type=Path,
        help="Public read-only-field integrity manifest (default: OUTPUT/RUN__blinded_manifest.json)",
    )
    args = parser.parse_args()

    records = load_run_records(args.run_dir)
    mapping = build_blind_mapping(records)
    write_private_mapping(args.mapping, mapping)
    manifest_path = args.blinded_manifest or args.output / f"{args.run_dir.name}__blinded_manifest.json"
    write_json(manifest_path, build_blinded_manifest(records, mapping, args.references))
    outputs = {}
    for rater, seed in (("rater_1", 241701), ("rater_2", 241702)):
        path = args.output / rater / f"{args.run_dir.name}__{rater}.xlsx"
        outputs[rater] = {"path": str(path), "sha256": create_rater_workbook(path, records, mapping, args.references, seed)}
    print(json.dumps({"blinded_manifest": str(manifest_path), "workbooks": outputs}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
