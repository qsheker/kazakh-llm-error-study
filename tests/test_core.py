import json
from pathlib import Path

from kazllm_eval.core import prompt_similarity, sha256_file, validate_test_prompts, word_tokens


ROOT = Path(__file__).resolve().parents[1]


def test_unicode_word_tokenization():
    assert word_tokens("Әке-шеше 2026 жылы қазақ’s сөз айтты.") == [
        "Әке-шеше",
        "жылы",
        "қазақ’s",
        "сөз",
        "айтты",
    ]


def test_prompt_similarity_identity():
    assert prompt_similarity("Қазақша мәтін", "Қазақша мәтін") == 1.0


def test_test_matrix_is_valid():
    report = validate_test_prompts(
        ROOT / "data/test/prompts_test.csv",
        ROOT / "data/dev/prompts_dev.csv",
    )
    assert report["valid"], report


def test_third_party_resource_hashes_match_provenance():
    downloads = json.loads((ROOT / "resources/downloads.json").read_text(encoding="utf-8"))
    for filename, metadata in downloads.items():
        path = ROOT / "resources" / filename
        assert path.stat().st_size == metadata["bytes"]
        assert sha256_file(path) == metadata["sha256"]
