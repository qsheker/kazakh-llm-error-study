from __future__ import annotations

import hashlib
import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .core import canonical_json, read_csv, sha256_file, stable_shuffle, write_json

Client = Callable[[str, dict[str, Any] | None, int], dict[str, Any]]


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def api_client(base_url: str) -> Client:
    def call(path: str, payload: dict[str, Any] | None = None, timeout: int = 30) -> dict[str, Any]:
        body = None if payload is None else json.dumps(payload, ensure_ascii=False).encode("utf-8")
        request = urllib.request.Request(
            base_url.rstrip("/") + path,
            data=body,
            headers={"Content-Type": "application/json"},
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                return json.load(response)
        except urllib.error.URLError as exc:
            raise RuntimeError(f"Ollama request failed for {path}: {exc}") from exc

    return call


def model_snapshot(protocol: dict[str, Any], client: Client) -> dict[str, Any]:
    tags = client("/api/tags", None, 30).get("models", [])
    version = client("/api/version", None, 30).get("version")
    snapshot: dict[str, Any] = {"runtime_version": version, "captured_utc": utc_now(), "models": {}}
    for model in protocol["models"]:
        tag = model["ollama_tag"]
        found = next((item for item in tags if item.get("name") == tag or item.get("model") == tag), None)
        if found is None:
            raise RuntimeError(f"required model is not installed: {tag}")
        info = client("/api/show", {"model": tag}, 60)
        digest = found.get("digest")
        if not digest:
            raise RuntimeError(f"Ollama did not report a digest for {tag}")
        details = found.get("details", {})
        expected_quantization = model.get("quantization")
        observed_quantization = details.get("quantization_level")
        if expected_quantization and observed_quantization != expected_quantization:
            raise RuntimeError(
                f"{tag}: expected quantization {expected_quantization}, got {observed_quantization}"
            )
        snapshot["models"][tag] = {
            "digest": digest,
            "size": found.get("size"),
            "details": details,
            "parameters_sha256": hashlib.sha256((info.get("parameters") or "").encode()).hexdigest(),
            "template_sha256": hashlib.sha256((info.get("template") or "").encode()).hexdigest(),
            "system_sha256": hashlib.sha256((info.get("system") or "").encode()).hexdigest(),
        }
    return snapshot


def build_pairs(prompts: list[dict[str, str]], protocol: dict[str, Any]) -> list[dict[str, str]]:
    pairs = [
        {
            "prompt_id": prompt["prompt_id"],
            "task_type": prompt["task_type"],
            "model_label": model["label"],
            "model": model["ollama_tag"],
            "prompt_text": prompt["prompt_text"],
        }
        for prompt in prompts
        for model in protocol["models"]
    ]
    return stable_shuffle(pairs, protocol["request_order_seed"])


def request_payload(pair: dict[str, str], instruction: str, protocol: dict[str, Any]) -> dict[str, Any]:
    controls = protocol["generation"]
    options = {
        key: controls[key]
        for key in ("temperature", "seed", "num_predict", "num_ctx", "top_k", "top_p", "repeat_penalty")
    }
    return {
        "model": pair["model"],
        "messages": [{"role": "user", "content": instruction.rstrip("\n") + "\n\n" + pair["prompt_text"]}],
        "options": options,
        "think": controls["think"],
        "stream": controls["stream"],
        "keep_alive": controls["keep_alive"],
    }


def record_name(pair: dict[str, str]) -> str:
    safe_model = pair["model_label"].replace(":", "_").replace("/", "_")
    return f"{pair['prompt_id']}__{safe_model}.json"


def collect_one(run_dir: Path, pair: dict[str, str], payload: dict[str, Any], client: Client) -> str:
    receipt = run_dir / "receipts" / record_name(pair)
    inflight = receipt.with_suffix(".inflight")
    receipt.parent.mkdir(parents=True, exist_ok=True)
    if receipt.exists():
        existing = json.loads(receipt.read_text(encoding="utf-8"))
        if canonical_json(existing["request"]) != canonical_json(payload):
            raise RuntimeError(f"saved request differs for {receipt}; use a new run ID")
        return "reused"
    if inflight.exists():
        raise RuntimeError(f"ambiguous prior request: inspect {inflight}; automatic retry is forbidden")

    inflight.write_text(
        json.dumps({"request": payload, "started_utc": utc_now()}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    started = time.perf_counter()
    returned = client("/api/chat", payload, 1800)
    elapsed_ms = (time.perf_counter() - started) * 1000
    message = returned.get("message", {})
    if not returned.get("done") or not isinstance(message.get("content"), str):
        raise RuntimeError(f"incomplete response for {receipt}; inflight marker retained")
    if returned.get("model") != pair["model"]:
        raise RuntimeError(
            f"unexpected returned model {returned.get('model')!r} for {pair['model']!r}; marker retained"
        )
    result = {
        "prompt_id": pair["prompt_id"],
        "task_type": pair["task_type"],
        "model_label": pair["model_label"],
        "request": payload,
        "received_utc": utc_now(),
        "client_latency_ms": elapsed_ms,
        "response": returned,
        "response_text_sha256": hashlib.sha256(message["content"].encode("utf-8")).hexdigest(),
    }
    write_json(receipt, result)
    inflight.unlink()
    return "received"


def build_manifest(
    protocol_path: Path,
    prompt_path: Path,
    instruction_path: Path,
    snapshot: dict[str, Any],
    pairs: list[dict[str, str]],
) -> dict[str, Any]:
    return {
        "created_utc": utc_now(),
        "protocol_path": str(protocol_path),
        "protocol_sha256": sha256_file(protocol_path),
        "prompt_path": str(prompt_path),
        "prompt_sha256": sha256_file(prompt_path),
        "instruction_path": str(instruction_path),
        "instruction_sha256": sha256_file(instruction_path),
        "model_snapshot": snapshot,
        "request_order": [
            {"prompt_id": pair["prompt_id"], "model_label": pair["model_label"], "model": pair["model"]}
            for pair in pairs
        ],
    }
