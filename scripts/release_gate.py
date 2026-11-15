#!/usr/bin/env python3
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from kazllm_eval.core import sha256_file


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


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
        "pre-adjudication agreement": root / "results/derived/agreement.json",
        "adjudicated gold": root / "annotations/adjudicated/final_test_v2__gold.xlsx",
        "adjudication log": root / "annotations/adjudicated/adjudication_log.csv",
        "final analysis summary": root / "results/derived/final_summary.json",
        "numerical consistency audit": root / "results/derived/numerical_consistency.json",
        "similarity report": root / "evidence/similarity_report.pdf",
        "ethics determination": root / "evidence/ethics_determination.pdf",
        "three-person exception proof": root / "evidence/three_person_team_approval.pdf",
        "outside-team reproduction": root / "evidence/reproduction.json",
    }
    for name, path in required_files.items():
        check(name, path.exists() and path.stat().st_size > 0, str(path.relative_to(root)))

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

    report = {"ready": all(item["passed"] for item in checks), "checks": checks}
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["ready"] else 1


if __name__ == "__main__":
    sys.exit(main())
