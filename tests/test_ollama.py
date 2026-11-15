from pathlib import Path

import pytest

from kazllm_eval.ollama import (
    build_manifest,
    build_pairs,
    normalize_manifest_paths,
    request_payload,
)


def protocol():
    return {
        "models": [{"label": "one", "ollama_tag": "model:1"}],
        "request_order_seed": 2417,
        "generation": {
            "temperature": 0.0,
            "seed": 2417,
            "num_predict": 768,
            "num_ctx": 4096,
            "top_k": 40,
            "top_p": 1.0,
            "repeat_penalty": 1.0,
            "think": False,
            "stream": False,
            "keep_alive": 0,
        },
    }


def test_payload_has_one_user_message_and_generation_seed():
    pair = build_pairs(
        [{"prompt_id": "D01", "task_type": "dev", "prompt_text": "Сұрақ"}], protocol()
    )[0]
    payload = request_payload(pair, "Нұсқау\n", protocol())
    assert payload["messages"] == [{"role": "user", "content": "Нұсқау\n\nСұрақ"}]
    assert payload["options"]["seed"] == 2417
    assert payload["options"]["num_predict"] == 768


def test_manifest_uses_repository_relative_paths(tmp_path: Path):
    root = tmp_path / "repository"
    protocol_path = root / "config" / "protocol.json"
    prompt_path = root / "data" / "dev.csv"
    instruction_path = root / "data" / "instruction.txt"
    for path, content in (
        (protocol_path, "{}"),
        (prompt_path, "prompt_id\nD01\n"),
        (instruction_path, "instruction"),
    ):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    manifest = build_manifest(protocol_path, prompt_path, instruction_path, {}, [])

    assert manifest["protocol_path"] == "config/protocol.json"
    assert manifest["prompt_path"] == "data/dev.csv"
    assert manifest["instruction_path"] == "data/instruction.txt"


def test_manifest_rejects_input_outside_repository(tmp_path: Path):
    root = tmp_path / "repository"
    protocol_path = root / "config" / "protocol.json"
    prompt_path = tmp_path / "outside.csv"
    instruction_path = root / "data" / "instruction.txt"
    for path in (protocol_path, prompt_path, instruction_path):
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x", encoding="utf-8")

    with pytest.raises(ValueError, match="outside repository"):
        build_manifest(protocol_path, prompt_path, instruction_path, {}, [])


def test_normalize_manifest_paths_migrates_absolute_paths(tmp_path: Path):
    root = tmp_path / "repository"
    manifest = {
        "protocol_path": str(root / "config" / "protocol.json"),
        "prompt_path": str(root / "data" / "dev.csv"),
        "instruction_path": "data/instruction.txt",
    }

    normalized = normalize_manifest_paths(manifest, root)

    assert normalized == {
        "protocol_path": "config/protocol.json",
        "prompt_path": "data/dev.csv",
        "instruction_path": "data/instruction.txt",
    }
    assert manifest["protocol_path"].startswith(str(root))


def test_normalize_manifest_paths_rejects_external_path(tmp_path: Path):
    root = tmp_path / "repository"
    manifest = {
        "protocol_path": str(tmp_path / "outside.json"),
        "prompt_path": "data/dev.csv",
        "instruction_path": "data/instruction.txt",
    }

    with pytest.raises(ValueError, match="outside repository"):
        normalize_manifest_paths(manifest, root)
