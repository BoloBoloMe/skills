# 执行计划编写

## 适用时机

已有 HILP 执行交接，但需要把已批准蓝图机械拆分为可执行任务清单时使用。

## 输入契约

- HILP design asset_ref。
- HILP blueprint asset_ref。
- HILP execution handoff asset_ref。
- 执行范围：整包、发布波次或 manifest 中已定义的切片集合。
- 禁止越界项、目标、执行约束和验证承诺。

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
```

先列文件结构和文件职责，再拆任务。每个任务的每步目标 2-5 分钟，包含精确文件路径、失败测试或验证命令、预期输出、最小实现、回归验证、提交或变更记录。计划保存后必须停止，不得执行任务、修改目标文件、派发 agent 或运行实现步骤。

No placeholders：禁止 TODO、TBD、后续再定、类似上一步、写适当测试、补齐错误处理、按需实现等占位符。每一步都必须可直接执行。

自检：蓝图覆盖、占位符扫描、类型 / 方法签名一致性、禁止越界项检查。发现计划需要新增方案选择或文件范围时，停止并回到 HILP。

## 禁止事项

- 不得新增方案选择或扩大范围。
- 不得写占位符、后续再定或执行时再判断。
- 不得把未批准规划内容写入任务。
- 不得让执行者自行选择蓝图外文件。

## 输出契约

输出已保存计划路径、任务列表摘要、绑定的 HILP asset_ref、禁止越界项、自检结果、推荐执行方式和用户确认请求。若发现蓝图无法拆分，停止并要求回到 HILP 变更重审或实施蓝图。

## 检查清单

- [ ] 计划头包含三类 HILP asset_ref。
- [ ] 已先列文件职责。
- [ ] 每个任务都有文件路径、验证命令和预期输出。
- [ ] No placeholders 扫描通过。
- [ ] 禁止越界项已检查。
