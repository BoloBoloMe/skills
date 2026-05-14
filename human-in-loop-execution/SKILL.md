---
name: human-in-loop-execution
description: "use for two cases only: suggestion-only preflight when a request provides an approved v2.24.1 hilp execution handoff or explicitly asks to execute an approved hilp handoff with scope gate, audit trail, verification gate, or multi-agent execution; formal hile protocol mode only after the user explicitly asks to use hile or confirms the suggestion and after a current hilp handoff plus workspace are available. if the user asks for controlled execution without an approved hilp handoff, route them to hilp instead of starting hile. do not suggest for ordinary coding, debugging, test explanation, or lightweight implementation unless the user explicitly asks to execute an approved hilp handoff."
---

# 人在回路执行

## 启动规则

This Skill is the HILE control entrypoint. It has two layers:

1. Suggestion layer: when the user provides an approved v2.24.0 HILP execution handoff, or explicitly asks to execute an approved HILP handoff with scope gate, audit trail, verification gate, or multi-agent execution, briefly suggest HILE and ask for confirmation. Do not suggest HILE for ordinary coding, debugging, test explanation, lightweight implementation, or controlled execution requests that do not include an approved HILP handoff; route those requests to HILP instead.
2. Execution layer: enter formal HILE only after the user explicitly asks to use HILE / human-in-loop execution / this skill, or confirms the suggestion.

Before confirmation, do not run intake, create an execution package, run file-scope gates, modify files, or claim that HILE has started. After confirmation, first read [agent directory](references/agent/00-directory.md), then load only the shortest path needed for intake, tiering, runbook/plan, verification, debugging, review, or finish.

HILE executes only within the scope of a current HILP handoff. It does not perform planning, replace approvals, expand file scope, or hide failures as blueprint changes.

If the user asks for controlled execution but does not provide or reference a current approved HILP handoff, do not start formal HILE intake. Explain that HILE requires an approved HILP execution handoff and route the user to HILP phase-02/phase-03/phase-05 as appropriate. Do not create an execution package, run intake, run file-scope gates, or modify files.

Assets from earlier pilot protocols are intentionally unsupported in v2.24.1. If a user provides an older handoff, ask them to regenerate a v2.24.0 HILP handoff.

## 协议版本号规范

HILE 使用三段版本号 `x.y.z`。`x.y` 是 HILP/HILE 共享的大协议线，当前为 `2.24`；`z` 是各协议自己的小版本迭代号，可以不一致。当前 HILE 版本为 `v2.24.1`。跨协议兼容性以 `references/shared/compatibility-contract.yaml` 为准，不要求 HILP 与 HILE 三段版本完全相等。

## Runtime Preconditions

正式 HILE 执行依赖可确认、可读取、可写入的 repo/worktree workspace，并依赖随附 Python 脚本完成 intake、allowed-files、manifest 和验证记录门禁。无法确认 workspace、不能读取 HILP handoff/manifest、不能写文件、不能运行脚本、或无法取得实际 changed files 时，只能输出草案、阻塞说明或人工检查清单；不得声称已完成 intake pass、已执行修改、allowed-files 已通过、验证已通过或 execution manifest 已完成。

## 入口前提

Formal HILE intake requires all of the following:

- Approved design: `phase-02/design-choice@vN` with `lifecycle_state=approved`.
- Approved blueprint: `phase-03/implementation-blueprint@vM` with `lifecycle_state=approved`.
- Current execution handoff: `phase-05/execution-handoff@vK` with `lifecycle_state=closed-record` and `record_role=handoff-record`.
- Explicit execution workspace / repo / worktree root.

Missing design approval returns to HILP phase-02. Missing blueprint approval returns to phase-03. Missing valid handoff, scope, prohibited files, stop conditions, verification contract, or workspace returns to phase-05. New facts that invalidate approval return to HILP phase-04.

Do not accept non-canonical handoff formats as a full intake pass.

## 双视图原则

所有正式执行资产都必须拆成两套视图：

- **人类审核视图**：自然语言说明本次会做什么、不会做什么、如何确认执行、失败后发生了什么、验证证据是什么。
- **agent 执行视图**：结构化记录 runbook、plan、execution_unit、allowed_files、stop_conditions、ledger、unit_summary、verification evidence。

