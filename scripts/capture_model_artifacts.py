#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path

from kazllm_eval.core import write_json
from kazllm_eval.ollama import api_client, model_snapshot


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads((root / "config/protocol.json").read_text(encoding="utf-8"))
    snapshot = model_snapshot(protocol, api_client(protocol["collection"]["endpoint"]))
    frozen = {
        "runtime_version": snapshot["runtime_version"],
        "models": snapshot["models"],
        "status": "complete",
    }
    write_json(root / "config/model_artifacts.json", frozen)
    print(json.dumps(frozen, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
