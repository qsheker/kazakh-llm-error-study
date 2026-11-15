#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from kazllm_eval.core import (
    canonical_json,
    read_csv,
    sha256_file,
    validate_test_prompts,
    write_json,
)

SIGNERS = {
    "aldiyar": "Aldiyar Zhaksylyk",
    "yerkebulan": "Yerkebulan Rakhymbay",
    "iliyas": "Iliyas Aitzhan",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Create one reviewer's protocol sign-off after personal review.")
    parser.add_argument("--signer", required=True, choices=sorted(SIGNERS))
    parser.add_argument("--approve", action="store_true", help="confirm that this signer personally reviewed every card")
    parser.add_argument("--notes", required=True, help="review notes in the signer's own words")
    args = parser.parse_args()
    if not args.approve:
        raise SystemExit("refused: --approve is required and may only be used by the named reviewer")

    root = Path(__file__).resolve().parents[1]
    protocol = json.loads((root / "config/protocol.json").read_text(encoding="utf-8"))
    test_path = root / protocol["dataset"]["test_path"]
    dev_path = root / protocol["dataset"]["dev_path"]
    instruction_path = root / protocol["dataset"]["instruction_path"]
    validation = validate_test_prompts(test_path, dev_path)
    if not validation["valid"]:
        raise SystemExit("refused: test prompt validation failed")

    card_hashes = {}
    for row in read_csv(test_path):
        card_path = root / "data/references" / f"{row['prompt_id']}.md"
        text = card_path.read_text(encoding="utf-8")
        if "READY_FOR_THREE_PERSON_REVIEW" not in text:
            raise SystemExit(f"refused: unexpected card status for {row['prompt_id']}")
        card_hashes[row["prompt_id"]] = sha256_file(card_path)

    record = {
        "name": SIGNERS[args.signer],
        "decision": "approved",
        "reviewed_utc": datetime.now(UTC).isoformat(),
        "test_sha256": validation["test_sha256"],
        "instruction_sha256": sha256_file(instruction_path),
        "reference_bundle_sha256": hashlib.sha256(canonical_json(card_hashes).encode()).hexdigest(),
        "model_artifacts_sha256": sha256_file(root / "config/model_artifacts.json"),
        "review_notes": args.notes.strip(),
    }
    output = root / "protocol/signoffs" / f"{args.signer}.json"
    if output.exists():
        raise SystemExit(f"refused: sign-off already exists: {output}")
    write_json(output, record)
    print(json.dumps(record, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
