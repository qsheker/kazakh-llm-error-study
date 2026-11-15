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


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit an immutable Ollama collection run.")
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
    expected_pairs = {(row["prompt_id"], row["model_label"]): row["model"] for row in order}
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
    options = []
    for path in receipt_paths:
        receipt = load_json(path)
        pair = (receipt.get("prompt_id"), receipt.get("model_label"))
        if pair in actual_pairs:
            errors.append(f"duplicate receipt pair {pair}")
        actual_pairs.add(pair)
        if pair not in expected_pairs:
            errors.append(f"unexpected receipt pair {pair}")
            continue
        response = receipt.get("response", {})
        request = receipt.get("request", {})
        text = response.get("message", {}).get("content")
        if response.get("done") is not True or not isinstance(text, str):
            errors.append(f"incomplete response {path.name}")
            continue
        if request.get("model") != expected_pairs[pair] or response.get("model") != expected_pairs[pair]:
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
    inflight = list((run_dir / "inflight").glob("*.json"))
    if inflight:
        errors.append(f"unresolved inflight markers={len(inflight)}")

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
        "generation_options_identical": len(set(options)) == 1,
        "metadata_unchanged": completion.get("metadata_unchanged"),
        "errors": errors,
    }
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
