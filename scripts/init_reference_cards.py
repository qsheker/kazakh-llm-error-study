#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path

from kazllm_eval.core import read_csv


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    output = root / "data/references"
    output.mkdir(parents=True, exist_ok=True)
    for row in read_csv(root / "data/test/prompts_test.csv"):
        path = output / f"{row['prompt_id']}.md"
        if path.exists():
            continue
        card_type = "REFERENCE" if row["task_type"] == "educational" else "CONSTRAINT"
        path.write_text(
            f"# {card_type} CARD — {row['prompt_id']}\n\n"
            f"- Status: PENDING_TEAM_REVIEW\n"
            f"- Task type: {row['task_type']}\n"
            f"- Domain: {row['domain']}\n"
            f"- Task form: {row['task_form']}\n\n"
            f"## Prompt\n\n{row['prompt_text']}\n\n"
            "## Required content or factual anchors\n\n- PENDING\n\n"
            "## Acceptable variants and exemptions\n\n- PENDING\n\n"
            "## Unsupported or prohibited claims\n\n- PENDING\n\n"
            "## Sources\n\n- PENDING: add authoritative URL, title, access date, and the claim it supports.\n",
            encoding="utf-8",
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
