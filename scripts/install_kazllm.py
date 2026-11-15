#!/usr/bin/env python3
from __future__ import annotations

import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

from huggingface_hub import hf_hub_download

from kazllm_eval.core import sha256_file, write_json


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    model_dir = root / "models/kazllm"
    source_path = model_dir / "source.json"
    source = json.loads(source_path.read_text(encoding="utf-8"))
    downloaded = Path(
        hf_hub_download(
            repo_id=source["repository"],
            filename=source["filename"],
            revision=source["revision"],
        )
    )
    destination = model_dir / source["filename"]
    downloaded_digest = sha256_file(downloaded)
    if not destination.exists():
        try:
            destination.hardlink_to(downloaded)
        except OSError:
            shutil.copy2(downloaded, destination)
    digest = sha256_file(destination)
    if digest != downloaded_digest:
        raise SystemExit(
            f"existing local KazLLM file differs from the pinned official download: {digest} != {downloaded_digest}"
        )
    expected = source.get("expected_sha256")
    if expected and digest != expected:
        raise SystemExit(f"KazLLM SHA-256 mismatch: expected {expected}, got {digest}")
    if not expected:
        # The file came from the pinned official repository and immutable
        # revision above. Persist the first authenticated digest so all later
        # installs and the protocol freeze verify the exact same artifact.
        source["expected_sha256"] = digest
        source["note"] = "SHA-256 frozen from the authenticated official download at the pinned revision."
        write_json(source_path, source)
    subprocess.run(
        ["ollama", "create", "kazllm:8b-q4_k_m", "-f", str(model_dir / "Modelfile")],
        cwd=model_dir,
        check=True,
    )
    receipt = {
        "created_utc": datetime.now(UTC).isoformat(),
        "repository": source["repository"],
        "revision": source["revision"],
        "filename": source["filename"],
        "sha256": digest,
        "ollama_tag": "kazllm:8b-q4_k_m",
    }
    write_json(root / "results/raw/kazllm_import_receipt.json", receipt)
    print(json.dumps(receipt, indent=2))
    if not expected:
        print("Frozen the authenticated official GGUF SHA-256 in models/kazllm/source.json.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
