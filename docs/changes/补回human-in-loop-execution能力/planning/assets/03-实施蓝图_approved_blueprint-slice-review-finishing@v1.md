asset_id: hilp-execution-capability-restoration-slice-review-finishing
artifact_name: stage-4-5/blueprint-slice-review-finishing
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
last_event: human-approval-granted
last_decision: human-approval-2026-04-29-approve-blueprint-package-v1
approval_marker: approved
approval_marker_label: 已批准

# 子蓝图：review-finishing

## 适用范围

本切片补强代码审查、反馈处理、最终审查 prompt 和分支收尾纪律。

## 所属主蓝图

- `stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`

## 文件范围

- 修改：`human-in-loop-execution/references/code-review.md`
- 修改：`human-in-loop-execution/references/finishing-branch.md`
- 修改：`human-in-loop-execution/references/prompt-templates/code-reviewer.md`

## 职责边界

- 只处理执行层代码质量 gate 和收尾动作。
- 不替代 HILP 规划资产归档。
- 不允许审查建议直接扩大蓝图范围。

## 具体改动约束

### `code-review.md`

必须补入：

- 请求审查工作流：BASE_SHA、HEAD_SHA、diff 范围、实现说明、计划或需求引用。
- 审查类型：规格符合性、代码质量、测试质量、生产就绪性、HILP 越界风险。
- 接收反馈流程：读完整反馈、理解、验证、评估、回应、逐项实现。
- 外部反馈怀疑性验证：检查是否适合当前代码库、是否破坏现有行为、是否违反 HILP 已批准边界。
- 禁止表演式附和：不得用赞同语替代技术判断。
- YAGNI 检查：蓝图外能力标记为需 HILP 重审或拒绝。
- 多项反馈处理顺序：先澄清不明项，再处理 Critical、简单修复、复杂修复。

### `code-reviewer.md`

必须补入：

- Git 范围：BASE_SHA..HEAD_SHA。
- 审查清单：代码质量、架构、测试、需求符合、生产就绪、HILP 越界。
- 输出格式：Strengths、Issues、Recommendations、Assessment。
- 每个 issue 必须有 file:line、问题、影响、修复方向。
- 严重性规则：Critical 只用于 bug、安全、数据丢失、破坏功能；Important 用于架构、缺失功能、错误处理、测试缺口；Minor 用于风格、文档、优化。

### `finishing-branch.md`

必须补入：

- 收尾前运行完成前验证和审查阻断项检查。
- 固定后续选项：本地合并、推送创建 PR、保留分支、丢弃工作。
- 丢弃工作必须要求用户输入精确确认词。
- 合并或创建 PR 前后都要验证；失败不得继续。
- worktree cleanup 只在安全选项下执行，不自动删除用户工作。
- 完成后输出 HILP 执行结果、偏差、新事实或重审触发。

## 局部风险检查点

- 不得在 Critical 未清零时继续。
- 不得把蓝图外审查建议直接实现。
- 不得在验证失败时提供 merge / PR 成功结论。
- 不得无确认删除用户工作。

## 局部验证命令

```bash
grep -n "BASE_SHA\|HEAD_SHA" human-in-loop-execution/references/code-review.md
grep -n "外部反馈\|YAGNI\|表演式" human-in-loop-execution/references/code-review.md
grep -n "BASE_SHA\|HEAD_SHA" human-in-loop-execution/references/prompt-templates/code-reviewer.md
grep -n "file:line\|Critical\|Important\|Minor" human-in-loop-execution/references/prompt-templates/code-reviewer.md
grep -n "本地合并\|创建 PR\|保留分支\|丢弃" human-in-loop-execution/references/finishing-branch.md
grep -n "确认" human-in-loop-execution/references/finishing-branch.md
```

## 确定性检查

- 未确定项：无。
- 模糊表达：无。
- 需要执行者自行裁量的规划判断：无。
- 禁止越界项：不触碰 `superpowers/`。
