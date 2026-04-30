# 优化HILP资产管理 manifest

| asset_id | artifact_name | version | asset_path | created_state | current_state | current_state_label | approval_marker | approval_marker_label | role | current_review_pack | supersedes | superseded_by | last_event | last_decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hilp-asset-management-design | stage-3/design-choice | v1 | [02-方案设计_approved_design-choice@v1.md](assets/02-方案设计_approved_design-choice@v1.md) | approved | approved | 已批准 | approved | 已批准 | design-choice | 无 | 无 | 无 | Human Approval Granted | human-approval-2026-04-29-hilp-asset-management-design-v1 |
| hilp-asset-management-design | stage-3/design-choice | v1 | [02-方案设计_needs-approval_design-choice@v1.md](assets/02-方案设计_needs-approval_design-choice@v1.md) | ready-for-approval | ready-for-approval | 待审批 | needs-approval | 需审批 | design-choice | 无 | 无 | 无 | none | none |
| hilp-asset-management-blueprint | stage-4-5/implementation-blueprint | v1 | [03-实施蓝图_approved_implementation-blueprint@v1.md](assets/03-实施蓝图_approved_implementation-blueprint@v1.md) | approved | approved | 已批准 | approved | 已批准 | implementation-blueprint | 无 | 无 | 无 | Human Approval Granted | human-approval-2026-04-29-hilp-asset-management-blueprint-v1 |
| hilp-asset-management-blueprint | stage-4-5/implementation-blueprint | v1 | [03-实施蓝图_needs-approval_implementation-blueprint@v1.md](assets/03-实施蓝图_needs-approval_implementation-blueprint@v1.md) | ready-for-approval | ready-for-approval | 待审批 | needs-approval | 需审批 | implementation-blueprint | 无 | 无 | 无 | none | none |
| hilp-asset-management-execution-handoff | stage-6/execution-handoff | v1 | [05-执行交接_no-approval_execution-handoff@v1.md](assets/05-执行交接_no-approval_execution-handoff@v1.md) | archived | archived | 已归档 | no-approval | 无需审批 | execution-handoff | 无 | 无 | 无 | none | human-approval-2026-04-29-hilp-asset-management-blueprint-v1 |
| hilp-asset-management-archive-manifest | stage-7/archive-manifest | v1 | [06-规划资产归档_no-approval_archive-manifest@v1.md](assets/06-规划资产归档_no-approval_archive-manifest@v1.md) | archived | archived | 已归档 | no-approval | 无需审批 | archive-manifest | 无 | 无 | 无 | execution-handoff-completed | none |

## 整理说明
- 本 manifest 由历史规划资产迁移到最新 `docs/changes/<变更概述>/planning/` 结构时补齐。
- 仅索引既有文件位置，不改变历史资产正文语义或审批结论。
