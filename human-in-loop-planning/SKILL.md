---
name: human-in-loop-planning
description: "use for two cases only: suggestion-only preflight when a request appears to involve gated approval, formal handoff, audit trail, high-risk irreversible change, multi-agent planning, or explicit hilp protocol; formal hilp protocol mode only after the user explicitly asks to use hilp or confirms the suggestion. do not suggest for ordinary coding, debugging, lightweight planning, or design discussion unless the user asks for approval gates or controlled handoff."
---

# 人在回路规划

## 启动规则

This Skill is the HILP control entrypoint. It has two layers:

1. Suggestion layer: for complex planning, high-risk design, refactoring, migration, approval, blueprint, reapproval, or handoff work, briefly suggest that HILP may be useful and ask whether the user wants to use it.
2. Execution layer: enter the formal HILP protocol only after the user explicitly asks to use HILP / human-in-loop planning / this skill, or confirms the suggestion.

Before confirmation, stay in ordinary chat or preflight analysis only. Do not create durable planning assets, run gates, update manifests, write review-packs, or claim that HILP has started. After confirmation, first read [agent directory](references/agent/00-directory.md), then load only the shortest path listed there.

Default user-facing prose should be concise Chinese unless the user asks otherwise. Machine fields such as phase_id, lifecycle_state, asset_ref, schema, and contract fields belong in agent-facing assets or debug explanations.

Assets from earlier pilot protocols are intentionally unsupported in v2.24.0. If a user provides an older asset, explain that it must be regenerated under the current v2.24.0 protocol rather than migrated.

## 协议版本号规范

HILP 使用三段版本号 `x.y.z`。`x.y` 是 HILP/HILE 共享的大协议线，当前为 `2.24`；`z` 是各协议自己的小版本迭代号，可以不一致。当前 HILP 版本为 `v2.24.0`。跨协议兼容性以 `references/shared/compatibility-contract.yaml` 为准，不要求 HILP 与 HILE 三段版本完全相等。

## Runtime Preconditions

正式 HILP 资产依赖可确认、可写入的 workspace 或项目根目录，并依赖随附 Python 脚本完成机械校验。无法确认保存位置、不能写入文件、不能运行脚本、或不能读取既有资产时，只能输出非落盘草案/预检说明，并明确哪些落盘、校验、审批或交接动作没有完成；不得声称已保存、已通过校验、已完成审批记录或已交接给 HILE。

## 双视图原则

所有正式规划资产都必须拆成两套视图，并保持同一事实来源：

- **人类审核视图**：只服务人类审核员，使用自然语言、清晰标题、前后文说明和连续链接。审核员应能从第一份文档一路点击到最后一份文档。
- **agent 执行视图**：只服务 agent，使用结构化字段、约束表、schema、目录和最短读取路径。agent 应能知道当前环节必须读什么、不能读什么、必须产出什么。

正式落盘布局见 [共享资产布局](references/shared/asset-layout.md)。输出资产不得把人类审核问题和 agent contract 混在同一个主视图里；必要时可以在两套视图之间互链，但不要复制无关噪声。

## 模式选择

1. **非落盘预检模式**：用户已明确要求使用 HILP，但只是要求咨询、评估、草拟方案或分析风险，且没有要求进入审批链或正式资产落盘时使用。只输出临时分析，不创建 manifest、review-pack、正式资产或 `_current`。
2. **保存型预检 scaffold**：用户明确要求保存预检笔记，但尚未要求正式审批链时使用。可以创建 `preflight-scaffold` manifest 和草稿记录；不得创建 approval-record、handoff-record、正式 `_current` 指针或 HILE handoff。
3. **标准 HILP 模式**：用户要求按 HILP 管理、生成规划资产、需要审批、需要执行交接，且风险中等、范围明确、可回滚、无安全/合规/数据高风险时使用。必须落盘双视图资产。
4. **严格 HILP 模式**：仅在用户已明确要求使用 HILP 后，若涉及高风险、不可逆操作、安全/合规/数据风险、大规模迁移、跨模块重构、多人/多 agent 并行或需要强审计链时使用。必须包含完整 manifest、review-pack、agent directory、审批记录、audit trail 和执行交接；只有触发 phase-04、批准资产被 invalidated，或生成重审 review-pack 时，才必须包含非空重审记录 / reapproval log。

模式可以升级；降级必须说明理由。标准或严格模式一旦产生已批准资产，不得用后续普通对话绕过重审。

## 阶段体系

Use only the canonical `phase-*` identifiers below for new assets:

| phase_id | Purpose |
|---|---|
| phase-00 | intake and routing |
| phase-01 | requirements and facts |
| phase-02 | design choice and approval |
| phase-03 | implementation blueprint |
| phase-04 | reapproval after new facts or invalidation |
| phase-05 | execution handoff |
| phase-06 | planning archive index |
| phase-99 | protocol pressure test |

Use only canonical phase identifiers in new assets. If a supplied asset uses non-canonical identifiers, do not migrate it in place; ask to regenerate the package under the current v2.24.0 protocol.



## HILP / HILE 职责边界

HILP `execution_units` are scope and intent contracts, not repository-aware patch plans. They must define what to accomplish, allowed and prohibited scope, dependencies, verification expectations, and stop conditions. Do not treat them as line-level implementation recipes.

Do not encode line-level patch instructions in HILP execution units unless the handoff also records the exact commit hash and the relevant context snippets. Prefer semantic anchors such as file paths, symbols, functions, classes, config keys, route names, test names, and blueprint references.

Concrete repository-aware implementation steps belong to HILE Plan or Runbook after HILE has inspected the actual repository/worktree. Phase-05 handoff must explicitly require HILE to generate, validate, and, for standard or strict execution, confirm a repo-aware Plan or Runbook before modifying files.

