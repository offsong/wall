import argparse
import json
import os
from collections import defaultdict
from typing import Dict, List, Tuple


def format_entries(entries: List[dict]) -> str:
    from collections import defaultdict
    import json

    # 1) 카테고리별 그룹화 (등장 순서 유지)
    grouped = defaultdict(list)
    order = []
    for item in entries:
        cat = item.get("categories", "")
        if cat not in grouped:
            order.append(cat)
        grouped[cat].append(item)

    # 2) 출력 생성
    lines = ["["]
    first_group = True

    for cat in order:
        group_items = grouped[cat]

        # 그룹 사이에 빈 줄 3줄 삽입
        if not first_group:
            lines.append("")
            lines.append("")
            lines.append("")

        first_group = False

        # 그룹의 모든 항목 출력
        for item in group_items:
            name = json.dumps(item.get("name", ""), ensure_ascii=True)
            url = json.dumps(item.get("url", ""), ensure_ascii=True)
            cat_json = json.dumps(item.get("categories", ""), ensure_ascii=True)
            premium = "true" if item.get("premium") else "false"

            lines.append(
                f'  {{ "name": {name}, "url": {url}, "categories": {cat_json}, "premium": {premium} }},'
            )

    # 마지막 콤마 제거
    if len(lines) > 1 and lines[-1].endswith(","):
        lines[-1] = lines[-1][:-1]

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


def process_file(path: str, ratio: float, min_true: int, dry_run: bool = False) -> Tuple[int, Dict[str, Tuple[int, int]], bool]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            original_text = f.read()
        data = json.loads(original_text)
    except Exception as exc:
        print(f"SKIP {path}: load error ({exc})")
        return 0, {}, False

    if not isinstance(data, list):
        print(f"SKIP {path}: not a list")
        return 0, {}, False

    changes, stats = rebalance(data, ratio, min_true)
    formatted = format_entries(data)
    needs_format = formatted != original_text
    wrote_file = (changes > 0 or needs_format) and not dry_run
    if wrote_file:
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(formatted)
    return changes, stats, changes > 0 or needs_format


def main():
    parser = argparse.ArgumentParser(description="Rebalance premium flags in wallpapers.json files.")

    # 기본 루트 폴더
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
        changes, stats, wrote_file = process_file(path, args.ratio, args.min_true, args.dry_run)
        if wrote_file:
            updated_files += 1
        print(f"{'[DRY]' if args.dry_run else 'DONE'} {path}: "
              f"{'changed' if wrote_file else 'no-change'}; "
              f"groups={', '.join(f'{k}:{v[0]}/{v[1]}' for k, v in stats.items())}")

    print(f"총 파일: {total_files}, 수정된 파일: {updated_files}")


if __name__ == "__main__":
    main()
