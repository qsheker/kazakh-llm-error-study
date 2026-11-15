#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import urllib.request
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Download and verify the official ACM Word template.")
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    provenance = json.loads((root / "resources/acm_template_source.json").read_text(encoding="utf-8"))
    request = urllib.request.Request(provenance["url"], headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        payload = response.read()
    digest = hashlib.sha256(payload).hexdigest()
    if digest != provenance["sha256"] or len(payload) != provenance["bytes"]:
        raise SystemExit(
            f"ACM template changed: sha256={digest}, bytes={len(payload)}; review before use"
        )
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_bytes(payload)
    print(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
