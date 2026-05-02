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
禁止越界项：来自执行交接资产，并必须复制到执行计划、每个 execution_unit 上下文和完成声明
停止并回退条件：来自执行交接资产
当前工作区：用户指定的执行工作区
执行交接包含 `execution_plan_contract` 时必须核对：`execution_scope`、`execution_mode`、`parallelization`、`units`、`parallel_group`、`parallel_eligible`、`file_domain`、`shared_state`、`verification_resources`
每个 execution_unit 的 context_packet:
  approved_design_ref: 已批准设计资产
  approved_blueprint_ref: 已批准蓝图资产
  handoff_ref: 当前有效执行交接
  required_sections: 当前单元必读章节
  relevant_decisions: 当前单元相关已批准决策
  prior_summaries: 当前单元依赖的前序摘要
  explicitly_ignore: 待忽略的未绑定、待审批、待修订或已废弃材料
```

## 执行规则

1. 读取实际设计资产文件，核对 front matter 状态、正文 `asset_ref` 状态、正文状态摘要、执行交接中的上游引用和 manifest 索引状态均为 `approved｜中文状态=已批准`；不能用草稿、待审批、待修订或已归档设计资产替代。
2. 读取实际蓝图资产文件，核对 front matter 状态、正文 `asset_ref` 状态、正文状态摘要、执行交接中的上游引用和 manifest 索引状态均为 `approved｜中文状态=已批准`；版本必须与执行交接引用一致。
3. front matter、正文 `asset_ref`、正文状态摘要、执行交接引用和 manifest 任一状态不一致时，不得进入实现，不得自行修正规划资产。
4. 核对执行交接资产 `owner_skill=hilp-execution-handoff`，已成功落盘，并明确写出“无阻断项”、执行范围、禁止越界项和停止并回退条件；执行交接资产自身不要求 `approved｜中文状态=已批准`。
5. 执行交接包含 `execution_plan_contract` 时，核对 contract 顶层字段、`parallelization`、每个 unit 的 `parallel_group`、`parallel_eligible`、`file_domain`、`shared_state` 和 `verification_resources` 均已由 HILP 给出；缺失时停止，不得由 HILE 补齐。
6. 逐个核对 `execution_unit.context_packet`：`approved_design_ref` 只能引用已批准设计，`approved_blueprint_ref` 只能引用已批准蓝图，`handoff_ref` 必须指向当前有效执行交接；不得把待审批、草稿、待修订、已废弃或已失效资产作为绑定性输入。
7. 核对每个 `context_packet.required_sections`、`relevant_decisions`、`prior_summaries` 和 `explicitly_ignore` 均已填写或明确为空；缺失时不得由执行阶段重读全部历史规划资产补齐。
8. 摘录禁止越界项，并在后续 runbook、计划、prompt、审查请求、每个 execution_unit 执行上下文和完成声明中保留。
9. 不接受自然语言开工许可替代 asset_ref；“可以开工”“按这个做”不是执行入口。
10. 设计或蓝图资产状态、版本缺失，执行交接 owner、落盘证据、执行范围、禁止越界项、停止并回退条件任一缺失，contract 调度字段缺失，或 context_packet 引用失效资产时，只输出失败原因、固定恢复建议和回退阶段，不进入实现。固定恢复建议为：回到 HILP 变更重审，执行“审批状态一致性修复”；若用户批准事实明确，不生成新内容版本，只同步同一版本的状态字段和当前入口。

## 禁止事项

- 不得凭自然语言许可替代 HILP asset_ref。
- 不得接受待审批蓝图、草稿蓝图、待修订蓝图或已归档蓝图作为执行依据。
- 不得仅因执行交接资产为 `archived｜中文状态=已归档` 就拒绝入口；执行交接资产按有效性检查判定，已归档设计或蓝图仍不得作为已批准输入。
- 不得在接收阶段补写蓝图未列文件、接口、数据形状或验证口径。
- 不得修改 HILP 规划资产状态。
- 不得在禁止越界项缺失时推断允许范围。
- 不得接受缺少 `context_packet` 或 `context_packet` 引用未批准、待修订、已废弃、已失效设计 / 蓝图资产的 execution_unit。
- 不得接受缺少 `execution_plan_contract.parallelization`、`parallel_group`、`parallel_eligible`、`file_domain`、`shared_state` 或 `verification_resources` 的并行调度交接。

## 输出契约

成功时输出执行接收摘要：HILP 三类 asset_ref、执行范围、禁止越界项、停止条件、当前工作区、入口检查结论、`execution_plan_contract` 核验结论，以及每个 execution_unit 的 context_packet 核验结论。失败时只输出缺失项或状态不一致项、为什么不能进入执行、固定恢复建议、应回到的 HILP 阶段；不得自行修正规划资产。

## 检查清单

- [ ] design asset_ref 已批准，且实际设计资产文件的 front matter、正文 `asset_ref`、正文状态摘要、执行交接引用和 manifest 状态一致。
- [ ] blueprint asset_ref 已批准，且实际蓝图资产文件的 front matter、正文 `asset_ref`、正文状态摘要、执行交接引用和 manifest 状态一致。
- [ ] execution handoff asset_ref 存在、owner_skill 正确、已成功落盘且入口检查无阻断项。
- [ ] 执行范围已确定。
- [ ] 执行交接包含 `execution_plan_contract` 时，`parallelization`、`parallel_group`、`parallel_eligible`、`file_domain`、`shared_state` 和 `verification_resources` 已由 HILP 给出。
- [ ] 每个 `execution_unit.context_packet` 只引用已批准设计、已批准蓝图和当前有效执行交接。
- [ ] 每个 `context_packet` 已列出 required_sections、relevant_decisions、prior_summaries 和 explicitly_ignore。
- [ ] 禁止越界项和停止并回退条件已复制到执行上下文。
