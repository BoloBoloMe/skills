---
name: human-in-loop-execution
description: Use when HILP execution handoff has completed intake with no blocking items and implementation, testing, review, debugging, or branch finishing needs execution discipline
---

# 人在回路执行

## 概览

本技能是 HILP 规划链完成执行交接之后的执行纪律入口。它只把已批准设计、已批准蓝图和执行交接资产转化为受约束的计划、实现、测试、审查、调试与收尾行为，不补做规划、不替代审批、不扩大执行范围。

本技能补回的是执行强制门和抗误用细节，不接管 HILP 规划审批。

## 入口前提

进入本技能前必须同时具备：

- `stage-3/design-choice@vN [state=approved｜中文状态=已批准]`
- `stage-4-5/implementation-blueprint@vM [state=approved｜中文状态=已批准]`
- 有效的 `stage-6/execution-handoff@vK [state=<state>｜中文状态=<state_label>]`
  - `owner_skill=hilp-execution-handoff`
  - 已成功落盘
  - 执行入口检查：无阻断项
  - 执行范围、禁止越界项、停止并回退条件齐备
- 当前工作区：用户指定的执行工作区。

执行交接资产自身不要求已批准；它是规划出口记录，按有效性检查判定。不得用执行交接资产的 `archived｜中文状态=已归档` 状态否定其入口有效性。

缺少已批准设计时，回到 HILP 方案设计阶段；缺少已批准蓝图时，回到实施蓝图阶段；缺少有效执行交接、执行范围、禁止越界项或停止条件时，回到执行交接阶段；发现新事实或上游失效时，回到变更重审阶段。

## 阶段名称

- 执行入口检查阶段
- 执行计划阶段
- subagent 执行阶段
- inline 执行阶段
- TDD 实现阶段
- 代码审查阶段
- review 反馈处理阶段
- 分支收尾阶段
- HILP 重审回退

## 资源加载顺序

1. 所有执行请求先读取 `references/hilp-handoff-intake.md`，确认 HILP 资产、执行交接、执行范围和禁止越界项。
2. 需要判断执行路径时读取 `references/execution-routing.md`。
3. 需要把蓝图拆为执行任务时读取 `references/writing-plans.md`。
4. 生产代码、bug 修复或行为变更前先读取 `references/test-driven-development.md`。
5. 测试失败、构建失败或异常行为出现时先读取 `references/systematic-debugging.md`；涉及异步或污染时再按需读取根因追踪、防御式验证、条件式等待和测试反模式参考。
6. 平台支持 subagent 且任务独立时读取 `references/subagent-driven-development.md`、`references/dispatching-parallel-agents.md` 和相应 prompt template。
7. 平台不支持 subagent、任务强耦合或用户要求单会话时读取 `references/executing-plans.md`。
8. 请求审查、处理反馈或准备最终审查前先读取 `references/code-review.md` 与相应审查 prompt。
9. 任何完成声明、提交、合并或交付前先读取 `references/verification-before-completion.md`；收尾动作再读取 `references/finishing-branch.md`。
10. 只有创建或修改技能时读取 `references/writing-skills.md`。

## 路由规则

- HILP 资产或执行交接缺失：停止，回到 HILP。
- 执行范围、禁止越界项、停止并回退条件缺失：停止，回到 HILP 执行交接或变更重审。
- 发现新事实、审批缺失、蓝图错误、回滚风险或蓝图外文件需求：HILP 重审回退优先于任何执行动作。
- 没有执行计划时进入执行计划阶段。
- 有独立任务、无共享文件、平台支持 subagent 时进入 subagent 执行阶段。
- 无 subagent、任务强耦合或平台限制时进入 inline 执行阶段。
- 任何生产代码或行为变更进入 TDD 实现阶段。
- 任何失败或异常进入系统化调试纪律。
- 完成一个任务或一组任务后进入代码审查阶段。
- 收到审查反馈后进入 review 反馈处理阶段。
- 准备声明完成、提交、合并或交付前进入完成前验证与分支收尾阶段。

## HILP 绑定纪律

- 所有执行计划、subagent prompt、审查请求和完成声明都必须引用 HILP 设计、蓝图与执行交接 asset_ref。
- 执行者只能按执行交接资产中的范围、顺序、禁止越界项和停止条件工作。
- 不得把待审批、草稿、待修订或已归档的设计资产或蓝图资产当作已批准输入；执行交接资产按 owner、落盘、无阻断项、执行范围、禁止越界项和停止条件做有效性检查。
- 不得用执行阶段补齐需求、设计、蓝图、接口、数据形状或验证口径缺口。
- 执行中发现前提变化时，输出“停止执行，回到 HILP 变更重审”，并列出触发原因。

## 输出纪律

- 开始执行前说明当前引用的 HILP 资产、执行范围、禁止越界项和当前阶段。
- 计划文件保存到 `docs/human-in-loop-execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
- 每次完成声明必须包含新鲜验证命令、退出结果和输出摘要。
- 审查结果按 Critical、Important、Minor 分类；Critical 阻断继续推进，Important 修完再继续，Minor 可记录但不得掩盖阻断。
- 若不能继续，明确写出缺少什么、为什么不能继续、应回到哪个 HILP 阶段。

## 参考文件

- `references/execution-routing.md`
- `references/hilp-handoff-intake.md`
- `references/writing-plans.md`
- `references/subagent-driven-development.md`
- `references/executing-plans.md`
- `references/test-driven-development.md`
- `references/code-review.md`
- `references/finishing-branch.md`
- `references/systematic-debugging.md`
- `references/verification-before-completion.md`
- `references/dispatching-parallel-agents.md`
- `references/writing-skills.md`
- `references/prompt-templates/implementer-prompt.md`
- `references/prompt-templates/spec-reviewer-prompt.md`
- `references/prompt-templates/code-quality-reviewer-prompt.md`
- `references/prompt-templates/code-reviewer.md`
- `references/prompt-templates/plan-document-reviewer-prompt.md`
- `references/testing-anti-patterns.md`
- `references/root-cause-tracing.md`
- `references/defense-in-depth.md`
- `references/condition-based-waiting.md`