## 用户动作语义

v2.24.0 起，正式批准与确认一律使用固定命令；自然语言不能直接落为批准或执行确认。

- `批准设计：批准 phase-02/design-choice@vN`
- `批准蓝图：批准 phase-03/implementation-blueprint@vN`
- `确认执行：确认执行 Runbook <path>` 或 `确认执行：确认执行 Plan <path>`

“可以了”“继续”“按这个来”只能触发 agent 回显唯一推荐命令并等待用户确认；不能直接把资产状态改为 `approved`，也不能开始执行。批准设计不等于批准蓝图；批准蓝图不等于确认执行；确认执行 runbook/plan 不会补足上游批准。详见 [审批语义](references/shared/approval-semantics.md)。

## 状态语义

Use `lifecycle_state` and `record_role` as separate canonical fields. The single source of truth for enums, fixed commands, required fields, and role/state matrix is [canonical protocol schema](references/shared/canonical-protocol-schema.yaml). [Lifecycle and state](references/shared/lifecycle-and-state.md) is a human-readable projection and must not define divergent enums.

Execution handoff records must use `lifecycle_state=closed-record` and `record_role=handoff-record`. Archive indexes must use `lifecycle_state=closed-record` and `record_role=archive-index`. Reapproval records use `record_role=reapproval-record`. Removed pilot state aliases are not supported in v2.24.0 assets.

## 规划最短路径

Route through [agent directory](references/agent/00-directory.md). Common paths:

- New confirmed HILP request: directory -> core contracts -> planning workflows -> output schemas.
- Approved design to blueprint: directory -> core contracts -> phase-03 workflow -> output schemas.
- New facts invalidate approval: directory -> core contracts -> phase-04 reapproval -> lifecycle rules.
- Execution handoff: directory -> core contracts -> phase-05 handoff -> output schemas -> HILE handoff contract.
- Planning archive: directory -> lifecycle rules -> phase-06 archive -> human archive summary and agent archive-index.

Do not infer semantics from older pilot material. If current v2.24.0 rules do not cover a user-supplied asset, stop and request regeneration under v2.24.0 instead of guessing.

## 落盘与交付纪律

- 无法确认项目根目录时，先输出非落盘预检或请求保存位置；不要声称已保存。
- 写入失败时明确报告失败，不得伪造路径。
- 所有 Markdown 文件引用必须使用可点击链接。
- 人类审核视图文件按顺序互链；agent 执行视图必须包含 `00-directory`，说明每个环节最小必读文件。
- 正式资产每次进入 `ready-for-review`、`approved`、`superseded`、`retired`、`closed-record` 都要更新 manifest，并按 [manifest 与版本规则](references/shared/manifest-and-versioning.md) 更新 `vN`、`supersedes`、`invalidated_by` 和 `_current/` 指针。
- 发现新事实、蓝图缺口、审批缺失、执行范围变化或验证口径变化时，停止推进并进入 phase-04 重审；phase-04 必须输出固定裁决命令，不得用自由文本批准。


## 工程化门禁

正式标准/严格模式不是纯文档流程；必须使用随附脚本作为机械校验门：

1. 首次落盘 formal package 前运行 `scripts/init_change_package.py <change_slug> --root docs/changes --mode standard|strict`。
2. 每次更新 `planning/manifest.md` 后运行 `scripts/validate_manifest.py <planning/manifest.md> --check-paths`；仅预检脚手架可加 `--allow-draft-paths`。
3. 每次生成或更新 phase-02/phase-03/phase-05 agent-facing 资产后运行 `scripts/validate_hilp_assets.py <planning-root> --manifest <planning/manifest.md>`，确保 design、blueprint 和 handoff 内容完整且互相一致。
4. 新增或移动 Markdown 资产后运行 `scripts/check_links_and_state.py <planning-root>`。
5. 打包、交接或修改 schema 文档后运行 `scripts/validate_yaml_blocks.py <skill-or-package-root> --shape`，发布打包前运行 `scripts/clean_build_artifacts.py <skill-root>` 清理构建产物。
6. 生成 review-pack 或批准命令前运行 `scripts/validate_placeholders.py <planning-root>`，确保没有 `@vN`、任何 `<...>`、`TODO` 等未替换占位。
7. 生成或更新 review-pack 后运行 `scripts/validate_review_pack.py <review-pack.md> --manifest <planning/manifest.md> --kind hilp --check-links --check-command`.

脚本失败时必须停止推进，修复资产或进入 phase-04 重审；不得用自然语言解释替代脚本通过。固定批准命令中的 `@vN` 必须替换成具体版本号，例如 `@v3`，不得要求用户批准模板版本。

Phase-05 handoff must pass both manifest validation and HILP asset content validation before it may be presented as ready for HILE intake.


## 路径引用说明

Markdown 正文中的文件引用必须使用可点击链接。YAML/code block 中的路径字段是 machine-readable contract，允许保持纯字符串；若同一信息面向人类导航，应在正文附近提供可点击链接。


## Mechanical validation rule

For formal standard or strict HILP packages, run `scripts/validate_manifest.py <planning/manifest.md> --check-paths` after manifest updates. Use `--allow-draft-paths` only for preflight scaffolds (`mode: preflight-scaffold`).

### Preflight landing rule

Default preflight is chat-only: do not create a manifest, review-pack, formal asset, `_current/` pointer, approval record, or HILE handoff. A `preflight-scaffold` may be created only when the user explicitly asks to save preflight notes; it is not a formal HILP package, must not contain approval records or `_current/` pointers, and must not be handed to HILE. Use `scripts/init_change_package.py <change_slug> --root docs/changes --mode preflight-scaffold` only for that explicit saved-preflight case.
