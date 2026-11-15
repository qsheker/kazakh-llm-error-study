#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
import subprocess
import sys
import zipfile
from collections import Counter
from datetime import datetime
from pathlib import Path

from kazllm_eval.annotation import load_annotation_workbook, validate_blinded_manifest
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


def pdf_page_count(path: Path) -> int:
    if not path.exists():
        return 0
    return len(re.findall(rb"/Type\s*/Page(?!s)\b", path.read_bytes()))


def joint_calibration_provenance_valid(text: str) -> bool:
    normalized = " ".join(text.lower().split())
    return (
        "совместная командная разметка" in normalized
        and "нельзя описывать как две независимые человеческие разметки" in normalized
    )


def valid_review_timestamp(value: str) -> bool:
    try:
        parsed = datetime.fromisoformat(value)
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.utcoffset() is not None


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    checks: list[dict[str, str | bool]] = []

    def check(name: str, passed: bool, detail: str) -> None:
        checks.append({"name": name, "passed": passed, "detail": detail})

    protocol_path = root / "config/protocol.json"
    protocol = load_json(protocol_path)
    freeze_path = root / "protocol/freeze_manifest.json"
    freeze = load_json(freeze_path) if freeze_path.exists() else {}
    authorization_path = root / protocol["annotation"]["authorization_path"]
    authorization_matches = (
        authorization_path.exists()
        and freeze.get("authorization_sha256") == sha256_file(authorization_path)
    )
    check(
        "protocol freeze",
        protocol.get("status") == "frozen_joint_ai_assisted_coordinator_confirmed"
        and freeze.get("status") == "frozen_joint_ai_assisted_coordinator_confirmed"
        and authorization_matches,
        "requires the frozen joint AI-assisted protocol and coordinator authorization record",
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

    calibration_dir = root / "annotations/calibration/dev_calibration_v2"
    completed_calibration_dir = root / "outputs/calibration_team_assisted_20261115"
    calibration_valid = False
    calibration_detail = "training or qualification files are incomplete"
    try:
        training_manifest = load_json(calibration_dir / "training_blinded_manifest.json")
        qualification_manifest = load_json(calibration_dir / "qualification_blinded_manifest.json")
        training = [
            load_annotation_workbook(
                completed_calibration_dir
                / f"dev_calibration_v2__training__rater_{rater}__completed_team_assisted.xlsx",
                expected_responses=12,
            )
            for rater in (1, 2)
        ]
        qualification = [
            load_annotation_workbook(
                completed_calibration_dir
                / f"dev_calibration_v2__qualification__rater_{rater}__completed_team_assisted.xlsx",
                expected_responses=20,
            )
            for rater in (1, 2)
        ]
        for workbook in training:
            validate_blinded_manifest(workbook, training_manifest)
        for workbook in qualification:
            validate_blinded_manifest(workbook, qualification_manifest)
        calibration_valid = (
            all(item["sha256"] for item in training + qualification)
            and joint_calibration_provenance_valid(
                (completed_calibration_dir / "PROVENANCE_AND_USE_RU.md").read_text(
                    encoding="utf-8"
                )
            )
        )
        calibration_detail = "four source-bound team-assisted workbooks; no reliability claim"
    except (FileNotFoundError, KeyError, TypeError, ValueError, OSError) as exc:
        calibration_detail = str(exc)
    check("team-assisted calibration package", calibration_valid, calibration_detail)

    team_workbook_path = root / "annotations/team_gold/final_test_v2__team_gold.xlsx"
    review_log_path = root / "annotations/team_gold/team_review_log.csv"
    final_blinded_manifest_path = root / "annotations/final_test_v2__blinded_manifest.json"
    final_blinded_manifest = load_json_or_empty(final_blinded_manifest_path)
    team_gold_valid = False
    team_gold_detail = str(team_workbook_path.relative_to(root))
    try:
        team_gold = load_annotation_workbook(team_workbook_path, expected_responses=240)
        validate_blinded_manifest(team_gold, final_blinded_manifest)
        review_rows = list(csv.DictReader(review_log_path.open(encoding="utf-8-sig", newline="")))
        team_names = set(protocol["team"])
        assignment_counts = Counter(row.get("assigned_reviewer") for row in review_rows)
        team_gold_valid = (
            len(review_rows) == 240
            and {row.get("blind_id") for row in review_rows} == set(team_gold["responses"])
            and set(assignment_counts) == team_names
            and set(assignment_counts.values()) == {80}
            and all(row.get("review_status") == "approved" for row in review_rows)
            and all(row.get("reviewer") in team_names for row in review_rows)
            and all(
                row.get("reviewer") == row.get("assigned_reviewer") for row in review_rows
            )
            and all(row.get("ai_assistance") in {"yes", "no"} for row in review_rows)
            and all(valid_review_timestamp(row.get("reviewed_utc", "")) for row in review_rows)
            and all(
                response.get(flag) in {"yes", "no"}
                for response in team_gold["responses"].values()
                for flag in (
                    "refusal",
                    "off_task",
                    "requirement_missing",
                    "repetition",
                    "fabricated_specificity",
                )
            )
            and all(
                response.get("requirement_missing") != "yes"
                or str(response.get("missing_requirements") or "").strip()
                for response in team_gold["responses"].values()
            )
            and all(event.get("needs_adjudication") == "no" for event in team_gold["events"])
        )
    except (FileNotFoundError, KeyError, TypeError, ValueError, OSError) as exc:
        team_gold_detail = str(exc)
    check("reviewed joint-team gold is valid and source-bound", team_gold_valid, team_gold_detail)

    required_files = {
        "joint-team gold workbook": team_workbook_path,
        "team review log": review_log_path,
        "final analysis summary": root / "results/derived/final_test_v2/summary.json",
        "detector analysis": root / "results/derived/final_test_v2/detector_metrics.json",
        "sensitivity analysis": root / "results/derived/final_test_v2/sensitivity.json",
        "model-by-task analysis": root / "results/derived/final_test_v2/model_task_interactions.csv",
        "numerical consistency audit": root / "results/derived/final_test_v2/input_hashes.json",
        "primary results figure": root / "results/derived/final_test_v2/model_error_rates.png",
        "similarity report": root / "evidence/similarity_report.pdf",
        "ethics determination": root / "evidence/ethics_determination.pdf",
        "coordinator-reported instructor permission": root / "protocol/team_authorization.json",
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
    deck_pages = pdf_page_count(deck_path)
    check(
        "final presentation PDF",
        deck_path.exists() and deck_path.stat().st_size > 0 and 8 <= deck_pages <= 12,
        f"{deck_path.relative_to(root)}; pages={deck_pages}",
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
        and bool(re.fullmatch(r"[0-9a-f]{40}", str(reproduction.get("commit", ""))))
        and isinstance(reproduction.get("commands"), list)
        and bool(reproduction.get("commands"))
        and isinstance(reproduction.get("result_hashes"), dict)
        and bool(reproduction.get("result_hashes"))
        and all(
            re.fullmatch(r"[0-9a-f]{64}", str(value))
            for value in reproduction.get("result_hashes", {}).values()
        )
        and bool(reproduction.get("completed_utc"))
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
    secret_pattern = (
        r"ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|hf_[A-Za-z0-9]{20,}|"
        r"sk-[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY"
    )
    secret_scan = subprocess.run(
        ["git", "grep", "-I", "-l", "-E", secret_pattern, "--", "."],
        cwd=root,
        capture_output=True,
        text=True,
        check=False,
    )
    secret_files = secret_scan.stdout.splitlines() if secret_scan.returncode == 0 else []
    check(
        "tracked credential-content audit",
        secret_scan.returncode in {0, 1} and not secret_files,
        ", ".join(secret_files) or "no high-risk credential patterns",
    )

    report = {"ready": all(item["passed"] for item in checks), "checks": checks}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