Plan/Runbook 在任何文件修改前必须同时记录“源码级修改意图”（`source_level_change_intent`）：它描述每个 planned file 中计划影响的类、函数、枚举、字段、配置键、路由、测试或其他符号级位置，以及计划新增、修改、删除或保留的源码行为。它不是最终 patch 或 diff，不得伪造尚未执行的实际代码变更；但必须足够让人类在执行前判断是否会改错位置、漏掉路径或破坏关键行为。人类视图必须用中文展示同一信息，作为代码审查入口；在 strict 人类版 Runbook 中，源码级修改意图必须嵌入对应 execution unit 的“分单元详细 Runbook”小节，不能生成独立的全局章节。

布局见 [共享资产布局](references/shared/execution-asset-layout.md)。人类视图不得被 `allowed_files`、`parallel_group`、`shared_state` 等字段淹没；agent 视图不得缺少约束字段。

`execution/human/00-start.md` 是人类审核员入口，不能是占位空文件。正式执行包必须让审核员从这里看到：本包执行什么变更、来自哪个 HILP handoff、当前执行分级、当前状态、阅读顺序、当前需要审核或确认的 review target、固定确认/审查命令、失败时回到哪里。

strict 执行生成 `agent/03-runbook.yaml.md` 时，必须同时生成完整的人类版 Strict Runbook（默认 `human/02-strict-runbook.md`）。该文档面向审核员组织内容，但不得丢失 agent runbook 信息：source refs、repo context、execution units、allowed/prohibited files、dependencies、repo observations、implementation steps、verification plan、risk checks、stop conditions、pre-modify gate 和 confirmation command 都必须可追溯呈现。不要要求人类直接审核 agent YAML 作为主入口。

## 执行规模分级

先按 [执行分级](references/agent/02-execution-tiers.md) 分类：

- **tiny**：单文件、小修复、低风险；需要入口检查和验证记录，不强制 runbook、ledger、unit summary。
- **standard**：多步骤或多文件常规执行；需要 plan、验证记录，必要时记录简化 ledger。
- **strict**：高风险、并行、迁移、共享状态、复杂验证或 HILP handoff 包含 `execution_plan_contract`；需要 runbook、用户确认、unit summary、ledger、review、failure forensics 纪律。

分级可以升级；不能用 tiny 规避蓝图约束或验证证据。



## Repo-aware Plan / Runbook 强制门

HILE must not modify files directly from HILP execution units. Before any file modification, HILE must inspect the actual repo/worktree and generate a repository-aware Plan or Runbook that maps each source execution unit to concrete planned files, repo observations, implementation steps, source-level change intent, verification plan, risk checks, and stop conditions.

If a valid Plan or Runbook cannot be generated, execution must stop and route to human review, HILP phase-04, or failure forensics. Standard execution requires a Plan; strict execution requires a Runbook. Strict execution also requires a complete human-readable Strict Runbook view before asking for confirmation. For standard and strict execution, file modification is forbidden until the Plan or Runbook is generated, validated, rendered into the required human review view, and explicitly confirmed with the fixed command. There is no standard no-confirmation path. Any execution that skips separate confirmation must qualify under the tiny exception rules; otherwise it must wait for the fixed Plan or Runbook confirmation command.

Tiny execution may skip a separate confirmation review only when all tiny exception conditions are true: exactly one execution unit, a very small planned file set, no high-risk or prohibited scope, verification available, no repo observation contradicting HILP assumptions, and an explicit same-context user instruction to execute. If any condition fails, tiny must also generate and confirm a Plan.

## 用户确认语义

HILE 只接受执行确认，不接受设计或蓝图批准。需要确认时，必须使用固定命令：

```text
确认执行：确认执行 Runbook <path>
确认执行：确认执行 Plan <path>
```

“继续”“可以了”“执行吧”不能直接授权 runbook/plan；只能触发 agent 回显唯一确认命令并等待用户回复。确认执行只授权当前 runbook/plan 的执行，不会批准上游设计或蓝图。若上游批准缺失或失效，停止并回到 HILP.

## 最短执行路径

Use [agent directory](references/agent/00-directory.md) for routing:

- Existing handoff, start execution: directory -> intake -> tiers -> routing -> runbook/plan -> confirmation decision.
- Tiny execution: directory -> intake -> tiering -> tiny plan -> scope gate -> verification -> completion record.
- Strict runbook: directory -> intake -> runbook/plan contract -> confirmation -> execution units -> ledger/unit summaries -> verification -> review -> finish.
- Failure or abnormal evidence: directory -> verification/debugging/review -> failure forensics -> return to HILP if planning scope changed.
- Parallel work: directory -> execution unit contract -> subagent/dispatch contract -> ledger summary.

