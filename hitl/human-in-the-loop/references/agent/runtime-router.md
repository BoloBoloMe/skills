# HITL Runtime Router

本文件是 HITL 0.0.1 的渐进读取入口。它只决定当前阶段需要读取哪些 reference，不改变协议语义。

## 接手顺序

1. 未正式启用 HITL 时，只做聊天级建议和澄清。
2. 新建资产包时，按“初始化资产包”路由读取后运行 `scripts/init_hitl_package.py`。
3. 继续既有资产包时，先读取根 `manifest.yaml`，用 `workflow.current_stage`、`workflow.next_action`、`current_pointers`、`interrogation_gates` 与 `asset_registry` 判断当前阶段。
4. 只读取下表当前阶段列出的 reference；不要预读无关阶段文档。
5. 写入、归档、关闭 gate、记录决策、生成人类视图和记录执行证据时，优先使用脚本。脚本用途见 `script-index.md`。

任一 agent 接手 HITL 工作时，最短入口永远是资产包根部的 `manifest.yaml`。manifest 必须说明当前阶段、active asset、下一步动作、阻塞原因和盘问门禁状态。

## 阶段路由表

| 当前任务 | 读取 reference |
|---|---|
| 初始化资产包 | `references/shared/asset-layout.md`; `references/shared/manifest-and-versioning.md`; `references/agent/script-index.md` |
| 恢复或交接 | 根 `manifest.yaml`; `references/shared/manifest-and-versioning.md`; active asset 对应 schema；若阻塞于 gate，读取对应 interrogation 文件；若失败/漂移/新事实/范围变化，读取 `references/agent/05-reassessment-and-resume.md` |
| facts | `references/agent/01-workflow.md`; `references/agent/interrogation-core.md`; `references/agent/schema-common.md`; `references/agent/schema-planning.md`; `references/agent/script-index.md` |
| pre_design gate 与 design | `references/agent/01-workflow.md`; `references/agent/interrogation-core.md`; `references/agent/interrogation-pre-design.md`; `references/agent/schema-common.md`; `references/agent/schema-planning.md`; `references/agent/script-index.md` |
| pre_blueprint gate 与 blueprint | `references/agent/01-workflow.md`; `references/agent/interrogation-core.md`; `references/agent/interrogation-pre-blueprint.md`; `references/agent/schema-common.md`; `references/agent/schema-blueprint.md`; `references/agent/script-index.md` |
| implementation-package | `references/agent/01-workflow.md`; `references/shared/manifest-and-versioning.md`; `references/agent/schema-common.md`; `references/agent/schema-implementation-package.md`; `references/agent/script-index.md` |
| asset-check | `references/agent/schema-asset-check.md`; `references/shared/file-scope-policy.md`; `references/agent/script-index.md` |
| pre_execution_plan gate 与 Plan / Runbook | `references/agent/01-workflow.md`; `references/agent/04-plan-runbook.md`; `references/agent/interrogation-core.md`; `references/agent/interrogation-pre-execution-plan.md`; `references/agent/schema-blueprint.md`; `references/agent/schema-execution-plan-runbook.md`; `references/shared/file-scope-policy.md`; `references/agent/script-index.md` |
| execute / verify / close | `references/agent/01-workflow.md`; `references/agent/schema-execution-plan-runbook.md`; `references/agent/schema-verification-close.md`; `references/shared/file-scope-policy.md`; `references/agent/script-index.md` |
| reassessment / resume | `references/agent/05-reassessment-and-resume.md`; `references/shared/manifest-and-versioning.md`; active asset 对应 schema；若涉及执行范围，读取 `references/shared/file-scope-policy.md` |

## 必要校验提示

- 写 `planning/design@vN` 前，运行 `scripts/validate_interrogation_gate.py --gate pre_design --target planning/design@vN`。
- 写 `planning/blueprint@vN` 前，运行 `scripts/validate_interrogation_gate.py --gate pre_blueprint --target planning/blueprint@vN`。
- 生成 Plan / Runbook 前，先用 `scripts/validate_asset_check.py --target-ref <implementation-package-ref> --workspace <repo> --record-ref checks/asset-check@vN` 记录 completed/pass/final check，再运行 `scripts/validate_interrogation_gate.py --gate pre_execution_plan --target execution/plan@vN|execution/runbook@vN`。
- 批准前运行 `scripts/validate_asset_check.py --pre-approval --target-ref <asset_ref> --record-ref checks/asset-check@vN` 并生成 completed/pass/pre-approval check。
- 任何批准或确认前运行 `scripts/transform_human_view.py --check`。
- 修改前和完成前都运行 allowed-files 门禁。

## 完整参考

`references/agent/02-interrogation-loop.md` 与 `references/agent/03-asset-schemas.md` 保留为完整兼容参考。常规阶段运行时优先读取拆分后的细粒度文档；只有在审计、排错、检查迁移一致性或 router 无法覆盖的边界情况中再读取完整参考。
