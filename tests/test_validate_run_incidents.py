from __future__ import annotations

import hashlib
import importlib.util
import json
from pathlib import Path

from kazllm_eval.core import canonical_json


def load_validator_module():
    path = Path(__file__).resolve().parents[1] / "scripts/validate_run.py"
    spec = importlib.util.spec_from_file_location("validate_run_script", path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_incident_evidence_is_bound_to_retry_request(tmp_path: Path) -> None:
    validator = load_validator_module()
    incident_dir = tmp_path / "incidents"
    incident_dir.mkdir()
    request = {"model": "gemma3:12b", "messages": [{"role": "user", "content": "x"}]}
    inflight_path = incident_dir / "001_E13__gemma3_12b.original.inflight"
    inflight_path.write_text("original request evidence", encoding="utf-8")
    incident = {
        "prompt_id": "E13",
        "model_label": "gemma3_12b",
        "request_sha256": hashlib.sha256(canonical_json(request).encode()).hexdigest(),
        "original_inflight_sha256": hashlib.sha256(inflight_path.read_bytes()).hexdigest(),
        "response_observed": False,
        "failure_class": "explicit_infrastructure_failure_before_generation",
        "server_evidence": "runner load failed before generation",
        "resolution": "identical-payload infrastructure retry",
    }
    (incident_dir / "001_E13__gemma3_12b_load_failure.json").write_text(
        json.dumps(incident), encoding="utf-8"
    )

    count, errors = validator.validate_incidents(
        tmp_path, {("E13", "gemma3_12b"): {"request": request}}
    )

    assert count == 1
    assert errors == []


def test_incident_request_hash_mismatch_is_rejected(tmp_path: Path) -> None:
    validator = load_validator_module()
    incident_dir = tmp_path / "incidents"
    incident_dir.mkdir()
    inflight_path = incident_dir / "001_E13__gemma3_12b.original.inflight"
    inflight_path.write_text("evidence", encoding="utf-8")
    incident = {
        "prompt_id": "E13",
        "model_label": "gemma3_12b",
        "request_sha256": "0" * 64,
        "original_inflight_sha256": hashlib.sha256(inflight_path.read_bytes()).hexdigest(),
        "response_observed": False,
        "failure_class": "explicit_infrastructure_failure_before_generation",
        "server_evidence": "runner load failed before generation",
        "resolution": "identical-payload infrastructure retry",
    }
    (incident_dir / "001_E13__gemma3_12b_load_failure.json").write_text(
        json.dumps(incident), encoding="utf-8"
    )

    _, errors = validator.validate_incidents(
        tmp_path, {("E13", "gemma3_12b"): {"request": {"model": "gemma3:12b"}}}
    )

    assert "incident request hash mismatch 001_E13__gemma3_12b_load_failure.json" in errors
