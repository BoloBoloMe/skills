# 审核包：02-design-choice@v1

| review_pack_id | target_asset_ref | target_asset_path | target_version | previous_asset_ref | review_status | opened_at | closed_at | close_result | close_decision | change_summary | reviewer_action_required |
|---|---|---|---|---|---|---|---|---|---|---|---|
| review-hilp-topic-layered-asset-dir-design-choice-v1 | `stage-3/design-choice@v1 [state=needs-revision｜中文状态=待修订]` | [02-方案设计_design-choice@v1.md](../assets/02-方案设计_design-choice@v1.md) | v1 | `stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`；[旧设计资产](../assets/02-方案设计_design-choice@v2.md) | closed | 2026-04-30 | 2026-04-30 | needs-revision | user-requested-review-pack-clarification | 将 HILP 文件存储从全局 planning/execution/review 根目录改为按变更概述聚合，再在主题内分 planning、execution、review。v1 表述容易让人误会 `review-pack/` 与 `review/` 的关系。 | 无；已生成 v2 审核包 [02-design-choice@v2-review.md](./02-design-choice@v2-review.md)。 |

## 关闭说明

- 用户指出：planning 的 `review-pack/` 属于 planning 的资产，`docs/hilp/<变更概述>/review/` 用于存放代码审查的审查结果文档。
- v1 关闭为待修订，修订版本为 [02-方案设计_design-choice@v2.md](../assets/02-方案设计_design-choice@v2.md)。
