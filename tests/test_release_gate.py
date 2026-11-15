import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("release_gate", ROOT / "scripts/release_gate.py")
assert SPEC and SPEC.loader
RELEASE_GATE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RELEASE_GATE)


def test_joint_calibration_provenance_accepts_explicit_disclosure():
    text = (
        "Это совместная командная разметка. "
        "Файлы нельзя описывать как две независимые человеческие разметки."
    )
    assert RELEASE_GATE.joint_calibration_provenance_valid(text)


def test_joint_calibration_provenance_rejects_independence_claim():
    text = "Два независимых аннотатора выполнили разметку."
    assert not RELEASE_GATE.joint_calibration_provenance_valid(text)
