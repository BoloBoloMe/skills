# Execution Unit Intake

## 适用时机

HILE 已收到执行计划确认，准备执行某一个 `execution_unit` 前使用。本规则只校验当前单元是否可以进入实现，不负责补写蓝图、重新规划或自动连续执行后续单元。

## 输入契约

当前 `execution_unit` 必须来自 HILP 执行交接或已确认的执行计划，并包含：

- `unit_id` 和标题。
- HILP design asset_ref，且状态为 `approved｜中文状态=已批准`。
- HILP blueprint asset_ref，且状态为 `approved｜中文状态=已批准`。
- HILP execution handoff asset_ref，且为当前执行入口。
- `context_packet`，且包含 `approved_design_ref`、`approved_blueprint_ref`、`handoff_ref`、`required_sections`、`relevant_decisions`、`prior_summaries`、`explicitly_ignore`。
- `allowed_files`。
- `must_haves`。
- `verification`。
- `stop_conditions`。
- `prior_summaries`。

## 接收检查

执行当前 `execution_unit` 前，逐项检查：

1. 资产引用：`context_packet.approved_design_ref` 必须是已批准设计资产；`context_packet.approved_blueprint_ref` 必须是已批准蓝图资产；`context_packet.handoff_ref` 必须与当前执行计划绑定的有效 handoff 一致。
2. required_sections：`context_packet.required_sections` 必须列出当前单元所需的 Context Packet、单元标题、执行范围、禁止越界项、验证或停止条件等章节；缺少必要章节时停止，不得自行搜索未绑定资产补齐。
3. relevant_decisions：`context_packet.relevant_decisions` 只能包含当前单元必须遵守的已批准决策；不得引用旧方案、草稿、待审批或待修订材料来决定实现路线。
4. prior_summaries：`context_packet.prior_summaries` 与单元级 `prior_summaries` 必须一致；列出的摘要必须存在且与依赖顺序一致，空列表或 `none` 表示当前单元无前序摘要输入。
5. explicitly_ignore：`context_packet.explicitly_ignore` 必须列出待审批资产、待修订资产、已废弃方案和其他未绑定材料；执行中遇到这些材料时只记录并忽略，不得作为实现依据。
6. 允许文件：所有计划修改必须落在 `allowed_files` 内；需要修改清单外产品文件时停止。
7. 上下文读取：只读取 `context_packet` 指定的必读章节、相关决策、前序摘要和明确允许的参考材料；不重读全部历史规划资产。
8. 验证：`verification` 必须包含当前单元完成前要运行的命令、期望退出码和输出摘要。
9. 停止条件：`stop_conditions` 必须覆盖执行阶段补做规划判断、runtime 需求、越界文件、新事实推翻资产和验证口径变化。

## 禁止事项

- 不得把 intake 变成蓝图补齐或方案选择。
- 不得读取未在 `context_packet` 或当前执行计划中绑定的资产来决定实现路线。
- 不得扩大 `allowed_files`。
- 不得跳过执行计划确认门。
- 不得自动连续执行全部 `execution_unit`。
- 不得把 failure forensics 用作继续修复机制。
- 不得把 `explicitly_ignore` 中列出的资产或材料升级为执行依据。

## 输出契约

接收通过时，在执行记录中保留当前 `unit_id`、资产引用、`context_packet` 核验结论、`allowed_files`、验证命令和停止条件。接收不通过时，停止当前单元，记录缺失项或越界项，并回到 HILP 变更重审或执行计划修正入口；不得边执行边补规划判断。

## 失效资产回退规则

- 若 `approved_design_ref` 或 `approved_blueprint_ref` 不是 `approved｜中文状态=已批准`，或被标记为待修订、已归档、已废弃、版本不一致，立即停止当前单元，记录失败摘要，并回到 HILP 变更重审。
- 若 `handoff_ref` 不是当前有效执行交接，缺少 owner、落盘证据、执行范围、禁止越界项或无阻断项结论，立即停止当前单元，并回到执行计划修正或 HILP 变更重审入口。
- 若 `required_sections`、`relevant_decisions`、`prior_summaries` 或 `explicitly_ignore` 缺失且无法从当前交接包直接确认，立即停止当前单元；不得通过搜索未绑定资产、补做蓝图判断或读取旧方案继续执行。
- 若执行中发现 `context_packet` 引用失效资产，回退前只做取证和记录，不继续修改产品文件。

## 检查清单

- [ ] `unit_id` 与执行计划一致。
- [ ] 设计资产引用为已批准。
- [ ] 蓝图资产引用为已批准。
- [ ] 交接引用与当前计划一致。
- [ ] `context_packet` 完整且未引用失效资产。
- [ ] `required_sections` 覆盖当前单元必读章节且不要求重读全部历史规划资产。
- [ ] `relevant_decisions` 均来自已批准设计、已批准蓝图或有效执行交接。
- [ ] `prior_summaries` 已存在且符合依赖顺序，或明确为 `none`。
- [ ] `explicitly_ignore` 已排除待审批资产、待修订资产、已废弃方案和未绑定材料。
- [ ] `allowed_files` 覆盖所有拟修改文件且无额外文件。
- [ ] `verification` 可直接运行或明确记录为人工检查。
- [ ] `stop_conditions` 已复制到当前执行上下文。
- [ ] 未要求 HILE 在执行阶段补做 HILP 蓝图判断。
