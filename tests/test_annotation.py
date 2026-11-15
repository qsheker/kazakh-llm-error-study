import hashlib
from pathlib import Path

from openpyxl import load_workbook

from kazllm_eval.annotation import (
    annotation_agreement,
    build_blinded_manifest,
    create_rater_workbook,
    load_annotation_workbook,
    validate_blinded_manifest,
)


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


def completed_workbook(tmp_path: Path, name: str, category: str = "grammatical") -> Path:
    records = [
        {
            "private_response_id": "E01__qwen",
            "prompt_id": "E01",
            "task_type": "educational",
            "model_label": "secret_model",
            "prompt_text": "Сұрақ",
            "response_text": "Қате мәтін.",
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
    path = tmp_path / name
    create_rater_workbook(path, records, mapping, tmp_path / "refs", 1)
    workbook = load_workbook(path)
    responses = workbook["Responses"]
    for column in (9, 10, 11, 13, 14):
        responses.cell(2, column).value = "no"
    events = workbook["Error events"]
    values = ["B-123", "E1", category, "Қате", 0, 4, 1, 1, "Дұрыс", "Rule", "", "no"]
    for column, value in enumerate(values, 1):
        events.cell(2, column).value = value
    workbook.save(path)
    return path


def test_completed_workbook_validation_and_agreement(tmp_path: Path):
    left_path = completed_workbook(tmp_path, "left.xlsx")
    right_path = completed_workbook(tmp_path, "right.xlsx")
    left = load_annotation_workbook(left_path, expected_responses=1)
    right = load_annotation_workbook(right_path, expected_responses=1)
    agreement = annotation_agreement(left, right)
    assert agreement["category_presence"]["agreement"] == 1.0
    assert agreement["total_primary_count"]["krippendorff_alpha_interval"] == 1.0
    assert agreement["exact_span_match"]["f1"] == 1.0


def test_workbook_validation_rejects_bad_fragment(tmp_path: Path):
    path = completed_workbook(tmp_path, "bad.xlsx")
    workbook = load_workbook(path)
    workbook["Error events"]["D2"] = "басқа"
    workbook.save(path)
    try:
        load_annotation_workbook(path, expected_responses=1)
    except ValueError as exc:
        assert "fragment does not match" in str(exc)
    else:
        raise AssertionError("invalid fragment was accepted")


def test_blinded_manifest_rejects_read_only_tampering(tmp_path: Path):
    reference_dir = tmp_path / "refs"
    reference_dir.mkdir()
    (reference_dir / "E01.md").write_text("Reference card", encoding="utf-8")
    response_text = "Қате мәтін."
    records = [
        {
            "private_response_id": "E01__qwen",
            "prompt_id": "E01",
            "task_type": "educational",
            "model_label": "secret_model",
            "prompt_text": "Сұрақ",
            "response_text": response_text,
            "word_count": 2,
            "finish_reason": "stop",
            "response_sha256": hashlib.sha256(response_text.encode("utf-8")).hexdigest(),
        }
    ]
    mapping = [
        {
            "blind_id": "B-123",
            "private_response_id": "E01__qwen",
            "prompt_id": "E01",
            "model_label": "secret_model",
            "response_sha256": records[0]["response_sha256"],
        }
    ]
    path = tmp_path / "completed.xlsx"
    create_rater_workbook(path, records, mapping, reference_dir, 1)
    workbook = load_workbook(path)
    for column in (9, 10, 11, 13, 14):
        workbook["Responses"].cell(2, column).value = "no"
    workbook.save(path)
    manifest = build_blinded_manifest(records, mapping, reference_dir)
    loaded = load_annotation_workbook(path, expected_responses=1)
    validate_blinded_manifest(loaded, manifest)

    workbook = load_workbook(path)
    workbook["Responses"]["E2"] = "Подменённый ответ"
    workbook.save(path)
    tampered = load_annotation_workbook(path, expected_responses=1)
    try:
        validate_blinded_manifest(tampered, manifest)
    except ValueError as exc:
        assert "response_text" in str(exc)
    else:
        raise AssertionError("tampered response text was accepted")
