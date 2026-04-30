# 调整HILP资产目录为主题分层 manifest

| asset_id | artifact_name | version | asset_path | created_state | current_state | current_state_label | approval_marker | approval_marker_label | role | current_review_pack | supersedes | superseded_by | last_event | last_decision |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| hilp-topic-layered-asset-dir-reapproval-v1 | stage-reapproval/reapproval-decision | v1 | [04-变更重审_reapproval@v1.md](assets/04-变更重审_reapproval@v1.md) | archived | archived | 已归档 | no-approval | 无需审批 | reapproval-record | 无 | 无 | 无 | upstream_design_superseded_by_new_path_requirement | none |
| hilp-topic-layered-asset-dir-requirements-facts-v1 | stage-1-2/requirements-and-facts | v1 | [01-需求对齐与事实求证_requirements-and-facts@v1.md](assets/01-需求对齐与事实求证_requirements-and-facts@v1.md) | archived | archived | 已归档 | no-approval | 无需审批 | facts-record | 无 | 无 | [01-需求对齐与事实求证_requirements-and-facts@v2.md](assets/01-需求对齐与事实求证_requirements-and-facts@v2.md) | facts_established_after_reapproval | none |
| hilp-topic-layered-asset-dir-requirements-facts-v2 | stage-1-2/requirements-and-facts | v2 | [01-需求对齐与事实求证_requirements-and-facts@v2.md](assets/01-需求对齐与事实求证_requirements-and-facts@v2.md) | archived | archived | 已归档 | no-approval | 无需审批 | facts-record | 无 | [01-需求对齐与事实求证_requirements-and-facts@v1.md](assets/01-需求对齐与事实求证_requirements-and-facts@v1.md) | 无 | user_selected_changes_root | user-selected-docs-changes-root-2026-04-30 |
| hilp-topic-layered-asset-dir-design-choice-v1 | stage-3/design-choice | v1 | [02-方案设计_design-choice@v1.md](assets/02-方案设计_design-choice@v1.md) | ready-for-approval | needs-revision | 待修订 | needs-revision | 待修订 | design-choice | [02-design-choice@v1-review.md](review-pack/02-design-choice@v1-review.md) | `stage-3/design-choice@v2`；[旧设计资产](assets/02-方案设计_design-choice@v2.md) | [02-方案设计_design-choice@v2.md](assets/02-方案设计_design-choice@v2.md) | user_requested_review_pack_clarification | none |
| hilp-topic-layered-asset-dir-design-choice-v2 | stage-3/design-choice | v2 | [02-方案设计_design-choice@v2.md](assets/02-方案设计_design-choice@v2.md) | ready-for-approval | needs-revision | 待修订 | needs-revision | 待修订 | design-choice | [02-design-choice@v2-review.md](review-pack/02-design-choice@v2-review.md) | [02-方案设计_design-choice@v1.md](assets/02-方案设计_design-choice@v1.md) | [02-方案设计_design-choice@v3.md](assets/02-方案设计_design-choice@v3.md) | user_selected_changes_root | user-selected-docs-changes-root-2026-04-30 |
| hilp-topic-layered-asset-dir-design-choice-v3 | stage-3/design-choice | v3 | [02-方案设计_design-choice@v3.md](assets/02-方案设计_design-choice@v3.md) | ready-for-approval | approved | 已批准 | approved | 已批准 | design-choice | [02-design-choice@v3-review.md](review-pack/02-design-choice@v3-review.md) | [02-方案设计_design-choice@v2.md](assets/02-方案设计_design-choice@v2.md) | 无 | human_approval_granted | human-approval-design-choice-v3-2026-04-30 |
| hilp-topic-layered-asset-dir-implementation-blueprint-v1 | stage-4-5/implementation-blueprint | v1 | [03-实施蓝图_implementation-blueprint@v1.md](assets/03-实施蓝图_implementation-blueprint@v1.md) | ready-for-approval | approved | 已批准 | approved | 已批准 | implementation-blueprint | [03-implementation-blueprint@v1-review.md](review-pack/03-implementation-blueprint@v1-review.md) | 无 | 无 | human_approval_granted | human-approval-implementation-blueprint-v1-2026-04-30 |
| hilp-topic-layered-asset-dir-execution-handoff-v1 | stage-6/execution-handoff | v1 | [05-执行交接_execution-handoff@v1.md](assets/05-执行交接_execution-handoff@v1.md) | archived | archived | 已归档 | no-approval | 无需审批 | execution-handoff | 无 | 无 | 无 | execution_handoff_created | none |
| hilp-topic-layered-asset-dir-archive-manifest-v1 | stage-7/archive-manifest | v1 | [06-规划资产归档_archive-manifest@v1.md](assets/06-规划资产归档_archive-manifest@v1.md) | archived | archived | 已归档 | no-approval | 无需审批 | archive-index | 无 | 无 | 无 | archive_after_execution_handoff | none |

## 当前入口
- 当前待审入口：[当前待审.md](_current/当前待审.md)
- 当前已批准入口：[当前已批准.md](_current/当前已批准.md)
- 归档阅读入口：[06-规划资产归档_archive-manifest@v1.md](assets/06-规划资产归档_archive-manifest@v1.md)

## 目录边界
- 本次规划资产保存于：[planning/](./)
- 未来 planning 资产目标目录：`docs/changes/<变更概述>/planning/`
- 未来 execution 资产目标目录：`docs/changes/<变更概述>/execution/`
- 未来代码审查结果目标目录：`docs/changes/<变更概述>/review/`
- planning 审批包 `review-pack/` 属于 planning 资产，不属于代码审查结果目录。
