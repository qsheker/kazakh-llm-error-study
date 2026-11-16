from kazllm_eval.detectors import (
    binary_metrics,
    clustered_f1_difference,
    fasttext_predict_one,
    fasttext_response_positive,
    latin_response_positive,
)


def test_fasttext_predict_one_bypasses_numpy_wrapper_and_normalizes_text():
    class NativePredictor:
        def __init__(self):
            self.call = None

        def predict(self, text, k, threshold, on_unicode_error):
            self.call = (text, k, threshold, on_unicode_error)
            return [(0.91, "__label__kk")]

    class Model:
        def __init__(self):
            self.f = NativePredictor()

    model = Model()
    assert fasttext_predict_one(model, "бірінші\nекінші") == ("kk", 0.91)
    assert model.f.call == ("бірінші екінші\n", 1, 0.0, "strict")


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


def test_fasttext_does_not_treat_all_caps_as_automatically_exempt():
    seen = []

    def predictor(text):
        seen.append(text)
        return "en", 0.99

    positive, _ = fasttext_response_positive("THIS IS FOREIGN TEXT", predictor)
    assert positive is True
    assert "THIS IS FOREIGN" in seen


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
