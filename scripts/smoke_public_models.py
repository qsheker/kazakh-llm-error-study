#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import time
from datetime import datetime, timezone
from pathlib import Path

from kazllm_eval.core import read_csv, word_tokens, write_json
from kazllm_eval.ollama import api_client, model_snapshot, request_payload


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads((root / "config/protocol.json").read_text(encoding="utf-8"))
    public_protocol = {**protocol, "models": protocol["models"][:3]}
    prompt = read_csv(root / "data/dev/prompts_dev.csv")[0]
    instruction = (root / "data/instruction.txt").read_text(encoding="utf-8")
    client = api_client(protocol["collection"]["endpoint"])
    snapshot = model_snapshot(public_protocol, client)
    outputs = []
    for model in public_protocol["models"]:
        pair = {
            "prompt_id": prompt["prompt_id"],
            "task_type": prompt["task_type"],
            "model_label": model["label"],
            "model": model["ollama_tag"],
            "prompt_text": prompt["prompt_text"],
        }
        payload = request_payload(pair, instruction, protocol)
        started = time.perf_counter()
        response = client("/api/chat", payload, 1800)
        elapsed = (time.perf_counter() - started) * 1000
        text = response.get("message", {}).get("content")
        if not response.get("done") or not isinstance(text, str):
            raise RuntimeError(f"smoke response incomplete for {model['ollama_tag']}")
        outputs.append(
            {
                "model_label": model["label"],
                "model": model["ollama_tag"],
                "request": payload,
                "response": response,
                "response_text_sha256": hashlib.sha256(text.encode()).hexdigest(),
                "word_count": len(word_tokens(text)),
                "client_latency_ms": elapsed,
            }
        )
        print(model["ollama_tag"], len(word_tokens(text)), response.get("done_reason"), flush=True)
    receipt = {
        "purpose": "technical dev-only smoke test; excluded from final results and calibration unless separately selected",
        "created_utc": datetime.now(timezone.utc).isoformat(),
        "prompt": prompt,
        "snapshot": snapshot,
        "outputs": outputs,
    }
    write_json(root / "results/raw/public_model_smoke.json", receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
