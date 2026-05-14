#!/usr/bin/env python3
"""Initialize a canonical HILE v2.24.1 execution package skeleton."""
import argparse
import os
from pathlib import Path
from datetime import datetime, timezone
import re

SLUG_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{0,80}$")

def safe_change_root(root_arg: str, change_slug: str) -> Path:
    if not SLUG_RE.fullmatch(change_slug):
        raise SystemExit("invalid change_slug: use lowercase letters, digits, _ or -, max 81 chars, no path separators")
    root = Path(root_arg).resolve()
    target = (root / change_slug).resolve()
    if target != root and root not in target.parents:
        raise SystemExit("invalid change_slug/root: target escapes --root")
    return target


def write_if_missing(path: Path, content: str):
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

def display_name_from_slug(change_slug: str) -> str:
    return change_slug.replace("_", " ").replace("-", " ").strip() or change_slug


def hile_human_start_content(change_slug: str, tier: str, source_handoff: str, planning_manifest_value: Path) -> str:
    title = display_name_from_slug(change_slug)
    strict_line = "2. [人类版 Strict Runbook](02-strict-runbook.md)：strict 执行的完整人类审核版 Runbook。\n3. [Runbook / Plan 确认审核](02-runbook-or-plan-review.md)：确认命令、边界和验证摘要。" if tier == "strict" else "2. [Runbook / Plan 确认审核](02-runbook-or-plan-review.md)：确认命令、边界和验证摘要。"
    return f"""# {title} HILE 人类审核入口

本目录保存 `{change_slug}` 的 HILE v2.24.1 执行资产。HILE 只执行已经由 HILP 批准并交接的范围；它不重新批准设计，不扩大文件边界，也不把执行失败伪装成方案变更。

## 本入口给谁看

这份文件是人类审核员进入执行包的第一页。审核员应从这里确认：来源 handoff 是否明确、执行分级是否合理、当前状态是什么、应该阅读哪些人类视图、是否已经到了需要确认 Runbook/Plan 或审核完成结果的节点。

## 当前执行上下文

| 项目 | 内容 |
|---|---|
| change slug | `{change_slug}` |
| 执行分级 | `{tier}` |
| 来源 HILP manifest | [`{planning_manifest_value.as_posix()}`](../{planning_manifest_value.as_posix()}) |
| 来源 HILP handoff | `{source_handoff}` |
| HILE manifest | [../manifest.md](../manifest.md) |
| 当前状态指针 | [../_current/human-status.md](../_current/human-status.md) |

## 建议阅读顺序

1. [入口检查摘要](01-intake-summary.md)：确认 HILP 批准、handoff、workspace 和范围门禁是否完整。
{strict_line}
4. [进度、失败与阻塞](03-progress-and-failures.md)：查看执行单元、ledger、失败或阻塞记录。
5. [验证与完成](04-verification-and-finish.md)：查看验证命令、证据、未验证项和残余风险。

## 当前需要审核什么

先打开 [../_current/human-status.md](../_current/human-status.md)。它应指向当前 review target：可能是待确认的 Runbook/Plan、失败取证记录，或完成审核包。

若当前处于待确认 Runbook/Plan 状态，审核员只应接受固定确认命令，不应把“继续”“可以了”“执行吧”当作正式确认。

```text
确认执行：确认执行 Runbook docs/changes/{change_slug}/execution/agent/03-runbook.yaml.md
确认执行：确认执行 Plan docs/changes/{change_slug}/execution/agent/03-plan.yaml.md
```

只使用实际存在且已通过校验的那一条命令。确认命令只授权当前 Runbook/Plan 的执行，不批准上游设计或蓝图。

## 审核员快速判断

- 如果缺少已批准 design、已批准 blueprint、closed-record handoff 或 workspace，停止 HILE，回到 HILP 补齐。
- 如果 Runbook/Plan 的 planned files 超出 handoff allowlist，停止执行，回到人工判断或 HILP phase-04。
- 如果执行中需要修改 prohibited 文件、SQL、依赖、数据库结构或 handoff 未允许的行为，停止执行，回到 HILP phase-04。
- 如果验证命令无法运行，必须记录阻塞原因、替代证据和残余风险；不得声明“已通过”。
- 如果完成审核缺少 actual changed-files gate、验证证据或未验证项说明，不应接受完成。

---

上一页：无  
下一页：[入口检查摘要](01-intake-summary.md)
"""


