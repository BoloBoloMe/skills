---
name: workflow-subagent-router
description: 根据 workflow skills 的阶段状态选择 saved subagent chains. 当工程任务已由 orchestrate 分类, 且需要 subagent 编排, 多阶段计划, 并行审查, async worker, 或标准化实现流程时使用. 本 skill 只做路由和执行前确认, 不直接实现.
---

# Workflow Subagent Router

本 skill 由父会话使用. 不注入普通子代理.

## 核心原则

- `orchestrate` 判断任务类型.
- 本 skill 判断是否需要 saved chain, 以及选择哪条 saved chain.
- saved chain 只定义怎么跑, 不决定是否该跑.
- 父会话保留最终决策权.
- 执行任何 chain 前必须问用户: `是否执行?`.
- 默认单 writer. 并行只用于 context, research, review, validation.
- review-only 子代理必须 fresh context, 且不得修改 project/source files.
- worker 完成不是最终完成. 实现类任务默认需要 review, 或明确说明为什么跳过 review.

## 路由表

| 当前任务状态 | saved chain | 说明 |
|---|---|---|
| 需求不清, 但需要读代码/文档后澄清 | `workflow-context-gate` | 收集上下文, 然后父会话问澄清问题 |
| 已知目标, 但缺实现方案 | `workflow-plan-only` | 只产计划, 不实现 |
| 计划已批准, 要实现并审查 | `workflow-implement-review` | 单 worker 实现, fresh reviewers 审查, worker 修 accepted findings |
| 未知根因 bug/报错/测试失败/性能回退 | `workflow-diagnose-to-tdd` | 先诊断, 根因明确后再决定是否 TDD 修复 |
| 已有上下文, 要 PRD 或拆 issue | `workflow-prd-to-issues` | PRD 和 tracer bullet issues |
| 只读架构评审/重构候选 | 不强制 chain | 可直接用 `improve-codebase-architecture` 或 review fanout |
| 小范围机械修改/普通问答 | 不用 chain | 父会话直接处理 |

## 父会话决策步骤

1. 判断用户是否明确点名 skill 或 chain.
2. 如果点名且不冲突, 优先尊重.
3. 如果点名明显冲突, 说明冲突并问用户.
4. 用 `orchestrate` 判断任务属于 diagnose, zoom-out, grill-with-docs, prototype, tdd, to-prd, to-issues, triage, use-worktree, 或普通任务.
5. 判断当前阶段:
   - 是否已有明确验收标准?
   - 是否已有批准计划?
   - 是否需要写代码?
   - 是否需要并行审查?
   - 是否存在未知根因?
6. 选择 saved chain, 或说明不使用 chain.
7. 在执行前问: `是否执行?`.

## Chain 选择规则

### `workflow-context-gate`

使用条件:

- 需求边界不清.
- 需要读取代码, 文档, ADR, tests, 或 config 后才能问出好问题.
- 当前不应直接计划或实现.

输出要求:

- 已知事实.
- 相关文件/模块.
- 风险和不确定点.
- 必须问用户的问题.
- 推荐下一步.

### `workflow-plan-only`

使用条件:

- 目标大体清楚.
- 需要实现计划.
- 尚未批准实现.

输出要求:

- 计划.
- 验收标准.
- 风险.
- 建议验证命令.
- 是否需要先做 prototype/TDD/diagnose.

### `workflow-implement-review`

使用条件:

- 计划已批准.
- 行为和验收标准明确.
- 用户允许实现.

输出要求:

- worker handoff.
- reviewer findings.
- accepted fixes.
- validation evidence.
- final remaining risks.

### `workflow-diagnose-to-tdd`

使用条件:

- 未知根因.
- 有 bug, 报错, 测试失败, 性能回退, 或行为异常.
- 不应先写大改动.

输出要求:

- 复现方式.
- 最小失败证据.
- 根因假设和验证.
- 修复建议.
- 是否进入 TDD 修复的确认点.

### `workflow-prd-to-issues`

使用条件:

- 用户要求 PRD, 工单, triage, 或从方案拆执行项.
- 上下文已足够, 或用户明确要求基于当前上下文生成.

输出要求:

- PRD 或 issue 列表.
- 每个 issue 的 vertical slice.
- 验收标准.
- 依赖关系.
- 风险和非目标.
