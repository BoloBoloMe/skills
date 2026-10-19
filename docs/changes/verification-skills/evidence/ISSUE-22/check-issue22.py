"""ISSUE-22 机械扫描: 粗估例外边界与指定长句.

两条规则:
1. 例外边界: `## 粗估与选型` 的豁免清单不得含 `## 基线与脚本固定前`; 该节必须把
   基线规划审查与脚本固定检查重新挂到那一节; 完成标准里也保留这两项.
2. 句子长度: 指定四段各自的每个句子 (以句号切分) 不超过 25 个汉字; 全文中每个
   子句 (以逗号/分号/冒号/句号切分) 也不超过 25 个汉字.

只管这些可判定的规则, 不做语义审读. 用法:
    uv run python check-issue22.py <SKILL.md 路径> [<SKILL.md 路径> ...]
    uv run python check-issue22.py --selftest
退出码 0 表示无命中, 1 表示有命中, 2 表示自检失败.
"""

import argparse
import re
import sys
from pathlib import Path

CJK = re.compile(r"[\u4e00-\u9fff]")
SENTENCE_SPLIT = re.compile(r"[.\u3002]")
CLAUSE_SPLIT = re.compile(r"[\u3002;:,.!?\uff1b\uff1a\uff0c]")
SECTION = "## 粗估与选型"
FIXING_SECTION = "## 基线与脚本固定前"
END_MARK = "## 判定"

# 四段锚点: 评审 STANDARDS-2 H1 点名的超长句所在段落.
ANCHORS = (
    "以下情形都会产出没有工作的快数字",
    "微结果旁边必须附用户端到端路径的实测",
    "同一轮只强制查两件事",
    "选型不算粗估",
)


def cjk_count(text):
    return len(CJK.findall(text))


def split_section(text):
    lines = text.splitlines()
    start = None
    for index, line in enumerate(lines):
        if line.strip() == SECTION:
            start = index
            break
    if start is None:
        return None
    end = len(lines)
    for index in range(start + 1, len(lines)):
        if lines[index].strip() == END_MARK:
            end = index
            break
    return lines[start:end]


def check_exemption(lines):
    """例外边界规则: 豁免清单不得把固定脚本检查一起省掉."""
    hits = []
    pattern = re.compile(r"不动用\s*(.+?)的完成标准")
    for line in lines:
        for block in pattern.findall(line):
            for name in re.findall(r"`(## [^`]+)`", block):
                if name.strip() == FIXING_SECTION:
                    hits.append("豁免清单仍含 " + FIXING_SECTION)
    return hits


def check_binding(lines):
    """边界规则的另一半: 规划审查与脚本固定检查必须仍被挂到那一节."""
    hits = []
    planning = [line for line in lines if FIXING_SECTION in line and "审查基线" in line]
    fixing = [line for line in lines if "团队入口" in line and "补齐" in line]
    if not planning:
        hits.append("粗估节没有保留基线规划审查句")
    if not fixing:
        hits.append("粗估节没有保留脚本固定检查句")
    return hits


def check_sentences(text):
    """句子长度规则: 锚点段逐句 25 字, 全文逐子句 25 字."""
    hits = []
    lines = text.splitlines()
    found = set()
    for number, line in enumerate(lines, 1):
        for anchor in ANCHORS:
            if anchor in line:
                found.add(anchor)
                for sentence in SENTENCE_SPLIT.split(line):
                    count = cjk_count(sentence)
                    if count > 25:
                        hits.append(
                            f"{number}: 长句 {count} 字 (锚点 {anchor}): {sentence.strip()[:40]}"
                        )
        for clause in CLAUSE_SPLIT.split(line):
            count = cjk_count(clause)
            if count > 25:
                hits.append(f"{number}: 长子句 {count} 字: {clause.strip()[:40]}")
    for anchor in ANCHORS:
        if anchor not in found:
            hits.append(f"0: 找不到锚点段: {anchor}")
    return hits


def scan(text):
    hits = []
    section = split_section(text)
    if section is None:
        hits.append(f"0: 找不到节 {SECTION}")
    else:
        hits.extend(check_exemption(section))
        hits.extend(check_binding(section))
    hits.extend(check_sentences(text))
    return hits


def report(paths):
    failures = 0
    for path in paths:
        hits = scan(path.read_text(encoding="utf-8"))
        for detail in hits:
            print(f"{path}: {detail}")
        print(f"{path}: {'OK' if not hits else f'{len(hits)} 处命中'}")
        failures += len(hits)
    return 1 if failures else 0


GOOD = """# 标题

## 粗估与选型

短句只说一件事.

- 粗估不动用 `## 重复与波动` 的完成标准.
- 粗估数字要用于规划时, 仍按 `## 基线与脚本固定前` 审查基线.
- 把粗估脚本固定成团队入口前, 仍按那一节补齐错误数与工作量.

以下情形都会产出没有工作的快数字. 无人迭代的生成器.

微结果旁边必须附用户端到端路径的实测. 实测走真实入口.

同一轮只强制查两件事: 第 4 问的失败计数与输出正确性.

选型不算粗估. 交替重复之后, 再按判定词给结论.

## 判定

短句.
"""

BAD = GOOD.replace(
    "短句只说一件事.",
    "这一句故意写得很长很长而且中间不放任何标点所以它一定会命中长子句规则.",
).replace(
    "- 粗估不动用 `## 重复与波动` 的完成标准.",
    "- 粗估不动用 `## 重复与波动`, `## 基线与脚本固定前` 的完成标准.",
).replace(
    "- 粗估数字要用于规划时, 仍按 `## 基线与脚本固定前` 审查基线.\n"
    "- 把粗估脚本固定成团队入口前, 仍按那一节补齐错误数与工作量.",
    "- 规划与固定沿用本节做法.",
).replace(
    "以下情形都会产出没有工作的快数字. 无人迭代的生成器.",
    "以下情形都会产出没有工作的快数字: 无人迭代的生成器, 无人 await 的异步任务,"
    " 算出结果又丢掉的代码, 运行时优化掉的计算, 把主要计算放在计时区外的脚本.",
).replace(
    "选型不算粗估. 交替重复之后, 再按判定词给结论.",
    "选型不算粗估: 在两个库或两套配置之间取舍时, 按完整对照处理两侧的版本,"
    " 数据, 缓存, 构建与配置条件, 一侧跑默认值就先调优它再测.",
)


def selftest():
    ok = scan(GOOD) == []
    bad = scan(BAD)
    rules = []
    for detail in bad:
        if "豁免清单" in detail:
            rules.append("豁免越界")
        elif "没有保留" in detail:
            rules.append("边界未挂回")
        elif "长句" in detail and "锚点" in detail:
            rules.append("锚点长句")
        elif "长子句" in detail:
            rules.append("长子句")
    missing = {"豁免越界", "边界未挂回", "锚点长句", "长子句"} - set(rules)
    for name in sorted(set(rules)):
        print(f"自检命中: {name}")
    if not ok:
        print(f"自检失败: 合格样本被误报 {scan(GOOD)}", file=sys.stderr)
        return 2
    if missing:
        print(f"自检失败: 违规样本漏报 {sorted(missing)}", file=sys.stderr)
        return 2
    print("自检通过: 合格样本无异报, 违规样本四类规则全覆盖")
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
