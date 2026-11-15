import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_dev_reference_cards_are_complete_and_separate_from_test_cards():
    with (ROOT / "data/dev/prompts_dev.csv").open(encoding="utf-8-sig", newline="") as stream:
        prompts = list(csv.DictReader(stream))
    assert len(prompts) == 20
    for prompt in prompts:
        path = ROOT / "data/dev/references" / f"{prompt['prompt_id']}.md"
        text = path.read_text(encoding="utf-8")
        assert prompt["prompt_text"] in text
        assert "CALIBRATION_ONLY_NOT_FOR_FINAL_ANALYSIS" in text
        assert "https://" in text
        assert "PENDING" not in text
