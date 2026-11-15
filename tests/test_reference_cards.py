from __future__ import annotations

import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_all_test_prompts_have_review_ready_reference_cards() -> None:
    with (ROOT / "data/test/prompts_test.csv").open(encoding="utf-8") as stream:
        prompt_ids = {row["prompt_id"] for row in csv.DictReader(stream)}
    card_paths = {path.stem: path for path in (ROOT / "data/references").glob("*.md")}
    assert set(card_paths) == prompt_ids

    for prompt_id, path in card_paths.items():
        text = path.read_text(encoding="utf-8")
        assert "READY_FOR_THREE_PERSON_REVIEW" in text, prompt_id
        assert not re.search(r"\b(PENDING|TODO|TBD)\b", text), prompt_id
        assert "## Required content or factual anchors" in text, prompt_id
        assert "## Unsupported or prohibited claims" in text, prompt_id
        assert "## Sources" in text, prompt_id
        assert "https://" in text, prompt_id
