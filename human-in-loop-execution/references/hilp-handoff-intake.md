# HILP 执行交接接收

## 适用时机

每次从规划层进入执行层前使用，确保执行请求绑定正确的 HILP 资产、执行范围、禁止越界项和停止并回退条件。

## 输入契约

必须提供：

```text
HILP design asset_ref: stage-3/design-choice@vN [state=approved｜中文状态=已批准]
HILP blueprint asset_ref: stage-4-5/implementation-blueprint@vM [state=approved｜中文状态=已批准]
HILP execution handoff asset_ref: stage-6/execution-handoff@vK [state=<state>｜中文状态=<state_label>]
HILP execution handoff owner_skill: hilp-execution-handoff
执行交接资产要求：已成功落盘；自身不要求已批准；可为 archived｜中文状态=已归档 的规划出口记录
执行入口检查：无阻断项
执行范围：整包、发布波次或 manifest 中已定义切片
禁止越界项：来自执行交接资产
停止并回退条件：来自执行交接资产
当前工作区：用户指定的执行工作区
```

## 执行规则

1. 核对设计资产状态为已批准，不能用草稿、待审批、待修订或已归档资产替代。
2. 核对蓝图资产状态为已批准，版本必须与执行交接引用一致。
3. 核对执行交接资产 `owner_skill=hilp-execution-handoff`，已成功落盘，并明确写出“无阻断项”、执行范围、禁止越界项和停止并回退条件；执行交接资产自身不要求 `approved｜中文状态=已批准`。
4. 摘录禁止越界项，并在后续计划、prompt、审查请求和完成声明中保留。
5. 不接受自然语言开工许可替代 asset_ref；“可以开工”“按这个做”不是执行入口。
6. 设计或蓝图资产状态、版本缺失，或执行交接 owner、落盘证据、执行范围、禁止越界项、停止并回退条件任一缺失时，只输出失败原因和回退阶段，不进入实现。

## 禁止事项

- 不得凭自然语言许可替代 HILP asset_ref。
- 不得接受待审批蓝图、草稿蓝图、待修订蓝图或已归档蓝图作为执行依据。
- 不得仅因执行交接资产为 `archived｜中文状态=已归档` 就拒绝入口；执行交接资产按有效性检查判定，已归档设计或蓝图仍不得作为已批准输入。
- 不得在接收阶段补写蓝图未列文件、接口、数据形状或验证口径。
- 不得修改 HILP 规划资产状态。
- 不得在禁止越界项缺失时推断允许范围。

## 输出契约

成功时输出执行接收摘要：HILP 三类 asset_ref、执行范围、禁止越界项、停止条件、当前工作区、入口检查结论。失败时只输出缺失项、为什么不能进入执行、应回到的 HILP 阶段。

## 检查清单

- [ ] design asset_ref 已批准。
- [ ] blueprint asset_ref 已批准。
- [ ] execution handoff asset_ref 存在、owner_skill 正确、已成功落盘且入口检查无阻断项。
- [ ] 执行范围已确定。
- [ ] 禁止越界项和停止并回退条件已复制到执行上下文。
