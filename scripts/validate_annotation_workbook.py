#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path

from kazllm_eval.annotation import load_annotation_workbook


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate one original blinded annotation workbook.")
    parser.add_argument("workbook", type=Path)
    parser.add_argument("--expected-responses", type=int)
    args = parser.parse_args()
    result = load_annotation_workbook(args.workbook, args.expected_responses)
    print(
        json.dumps(
            {
                "path": str(args.workbook),
                "sha256": result["sha256"],
                "responses": len(result["responses"]),
                "events": len(result["events"]),
                "valid": True,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
