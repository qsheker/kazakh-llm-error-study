#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
import zipfile
from pathlib import Path

from kazllm_eval.core import sha256_file


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def load_json_or_empty(path: Path) -> dict:
    try:
        value = load_json(path)
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return {}
    return value if isinstance(value, dict) else {}


def docx_text(path: Path) -> str:
    if not path.exists():
        return ""
    with zipfile.ZipFile(path) as archive:
        document_xml = archive.read("word/document.xml").decode("utf-8", errors="replace")
    return " ".join(document_xml.replace("</w:p>", "\n").split())


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    checks: list[dict[str, str | bool]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    protocol_path = root / "config/protocol.json"
    protocol = load_json(protocol_path)
    freeze_path = root / "protocol/freeze_manifest.json"
    freeze = load_json(freeze_path) if freeze_path.exists() else {}
    check(
        "protocol freeze",
        protocol.get("status") == "frozen_three_person_signoff" and freeze.get("status") == "frozen_three_person_signoff",
        "requires the three personal sign-offs and freeze manifest",
    )
    exemptions_path = root / protocol["analysis"]["latin_exemptions_path"]
    exemptions_text = exemptions_path.read_text(encoding="utf-8") if exemptions_path.exists() else "REVIEW_REQUIRED"
    check(
        "Latin-script exemption freeze",
        "REVIEW_REQUIRED" not in exemptions_text
        and freeze.get("latin_exemptions_sha256") == sha256_file(exemptions_path),
        str(exemptions_path.relative_to(root)),
    )

    run_dir = root / "runs/final_test_v2"
    manifest_path = run_dir / "manifest.json"
    completion_path = run_dir / "completion.json"
    receipts = list((run_dir / "receipts").glob("*.json")) if run_dir.exists() else []
    completion = load_json(completion_path) if completion_path.exists() else {}
    accounted = int(completion.get("received", 0)) + int(completion.get("reused", 0))
    check(
        "240 immutable test receipts",
        manifest_path.exists() and len(receipts) == 240 and accounted == 240 and completion.get("metadata_unchanged") is True,
        f"receipts={len(receipts)}, accounted={accounted}, metadata_unchanged={completion.get('metadata_unchanged')}",
    )

    rater_paths = {
        "rater 1": root / "annotations/rater_1/final_test_v2__rater_1.xlsx",
        "rater 2": root / "annotations/rater_2/final_test_v2__rater_2.xlsx",
    }
    for name, path in rater_paths.items():
        check(f"{name} original", path.exists(), str(path.relative_to(root)))
    check(
        "rater files differ",
        all(path.exists() for path in rater_paths.values())
        and sha256_file(rater_paths["rater 1"]) != sha256_file(rater_paths["rater 2"]),
        "independent originals must exist and have different hashes",
    )

    required_files = {
        "pre-adjudication agreement": root / "annotations/adjudication/agreement.json",
        "adjudicated response labels": root / "annotations/adjudicated/response_labels.csv",
        "adjudicated error events": root / "annotations/adjudicated/error_events.csv",
        "adjudication log": root / "annotations/adjudicated/adjudication_log.csv",
        "final analysis summary": root / "results/derived/final_test_v2/summary.json",
        "detector analysis": root / "results/derived/final_test_v2/detector_metrics.json",
        "sensitivity analysis": root / "results/derived/final_test_v2/sensitivity.json",
        "model-by-task analysis": root / "results/derived/final_test_v2/model_task_interactions.csv",
        "numerical consistency audit": root / "results/derived/final_test_v2/input_hashes.json",
        "primary results figure": root / "results/derived/final_test_v2/model_error_rates.png",
        "similarity report": root / "evidence/similarity_report.pdf",
        "ethics determination": root / "evidence/ethics_determination.pdf",
        "three-person exception proof": root / "evidence/three_person_team_approval.pdf",
    }
    for name, path in required_files.items():
        check(name, path.exists() and path.stat().st_size > 0, str(path.relative_to(root)))

    manuscript_path = root / "deliverables/Kazakh_LLM_Study_ACM_Submission.docx"
    manuscript_text = docx_text(manuscript_path).lower()
    manuscript_sentinels = ("results reporting contract", "controlled pre-results", "confirmatory results are unavailable")
    check(
        "result-bearing official-template manuscript",
        bool(manuscript_text) and not any(marker in manuscript_text for marker in manuscript_sentinels),
        str(manuscript_path.relative_to(root)),
    )
    cover_path = root / "deliverables/Cover_Letter_TALLIP.docx"
    cover_text = docx_text(cover_path).lower()
    check(
        "final cover letter",
        bool(cover_text) and "do not submit" not in cover_text and "controlled draft" not in cover_text,
        str(cover_path.relative_to(root)),
    )
    deck_path = root / "output/pdf/Kazakh_LLM_Defense_Deck.pdf"
    check(
        "final presentation PDF",
        deck_path.exists() and deck_path.stat().st_size > 0,
        str(deck_path.relative_to(root)),
    )

    team_names = {"Aldiyar Zhaksylyk", "Yerkebulan Rakhymbay", "Iliyas Aitzhan"}
    reference_path = root / "evidence/reference_verification.json"
    reference_evidence = load_json_or_empty(reference_path)
    reference_authors = reference_evidence.get("authors", [])
    reference_valid = (
        manuscript_path.exists()
        and reference_evidence.get("manuscript_sha256") == sha256_file(manuscript_path)
        and {row.get("name") for row in reference_authors if isinstance(row, dict)} == team_names
        and all(
            row.get("confirmed_read") is True
            and set(row.get("references", [])) == set(range(1, 29))
            and bool(row.get("signed_utc"))
            for row in reference_authors
            if isinstance(row, dict)
        )
        and len(reference_authors) == 3
    )
    check("reference-reading verification", reference_valid, str(reference_path.relative_to(root)))

    approval_path = root / "evidence/all_author_approval.json"
    approval = load_json_or_empty(approval_path)
    approval_authors = approval.get("authors", [])
    approval_valid = (
        manuscript_path.exists()
        and approval.get("manuscript_sha256") == sha256_file(manuscript_path)
        and {row.get("name") for row in approval_authors if isinstance(row, dict)} == team_names
        and all(
            row.get("approved") is True and bool(row.get("signed_utc"))
            for row in approval_authors
            if isinstance(row, dict)
        )
        and len(approval_authors) == 3
    )
    check("all-author final approval", approval_valid, str(approval_path.relative_to(root)))

    presentation_review_path = root / "evidence/presentation_review.json"
    presentation_review = load_json_or_empty(presentation_review_path)
    presentation_valid = (
        deck_path.exists()
        and presentation_review.get("deck_sha256") == sha256_file(deck_path)
        and presentation_review.get("page_count") in range(8, 13)
        and presentation_review.get("result_numbers_checked") is True
        and presentation_review.get("all_authors_approved") is True
    )
    check("presentation review", presentation_valid, str(presentation_review_path.relative_to(root)))

    reproduction_path = root / "evidence/reproduction.json"
    reproduction = load_json_or_empty(reproduction_path)
    reproduction_valid = (
        reproduction.get("outside_team") is True
        and reproduction.get("success") is True
        and bool(reproduction.get("reproducer"))
        and bool(reproduction.get("commit"))
        and isinstance(reproduction.get("commands"), list)
        and bool(reproduction.get("commands"))
        and isinstance(reproduction.get("result_hashes"), dict)
        and bool(reproduction.get("result_hashes"))
    )
    check("outside-team reproduction", reproduction_valid, str(reproduction_path.relative_to(root)))

    origin = subprocess.run(
        ["git", "remote", "get-url", "origin"], cwd=root, capture_output=True, text=True, check=False
    ).stdout.strip()
    check(
        "public repository remote",
        origin == "https://github.com/qsheker/kazakh-llm-error-study.git",
        origin or "origin missing",
    )
    status = subprocess.run(
        ["git", "status", "--porcelain"], cwd=root, capture_output=True, text=True, check=False
    ).stdout.strip()
    check("clean worktree", not status, status or "clean")

    tracked = subprocess.run(
        ["git", "ls-files"], cwd=root, capture_output=True, text=True, check=False
    ).stdout.splitlines()
    forbidden = [
        path
        for path in tracked
        if path == "data/blinding/private_model_key.csv"
        or path.endswith((".gguf", ".token"))
        or "/.venv/" in f"/{path}/"
    ]
    check("tracked secret/model audit", not forbidden, ", ".join(forbidden) or "no forbidden paths")

    report = {"ready": all(item["passed"] for item in checks), "checks": checks}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
