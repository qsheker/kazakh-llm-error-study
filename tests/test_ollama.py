from kazllm_eval.ollama import build_pairs, request_payload


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
