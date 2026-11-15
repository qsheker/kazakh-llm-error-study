#!/usr/bin/env python3
from __future__ import annotations

import argparse
import re
from pathlib import Path

from PIL import Image


def slide_number(path: Path) -> int:
    match = re.fullmatch(r"slide-(\d+)\.png", path.name)
    if not match:
        raise ValueError(f"Unexpected slide filename: {path.name}")
    return int(match.group(1))


def main() -> None:
    parser = argparse.ArgumentParser(description="Build a presentation PDF from rendered slide PNGs.")
    parser.add_argument("--slides-dir", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    slide_paths = sorted(args.slides_dir.glob("slide-*.png"), key=slide_number)
    if [slide_number(path) for path in slide_paths] != list(range(1, 11)):
        raise SystemExit("Expected exactly slide-1.png through slide-10.png")

    images: list[Image.Image] = []
    try:
        for path in slide_paths:
            image = Image.open(path).convert("RGB")
            if image.width / image.height < 1.7 or image.width / image.height > 1.8:
                raise SystemExit(f"Unexpected aspect ratio for {path.name}: {image.size}")
            images.append(image)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        images[0].save(
            args.output,
            "PDF",
            resolution=144.0,
            save_all=True,
            append_images=images[1:],
        )
    finally:
        for image in images:
            image.close()

    print(f"{args.output}\nslides={len(slide_paths)}")


if __name__ == "__main__":
    main()
