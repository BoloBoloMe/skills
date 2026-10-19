"""ISSUE-19 机械扫描: 标点, 破折号, 被动残句, 超长句, 悬空引用, 第三人称视角.

只管这些可判定的规则, 不做语义审读. 用法:
    uv run python check-issue19.py <SKILL.md 路径> [<SKILL.md 路径> ...]
    uv run python check-issue19.py --selftest
退出码 0 表示无命中, 1 表示有命中, 2 表示自检失败.
"""

import argparse
import re
import sys
import tempfile
from pathlib import Path

FULLWIDTH = re.compile(r"[\u3001\u3002\uff0c\uff1b\uff1a\uff01\uff1f\uff08\uff09\u3010\u3011]")
EM_DASH = "\u2014"
PASSIVE = "被"
CJK = re.compile(r"[\u4e00-\u9fff]")
CLAUSE_SPLIT = re.compile(r"[\u3002;:,.!?\uff1b\uff1a\uff0c]")
QUESTION = re.compile(r"第\s*(\d)\s*问")
SECTION_POINTER = re.compile(r"`(## [^`]+)`")
HEADING = re.compile(r"^## (.+)$")


def clauses(line):
    return [part.strip() for part in CLAUSE_SPLIT.split(line) if part.strip()]


def scan(text):
    """返回命中清单, 每项是 (规则, 行号, 说明)."""
    hits = []
    headings = set()
    lines = text.splitlines()
    for line in lines:
        match = HEADING.match(line)
        if match:
            headings.add(match.group(1).strip())

    mapping = {}
    for line in lines:
        for numbers, section in re.findall(r"第\s*([\d\s与和第]+?)问在 `## ([^`]+)`", line):
            for number in re.findall(r"\d", numbers):
                mapping[number] = section.strip()

    for number, line in enumerate(lines, 1):
        if EM_DASH in line:
            hits.append(("破折号", number, "出现 U+2014"))
        if FULLWIDTH.search(line):
            hits.append(("全角标点", number, FULLWIDTH.search(line).group(0)))
        if PASSIVE in line:
            hits.append(("被动残句", number, "出现 被"))
        for part in clauses(line):
            if len(CJK.findall(part)) > 25:
                hits.append(("超长句", number, f"{len(CJK.findall(part))} 字: {part[:40]}"))
        for number_hit in QUESTION.findall(line):
            if number_hit not in mapping:
                hits.append(("悬空引用", number, f"第 {number_hit} 问没有节对照"))
        for section in SECTION_POINTER.findall(line):
            name = section[len("## ") :].strip()
            if name not in headings:
                hits.append(("悬空引用", number, f"节不存在: {name}"))
        for match in re.finditer(r"用户(?!路径|端到端)", line):
            hits.append(("第三人称", number, match.group(0)))
    if not mapping:
        hits.append(("悬空引用", 0, "全文没有 第 N 问 到节的对照"))
    return hits


def report(paths):
    failures = 0
    for path in paths:
        hits = scan(path.read_text(encoding="utf-8"))
        for rule, line, detail in hits:
            print(f"{path}:{line}: {rule}: {detail}")
        print(f"{path}: {'OK' if not hits else f'{len(hits)} 处命中'}")
        failures += len(hits)
    return 1 if failures else 0


GOOD = """# 标题

正文按阶段分节, 第 1 问在 `## 测量前`, 第 4 与第 7 问在 `## 收益上限与端到端`.

## 测量前

短句.

## 收益上限与端到端

第 1 问的结果可复核.
"""

BAD = """# 标题

正文 —— 这里有破折号, 结果被丢掉了, 而且这句话故意写得非常非常长超过二十五个汉字这样扫描才会命中它, 第 4 问没有节对照, 用户说只要大致数字, `## 不存在的节` 也指不到.
"""


def selftest():
    ok = scan(GOOD) == []
    bad_rules = {rule for rule, _, _ in scan(BAD)}
    expected = {"破折号", "被动残句", "超长句", "悬空引用", "第三人称"}
    missing = expected - bad_rules
    for rule in sorted(bad_rules):
        print(f"自检命中: {rule}")
    if not ok:
        print("自检失败: 合格样本被误报", file=sys.stderr)
        return 2
    if missing:
        print(f"自检失败: 合格样本漏报 {sorted(missing)}", file=sys.stderr)
        return 2
    print("自检通过: 合格样本无异报, 违规样本五类规则全覆盖")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("paths", nargs="*", type=Path, help="待扫描的 SKILL.md")
    parser.add_argument("--selftest", action="store_true", help="跑内置合格/违规样本")
    args = parser.parse_args()
    if args.selftest:
        return selftest()
    if not args.paths:
        parser.error("需要至少一个路径")
    return report(args.paths)


if __name__ == "__main__":
    raise SystemExit(main())
