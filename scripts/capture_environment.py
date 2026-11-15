#!/usr/bin/env python3
from __future__ import annotations

import importlib.metadata
import json
import platform
import shutil
import subprocess
import sys
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

from kazllm_eval.core import write_json


def command(*args: str) -> str | None:
    try:
        return subprocess.run(args, check=True, capture_output=True, text=True).stdout.strip()
    except (FileNotFoundError, subprocess.CalledProcessError):
        return None


def ollama_json(path: str):
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434" + path, timeout=10) as response:
            return json.load(response)
    except Exception as exc:
        return {"unavailable": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    root = Path(__file__).resolve().parents[1]
    try:
        python_executable = str(Path(sys.executable).resolve().relative_to(root.resolve()))
    except ValueError:
        python_executable = Path(sys.executable).name
    packages = {}
    for name in (
        "fasttext-wheel",
        "huggingface-hub",
        "jsonschema",
        "matplotlib",
        "numpy",
        "openpyxl",
        "pandas",
        "python-docx",
        "scipy",
        "pytest",
    ):
        try:
            packages[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            packages[name] = None
    disk = shutil.disk_usage(root)
    receipt = {
        "captured_utc": datetime.now(timezone.utc).isoformat(),
        "platform": {
            "system": platform.system(),
            "release": platform.release(),
            "machine": platform.machine(),
            "macos": command("sw_vers", "-productVersion"),
            "model": command("sysctl", "-n", "hw.model"),
            "cpu": command("sysctl", "-n", "machdep.cpu.brand_string"),
            "physical_memory_bytes": command("sysctl", "-n", "hw.memsize"),
        },
        "python": {"version": sys.version, "executable": python_executable},
        "packages": packages,
        "ollama": {
            "client_version": command("ollama", "--version"),
            "server_version": ollama_json("/api/version"),
            "models": ollama_json("/api/tags"),
        },
        "workspace_disk": {"total": disk.total, "used": disk.used, "free": disk.free},
        "privacy": "Serial number, hardware UUID, usernames, tokens, and private blinding keys are intentionally excluded.",
    }
    output = root / "results/raw/environment.json"
    write_json(output, receipt)
    print(json.dumps(receipt, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
