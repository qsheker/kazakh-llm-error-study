#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import zipfile
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "packages" / "Kazakh_LLM_Final_Course_Submission.zip"

FILES = [
    "README.md",
    "deliverables/Kazakh_LLM_Study_ACM_Submission.docx",
    "deliverables/Kazakh_LLM_Study_Manuscript.docx",
    "deliverables/Cover_Letter_TALLIP.docx",
    "deliverables/Final_Submission_and_Defense_Guide_RU.docx",
    "deliverables/Kazakh_LLM_Defense_Deck.pptx",
    "output/pdf/Kazakh_LLM_Defense_Deck.pdf",
    "docs/JOURNAL_FIT_STATEMENT.md",
    "docs/RELEASE_CHECKLIST.md",
    "docs/CRITERIA_MATRIX.md",
    "docs/FINAL_SUBMISSION_AND_DEFENSE_RU.md",
    "annotations/team_gold/final_test_v2__team_gold.xlsx",
    "annotations/team_gold/team_review_log.csv",
    "results/derived/final_test_v2/summary.json",
    "results/derived/final_test_v2/model_rates.csv",
    "results/derived/final_test_v2/pairwise.csv",
    "results/derived/final_test_v2/detector_metrics.json",
    "results/derived/final_test_v2/sensitivity.json",
    "results/derived/final_test_v2/model_task_interactions.csv",
    "results/derived/final_test_v2/input_hashes.json",
    "results/derived/final_test_v2/model_error_rates.png",
]


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main() -> None:
    paths = [ROOT / relative for relative in FILES]
    missing = [str(path.relative_to(ROOT)) for path in paths if not path.is_file()]
    if missing:
        raise SystemExit(f"Missing required course-submission files: {missing}")

    manifest = {
        "schema_version": "course-submission-package.v1",
        "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "team": ["Aldiyar Zhaksylyk", "Yerkebulan Rakhymbay", "Iliyas Aitzhan"],
        "repository": "https://github.com/qsheker/kazakh-llm-error-study",
        "course_submission_ready": True,
        "journal_release_ready": False,
        "journal_release_blockers": [
            "university similarity report",
            "ethics determination",
            "personal reference-reading verification",
            "all-author approval of the exact final artifacts",
            "team review of the exact result-bearing presentation",
            "outside-team reproduction",
            "clean commit and final release tag",
        ],
        "annotation_provenance": (
            "AI-assisted drafts were reviewed by assigned team members; the coordinator entered "
            "approval records after reviewer confirmation. This is one team-consensus gold set, "
            "not independent human annotation."
        ),
        "files": [
            {
                "path": relative,
                "sha256": sha256(ROOT / relative),
                "bytes": (ROOT / relative).stat().st_size,
            }
            for relative in FILES
        ],
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(OUTPUT, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        archive.writestr(
            "SUBMISSION_MANIFEST.json",
            json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        )
        for relative in FILES:
            archive.write(ROOT / relative, arcname=relative)

    print(
        json.dumps(
            {
                "output": str(OUTPUT),
                "sha256": sha256(OUTPUT),
                "files": len(FILES) + 1,
                "bytes": OUTPUT.stat().st_size,
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
