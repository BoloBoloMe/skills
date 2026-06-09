# HITL 工作流

## 阶段

HITL 0.0.1 的语义阶段为：

`intake → facts → pre_design gate closed → design → pre_blueprint gate closed → blueprint → implementation-package → asset-check → pre_execution_plan gate closed → plan / runbook → execute → verify → close`

失败、漂移、新事实、范围变化或验证契约变化时进入 `reassessment`。

## tier 规则

### tiny

- 小范围、低风险变更。
- 可使用 implementation-package 合并批准。
- 满足例外条件时，可跳过单独执行确认。

### standard

- 常规多步骤或多文件变更。
- 使用 implementation-package 合并批准；implementation-package 是 approval-target。
- 批准前必须生成 completed/pass/pre-approval asset-check 记录；最终 asset-check 记录 completed/pass/final 后生成 repo-aware Plan。
- 修改业务文件前必须获得固定 Plan 确认。

### strict

- 高风险、迁移、并行、多 agent、安全、合规或复杂验证变更。
- 设计与蓝图必须分开批准。
- implementation-package 是 completed/content-asset，只作为资产绑定包和 asset-check 输入，不新增第三个人类批准点。
- strict 的 design、blueprint 每次批准前都必须生成各自 completed/pass/pre-approval asset-check 记录；最终 asset-check 记录 completed/pass/final 后生成 repo-aware Runbook。
- 修改业务文件前必须获得固定 Runbook 确认。

## 决策记录

批准和确认只记录在 `manifest.decision_log`。agent asset 内不得写入 approval 或 confirmation 决策字段。固定命令应通过 `scripts/transition_manifest.py record-decision` 记录；该脚本只允许 `ready-for-approval → approved` 与 `ready-for-confirmation → confirmed`，并同步更新 workflow/current_pointers/human-view。

## 状态转换脚本

- 关闭盘问 gate：使用 `scripts/transition_manifest.py close-gate`，必须显式传入固定 `--command`，已关闭 gate 不得重复关闭。
- 生成 implementation-package：优先使用 `scripts/compose_implementation_package.py`，它按 tier 推导 state/role，并为 facts/design/blueprint 写入 path + sha256 references。
- 生成 Plan / Runbook：优先使用 `scripts/scaffold_execution_plan.py`；它要求已有匹配 completed/pass/final asset-check，随后即时重跑最终 asset-check、校验 closed pre-execution gate，并补齐机械结构；业务判断仍由 content-file 提供。
- 记录执行证据：使用 `scripts/record_execution_evidence.py verification|close`，close 前必须通过 changed-files gate。

## HTML 门禁

任何批准或确认前，必须满足：

1. `human-view.html` 已由 `transform_human_view.py` 生成；
2. manifest 中已登记 `human-view@current`；
3. `transform_human_view.py --check` 通过。

HTML 生成失败或漂移时，不得用聊天摘要替代人类审核入口。
