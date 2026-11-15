#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from kazllm_eval.core import canonical_json, read_csv, sha256_file, validate_test_prompts, write_json

EXPECTED_SIGNERS = {
    "aldiyar": "Aldiyar Zhaksylyk",
    "yerkebulan": "Yerkebulan Rakhymbay",
    "iliyas": "Iliyas Aitzhan",
}


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate all freeze prerequisites and create an immutable manifest.")
    parser.add_argument("--apply", action="store_true", help="write the freeze manifest and update protocol status")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    protocol_path = root / "config/protocol.json"
    protocol = json.loads(protocol_path.read_text(encoding="utf-8"))
    test_path = root / protocol["dataset"]["test_path"]
    dev_path = root / protocol["dataset"]["dev_path"]
    instruction_path = root / protocol["dataset"]["instruction_path"]
    validation = validate_test_prompts(test_path, dev_path)
    errors = list(validation["errors"])

    cards = {}
    for row in read_csv(test_path):
        path = root / "data/references" / f"{row['prompt_id']}.md"
        if not path.exists():
            errors.append(f"missing reference card: {path}")
            continue
        text = path.read_text(encoding="utf-8")
        if "PENDING" in text:
            errors.append(f"reference card is still pending: {row['prompt_id']}")
        cards[row["prompt_id"]] = sha256_file(path)

    instruction_sha256 = sha256_file(instruction_path)
    reference_bundle_sha256 = hashlib.sha256(canonical_json(cards).encode()).hexdigest()
    signoffs = {}
    for slug, expected_name in EXPECTED_SIGNERS.items():
        path = root / "protocol/signoffs" / f"{slug}.json"
        if not path.exists():
            errors.append(f"missing sign-off: {expected_name}")
            continue
        record = json.loads(path.read_text(encoding="utf-8"))
        if record.get("name") != expected_name or record.get("decision") != "approved":
            errors.append(f"invalid sign-off for {expected_name}")
        if record.get("test_sha256") != validation.get("test_sha256"):
            errors.append(f"{expected_name} signed a different test-set hash")
        if record.get("instruction_sha256") != instruction_sha256:
            errors.append(f"{expected_name} signed a different instruction hash")
        if record.get("reference_bundle_sha256") != reference_bundle_sha256:
            errors.append(f"{expected_name} signed a different reference-card bundle")
        signoffs[slug] = record

    source = json.loads((root / "models/kazllm/source.json").read_text(encoding="utf-8"))
    if not source.get("expected_sha256"):
        errors.append("KazLLM official GGUF SHA-256 has not been frozen")
    model_artifacts_path = root / "config/model_artifacts.json"
    model_artifacts = json.loads(model_artifacts_path.read_text(encoding="utf-8"))
    required_tags = {model["ollama_tag"] for model in protocol["models"]}
    if set(model_artifacts.get("models", {})) != required_tags:
        errors.append("model_artifacts.json does not contain exactly the four protocol tags")
    if any(model_artifacts.get("models", {}).get(tag) is None for tag in required_tags):
        errors.append("one or more exact model artifacts are still pending")
    if model_artifacts.get("status") != "complete":
        errors.append("model_artifacts.json status is not complete")
    model_artifacts_sha256 = sha256_file(model_artifacts_path)
    for slug, record in signoffs.items():
        if record.get("model_artifacts_sha256") != model_artifacts_sha256:
            errors.append(f"{EXPECTED_SIGNERS[slug]} signed a different model-artifact manifest")

    report = {
        "ready": not errors,
        "validation": validation,
        "test_sha256": validation.get("test_sha256"),
        "instruction_sha256": instruction_sha256,
        "protocol_sha256_before_freeze": sha256_file(protocol_path),
        "reference_card_hashes": cards,
        "reference_bundle_sha256": reference_bundle_sha256,
        "model_artifacts_sha256": model_artifacts_sha256,
        "signoffs": signoffs,
        "errors": errors,
    }
    if not args.apply:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ready"] else 1
    if errors:
        raise SystemExit("freeze refused:\n- " + "\n- ".join(errors))

    protocol["status"] = "frozen_three_person_signoff"
    protocol["protocol_version"] = "2.0"
    write_json(protocol_path, protocol)
    manifest = {
        **report,
        "frozen_utc": datetime.now(timezone.utc).isoformat(),
        "status": "frozen_three_person_signoff",
        "protocol_sha256": sha256_file(protocol_path),
    }
    write_json(root / "protocol/freeze_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
