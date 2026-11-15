#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from kazllm_eval.core import validate_test_prompts


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--test", type=Path, default=Path("data/test/prompts_test.csv"))
    parser.add_argument("--dev", type=Path, default=Path("data/dev/prompts_dev.csv"))
    args = parser.parse_args()
    report = validate_test_prompts(args.test, args.dev)
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["valid"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
