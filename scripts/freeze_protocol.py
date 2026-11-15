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

FROZEN_STATUS = "frozen_joint_ai_assisted_coordinator_confirmed"


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
    exemptions_path = root / protocol["analysis"]["latin_exemptions_path"]
    exemptions_text = exemptions_path.read_text(encoding="utf-8")
    if "REVIEW_REQUIRED" in exemptions_text:
        errors.append("Latin-script exemption list still requires team review")
    latin_exemptions_sha256 = sha256_file(exemptions_path)
    reference_bundle_sha256 = hashlib.sha256(canonical_json(cards).encode()).hexdigest()
    annotation = protocol.get("annotation", {})
    if annotation.get("mode") != "joint_team_ai_assisted":
        errors.append("annotation mode is not joint_team_ai_assisted")
    if annotation.get("independent_rater_reliability_claimed") is not False:
        errors.append("joint protocol must explicitly disable independent-rater reliability claims")
    authorization_path = root / annotation.get(
        "authorization_path", "protocol/team_authorization.json"
    )
    authorization = {}
    if not authorization_path.exists():
        errors.append("coordinator authorization record is missing")
    else:
        authorization = json.loads(authorization_path.read_text(encoding="utf-8"))
        if authorization.get("record_type") != "coordinator_report_of_instructor_permission":
            errors.append("authorization record type is invalid")
        if authorization.get("reported_by") != "Aldiyar Zhaksylyk":
            errors.append("authorization must identify the reporting coordinator")
        if authorization.get("instructor_permission_reported") is not True:
            errors.append("authorization does not report instructor permission")
        if authorization.get("annotation_mode") != annotation.get("mode"):
            errors.append("authorization and protocol annotation modes differ")

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
    authorization_sha256 = (
        sha256_file(authorization_path) if authorization_path.exists() else None
    )
    protocol_document_hashes = {}
    for relative_path in annotation.get("frozen_documents", []):
        document_path = root / relative_path
        if not document_path.exists():
            errors.append(f"missing frozen protocol document: {relative_path}")
            continue
        protocol_document_hashes[relative_path] = sha256_file(document_path)
    if set(protocol_document_hashes) != set(annotation.get("frozen_documents", [])):
        errors.append("frozen protocol document set is incomplete")

    report = {
        "ready": not errors,
        "validation": validation,
        "test_sha256": validation.get("test_sha256"),
        "instruction_sha256": instruction_sha256,
        "protocol_sha256_before_freeze": sha256_file(protocol_path),
        "reference_card_hashes": cards,
        "reference_bundle_sha256": reference_bundle_sha256,
        "latin_exemptions_sha256": latin_exemptions_sha256,
        "model_artifacts_sha256": model_artifacts_sha256,
        "authorization": authorization,
        "authorization_path": str(authorization_path.relative_to(root)),
        "authorization_sha256": authorization_sha256,
        "protocol_document_hashes": protocol_document_hashes,
        "errors": errors,
    }
    if not args.apply:
        print(json.dumps(report, ensure_ascii=False, indent=2))
        return 0 if report["ready"] else 1
    if errors:
        raise SystemExit("freeze refused:\n- " + "\n- ".join(errors))

    protocol["status"] = FROZEN_STATUS
    protocol["protocol_version"] = "2.1"
    write_json(protocol_path, protocol)
    manifest = {
        **report,
        "frozen_utc": datetime.now(UTC).isoformat(),
        "status": FROZEN_STATUS,
        "protocol_sha256": sha256_file(protocol_path),
    }
    write_json(root / "protocol/freeze_manifest.json", manifest)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
