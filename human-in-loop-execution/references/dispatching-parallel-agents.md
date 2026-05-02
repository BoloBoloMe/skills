# 并行 agent 派发

## 适用时机

存在两个以上可独立处理的任务、失败或文件域，且它们互不共享状态、无顺序依赖、不会编辑同一文件集时使用。

## 输入契约

- HILP execution handoff asset_ref。
- 每个候选任务的文件范围、目标、验证命令。
- 禁止越界项。
- 独立域判定依据：来自已确认 runbook 的 `copied_parallel_group`、`copied_parallel_eligible`、`copied_file_domain`、`copied_shared_state` 和 `copied_verification_resources`。

## 执行规则

1. 只从已确认 runbook 读取候选 EU 的 `copied_parallel_group`、`copied_parallel_eligible`、`copied_file_domain`、`copied_shared_state` 和 `copied_verification_resources`，不得临场划分新独立域。
2. 只有 `copied_parallel_eligible=true`、同一 `copied_parallel_group` 内依赖已满足、无文件域冲突、无共享状态冲突、无 `verification_resources` 冲突时才并行。
3. prompt 结构固定包含：范围、目标、约束、输出格式、HILP asset_ref、禁止越界项、停止条件。
4. 不适用场景：相关失败、共享状态、需要全局理解、编辑同一文件集、同一验证资源互斥、`copied_parallel_eligible=false`、缺少 `copied_parallel_group` 或 runbook 未确认。
5. 集成检查：agent 返回后做冲突检查、全体验证和 spot check。

## 禁止事项

- 不得让多个 agent 编辑同一文件或同一 HILP 资产。
- 不得并行处理有顺序依赖的任务。
- 不得把不清楚的任务并行派发以逃避理解。
- 不得把 `file_domain`、`shared_state` 或 `verification_resources` 冲突的 EU 并行派发。
- 不得绕过执行交接范围。

## 输出契约

输出独立域划分、每个 agent 的任务摘要、冲突检查、集成验证结果和 spot check 结果。若独立性不足，输出改用顺序执行的理由。

## 检查清单

- [ ] 候选 EU 均为 `copied_parallel_eligible=true`。
- [ ] 任务互不共享文件。
- [ ] 无顺序依赖、无共享状态、无 `verification_resources` 冲突。
- [ ] prompt 包含执行交接和禁止越界项。
- [ ] 已完成冲突检查。
- [ ] 集成验证已运行。
