#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

from kazllm_eval.core import canonical_json, read_csv, sha256_file, validate_test_prompts, write_json
from kazllm_eval.ollama import (
    api_client,
    build_manifest,
    build_pairs,
    collect_one,
    model_snapshot,
    request_payload,
)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def snapshot_identity(snapshot):
    return {key: value for key, value in snapshot.items() if key != "captured_utc"}


def verify_test_freeze(root: Path, protocol: dict, prompt_path: Path, instruction_path: Path) -> None:
    manifest_path = root / "protocol/freeze_manifest.json"
    if not manifest_path.exists():
        raise SystemExit("test collection is locked: protocol/freeze_manifest.json is missing")
    manifest = load_json(manifest_path)
    failures = []
    if manifest.get("status") != "frozen_three_person_signoff":
        failures.append("freeze status is not frozen_three_person_signoff")
    if manifest.get("test_sha256") != sha256_file(prompt_path):
        failures.append("test CSV differs from the frozen hash")
    if manifest.get("instruction_sha256") != sha256_file(instruction_path):
        failures.append("instruction differs from the frozen hash")
    if manifest.get("protocol_sha256") != sha256_file(root / "config/protocol.json"):
        failures.append("protocol config differs from the frozen hash")
    if manifest.get("model_artifacts_sha256") != sha256_file(root / "config/model_artifacts.json"):
        failures.append("model artifact manifest differs from the frozen hash")
    card_hashes = manifest.get("reference_card_hashes", {})
    for prompt_id, expected in card_hashes.items():
        path = root / "data/references" / f"{prompt_id}.md"
        if not path.exists() or sha256_file(path) != expected:
            failures.append(f"reference card differs from freeze: {prompt_id}")
    if set(manifest.get("signoffs", {})) != {"aldiyar", "yerkebulan", "iliyas"}:
        failures.append("all three sign-offs are not present")
    if failures:
        raise SystemExit("test collection is locked: " + "; ".join(failures))


def main() -> int:
    parser = argparse.ArgumentParser(description="Plan, preflight, or execute a local Ollama collection.")
    parser.add_argument("--dataset", choices=("dev", "test"), default="dev")
    parser.add_argument("--preflight", action="store_true")
    parser.add_argument("--send", action="store_true")
    parser.add_argument("--run-id")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    protocol_path = root / "config/protocol.json"
    protocol = load_json(protocol_path)
    prompt_path = root / protocol["dataset"][f"{args.dataset}_path"]
    instruction_path = root / protocol["dataset"]["instruction_path"]
    prompts = read_csv(prompt_path)
    instruction = instruction_path.read_text(encoding="utf-8")
    pairs = build_pairs(prompts, protocol)

    if args.dataset == "test":
        validation = validate_test_prompts(
            prompt_path, root / protocol["dataset"]["dev_path"]
        )
        if not validation["valid"]:
            raise SystemExit("test prompt validation failed: " + "; ".join(validation["errors"]))
        if args.send and protocol.get("status") != "frozen_three_person_signoff":
            raise SystemExit("test collection is locked until protocol status is frozen_three_person_signoff")
        if args.send:
            verify_test_freeze(root, protocol, prompt_path, instruction_path)

    plan = {
        "mode": "plan",
        "dataset": args.dataset,
        "requests": len(pairs),
        "models": [model["ollama_tag"] for model in protocol["models"]],
        "generation": protocol["generation"],
        "order_seed": protocol["request_order_seed"],
    }
    if not (args.preflight or args.send):
        print(json.dumps(plan, ensure_ascii=False, indent=2))
        return 0

    client = api_client(protocol["collection"]["endpoint"])
    try:
        before = model_snapshot(protocol, client)
    except RuntimeError as exc:
        raise SystemExit(f"preflight failed: {exc}") from exc
    if args.dataset == "test" and args.send:
        frozen_models = load_json(root / "config/model_artifacts.json")
        if canonical_json(snapshot_identity(before)) != canonical_json(
            {"runtime_version": frozen_models["runtime_version"], "models": frozen_models["models"]}
        ):
            raise SystemExit("test collection is locked: installed model metadata differs from model_artifacts.json")
    if not args.send:
        print(json.dumps(before, ensure_ascii=False, indent=2))
        return 0
    if not args.run_id or not re.fullmatch(r"[A-Za-z0-9_-]{1,50}", args.run_id):
        parser.error("--send requires --run-id with only letters, digits, underscore, or hyphen")

    run_dir = root / "runs" / args.run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    manifest = build_manifest(protocol_path, prompt_path, instruction_path, before, pairs)
    manifest_path = run_dir / "manifest.json"
    if manifest_path.exists():
        existing = load_json(manifest_path)
        comparable_existing = {k: v for k, v in existing.items() if k != "created_utc"}
        comparable_new = {k: v for k, v in manifest.items() if k != "created_utc"}
        comparable_existing["model_snapshot"] = snapshot_identity(comparable_existing["model_snapshot"])
        comparable_new["model_snapshot"] = snapshot_identity(comparable_new["model_snapshot"])
        if canonical_json(comparable_existing) != canonical_json(comparable_new):
            raise RuntimeError("run manifest differs; choose a new run ID")
    else:
        write_json(manifest_path, manifest)

    counters = {"received": 0, "reused": 0}
    for index, pair in enumerate(pairs, start=1):
        status = collect_one(run_dir, pair, request_payload(pair, instruction, protocol), client)
        counters[status] += 1
        print(f"{index}/{len(pairs)} {pair['prompt_id']} {pair['model_label']} {status}", flush=True)
    after = model_snapshot(protocol, client)
    before_comparable = snapshot_identity(before)
    after_comparable = snapshot_identity(after)
    unchanged = canonical_json(before_comparable) == canonical_json(after_comparable)
    write_json(run_dir / "completion.json", {**counters, "metadata_unchanged": unchanged, "after": after})
    if not unchanged:
        raise RuntimeError("model metadata changed during collection")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
