#!/usr/bin/env python3
"""check-diff-anchors: 核对两份 reference/PROVENANCE.md 的差异表与上游原文的对应关系 (TS-001).

逐行核对: 差异表每一行都指到上游原文行号与本地行号, 引文必须真的出现在所标行.
另外核对两处评审发现:
- H5: 不把未变化的 frontmatter 记为调用模式改变 (上游第 4 行原本已有 disable-model-invocation).
- H6: 不声称 check_skill.py 校验标题结构, 标题结构标为人工检查.

只做静态审计 (差异范围, 引文位置), 不判断译文忠实性.

用法:
  uv run python check-diff-anchors.py [--repo-root <路径>] [--markdown]
退出码 0 表示全部通过, 1 表示有失败项.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass
from pathlib import Path

UPSTREAM_DIR = "docs/changes/verification-skills/evidence/ISSUE-13/upstream"
PACKAGES = {
    "workflow/blast-radius": {
        "upstream": "blast-radius-SKILL.md",
        "skill": "workflow/blast-radius/SKILL.md",
        "provenance": "workflow/blast-radius/reference/PROVENANCE.md",
        "heading_line": "# Blast radius",
    },
    "workflow/benchmark-checklist": {
        "upstream": "benchmark-checklist-SKILL.md",
        "skill": "workflow/benchmark-checklist/SKILL.md",
        "provenance": "workflow/benchmark-checklist/reference/PROVENANCE.md",
        "heading_line": "# Benchmark checklist",
    },
}


@dataclass(frozen=True)
class Anchor:
    """差异表一行的上游/本地原文位置."""

    package: str
    row: int
    upstream_lines: tuple[int, int] | None
    upstream_has: str
    upstream_absent: str | None
    local_lines: tuple[int, int] | None
    local_has: str
    note: str


ANCHORS: tuple[Anchor, ...] = (
    # ---- workflow/blast-radius ----
    Anchor("workflow/blast-radius", 1, (2, 4), 'description: "Find what a change could break', None, (2, 4), "description: 调查变更在 diff 之外", "frontmatter 上游第 4 行原本就是 disable-model-invocation: true, 只改 description 措辞"),
    Anchor("workflow/blast-radius", 2, (7, 7), "# Blast radius", None, (7, 7), "调查一个变更在别处会破坏什么", "上游 H1 在本地没有对应标题, 本地从引言起"),
    Anchor("workflow/blast-radius", 3, (11, 11), "Companion to `how` and `why`", None, (15, 25), "gh pr view", "上游 companion 指针换成第 1 节内联历史定位命令"),
    Anchor("workflow/blast-radius", 4, (15, 27), "### How sure are you", None, (37, 47), "## 3. 给每个事实标证据级别", "上游 H2+H3 拍平成第 3 节与第 4 节"),
    Anchor("workflow/blast-radius", 5, (33, 33), "Use `why` step 2 to pull the PR and commits", None, (17, 25), "git log --oneline -20", "上游指针换成可直接执行的 git 命令"),
    Anchor("workflow/blast-radius", 6, (35, 35), "Solid versus React", None, (33, 33), "运行时机 (注册时机, 异步, 卸载, 生命周期)", "框架专名换成通用运行时机说法"),
    Anchor("workflow/blast-radius", 7, (36, 36), "Same rules as `why`", None, (66, 68), "真实 file:line", "诚实纪律内联到第 5 节"),
    Anchor("workflow/blast-radius", 8, (36, 36), "a search that finds nothing is still an answer", None, (68, 68), "符号检索没有结果也是答案", "空结果报告要求收紧为写明范围与边界"),
    Anchor("workflow/blast-radius", 9, (37, 37), "Write a script or test that runs the real code", None, (49, 60), "## 4. 写可失败的证明脚本", "一句要求扩成可失败脚本的完成标准"),
    Anchor("workflow/blast-radius", 10, (38, 38), "run it as an `arena`", None, (72, 80), "reference/multimodel.md", "arena 产物流程换成 use-herdr/llm-select 承接"),
    Anchor("workflow/blast-radius", 11, (48, 48), "Write it through `unslop`", None, (92, 92), "reference/report-style-zh.md", "英文文风清单换成中文报告规则"),
    Anchor("workflow/blast-radius", 12, None, "", r"permission|authoriz|approv", (55, 55), "只读调查不需要额外授权", "上游无写入授权句, 本地新增"),
    Anchor("workflow/blast-radius", 13, None, "", r"verifier|acceptance|delegate|subagent", (9, 9), "自己调查并运行证明是我的角色", "上游无角色句, 本地按 D025 新增"),
    Anchor("workflow/blast-radius", 14, None, "", r"only one model", (77, 77), "只有一款模型可用", "上游无单模型缺口处理, 本地新增"),
    Anchor("workflow/blast-radius", 15, (46, 46), "Before you merge", None, (92, 92), "不自动合并", "上游只有合并前检查项, 没有交付边界句"),
    Anchor("workflow/blast-radius", 16, (48, 48), "strip anything private", None, (92, 92), "对外发出前脱敏", "原意保留"),
    # ---- workflow/benchmark-checklist ----
    Anchor("workflow/benchmark-checklist", 1, (2, 4), 'description: "Vet a perf measurement', None, (2, 4), "description: 报告或采信性能数字前的测量核查", "frontmatter 上游第 4 行原本就是 disable-model-invocation: true, 只改 description 措辞"),
    Anchor("workflow/benchmark-checklist", 2, (7, 7), "# Benchmark checklist", None, (7, 7), "# 性能测量核查", "H1 中文化, 层级不变"),
    Anchor("workflow/benchmark-checklist", 3, (9, 11), "one run is enough", None, (98, 108), "## 粗估与选型", "粗估例外后移到粗估与选型节"),
    Anchor("workflow/benchmark-checklist", 4, (13, 17), "## Before you run anything", None, (30, 38), "## 测量前", "三条测量前检查保留并收紧"),
    Anchor("workflow/benchmark-checklist", 5, (19, 27), "## The questions", None, (40, 96), "## 两侧按生产方式调优", "单节七个编号问题拆成六个测量阶段节"),
    Anchor("workflow/benchmark-checklist", 6, (21, 21), "`pidstat`", None, (78, 82), "用分析器找限制因素时", "工具名不逐项列, 限制因素规则保留"),
    Anchor("workflow/benchmark-checklist", 7, (23, 23), "Compare bytes per second with disk and network bandwidth", None, (72, 72), "每秒字节数对磁盘与网络带宽", "物理上限三组算式补齐"),
    Anchor("workflow/benchmark-checklist", 8, (24, 24), "If the script does not count errors, add the count", None, (58, 58), "脚本没计数时", "改为授权内独立脚本补计数"),
    Anchor("workflow/benchmark-checklist", 9, (25, 25), "at least 5 times, alternating", None, (50, 50), "每侧至少 5 次", "交替重复与统计判断逐条保留"),
    Anchor("workflow/benchmark-checklist", 10, (26, 26), "measure the end-to-end path", None, (76, 76), "补测真实入口的端到端", "端到端实测保留"),
    Anchor("workflow/benchmark-checklist", 11, (27, 27), "Lazy code", None, (60, 60), "无人迭代的生成器", "工作是否真的发生保留并列举"),
    Anchor("workflow/benchmark-checklist", 12, (29, 34), "## Report", None, (110, 122), "## 判定", "Report 四条拆成判定与对外报告两节"),
    Anchor("workflow/benchmark-checklist", 13, (36, 39), "## Other perf material", None, (86, 96), "## 基线与脚本固定前", "两套 playbook 指针换成检查接入要求"),
    Anchor("workflow/benchmark-checklist", 14, None, "", r"permission|authoriz|approv", (11, 11), "## 输入与授权", "上游无输入定义与写入授权, 本地新增"),
    Anchor("workflow/benchmark-checklist", 15, None, "", r"temporary|one-off|throwaway", (15, 15), "## 一次性实验的边界", "上游无一次性实验边界, 本地新增"),
    Anchor("workflow/benchmark-checklist", 16, None, "", r"merge|push", (124, 124), "这份清单只产出草稿与判定", "上游无交付边界, 本地按 D024 新增"),
)

# 差异表里不得出现的旧说法: 把未变化的调用方式记成改变.
FORBIDDEN_INVOCATION_CLAIM = re.compile(r"调用方式从[^|]*改为")
REQUIRED_NO_CHANGE = ("上游", "第 4 行", "disable-model-invocation", "调用方式没有改变")


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def diff_rows(text: str) -> list[str]:
    """取出差异表的正文行 (去掉表头与分隔行)."""
    start = text.index("## 逐项差异表")
    end = text.index("## 没有搬入的部分")
    rows = []
    for line in text[start:end].splitlines():
        if not line.startswith("| "):
            continue
        if line.startswith("| 源版位置") or set(line) <= {"|", "-", " "}:
            continue
        rows.append(line)
    return rows


def cell(row: str, index: int) -> str:
    return [part.strip() for part in row.strip().strip("|").split("|")][index]


def esc(value: str) -> str:
    """表格单元里的竖线转义, 避免把 markdown 表拆坏."""
    return value.replace("|", "\\|")


def slice_lines(lines: list[str], span: tuple[int, int]) -> str:
    return "\n".join(lines[span[0] - 1 : span[1]])


def where(span: tuple[int, int]) -> str:
    """单行写 "第 N 行", 跨行写 "第 N-M 行"."""
    return f"第 {span[0]} 行" if span[0] == span[1] else f"第 {span[0]}-{span[1]} 行"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", default=None)
    parser.add_argument("--markdown", action="store_true")
    args = parser.parse_args()
    root = Path(args.repo_root).resolve() if args.repo_root else Path(__file__).resolve().parents[5]

    failures: list[str] = []
    checks = 0
    rendered: list[str] = []

    for package, files in PACKAGES.items():
        provenance = read(root / files["provenance"])
        upstream = read(root / UPSTREAM_DIR / files["upstream"])
        local = read(root / files["skill"])
        upstream_lines = upstream.splitlines()
        local_lines = local.splitlines()

        rows = diff_rows(provenance)
        anchors = [anchor for anchor in ANCHORS if anchor.package == package]
        checks += 1
        if len(rows) != len(anchors):
            failures.append(f"[{package}] 差异表 {len(rows)} 行, 对照记录 {len(anchors)} 条, 条数不一致")

        rendered.append(f"### {package}\n")
        rendered.append("| 行 | 上游原文位置与引文 | 本地位置与引文 | 对照结论 |")
        rendered.append("| --- | --- | --- | --- |")

        for anchor in anchors:
            label = f"[{package} 差异表第 {anchor.row} 行]"
            if anchor.upstream_lines is None:
                checks += 1
                if re.search(anchor.upstream_absent or "", upstream, re.IGNORECASE):
                    failures.append(f"{label} 声称上游没有, 但上游原文命中 {anchor.upstream_absent}")
                upstream_cell = f"无对应行; 全文无 `{anchor.upstream_absent}`"
            else:
                span = slice_lines(upstream_lines, anchor.upstream_lines)
                checks += 1
                if anchor.upstream_has not in span:
                    failures.append(f"{label} 上游第 {anchor.upstream_lines[0]}-{anchor.upstream_lines[1]} 行找不到引文: {anchor.upstream_has}")
                upstream_cell = f"{where(anchor.upstream_lines)}: `{anchor.upstream_has}`"

            checks += 1
            if anchor.local_lines is None or anchor.local_has not in slice_lines(local_lines, anchor.local_lines):
                failures.append(f"{label} 本地第 {anchor.local_lines} 行找不到引文: {anchor.local_has}")
                local_cell = f"{where(anchor.local_lines)}: `{anchor.local_has}`"
            else:
                local_cell = f"{where(anchor.local_lines)}: `{anchor.local_has}`"

            rendered.append(f"| {anchor.row} | {esc(upstream_cell)} | {esc(local_cell)} | {esc(anchor.note)} |")

        # H5: 不把未变的调用方式记成改变.
        for index, row in enumerate(rows, start=1):
            checks += 1
            if FORBIDDEN_INVOCATION_CLAIM.search(row):
                failures.append(f"[{package} 差异表第 {index} 行] 仍把调用方式记为改变: {cell(row, 2)}")

        checks += 1
        frontmatter_row = rows[0]
        for needle in REQUIRED_NO_CHANGE:
            checks += 1
            if needle not in frontmatter_row:
                failures.append(f"[{package} 差异表第 1 行] 缺少声明: {needle}")

        # H6: 标题结构不得归给 check_skill.py.
        checks += 1
        if "不检查标题" not in provenance:
            failures.append(f"[{package}] 没有写明 check_skill.py 不检查标题")
        checks += 1
        heading_row = rows[1]
        if "人工" not in cell(heading_row, 3):
            failures.append(f"[{package} 差异表第 2 行] 标题结构未标为人工检查: {cell(heading_row, 3)}")
        checks += 1
        if "check_skill.py" in cell(heading_row, 3) and "不检查标题" not in cell(heading_row, 3):
            failures.append(f"[{package} 差异表第 2 行] 仍把标题结论挂在 check_skill.py 上")
        checks += 1
        if "人工标题结构检查" not in provenance:
            failures.append(f"[{package}] 标题结构小节未标为人工检查")

        rendered.append("")

    print(f"checks={checks} failures={len(failures)}")
    for item in failures:
        print(f"FAIL {item}")
    if args.markdown:
        print()
        print("\n".join(rendered))
    if failures:
        return 1
    print("OK 两份差异表逐行指到上游原文与本地行, 调用方式与标题结构说法已更正")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
