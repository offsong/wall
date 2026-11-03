#!/usr/bin/env python3
"""Change Pinterest JPG image URLs in categories.json files to 474x."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path


PINIMG_JPG_URL = re.compile(
    r"(?P<prefix>https://i\.pinimg\.com/)(?P<size>[^/\"\s]+)/"
    r"(?P<path>[^\"\s?#]+\.jpg)(?P<suffix>(?:[?#][^\"\s]*)?)(?=$|[\"\s])",
    re.IGNORECASE,
)


def convert_pinimg_jpg_urls(text: str) -> tuple[str, int]:
    """Return text with Pinterest JPG size paths changed to 474x."""

    replacements = 0

    def replace(match: re.Match[str]) -> str:
        nonlocal replacements
        if match.group("size") == "474x":
            return match.group(0)

        replacements += 1
        return (
            f'{match.group("prefix")}474x/'
            f'{match.group("path")}{match.group("suffix")}'
        )

    return PINIMG_JPG_URL.sub(replace, text), replacements


def update_file(path: Path, *, dry_run: bool) -> int:
    original = path.read_text(encoding="utf-8")

    # 변경 전후가 모두 정상 JSON인지 확인해 손상된 파일을 만들지 않는다.
    json.loads(original)
    updated, replacements = convert_pinimg_jpg_urls(original)
    json.loads(updated)

    if replacements and not dry_run:
        path.write_text(updated, encoding="utf-8")

    return replacements


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Recursively change the size path of i.pinimg.com JPG URLs in "
            "categories.json files to 474x. GIF and video URLs are unchanged."
        )
    )
    parser.add_argument(
        "root",
        nargs="?",
        type=Path,
        default=Path(__file__).resolve().parent,
        help="directory to search (default: directory containing this script)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="show what would change without writing files",
    )
    args = parser.parse_args()

    files_changed = 0
    urls_changed = 0

    for path in sorted(args.root.rglob("categories.json")):
        replacements = update_file(path, dry_run=args.dry_run)
        if replacements:
            files_changed += 1
            urls_changed += replacements
            action = "Would update" if args.dry_run else "Updated"
            print(f"{action}: {path} ({replacements} URL(s))")

    action = "Would update" if args.dry_run else "Updated"
    print(f"{action} {urls_changed} URL(s) in {files_changed} file(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
