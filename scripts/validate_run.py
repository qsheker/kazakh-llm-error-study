#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

from kazllm_eval.core import canonical_json, sha256_file


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_identity(snapshot: dict) -> dict:
    return {key: value for key, value in snapshot.items() if key != "captured_utc"}


def validate_incidents(
    run_dir: Path, receipts: dict[tuple[str, str], dict]
) -> tuple[int, list[str]]:
    incident_dir = run_dir / "incidents"
    if not incident_dir.exists():
        return 0, []
    errors: list[str] = []
    incident_paths = sorted(incident_dir.glob("*.json"))
    evidence_paths = set(incident_dir.glob("*.original.inflight"))
    referenced_evidence: set[Path] = set()
    for path in incident_paths:
        incident = load_json(path)
        pair = (
            str(incident.get("prompt_id") or ""),
            str(incident.get("model_label") or ""),
        )
        receipt = receipts.get(pair)
        if receipt is None:
            errors.append(f"incident {path.name} has no matching receipt")
            continue
        expected_request_hash = hashlib.sha256(
            canonical_json(receipt.get("request", {})).encode("utf-8")
        ).hexdigest()
        if incident.get("request_sha256") != expected_request_hash:
            errors.append(f"incident request hash mismatch {path.name}")
        candidates = list(
            incident_dir.glob(f"*_{pair[0]}__{pair[1]}.original.inflight")
        )
        if len(candidates) != 1:
            errors.append(
                f"incident {path.name} has {len(candidates)} original inflight records"
            )
        else:
            evidence_path = candidates[0]
            referenced_evidence.add(evidence_path)
            if sha256_file(evidence_path) != incident.get("original_inflight_sha256"):
                errors.append(f"incident inflight hash mismatch {path.name}")
        if incident.get("response_observed") is not False:
            errors.append(
                f"incident {path.name} does not confirm response_observed=false"
            )
        if (
            incident.get("failure_class")
            != "explicit_infrastructure_failure_before_generation"
        ):
            errors.append(f"incident {path.name} has unsupported failure_class")
        if not str(incident.get("server_evidence") or "").strip():
            errors.append(f"incident {path.name} lacks server evidence")
        if not str(incident.get("resolution") or "").strip():
            errors.append(f"incident {path.name} lacks a resolution record")
    for path in sorted(evidence_paths - referenced_evidence):
        errors.append(f"unreferenced incident evidence {path.name}")
    return len(incident_paths), errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Audit an immutable Ollama collection run."
    )
    parser.add_argument("run_dir", type=Path)
    parser.add_argument("--expected", type=int, required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    run_dir = args.run_dir.resolve()
    try:
        run_dir.relative_to(root / "runs")
    except ValueError as exc:
        raise SystemExit(f"run directory must be inside {root / 'runs'}") from exc

    manifest = load_json(run_dir / "manifest.json")
    completion = load_json(run_dir / "completion.json")
    errors = []
    order = manifest.get("request_order", [])
    if len(order) != args.expected:
        errors.append(f"manifest requests={len(order)}, expected={args.expected}")
    expected_pairs = {
        (row["prompt_id"], row["model_label"]): row["model"] for row in order
    }
    if len(expected_pairs) != len(order):
        errors.append("manifest contains duplicate prompt/model-label pairs")

    for key in ("protocol_path", "prompt_path", "instruction_path"):
        value = Path(manifest.get(key, ""))
        if value.is_absolute() or ".." in value.parts:
            errors.append(f"{key} is not repository-relative")
    for key, hash_key in (
        ("prompt_path", "prompt_sha256"),
        ("instruction_path", "instruction_sha256"),
    ):
        path = root / manifest[key]
        if not path.exists() or sha256_file(path) != manifest.get(hash_key):
            errors.append(f"{key} no longer matches its manifest hash")

    receipt_paths = sorted((run_dir / "receipts").glob("*.json"))
    actual_pairs = set()
    receipts_by_pair: dict[tuple[str, str], dict] = {}
    options = []
    for path in receipt_paths:
        receipt = load_json(path)
        pair = (receipt.get("prompt_id"), receipt.get("model_label"))
        if pair in actual_pairs:
            errors.append(f"duplicate receipt pair {pair}")
        actual_pairs.add(pair)
        receipts_by_pair[pair] = receipt
        if pair not in expected_pairs:
            errors.append(f"unexpected receipt pair {pair}")
            continue
        response = receipt.get("response", {})
        request = receipt.get("request", {})
        text = response.get("message", {}).get("content")
        if response.get("done") is not True or not isinstance(text, str):
            errors.append(f"incomplete response {path.name}")
            continue
        if (
            request.get("model") != expected_pairs[pair]
            or response.get("model") != expected_pairs[pair]
        ):
            errors.append(f"model mismatch {path.name}")
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if digest != receipt.get("response_text_sha256"):
            errors.append(f"response hash mismatch {path.name}")
        if not isinstance(receipt.get("client_latency_ms"), (int, float)):
            errors.append(f"missing client latency {path.name}")
        options.append(canonical_json(request.get("options", {})))
    if actual_pairs != set(expected_pairs):
        errors.append(
            f"receipt pair coverage differs: missing={len(set(expected_pairs) - actual_pairs)}, "
            f"extra={len(actual_pairs - set(expected_pairs))}"
        )
    if len(set(options)) != 1:
        errors.append("request generation options are not identical across receipts")
    inflight = list((run_dir / "receipts").glob("*.inflight"))
    if inflight:
        errors.append(f"unresolved inflight markers={len(inflight)}")
    incident_count, incident_errors = validate_incidents(run_dir, receipts_by_pair)
    errors.extend(incident_errors)

    accounted = int(completion.get("received", 0)) + int(completion.get("reused", 0))
    if accounted != args.expected or len(receipt_paths) != args.expected:
        errors.append(
            f"accounting mismatch: completion={accounted}, receipts={len(receipt_paths)}, "
            f"expected={args.expected}"
        )
    if completion.get("metadata_unchanged") is not True:
        errors.append("completion does not confirm unchanged model metadata")
    before = snapshot_identity(manifest.get("model_snapshot", {}))
    after = snapshot_identity(completion.get("after", {}))
    if canonical_json(before) != canonical_json(after):
        errors.append("before/after model snapshots differ")

    report = {
        "valid": not errors,
        "run": str(run_dir.relative_to(root)),
        "requests": len(order),
        "receipts": len(receipt_paths),
        "accounted": accounted,
        "incidents": incident_count,
        "generation_options_identical": len(set(options)) == 1,
        "metadata_unchanged": completion.get("metadata_unchanged"),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
