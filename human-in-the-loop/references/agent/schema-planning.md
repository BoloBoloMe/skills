# Planning Assets Schema

本文件只覆盖 facts 与 design。通用头字段和禁止字段见 `schema-common.md`。

## planning/facts

必须覆盖：

- 目标；
- 范围；
- 非范围；
- 已验证事实与来源；
- 假设；
- 未知项；
- 验收口径；
- 验证策略。

写入前应先探索仓库、配置、测试、文档和已有资产，避免把可验证事实转嫁给用户。

## planning/design

必须覆盖：

- 候选方案；
- 每个候选方案的复杂度 / 代码量 / 影响范围 / 风险 / 测试工作量评价；
- 推荐方案；
- 取舍理由；
- 被拒方案；
- 风险与边界。

写 `planning/design@vN` 前必须关闭并校验 `pre_design` gate。
