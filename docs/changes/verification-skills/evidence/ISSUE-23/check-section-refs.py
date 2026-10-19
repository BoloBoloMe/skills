#!/usr/bin/env python3
"""check-section-refs: 核对 PROVENANCE 的节数/节号/节名与正文标题 (N2).

规则:
1. SKILL.md 里 `## N. 名` 顺序编号连续, 无 H1.
2. PROVENANCE 的人工核对结论: 声称的 H2 个数等于实际个数, 八个节名按正文顺序逐个列出.
3. 逐项差异表内每处 `第 N 节` 都带现有节名, 写成 `第 N 节 (名)`, 且名与正文一致.

用法: uv run python check-section-refs.py [--repo-root <路径>]
退出码 0 表示全部通过, 1 表示有不符合项.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

CN_NUM = {"一": 1, "二": 2, "三": 3, "四": 4, "五": 5, "六": 6, "七": 7, "八": 8, "九": 9, "十": 10}
HEADING = re.compile(r"^## (\d+)\. (.+)$")
H1 = re.compile(r"^# ")
CN_COUNT = re.compile(r"([一二三四五六七八九十])个 H2")
REF_NAMED = re.compile(r"第 (\d+) 节 \(([^()]+)\)")
REF_ANY = re.compile(r"第 (\d+) 节")
TABLE_START = "## 逐项差异表"
TABLE_END = "## 没有搬入的部分"


def load(root: Path) -> tuple[str, str]:
    skill = root / "workflow/blast-radius/SKILL.md"
    provenance = root / "workflow/blast-radius/reference/PROVENANCE.md"
    return skill.read_text(encoding="utf-8"), provenance.read_text(encoding="utf-8")


def headings(text: str) -> list[tuple[int, str]]:
    found: list[tuple[int, str]] = []
    for line in text.splitlines():
        match = HEADING.match(line)
        if match:
            found.append((int(match.group(1)), match.group(2).strip()))
    return found


def check(skill_text: str, provenance_text: str) -> list[str]:
    errors: list[str] = []
    sections = headings(skill_text)
    names = [name for _, name in sections]
    if not sections:
        return ["SKILL.md 里没有 `## N. 名` 形式的节标题"]
    if [number for number, _ in sections] != list(range(1, len(sections) + 1)):
        errors.append(f"节号不连续: {[number for number, _ in sections]}")
    if any(H1.match(line) for line in skill_text.splitlines()):
        errors.append("SKILL.md 出现 H1, 与人工结论不符")

    manual = [line for line in provenance_text.splitlines() if "人读结果" in line]
    if len(manual) != 1:
        errors.append(f"PROVENANCE 里带 `人读结果` 的人工结论行数为 {len(manual)}, 应为 1")
    else:
        line = manual[0]
        for claim in CN_COUNT.finditer(provenance_text):
            claimed = CN_NUM[claim.group(1)]
            if claimed != len(sections):
                errors.append(f"人工结论称 {claim.group(1)}个 H2, 正文实际 {len(sections)} 个")
        positions: list[int] = []
        for name in names:
            index = line.find(name)
            if index < 0:
                errors.append(f"人工结论没有列出节名: {name}")
            else:
                positions.append(index)
        if len(positions) == len(names) and positions != sorted(positions):
            errors.append("人工结论里的节名顺序与正文不一致")

    lines = provenance_text.splitlines()
    try:
        start = lines.index(TABLE_START) + 1
        end = lines.index(TABLE_END)
    except ValueError as exc:
        return errors + [f"差异表边界找不到: {exc}"]
    named = {(number, name) for number, name in sections}
    for number, line in enumerate(lines[start:end], start + 1):
        for match in REF_NAMED.finditer(line):
            pair = (int(match.group(1)), match.group(2))
            if pair not in named:
                errors.append(f"PROVENANCE.md:{number}: 节号加节名对不上正文: {match.group(0)}")
        for match in REF_ANY.finditer(line):
            tail = line[match.end():]
            if not tail.startswith(" ("):
                errors.append(f"PROVENANCE.md:{number}: `{match.group(0)}` 没带现有节名")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[5]
    skill_text, provenance_text = load(root)
    errors = check(skill_text, provenance_text)
    sections = headings(skill_text)
    print(f"正文节数={len(sections)}")
    for number, name in sections:
        print(f"  ## {number}. {name}")
    if errors:
        print(f"不符合项={len(errors)}")
        for error in errors:
            print(f"  - {error}")
        return 1
    print("不符合项=0")
    return 0


if __name__ == "__main__":
    sys.exit(main())
