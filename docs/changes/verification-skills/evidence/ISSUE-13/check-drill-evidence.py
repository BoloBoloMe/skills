#!/usr/bin/env python3
"""check-drill-evidence: 核对两个复刻的行为保真演练记录可对照 (TS-002, TC-108).

只做记录完整性核对: 演练报告是否记了固定项, 两份差异记录是否真的被对照,
会话转录是否存在. 不判断行为是否正确, 行为结论由演练报告与原始输出承担.

用法: uv run python check-drill-evidence.py [--repo-root <路径>]
退出码 0 表示记录齐全, 1 表示有缺失项.
"""

from __future__ import annotations

import argparse
import re
from pathlib import Path

FIXED_SHA = "4382e687a50b8d2c5ce4d141d001186589cff8d5"

REPORT_SECTIONS = (
    "## 固定记录",
    "## blast-radius 演练",
    "## benchmark-checklist 演练",
    "## 对照差异记录",
    "## 结论",
)

COMMON_FIELDS = (
    "待测源路径",
    "提交",
    "宿主",
    "pi 版本",
    "加载方式",
    "临时项目",
    "起始提交",
    "会话名",
    "提交渠道",
    "原始输出",
    "清理结果",
)

BLAST_FIELDS = ("/skill:blast-radius", "证据级别", "file:line", "证明脚本", "未证实")
BENCH_FIELDS = (
    "/skill:benchmark-checklist",
    "交替",
    "中位数",
    "极差",
    "失败",
    "判定",
)
RED_FIELDS = ("变异版", "偏离", "红轮")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=None)
    args = parser.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[5]
    evidence = root / "docs/changes/verification-skills/evidence/ISSUE-13"

    failures: list[str] = []
    checks = 0

    report = evidence / "TS-002-drill.md"
    checks += 1
    if not report.is_file():
        print(f"checks={checks} failures=1")
        print(f"FAIL 缺少演练报告: {report}")
        return 1
    text = report.read_text(encoding="utf-8")

    for section in REPORT_SECTIONS:
        checks += 1
        if section not in text:
            failures.append(f"[TS-002-drill.md] 缺少小节: {section}")

    for field in COMMON_FIELDS + BLAST_FIELDS + BENCH_FIELDS + RED_FIELDS:
        checks += 1
        if field not in text:
            failures.append(f"[TS-002-drill.md] 缺少固定项: {field}")

    checks += 1
    if FIXED_SHA not in text:
        failures.append("[TS-002-drill.md] 未引用固定 SHA")

    sessions = sorted((evidence / "sessions").glob("*.jsonl"))
    checks += 1
    if len(sessions) < 2:
        failures.append(f"[sessions/] 会话转录不足两份: 现有 {len(sessions)}")

    skills_seen = {name: False for name in ("blast-radius", "benchmark-checklist")}
    for transcript in sessions:
        body = transcript.read_text(encoding="utf-8", errors="replace")
        for name in skills_seen:
            # pi 把加载来源写成 <skill name="X" location="/tmp/.../.agents/skills/X/SKILL.md">,
            # 在会话转录里被 JSON 转义成 \" ; 只认这种点名加载标记, 不认可用技能清单.
            pattern = (
                r'skill name=\\?"' + name + r'\\?" location=\\?"[^"]*'
                r'\.agents/skills/' + name + r'/SKILL\.md'
            )
            if re.search(pattern, body):
                skills_seen[name] = True
    for name, ok in skills_seen.items():
        checks += 1
        if not ok:
            failures.append(f"[sessions/] 没有从临时项目 .agents/skills/{name}/ 加载的转录")

    for package in ("workflow/blast-radius", "workflow/benchmark-checklist"):
        provenance = root / package / "reference/PROVENANCE.md"
        checks += 1
        if not provenance.is_file():
            failures.append(f"[{package}] 缺少 reference/PROVENANCE.md")
            continue
        rows = [
            line
            for line in provenance.read_text(encoding="utf-8").splitlines()
            if line.startswith("|") and "| --- |" not in line
        ]
        checks += 1
        if len(rows) < 5:
            failures.append(f"[{package}] 差异表条目不足: {len(rows)} 行")

    print(f"checks={checks} failures={len(failures)}")
    for item in failures:
        print(f"FAIL {item}")
    if failures:
        return 1
    print("OK 两个复刻的演练记录与差异记录可对照")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
