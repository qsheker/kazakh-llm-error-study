import numpy as np

from scripts.analyze_final import (
    stratified_category_bootstrap,
    stratified_difference_in_differences,
)


def test_category_bootstrap_reports_pooled_rate_and_code_switching_contrast():
    rows = [
        {
            "prompt_id": "E01",
            "task_type": "educational",
            "word_count": 100,
            "grammatical": 1,
            "lexical": 0,
            "semantic": 0,
            "code_switching": 2,
        },
        {
            "prompt_id": "P01",
            "task_type": "public_information",
            "word_count": 100,
            "grammatical": 1,
            "lexical": 0,
            "semantic": 0,
            "code_switching": 2,
        },
    ]
    categories = ("grammatical", "lexical", "semantic", "code_switching")

    summaries, contrasts = stratified_category_bootstrap(rows, categories, 50, 2417)

    assert summaries["grammatical"]["pooled_rate_per_100_words"] == 1.0
    assert summaries["code_switching"]["pooled_rate_per_100_words"] == 2.0
    assert contrasts["code_switching_minus_grammatical"]["difference"] == 1.0


def test_model_task_difference_in_differences_uses_public_minus_educational():
    matrix = np.array(
        [
            [4.0, 2.0],
            [6.0, 2.0],
            [8.0, 2.0],
            [10.0, 2.0],
        ]
    )
    strata = ["educational", "educational", "public_information", "public_information"]

    result = stratified_difference_in_differences(matrix, strata, 0, 1, 50, 2417)

    assert result["public_minus_educational_model_difference"] == 4.0
