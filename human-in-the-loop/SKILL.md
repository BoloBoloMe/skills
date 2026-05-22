---
name: human-in-the-loop
description: 当用户明确要求 HITL / human-in-the-loop，或确认启用受控规划、人工批准、执行确认、审计追踪、低上下文交接或高风险编码流程时使用。本技能实现 HITL 0.0.1：单一 manifest.yaml、单一 HTML 人类视图、单一人在回路协议，并按阶段渐进读取 reference。
---

# HITL 0.0.1 技能

## 启用契约

只有在用户明确要求 `human-in-the-loop` / `HITL`，或用户确认你提出的受控流程建议后，才正式启用本技能。

正式启用前只能进行聊天级建议和澄清，不得创建资产目录、写入 manifest、生成 HTML 人类视图、运行门禁脚本或声称 HITL 已启动。

## 强制盘问红线

HITL 正式启用后，除读取本技能和 runtime-router、读取既有 manifest以判断阶段外，第一条业务响应必须进入盘问环节。
新建资产包或进入任一未关闭 gate 时，必须先向用户提出盘问问题；不得直接写facts/design/blueprint/implementation-package，不得直接关闭 gate，不得请求批准命令。

盘问规则:
- 每次只问一个问题。
- 问题必须包含推荐答案和备选答案。
- 用户明确回答前，不得把任何决策项记录为 human-confirmed。
- evidence-closed 只能关闭客观仓库事实，不能替代目标、范围、方案、风险、验证、批准边界、执行分级等决策确认。
- 任何 gate 至少必须包含一个来自真实问答的 human-confirmed resolution_item；否则禁止关闭 gate。


## 始终生效的不变量

- 协议固定为 `HITL`，`schema_version: "0.0.1"`，`protocol_version: "0.0.1"`。
- 唯一业务事实源是 `docs/changes/<中文变更>/manifest.yaml`。
- 唯一正式人类审核入口是 `docs/changes/<中文变更>/human-view.html`。
- 当前 agent 资产只允许放在 `agent/<artifact>.vN.yaml`；历史资产只允许放在 `agent/archive/<artifact>.vN.yaml`。
- agent 资产必须通过 `scripts/write_agent_asset.py` 或更专用的 compose/scaffold/evidence 脚本写入，通过 `scripts/archive_asset.py` 归档。
- 批准和确认事实只记录在 `manifest.decision_log`；agent asset 内不得写入 approval 或 confirmation 决策字段。
- `human-view@current` 是派生的人类视图 registry 记录，不是 YAML agent 资产输入。
- 面向用户审阅的方案正文、盘问问题、取舍说明、风险、验证说明、摘要与结论，必须使用用户提出 HITL 请求时所用的主要语言；仅代码标识符、文件路径、命令、asset_ref、协议字段名、第三方产品名和原始错误片段可保留原文。

## 全局门禁

- 初始化必须使用 `scripts/init_hitl_package.py`，且初始化不得创建 `human-view.html`。
- 每次写入、替换、归档 agent 资产或修改 manifest 状态后，必须由脚本同步刷新 `human-view.html` 与 `human-view@current`；不得让人类视图落后于资产内容。
- 任何批准或确认前，必须运行 `scripts/transform_human_view.py --check` 并通过。
- 展示批准命令前，必须运行 `scripts/validate_asset_check.py --pre-approval --target-ref <asset_ref> --record-ref checks/asset-check@vN` 并生成 completed/pass/pre-approval check 记录。
- 写 `planning/design@vN`、`planning/blueprint@vN`、`execution/plan|runbook@vN` 的 draft 允许先存在；但推进到非 draft 前必须关闭并校验对应 interrogation gate。
- 生成 Plan / Runbook 前必须已有匹配的 completed/pass/final asset-check 记录，并关闭、校验 `pre_execution_plan` gate。
- 需要固定执行确认时，确认前不得修改业务文件。
- 修改前和完成前都必须运行 allowed-files 门禁；完成前可用 `check_allowed_files.py --changed-from-git` 与 snapshot 排除执行前既有变更。
- 声明完成前必须通过 `scripts/record_execution_evidence.py` 写入 verification 与 close 记录。

## 固定命令

- tiny / standard 合并批准：`批准方案: planning/implementation-package@vN`
- strict 设计批准：`批准设计: planning/design@vN`
- strict 蓝图批准：`批准蓝图: planning/blueprint@vN`
- 关闭盘问门禁：`关闭盘问: pre_design planning/design@vN`
- 关闭盘问门禁：`关闭盘问: pre_blueprint planning/blueprint@vN`
- 关闭盘问门禁：`关闭盘问: pre_execution_plan execution/plan@vN`
- 关闭盘问门禁：`关闭盘问: pre_execution_plan execution/runbook@vN`
- standard 执行确认：`执行计划: execution/plan@vN`
- strict 执行确认：`执行计划: execution/runbook@vN`

`继续`、`可以了`、`执行吧` 等自然语言不得替代需要的固定命令。

## 渐进读取规则

不要在启用时一次性读取全部 `references/`。正式操作本技能时：

1. 先读取 `references/agent/runtime-router.md`。
2. 如果资产包已存在，先读取根部 `manifest.yaml`，根据 `workflow`、`current_pointers`、`interrogation_gates` 判断当前阶段和阻塞点。
3. 只读取 `runtime-router.md` 为当前阶段列出的 reference。
4. 除非脚本报错、需要调试或 router 明确要求，不要读取脚本源码；优先使用 `references/agent/script-index.md`、`references/agent/e2e-command-chain.md` 或脚本 `--help`。
5. `references/agent/02-interrogation-loop.md` 与 `references/agent/03-asset-schemas.md` 是兼容性完整参考；常规运行优先读取拆分后的细粒度文件。
