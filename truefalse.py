import argparse
import json
import os
from collections import defaultdict
from typing import Dict, List, Tuple


def format_entries(entries: List[dict]) -> str:
    lines = ["["]
    for i, item in enumerate(entries):
        name = json.dumps(item.get("name", ""), ensure_ascii=True)
        url = json.dumps(item.get("url", ""), ensure_ascii=True)
        cat = json.dumps(item.get("categories", ""), ensure_ascii=True)
        premium = "true" if item.get("premium") else "false"
        line = f'  {{ "name": {name}, "url": {url}, "categories": {cat}, "premium": {premium} }}'
        if i < len(entries) - 1:
            line += ","
        lines.append(line)
    lines.append("]")
    return "\n".join(lines) + "\n"


def rebalance(entries: List[dict], ratio: float, min_true: int) -> Tuple[int, Dict[str, Tuple[int, int]]]:
    groups: Dict[str, List[int]] = defaultdict(list)
    for idx, item in enumerate(entries):
        if not isinstance(item, dict):
            continue
        key = item.get("categories") or item.get("name") or "__ungrouped__"
        groups[key].append(idx)

    changes = 0
    stats: Dict[str, Tuple[int, int]] = {}
    for key, idxs in groups.items():
        total = len(idxs)
        if total == 0:
            continue
        true_count = max(min_true, int(total * ratio))
        stats[key] = (true_count, total)
        for order, data_idx in enumerate(idxs):
            target = order < true_count
            if entries[data_idx].get("premium") != target:
                entries[data_idx]["premium"] = target
                changes += 1
    return changes, stats


def process_file(path: str, ratio: float, min_true: int, dry_run: bool = False) -> Tuple[int, Dict[str, Tuple[int, int]]]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        print(f"SKIP {path}: load error ({exc})")
        return 0, {}

    if not isinstance(data, list):
        print(f"SKIP {path}: not a list")
        return 0, {}

    changes, stats = rebalance(data, ratio, min_true)
    if changes and not dry_run:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(format_entries(data))
    return changes, stats


def main():
    parser = argparse.ArgumentParser(description="Rebalance premium flags in wallpapers.json files.")

    # ▼ 디폴트 폴더를 현재 위치로 변경
    parser.add_argument("-r", "--root", default=".", help="기준 폴더 (기본: 현재 위치)")

    parser.add_argument("--ratio", type=float, default=0.2, help="premium 비율 (기본: 0.2)")
    parser.add_argument("--min-true", type=int, default=1, help="그룹당 최소 premium 개수 (기본: 1)")
    parser.add_argument("--dry-run", action="store_true", help="파일을 수정하지 않고 결과만 표시")
    args = parser.parse_args()

    total_files = 0
    updated_files = 0
    for dirpath, _, filenames in os.walk(args.root):
        if "wallpapers.json" not in filenames:
            continue
        total_files += 1
        path = os.path.join(dirpath, "wallpapers.json")
        changes, stats = process_file(path, args.ratio, args.min_true, args.dry_run)
        if changes:
            updated_files += 1
        print(f"{'[DRY]' if args.dry_run else 'DONE'} {path}: "
              f"{'changed' if changes else 'no-change'}; "
              f"groups={', '.join(f'{k}:{v[0]}/{v[1]}' for k, v in stats.items())}")

    print(f"총 파일: {total_files}, 수정된 파일: {updated_files}")


if __name__ == "__main__":
    main()