Do not infer behavior from older pilot prompt templates or obsolete handoff shapes. If current v2.24.1 rules do not cover a supplied handoff, stop and request a regenerated v2.24.0 HILP handoff.

## Manifest 与版本纪律

正式执行资产每次进入待确认、执行中、完成、失败、阻塞或回交 HILP 状态时，都要更新 execution manifest。manifest schema、`_current/` 指针和版本规则见 [canonical protocol schema](references/shared/canonical-protocol-schema.yaml)、[执行资产布局](references/shared/execution-asset-layout.md) 与 [manifest 与版本规则](references/shared/manifest-and-versioning.md)。

## 完成声明纪律

任何完成声明、提交、合并或交付前，必须有新鲜验证证据。不能说“应该通过”“看起来没问题”。必须说明验证命令、执行时间、结果、未验证项和残余风险。若验证无法运行，说明原因并给出替代证据；不能伪造通过。


## 工程化门禁

HILE 执行不是纯文本纪律；必须把随附脚本作为执行门禁：

1. 正式落盘 execution package 前运行 `scripts/init_execution_package.py <change_slug> --root docs/changes --source-handoff <handoff-ref-or-path> --planning-manifest <planning-manifest-path> --tier tiny|standard|strict`。
2. 声明完整 intake pass 前运行 `scripts/validate_handoff_intake.py <handoff.md> --planning-manifest <planning/manifest.md> --workspace <repo-or-worktree-root>`。没有 `--planning-manifest` 时只能使用 `--allow-partial`，且不得声明完整 intake pass。
3. 修改文件前，先生成 repo-aware Plan/Runbook，其中每个 unit plan 必须包含 `source_level_change_intent`；提取 planned files，并运行：`scripts/check_allowed_files.py --handoff <handoff.md> --planned-file <planned-files.txt> --workspace <repo-or-worktree-root>`。把 planned-files gate 的 pass/fail 结果写回 Plan/Runbook 的 `pre_modify_gate.planned_files_check`。
4. planned-files gate 通过并写回 Plan/Runbook 后，再运行 `scripts/validate_plan_or_runbook.py <plan-or-runbook.md> --handoff <handoff.md> --execution-manifest <execution/manifest.md> --workspace <repo-or-worktree-root>`；该 validator 会校验 `pre_modify_gate` 记录并重新检查 planned files 是否仍在 scope 内。
5. 修改后、完成声明前，对实际变更文件运行：`scripts/check_allowed_files.py --handoff <handoff.md> --changed-file <actual-changed-files.txt> --workspace <repo-or-worktree-root>`。
6. 记录验证证据时优先运行 `scripts/write_verification_record.py`。
7. completion review 或打包前运行 `scripts/validate_execution_manifest.py <execution/manifest.md> --check-paths --planning-manifest <planning/manifest.md>`，并运行 `scripts/validate_yaml_blocks.py <skill-or-package-root> --shape`，发布打包前运行 `scripts/clean_build_artifacts.py <skill-root>` 清理构建产物。
8. 生成确认命令或 review-pack 前运行 `scripts/validate_placeholders.py <execution-root>`，确保没有 `@vN`、任何 `<...>`、`TODO` 等未替换占位。
9. 生成或更新 review-pack 后运行 `scripts/validate_review_pack.py <review-pack.md> --manifest <execution/manifest.md> --kind hile --check-links --check-command`。

脚本失败时必须停止执行并报告阻塞项；不得用人工解释覆盖脚本失败。固定确认命令中的 `<path>` 必须替换为被执行的 canonical agent Plan/Runbook 文件路径；在生成的 review-pack 中，该值必须等于 `review_target.agent_view`，不是 review-pack 文件路径。默认对用户使用中文自然语言，agent 字段和 YAML schema 保持 canonical English。


## 路径引用说明

Markdown 正文中的文件引用必须使用可点击链接。YAML/code block 中的路径字段是 machine-readable contract，允许保持纯字符串；若同一信息面向人类导航，应在正文附近提供可点击链接。

## v2.24.1 allowed-file double gate

Before modifying files, run:

```bash
scripts/check_allowed_files.py --handoff <handoff.md> --planned-file <planned-files.txt> --workspace <repo-or-worktree-root>
```

After modification and before completion, run:

```bash
scripts/check_allowed_files.py --handoff <handoff.md> --changed-file <actual-changed-files.txt> --workspace <repo-or-worktree-root>
```

Do not claim completion unless both checks pass or the inability to run a check is explicitly recorded and routed to a human/HILP decision.