def scaffold_page(title: str, body: str, previous_link: str | None, next_link: str | None) -> str:
    previous = f"上一页：[{previous_link[0]}]({previous_link[1]})" if previous_link else "上一页：无"
    next_ = f"下一页：[{next_link[0]}]({next_link[1]})" if next_link else "下一页：无"
    return f"""# {title}

{body}

---

{previous}  
{next_}  
回到入口：[00-start.md](00-start.md)
"""


def initial_human_status_content(change_slug: str, tier: str) -> str:
    return f"""# Current Human Status

当前状态：HILE 执行包已初始化，尚未完成 intake、repo-aware Plan/Runbook、执行或验证。

- change slug：`{change_slug}`
- execution tier：`{tier}`
- 审核入口：[../human/00-start.md](../human/00-start.md)
- HILE manifest：[../manifest.md](../manifest.md)

下一步：完成入口检查后，生成对应的人类视图和 agent 视图。standard 执行需要 Plan；strict 执行需要 agent Runbook 与完整的人类版 Strict Runbook。
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("change_slug")
    ap.add_argument("--root", default="docs/changes", help="Root containing change packages. Default: docs/changes")
    ap.add_argument("--source-handoff", required=True, help="Path or asset_ref for the HILP execution handoff")
    ap.add_argument("--planning-manifest", required=True, help="Path to HILP planning/manifest.md")
    ap.add_argument("--allow-absolute-source-manifest", action="store_true", help="Persist an absolute source_hilp_manifest path. Default is a relative path for portability.")
    ap.add_argument("--tier", default="standard", choices=["tiny", "standard", "strict"])
    args = ap.parse_args()
    change_root = safe_change_root(args.root, args.change_slug)
    execution = change_root / "execution"
    for name in ["human", "agent", "review-pack", "_current"]:
        (execution / name).mkdir(parents=True, exist_ok=True)
    now = datetime.now(timezone.utc).isoformat()
    planning_manifest = Path(args.planning_manifest)
    if planning_manifest.is_absolute() and args.allow_absolute_source_manifest:
        planning_manifest_value = planning_manifest
    else:
        # Persist source_hilp_manifest relative to execution/manifest.md for portability.
        # This handles repo-root inputs like docs/changes/demo/planning/manifest.md
        # and change-root inputs like planning/manifest.md.
        if planning_manifest.is_absolute():
            planning_abs = planning_manifest
        elif (Path.cwd() / planning_manifest).exists():
            planning_abs = Path.cwd() / planning_manifest
        elif (change_root / planning_manifest).exists():
            planning_abs = change_root / planning_manifest
        else:
            planning_abs = Path.cwd() / planning_manifest
        execution_abs = execution.resolve()
        try:
            rel = os.path.relpath(planning_abs.resolve(strict=False), execution_abs)
            planning_manifest_value = Path(rel)
        except Exception:
            planning_manifest_value = Path("..") / "planning" / "manifest.md"
    manifest_content = f"""# HILE Execution Manifest

