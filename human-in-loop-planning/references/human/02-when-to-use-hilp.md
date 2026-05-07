# 显式请求 HILP 后如何选择流程重量

HILP 只在用户明确要求使用 HILP、human-in-loop planning 或本 Skill 后进入。普通分析、评估、方案草稿、设计讨论、重构建议或 review 请求不自动进入 HILP。

进入 HILP 后，如果用户只是想先保存预检笔记，可以使用非正式的 preflight-scaffold；默认预检仍是 chat-only，不创建正式 manifest、review-pack、审批记录、`_current/` 指针或 HILE handoff。

正式流程用于用户明确要求按 HILP 管理本次变更、生成规划资产、走审批链或交付执行层时。正式流程会保存两套视图：一套给人审核，一套给 agent 执行。

严格模式用于已经显式进入 HILP 且涉及不可逆操作、安全、合规、数据风险、大范围迁移、多人/多 agent 并行或强审计链的变更。严格模式必须保留 audit trail；只有触发 phase-04、批准资产被 invalidated，或生成重审 review-pack 时，才需要非空重审记录。

上一页：[术语和阅读方式](01-glossary-and-reading.md) ｜ 下一页：[需求事实与方案审批](03-requirements-and-design.md)

## 进入 strict 的典型例子

以下情况通常进入 strict，而不是停留在预检或 standard：

- 修改认证、权限、支付、加密、审计或合规逻辑。
- 批量迁移用户数据、生产数据或不可轻易回滚的状态。
- 跨多个服务重构 API contract、事件 schema 或共享库。
- 引入并行 subagent 修改共享状态或相邻文件域。
- 验证口径变化会影响能否证明设计目标达成。
- 失败后需要判断是 blueprint gap 还是 design gap。
