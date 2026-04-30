asset_id: hilp-execution-capability-restoration-slice-planning-orchestration
artifact_name: stage-4-5/blueprint-slice-planning-orchestration
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: human-in-loop-planning
created_from: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批

# 子蓝图：planning-orchestration

## 适用范围

本切片补强执行计划、subagent 编排、并行 agent、计划审查和实现 / 审查 prompt。

## 所属主蓝图

- `stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`

## 文件范围

- 修改：`human-in-loop-execution/references/writing-plans.md`
- 修改：`human-in-loop-execution/references/subagent-driven-development.md`
- 修改：`human-in-loop-execution/references/dispatching-parallel-agents.md`
- 修改：`human-in-loop-execution/references/prompt-templates/implementer-prompt.md`
- 修改：`human-in-loop-execution/references/prompt-templates/spec-reviewer-prompt.md`
- 修改：`human-in-loop-execution/references/prompt-templates/code-quality-reviewer-prompt.md`
- 修改：`human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md`

## 职责边界

- 只把已批准蓝图拆成可执行任务和 agent prompt。
- 不让计划或 subagent 重新设计。
- 不让多个 agent 编辑同一文件或同一 HILP 资产。

## 具体改动约束

### `writing-plans.md`

必须补入：

- 固定计划头：HILP design asset_ref、blueprint asset_ref、execution handoff asset_ref、禁止越界项、目标、执行约束。
- 文件结构锁定：先列文件职责，再拆任务。
- 任务粒度：每步 2-5 分钟。
- 每个任务包含：精确文件路径、失败测试或验证命令、预期输出、最小实现、回归验证、提交或变更记录。
- No placeholders：禁止 TODO、TBD、后续再定、类似上一步、写适当测试。
- 自检：蓝图覆盖、占位符扫描、类型 / 方法签名一致性、禁止越界项检查。

### `subagent-driven-development.md`

必须补入：

- 控制者读取计划并抽取任务全文。
- subagent 不自行读取整份计划。
- 状态处理：DONE、DONE_WITH_CONCERNS、NEEDS_CONTEXT、BLOCKED。
- 提问循环：有疑问先问，控制者补上下文后重派。
- 审查顺序：规格审查通过后才能质量审查。
- 复审循环：审查有问题时修复并复审。
- 失败处理：补上下文、换更强模型、拆任务、回到 HILP。
- 禁止静默手工修复 subagent 失败。

### `dispatching-parallel-agents.md`

必须补入：

- 独立域判定：文件集、子系统、状态依赖、验证资源。
- prompt 结构：范围、目标、约束、输出格式、HILP asset_ref、禁止越界项。
- 不适用场景：相关失败、共享状态、需要全局理解、编辑同一文件集。
- 集成检查：冲突检查、全体验证、spot check。

### `implementer-prompt.md`

必须补入：

- 背景上下文。
- 开始前提问。
- 代码组织规则。
- 升级条件：架构决策、上下文不足、重构超出计划、连续阅读无进展。
- 自查维度：完整性、质量、纪律、测试、HILP 越界。
- 报告格式：状态、实现内容、测试结果、文件变更、自查发现、阻断项。

### `spec-reviewer-prompt.md`

必须补入：

- 不信任实现报告。
- 读取实际变更。
- 对照任务全文逐项检查。
- 输出缺失项、额外项、误解项、越界项和 file:line。

### `code-quality-reviewer-prompt.md`

必须补入：

- 只能在规格审查通过后使用。
- 检查职责清晰、错误处理、测试真实行为、文件结构一致性、执行交接越界。
- 严重性校准：Critical、Important、Minor。

### `plan-document-reviewer-prompt.md`

必须补入：

- 检查完整性、蓝图对齐、任务分解、可构建性、无占位符。
- 只阻断会导致执行者构建错误或卡住的问题。

## 局部风险检查点

- prompt 不得省略 HILP 三类 asset_ref。
- subagent 不得被允许重设计。
- 计划不得出现占位符。

## 局部验证命令

```bash
grep -n "No placeholders\|占位符" human-in-loop-execution/references/writing-plans.md
grep -n "DONE_WITH_CONCERNS\|NEEDS_CONTEXT\|BLOCKED" human-in-loop-execution/references/subagent-driven-development.md
grep -n "同一文件" human-in-loop-execution/references/dispatching-parallel-agents.md
grep -n "开始前\|提问" human-in-loop-execution/references/prompt-templates/implementer-prompt.md
grep -n "不信任实现报告" human-in-loop-execution/references/prompt-templates/spec-reviewer-prompt.md
grep -n "Critical\|Important\|Minor" human-in-loop-execution/references/prompt-templates/code-quality-reviewer-prompt.md
grep -n "占位符\|可构建" human-in-loop-execution/references/prompt-templates/plan-document-reviewer-prompt.md
```

## 确定性检查

- 未确定项：无。
- 模糊表达：无。
- 需要执行者自行裁量的规划判断：无。
- 禁止越界项：不触碰 `superpowers/`。
