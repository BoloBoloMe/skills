# subagent 驱动执行

## 适用时机

执行计划已存在，任务彼此独立、无顺序依赖、不会编辑同一文件集，且当前平台支持派发 subagent 时使用。

## 输入契约

- 已保存执行计划或 Execution Runbook 路径。
- 用户已明确确认当前执行计划或 runbook 文件路径。
- HILP design asset_ref、blueprint asset_ref、execution handoff asset_ref。
- 每个任务的完整文本、局部上下文、文件范围、验证命令、禁止越界项和停止条件。
- 已确认 runbook 中复制的 `copied_parallel_group`、`copied_parallel_eligible`、`copied_file_domain`、`copied_shared_state` 和 `copied_verification_resources`。
- subagent 可用性确认。

## 执行规则

1. 若用户未明确确认当前执行计划或 runbook 文件路径，不派发 subagent，停止在执行计划确认阶段。
2. 控制者读取计划并抽取每个任务全文，不要求 subagent 自行读取整份计划。
3. subagent prompt 必须包含 HILP 执行交接 asset_ref、禁止越界项、完整任务、局部上下文、验证命令、停止条件、`copied_parallel_group`、`copied_parallel_eligible`、`copied_file_domain`、`copied_shared_state` 和 `copied_verification_resources`。
4. 只有用户选择子代理模式，且 runbook 中 `copied_parallel_eligible=true`、依赖已满足、同组无文件域冲突、无共享状态冲突、无验证资源冲突的 EU 才能派发 subagent；`parallel_eligible=false` 或缺失并行字段的 EU 必须串行。
5. subagent 状态只接受 DONE、DONE_WITH_CONCERNS、NEEDS_CONTEXT、BLOCKED。
6. 提问循环：subagent 可在开始前或过程中提问；控制者补上下文后重派，不让其猜测。
7. 审查顺序：规格审查通过后才能质量审查。
8. 复审循环：审查有问题时由实现方修复并复审，直至通过或阻断。
9. 禁止静默手工修复 subagent 失败；修复也要进入同样审查和验证门。

模型选择：机械任务使用较轻模型；多文件集成、调试、模式匹配使用标准模型；架构、设计判断、最终审查使用最强可用模型。若模型选择错误导致 BLOCKED，不重复同样派发。

失败重派策略：

| 状态 | 处理 |
|---|---|
| NEEDS_CONTEXT | 补充缺失上下文后重派。 |
| BLOCKED 且上下文不足 | 补上下文后重派。 |
| BLOCKED 且模型能力不足 | 换更强模型。 |
| BLOCKED 且任务过大 | 拆成更小任务。 |
| BLOCKED 且蓝图错误 | 停止并回到 HILP 变更重审。 |

复杂任务调度校准：每个任务给完整任务文本、局部上下文、验证命令和停止条件；任务完成后先 spec compliance，再 code quality；DONE_WITH_CONCERNS 先读 concerns，再决定补上下文、复审或回到 HILP。

红旗清单：让 subagent 自己读整份计划；跳过规格审查或质量审查；规格审查未通过就做质量审查；多个实现 subagent 并行编辑同一文件；reviewer 有问题但不复审；实现者自查替代真正审查；控制者手工修 subagent 失败以绕过流程。

## 禁止事项

- 不得并行派发会编辑同一文件或同一 HILP 资产的任务。
- 不得并行派发 runbook 中 `copied_parallel_eligible` 不是 `true` 的 EU。
- 不得让 HILE 或 subagent 推断未标记 `parallel_eligible` 的 EU 可并行。
- 不得跳过规格审查或代码质量审查。
- 不得让 subagent 重新设计或扩大执行范围。
- 不得在 subagent 中隐藏禁止越界项。
- 不得接受 BLOCKED 后无变化重试。

## 输出契约

每个任务输出状态、文件变更、验证结果、规格审查、代码质量审查、模型选择理由和未解决问题。整体输出必须引用执行交接资产并说明是否可进入分支收尾。

## 检查清单

- [ ] 用户已明确确认当前执行计划或 runbook 文件路径。
- [ ] 任务相互独立，且独立性来自已确认 runbook 的 `copied_parallel_eligible=true` 与冲突检查结果。
- [ ] prompt 包含 HILP 三类 asset_ref。
- [ ] 已处理 DONE_WITH_CONCERNS、NEEDS_CONTEXT、BLOCKED。
- [ ] 模型选择与任务复杂度匹配。
- [ ] 规格审查先于质量审查。
