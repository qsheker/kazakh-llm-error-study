import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_gate", ROOT / "scripts/release_gate.py")
assert SPEC and SPEC.loader
RELEASE_GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE_GATE)


def test_qualification_threshold_boundaries_pass():
    agreement = {
        "category_presence": {"agreement": 0.80, "cohen_kappa": 0.60},
        "total_primary_count": {"krippendorff_alpha_interval": 0.67},
        "exact_span_match": {"f1": 0.60},
    }
    assert RELEASE_GATE.qualification_thresholds_passed(agreement)


def test_qualification_rejects_failed_span_threshold():
    agreement = {
        "category_presence": {"agreement": 0.90, "cohen_kappa": None},
        "total_primary_count": {"krippendorff_alpha_interval": 0.80},
        "exact_span_match": {"f1": 0.59},
    }
    assert not RELEASE_GATE.qualification_thresholds_passed(agreement)