```yaml
manifest:
  schema_version: "2.24.1"
  protocol_version: "2.24.1"
  change_slug: {args.change_slug}
  protocol: HILE
  source_hilp_manifest: {planning_manifest_value.as_posix()}
  source_handoff_ref: {args.source_handoff}
  execution_tier: {args.tier}
  package_stage: initialized
  intake_status: draft
  current_assets:
    intake_summary: null
    current_runbook: null
    current_plan: null
    tiny_inline_record: null
    ledger: null
    unit_summaries: null
    verification_evidence: null
    failure_forensics: null
    completion_review: null
  asset_registry: []
  current_pointers:
    human_status: _current/human-status.md
    agent_directory: agent/00-directory.md
    active_runbook_or_plan: null
    latest_runbook_or_plan: null
    latest_verification: null
    latest_completion_review: null
  last_updated_at: {now}
```
"""
    write_if_missing(execution / "manifest.md", manifest_content)
    write_if_missing(execution / "human/00-start.md", hile_human_start_content(args.change_slug, args.tier, args.source_handoff, planning_manifest_value))
    write_if_missing(
        execution / "human/01-intake-summary.md",
        scaffold_page(
            "HILE 入口检查摘要",
            "当前执行包已初始化，但尚未记录完整 intake 结果。正式进入执行前，必须确认已批准 design、已批准 blueprint、closed-record handoff、workspace、allowed/prohibited scope、verification contract 和 stop conditions。",
            ("审核入口", "00-start.md"),
            ("Runbook / Plan 确认审核", "02-runbook-or-plan-review.md"),
        ),
    )
    if args.tier == "strict":
        write_if_missing(
            execution / "human/02-strict-runbook.md",
            scaffold_page(
                "HILE Strict Runbook（人类审核版）",
                "当前 strict 执行包尚未生成完整人类版 Runbook。生成 agent/03-runbook.yaml.md 后，必须把 source refs、repo context、execution units、allowed/prohibited files、dependencies、repo observations、implementation steps、source-level change intent、verification plan、risk checks、stop conditions、pre-modify gate 和 confirmation command 全部重组到本文件，供人类审核员阅读。",
                ("入口检查摘要", "01-intake-summary.md"),
                ("Runbook / Plan 确认审核", "02-runbook-or-plan-review.md"),
            ),
        )
    write_if_missing(
        execution / "human/02-runbook-or-plan-review.md",
        scaffold_page(
            "Runbook / Plan 确认审核",
            "当前执行包尚未生成待确认的 Runbook 或 Plan。生成后，本页应给出本次会做什么、不会做什么、会改哪些文件、失败时停在哪里、验证标准，以及唯一固定确认命令。strict 执行还必须链接到完整的人类版 Strict Runbook。",
            ("入口检查摘要", "01-intake-summary.md"),
            ("进度、失败与阻塞", "03-progress-and-failures.md"),
        ),
    )
    write_if_missing(
        execution / "human/03-progress-and-failures.md",
        scaffold_page(
            "进度、失败与阻塞",
            "当前执行包尚未开始执行。执行后，本页应概述 execution ledger、unit summaries、失败或阻塞原因，以及是否需要回到 HILP phase-04。",
            ("Runbook / Plan 确认审核", "02-runbook-or-plan-review.md"),
            ("验证与完成", "04-verification-and-finish.md"),
        ),
    )
    write_if_missing(
        execution / "human/04-verification-and-finish.md",
        scaffold_page(
            "验证与完成",
            "当前执行包尚未产生验证证据。完成前，本页必须记录验证命令、执行时间、结果、actual changed-files gate、未验证项、残余风险和 completion review 链接。",
            ("进度、失败与阻塞", "03-progress-and-failures.md"),
            None,
        ),
    )
    write_if_missing(execution / "agent/00-directory.md", "# HILE Agent Directory\n\nSee the skill canonical `references/agent/00-directory.md`.\n")
    write_if_missing(execution / "_current/human-status.md", initial_human_status_content(args.change_slug, args.tier))
    write_if_missing(execution / "_current/agent-directory.md", "# Current Agent Directory\n\n[Agent directory](../agent/00-directory.md)\n")
    write_if_missing(execution / "_current/active-runbook-or-plan.md", "# Active Runbook Or Plan\n\nNo active runbook or plan yet.\n")
    print(execution)

if __name__ == "__main__":
    main()
