# 计划文档审查 prompt 模板

## 适用时机

执行计划写完后，审查计划是否可按 HILP 执行交接安全实施时使用。

## 输入契约

```text
HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:
计划或 runbook 文件路径:
蓝图或执行交接引用:
execution_runbook source_contract_ref:
user_selected_mode:
```

## 执行规则

prompt 必须包含：

```text
你正在审查一个 HILP 执行交接后的执行计划。

HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
禁止越界项:

检查项：完整性、蓝图对齐、任务分解、可构建性、无占位符、runbook 与 execution_plan_contract 一致性。
只阻断会导致执行者构建错误或卡住的问题，例如缺文件范围、缺验证命令、任务依赖矛盾、占位符、越过执行交接、缺少 runbook 确认门、HILE 改变 contract 字段、并行结果未收口。
输出 Status: Approved 或 Issues Found。
```

## 禁止事项

- 不得审查成新设计。
- 不得允许计划补齐蓝图缺口。
- 不得忽略执行交接范围。
- 不得允许 runbook 改变 `parallel_group`、`parallel_eligible`、`file_domain`、`shared_state` 或 `verification_resources`。
- 不得因风格偏好阻断计划。

## 输出契约

输出计划审查状态、阻断问题、建议和是否允许进入执行。阻断问题必须给出文件或任务位置。

## 检查清单

- [ ] HILP asset_ref 完整。
- [ ] 执行交接已引用。
- [ ] 禁止越界项已检查。
- [ ] 计划或 runbook 无占位符且可构建。
- [ ] runbook 绑定 HILP 三类 asset_ref，复制 contract 字段，保留确认门，并记录并行结果 conflict check、integration verification、spot check、unit summary 和 ledger 收口。
- [ ] 结论明确。
