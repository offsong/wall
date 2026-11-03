#!/usr/bin/env python3
"""wallpapers.json 중복 행 삭제 + 카테고리 이름 검사.

1. 같은 파일 안에서 같은 이미지(pinimg 32자리 해시 기준)가 두 번 이상 나오는 행
   - 완전 중복: categories까지 같음
   - 카테고리만 다름: 같은 이미지가 다른 categories로 들어감
   - 이름 표기만 다름: 대소문자/공백만 다른 categories (예: JAKE ↔ Jake) → 잘못 올린 경우
2. 같은 폴더의 categories.json에 없는 categories를 쓰는 행
   - 대소문자/공백만 다르면 categories.json의 올바른 이름을 같이 알려줌

삭제: 완전 중복, 카테고리만 다름 → 처음 나온 행만 남기고 삭제
삭제 안 함: 이름 표기만 다름(JAKE ↔ Jake) → 직접 고치도록 로그로만 알림
수정 전 원본은 ../dup_backup/<날짜시간>/ 에 백업한다.
결과는 화면과 dup_report.txt에 저장한다.
"""
import json
import os
import re
import shutil
from collections import Counter
from datetime import datetime

ROOTS = ["wall", "worldwall"]
REPORT = "dup_report.txt"
HASH_RE = re.compile(r"([0-9a-f]{32})")
BACKUP_DIR = os.path.join("..", "dup_backup", datetime.now().strftime("%Y%m%d_%H%M%S"))


def image_key(url):
    match = HASH_RE.search(url.rsplit("/", 1)[-1])
    return match.group(1) if match else url


def loose(name):
    """대소문자·공백·_·- 무시한 비교용 이름."""
    return re.sub(r"[\s_\-]+", "", str(name)).lower()


def check_file(folder):
    path = os.path.join(folder, "wallpapers.json")
    try:
        with open(path, "r", encoding="utf-8") as handle:
            rows = json.load(handle)
    except (OSError, ValueError) as exc:
        return [f"  ⚠️ 읽기 실패: {exc}"], 0, 0, 0

    known = None
    categories_path = os.path.join(folder, "categories.json")
    if os.path.isfile(categories_path):
        try:
            with open(categories_path, "r", encoding="utf-8") as handle:
                known = {item.get("name") for item in json.load(handle) if isinstance(item, dict)}
        except (OSError, ValueError):
            known = None

    known_loose = {loose(name): name for name in known} if known else {}
    lines = []
    drop = set()
    first_seen = {}
    same = diff = 0
    unknown = Counter()
    for line_no, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            continue
        url = row.get("url", "")
        category = row.get("categories", "")
        # "Demon Slayer, Tanjiro Kamado"처럼 쉼표로 여러 카테고리를 넣은 경우 각각 확인
        parts = [part.strip() for part in str(category).split(",") if part.strip()]
        if known is not None and category not in known and not all(part in known for part in parts):
            unknown[category] += 1

        key = image_key(url)
        if key in first_seen:
            first_no, first_row = first_seen[key]
            if first_row.get("categories") == category:
                same += 1
                kind = "완전 중복 → 삭제"
                drop.add(line_no)
            elif loose(first_row.get("categories")) == loose(category):
                diff += 1
                kind = "⚠️ 이름 표기만 다름"
            else:
                diff += 1
                kind = "카테고리만 다름 → 삭제"
                drop.add(line_no)
            lines.append(f"  [{kind}] {first_no}행({first_row.get('categories')}) = {line_no}행({category})  {url}")
        else:
            first_seen[key] = (line_no, row)

    for category, count in sorted(unknown.items()):
        correct = known_loose.get(loose(category))
        if correct:
            lines.append(f"  [⚠️ 이름 다름] '{category}' {count}행 → categories.json에는 '{correct}'")
        else:
            lines.append(f"  [categories.json에 없음] '{category}' {count}행")
    if drop:
        backup = os.path.join(BACKUP_DIR, path)
        os.makedirs(os.path.dirname(backup), exist_ok=True)
        shutil.copy2(path, backup)
        kept = [row for line_no, row in enumerate(rows, start=1) if line_no not in drop]
        write_rows(path, kept)
    return lines, same, diff, sum(unknown.values())


def write_rows(path, rows):
    """truefalse.py와 같은 한 줄 형식으로 저장."""
    out = ["["]
    for row in rows:
        if not isinstance(row, dict):
            continue
        parts = ", ".join(f"{json.dumps(key)}: {json.dumps(value, ensure_ascii=True)}" for key, value in row.items())
        out.append(f"  {{ {parts} }},")
    if len(out) > 1:
        out[-1] = out[-1][:-1]
    out.append("]")
    with open(path, "w", encoding="utf-8", newline="\n") as handle:
        handle.write("\n".join(out) + "\n")


def main():
    output = []
    total_same = total_diff = total_unknown = files = 0
    for root in ROOTS:
        for dirpath, dirnames, filenames in os.walk(root):
            dirnames[:] = sorted(d for d in dirnames if d not in (".git", "@@error"))
            if "wallpapers.json" not in filenames:
                continue
            lines, same, diff, unknown = check_file(dirpath)
            if lines:
                files += 1
                output.append(f"■ {dirpath}/wallpapers.json  (완전 중복 {same}, 카테고리만 다름 {diff}, categories.json에 없음 {unknown})")
                output.extend(lines)
                output.append("")
            total_same += same
            total_diff += diff
            total_unknown += unknown

    name_only = sum(1 for line in output if "이름 표기만 다름" in line)
    summary = (
        f"문제 있는 파일 {files}개 | 삭제한 행 {total_same + total_diff - name_only}개 "
        f"(완전 중복 {total_same}, 카테고리만 다름 {total_diff - name_only}) | "
        f"이름 표기만 다른 중복 {name_only}행(삭제 안 함) | categories.json에 없는 카테고리 {total_unknown}행"
    )
    with open(REPORT, "w", encoding="utf-8") as handle:
        handle.write("\n".join(output + [summary]) + "\n")

    for line in output:
        if line.startswith("■"):
            print(line)
    warnings = [line for line in output if "⚠️ 이름" in line]
    if warnings:
        print("\n⚠️ 카테고리 이름이 categories.json과 다른 항목 (잘못 올린 것일 수 있음, 삭제 안 함):")
        current = None
        for line in output:
            if line.startswith("■"):
                current = line.split("  (")[0]
            elif "⚠️ 이름" in line:
                print(f"{current}\n{line}")
    print(summary)
    print(f"📄 자세한 목록: {os.path.abspath(REPORT)}")
    if os.path.isdir(BACKUP_DIR):
        print(f"💾 수정 전 원본 백업: {os.path.abspath(BACKUP_DIR)}")


if __name__ == "__main__":
    main()
