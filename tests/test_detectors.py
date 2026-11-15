from kazllm_eval.detectors import (
    binary_metrics,
    clustered_f1_difference,
    fasttext_response_positive,
    latin_response_positive,
)


def test_latin_detector_and_exemption():
    assert latin_response_positive("Қазақша WiFi белгісі")
    assert not latin_response_positive("Қазақша WiFi белгісі", {"wifi"})


def test_fasttext_threshold_is_binding():
    def predictor(text):
        return ("ru", 0.84 if "төмен" in text else 0.90)

    low, _ = fasttext_response_positive("төмен төмен төмен төмен", predictor)
    high, _ = fasttext_response_positive("жоғары жоғары жоғары жоғары", predictor)
    assert not low
    assert high


def test_binary_metrics_keep_undefined_denominators():
    result = binary_metrics([False, False], [False, False])
    assert result["precision"] is None
    assert result["recall"] is None
    assert result["f1"] is None


def test_cluster_bootstrap_uses_prompt_blocks():
    result = clustered_f1_difference(
        [False, False, False, False],
        [True, False, True, False],
        [True, False, True, False],
        ["P1", "P1", "P2", "P2"],
        replicates=200,
        seed=1,
    )
    assert result["difference"] == 1.0
    assert result["valid_replicates"] > 0
