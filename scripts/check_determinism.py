#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
from datetime import UTC, datetime
from pathlib import Path

from kazllm_eval.core import read_csv, write_json
from kazllm_eval.ollama import api_client, request_payload


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    protocol = json.loads((root / "config/protocol.json").read_text(encoding="utf-8"))
    model = protocol["models"][0]
    prompt = read_csv(root / "data/dev/prompts_dev.csv")[1]
    instruction = (root / "data/instruction.txt").read_text(encoding="utf-8")
    pair = {
        "prompt_id": prompt["prompt_id"],
        "task_type": prompt["task_type"],
        "model_label": model["label"],
        "model": model["ollama_tag"],
        "prompt_text": prompt["prompt_text"],
    }
    payload = request_payload(pair, instruction, protocol)
    client = api_client(protocol["collection"]["endpoint"])
    responses = [client("/api/chat", payload, 1800), client("/api/chat", payload, 1800)]
    texts = [response["message"]["content"] for response in responses]
    hashes = [hashlib.sha256(text.encode()).hexdigest() for text in texts]
    receipt = {
        "purpose": "dev-only repeated-request determinism check",
        "created_utc": datetime.now(UTC).isoformat(),
        "model": model,
        "prompt": prompt,
        "request": payload,
        "response_text_sha256": hashes,
        "exact_text_match": texts[0] == texts[1],
        "response_metadata": [
            {key: response.get(key) for key in ("model", "done", "done_reason", "eval_count")}
            for response in responses
        ],
    }
    write_json(root / "results/raw/determinism_check.json", receipt)
    print(json.dumps({"hashes": hashes, "exact_text_match": receipt["exact_text_match"]}, indent=2))
    return 0 if receipt["exact_text_match"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
