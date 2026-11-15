from pathlib import Path

from openpyxl import load_workbook

from kazllm_eval.annotation import create_rater_workbook


def test_workbook_hides_model_labels(tmp_path: Path):
    records = [
        {
            "private_response_id": "E01__qwen",
            "prompt_id": "E01",
            "task_type": "educational",
            "model_label": "secret_model",
            "prompt_text": "Сұрақ",
            "response_text": "Жауап мәтіні.",
            "word_count": 2,
            "finish_reason": "stop",
            "response_sha256": "abc",
        }
    ]
    mapping = [
        {
            "blind_id": "B-123",
            "private_response_id": "E01__qwen",
            "prompt_id": "E01",
            "model_label": "secret_model",
            "response_sha256": "abc",
        }
    ]
    path = tmp_path / "rater.xlsx"
    create_rater_workbook(path, records, mapping, tmp_path / "refs", 1)
    assert "secret_model" not in path.read_bytes().decode("latin1", errors="ignore")
    workbook = load_workbook(path, read_only=True)
    values = [value for row in workbook["Responses"].iter_rows(values_only=True) for value in row if value]
    assert "secret_model" not in values
    assert "B-123" in values
