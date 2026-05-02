# 执行计划编写

## 适用时机

已有 HILP 执行交接，但需要把已批准蓝图机械拆分为可执行任务清单时使用。若执行交接包含 `execution_plan_contract`，必须优先使用 `references/writing-runbooks.md` 生成 Execution Runbook；本文件只作为普通计划兼容入口或 runbook 下的任务细化规则。

## 输入契约

- HILP design asset_ref。
- HILP blueprint asset_ref。
- HILP execution handoff asset_ref。
- 执行范围：整包、发布波次或 manifest 中已定义的切片集合。
- 已批准蓝图或执行交接中的 `execution_unit` 契约；存在 `execution_plan_contract` 时，必须读取已确认 runbook 并复制其中的 `copied_order`、`copied_depends_on`、`copied_parallel_group`、`copied_parallel_eligible`、`copied_file_domain`、`copied_shared_state` 和 `copied_verification_resources`。
- 禁止越界项、目标、执行约束和验证承诺。
- execution ledger 目标路径与每个 unit summary 目标路径。

## 执行规则

计划保存到：`docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。

固定计划头：

```text
HILP design asset_ref:
HILP blueprint asset_ref:
HILP execution handoff asset_ref:
执行确认状态: waiting-for-user-confirmation
禁止越界项:
目标:
执行约束:
execution ledger 路径:
unit summary 路径:
```

先列文件结构和文件职责，再按 `execution_unit` 逐单元拆任务；每个单元必须保留来自交接包或已确认 runbook 的 `unit_id`、允许修改文件、context_packet、verification、stop_conditions、前序摘要、execution ledger 更新要求和 unit summary 输出路径。存在 runbook 时，不得改变 `copied_order`、`copied_depends_on`、`copied_parallel_group`、`copied_parallel_eligible`、`copied_file_domain`、`copied_shared_state` 或 `copied_verification_resources`。每个任务的每步目标 2-5 分钟，包含精确文件路径、失败测试或验证命令、预期输出、最小实现、回归验证、提交或变更记录。计划保存后必须停止，不得执行任务、修改目标文件、派发 agent 或运行实现步骤。

No placeholders：禁止 TODO、TBD、后续再定、类似上一步、写适当测试、补齐错误处理、按需实现等占位符。每一步都必须可直接执行。

自检：蓝图覆盖、占位符扫描、类型 / 方法签名一致性、禁止越界项检查。发现计划需要新增方案选择或文件范围时，停止并回到 HILP。

## 禁止事项

- 不得新增方案选择或扩大范围。
- 不得写占位符、后续再定或执行时再判断。
- 不得把未批准规划内容写入任务。
- 不得让执行者自行选择蓝图外文件。
- 不得用普通执行计划覆盖或改变已确认 runbook 中复制的 contract 调度字段。

## 输出契约

输出已保存计划路径、任务列表摘要、绑定的 HILP asset_ref、禁止越界项、自检结果、推荐执行方式和用户确认请求。若发现蓝图无法拆分，停止并要求回到 HILP 变更重审或实施蓝图。

## 检查清单

- [ ] 计划头包含三类 HILP asset_ref。
- [ ] 已先列文件职责。
- [ ] 每个任务都有文件路径、验证命令和预期输出。
- [ ] 已列出 execution ledger 路径和每个 unit summary 路径。
- [ ] No placeholders 扫描通过。
- [ ] 禁止越界项已检查。
