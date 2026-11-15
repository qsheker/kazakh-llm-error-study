#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from kazllm_eval.core import write_json
from kazllm_eval.ollama import normalize_manifest_paths


def main() -> int:
    parser = argparse.ArgumentParser(description="Replace private absolute paths in a run manifest.")
    parser.add_argument("run_dir", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    manifest_path = args.run_dir.resolve() / "manifest.json"
    try:
        manifest_path.relative_to(root / "runs")
    except ValueError as exc:
        raise SystemExit(f"run directory must be inside {root / 'runs'}") from exc
    if not manifest_path.exists():
        raise SystemExit(f"missing manifest: {manifest_path}")

    original = json.loads(manifest_path.read_text(encoding="utf-8"))
    normalized = normalize_manifest_paths(original, root)
    write_json(manifest_path, normalized)
    print(manifest_path.relative_to(root))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
