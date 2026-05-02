# Execution Unit Contract

## 适用时机

当实施蓝图或执行交接需要把变更拆成 `execution_unit` 时使用。本契约只定义规划层和执行层共同遵守的单元字段、边界和检查项，不引入 runtime、CLI、自动调度或连续执行机制。

## 输入契约

每个 `execution_unit` 必须来自已批准蓝图或有效执行交接摘录，并绑定以下输入：

- 已批准设计资产引用。
- 已批准蓝图资产引用。
- 有效执行交接资产引用。
- 当前单元在蓝图中的依赖位置。
- 当前单元允许修改的精确文件清单。
- 当前单元必须满足的验证承诺和停止条件。

禁止使用 `draft`（草稿）、`ready-for-approval`（待审批）、`needs-revision`（待修订）或已失效资产作为绑定性输入。执行交接资产可以是已归档交接记录，但它只能作为入口记录，不得替代已批准设计或已批准蓝图。

## 必需字段

每个 `execution_unit` 必须包含以下字段，字段名保持稳定，供蓝图、交接和执行计划逐项摘录：

```yaml
execution_unit:
  unit_id: EU-001
  title: 引入 Execution Unit Contract
  context_packet:
    approved_design_ref: stage-3/design-choice@v1
    approved_blueprint_ref: stage-4-5/implementation-blueprint@v1
    handoff_ref: stage-6/execution-handoff@v1
    required_sections: []
    relevant_decisions: []
    prior_summaries: []
    explicitly_ignore: []
  allowed_files: []
  dependencies: []
  must_haves: []
  verification:
    commands: []
    expected_exit_codes: []
    expected_output_summary: []
  stop_conditions: []
  prior_summaries: []
```

字段含义：

- `unit_id`：稳定单元编号；在蓝图、交接、执行计划、ledger 和 summary 中一致。
- `title`：单元标题；描述单元目标，不承载新需求。
- `context_packet`：当前单元可读取的最小上下文包；只引用当前单元需要的已批准设计、已批准蓝图、有效交接、必读章节、相关决策、前序摘要和明确忽略项。
- `allowed_files`：当前单元允许修改的精确文件路径；执行层不得自行扩展。
- `dependencies`：当前单元依赖的前序单元或资产条件；无依赖时写空列表。
- `must_haves`：当前单元完成前必须满足的结果承诺。
- `verification`：当前单元必须运行或说明的验证命令、期望退出码和输出摘要。
- `stop_conditions`：命中后必须停止并回退的条件。
- `prior_summaries`：当前单元允许引用的前序 unit summary；无前序时写空列表。

## 禁止事项

- 不得让执行层在当前 `execution_unit` 中补做蓝图判断。
- 不得把未批准、待修订或已失效资产写入 `context_packet` 作为绑定性输入。
- 不得把 `allowed_files` 写成目录级模糊范围或“按需修改”。
- 不得把 `verification` 留给执行者临场定义。
- 不得省略 `stop_conditions` 或把停止条件改成继续修复策略。
- 不得引入 runtime、CLI、auto loop、dashboard、provider routing 或 Git worktree 自动化。
- 不得把多个单元合并为可自动连续执行的批处理。

## 输出契约

实施蓝图输出 `execution_unit` 时，必须为每个单元固定 `unit_id`、`title`、`context_packet`、`allowed_files`、`dependencies`、`must_haves`、`verification`、`stop_conditions` 和 `prior_summaries`。执行交接只能摘录和重组已批准蓝图中的单元契约，不得新增、修订或解释性扩展规划内容。

执行计划接收 `execution_unit` 时，必须逐单元列出允许修改文件、验证命令、退出码预期、summary 路径和 ledger 更新要求。每个单元完成或阻断后，执行记录必须保留验证结果、偏差结论和重审结论。

## 检查清单

- [ ] `unit_id` 与蓝图、交接、计划、ledger、summary 一致。
- [ ] `title` 与单元目标一致，未新增需求。
- [ ] `context_packet` 只引用已批准设计、已批准蓝图和有效执行交接。
- [ ] `allowed_files` 为精确文件路径，且未扩大执行范围。
- [ ] `dependencies` 已固定，执行顺序不需要临场判断。
- [ ] `must_haves` 可被验证，不是泛泛目标。
- [ ] `verification` 包含命令、期望退出码和输出摘要。
- [ ] `stop_conditions` 覆盖越界文件、runtime 需求、验证口径变化和新事实推翻资产。
- [ ] `prior_summaries` 只列当前单元允许读取的前序摘要。
- [ ] 未出现 TODO、TBD、后续再定、按需实现或执行时再判断。
