---
name: human-in-loop-planning
description: 面向人在回路规划协议的总入口。用于把复杂变更、重构、迁移、调查、设计审批、蓝图编制、重审和执行交接纳入同一状态机。适用于用户要求按 hilp 或人在回路流程规划任务、比较方案、补齐需求事实、处理旧批准被新事实推翻、生成已批准设计后的实施蓝图、交接已批准蓝图到执行层，或压测该协议本身。不要用于直接写代码或绕过人工决策；若只是普通问答且不需要阶段门控，不触发。
---

# 人在回路规划

## 概览

将本 Skill 作为一个整体规划协议使用，而不是 7 个独立 Skill 使用。`hilp-router`、`hilp-requirements-facts`、`hilp-design-approval`、`hilp-blueprint`、`hilp-reapproval`、`hilp-execution-handoff` 和 `hilp-skill-pressure-test` 都是本 Skill 内部模块，详细规则放在 `references/` 下。

本 Skill 的职责是在处理用户任务时，保持阶段门控、资产状态、审批边界和重审行为一致，并把当前任务路由到正确的内部模块。

## 资源加载顺序

触发本 Skill 后，按需逐步读取参考文件：

1. 涉及阻断事件、状态转换、失效、审批、必须人工裁决的决策或 允许状态转移时，优先读取 `references/event-action-rules.md`。
2. 涉及交接、最小输入契约、最小输出契约或禁止转移时，其次读取 `references/handoff-contracts.md`。
3. 涉及初始路由、规划原型、治理模式、规格策略、验证策略、升级或降级时，再读取 `references/routing-matrix.md`。
4. 最后只读取当前步骤需要的内部模块参考文件：
   - `references/router.md`
   - `references/requirements-facts.md`
   - `references/design-approval.md`
   - `references/blueprint.md`
   - `references/reapproval.md`
   - `references/execution-handoff.md`
   - `references/skill-pressure-test.md`

参考文件优先级固定为：`event-action-rules.md` > `handoff-contracts.md` > `routing-matrix.md` > 当前模块参考文件。

## 路由决策树

1. 如果用户是在测试、审查、验证或压力测试本协议本身，使用 `hilp-skill-pressure-test`。
2. 如果输入提到之前方案、旧判断、已批准结论、返工、重新看、推翻、新证据、运行中、已交接、已进入执行、治理变化、回滚、兼容窗口，或必须人工裁决阻断既有路径，先使用 `hilp-reapproval`。即使资产引用不完整，也按重审入口处理。
3. 如果这是没有既有资产、旧判断、当前阶段或重审语义的新规划任务，先使用 `hilp-router`。
4. 如果需求、范围、成功标准、当前行为、根因或影响面不清楚，使用 `hilp-requirements-facts`。
5. 如果目标、范围 / 非目标、成功标准、当前行为或证据基础、至少有界的影响面，以及不阻断方案比较的核心未知项都已建立，使用 `hilp-design-approval`。
6. 只有存在已批准的 Stage 3 设计资产，并且具备完整资产引用、owner_skill 和人工批准授予（Human Approval Granted） 决策时，才使用 `hilp-blueprint`。
7. 只有存在已批准的 Stage 4/5 蓝图资产、owner_skill、人工批准授予（Human Approval Granted） 决策、仍有效的上游已批准设计资产，且没有未解决阻断项时，才使用 `hilp-execution-handoff`。

不要把内部模块名当作真实的独立 Skill 调用。应在本 Skill 内部读取相应参考文件，并按该模块的输出模板完成响应。

## 资产与审批纪律

资产状态只允许以下六种：

- `draft`
- `ready-for-human-decision`
- `ready-for-approval`
- `approved`
- `needs-revision`
- `archived`

`ready-for-approval` 不是 `approved`。只有明确的人工批准授予（Human Approval Granted） 才能把某个带版本的资产推进为 `approved`。只有 `approved` 资产可以作为下游规划的绑定性输入。

人工批准授予（Human Approval Granted）必须明确批准当前具体资产版本。泛泛的“可以执行了”“差不多了”或“按这个来”不足以构成批准，除非上下文已经明确绑定到当前 `asset_ref`。

## 输出纪律

在本协议下输出任何响应时，必须：

1. 使用所选内部模块参考文件中的输出模板。
2. 标明当前内部模块。
3. 标明任何阻断事件、必须人工裁决的人类决策、缺失输入或已失效资产。
4. 只有交接契约允许时，才标明下一内部模块。
5. 若输出会驱动下游工作，必须包含带版本和状态的资产引用。

当必须人工裁决的决策、证据缺失、上游资产失效或审批缺失阻断转移时，不得写实现代码、最终执行步骤或绑定性下游计划。

## 参考文件

- `references/event-action-rules.md`
- `references/handoff-contracts.md`
- `references/routing-matrix.md`
- `references/router.md`
- `references/requirements-facts.md`
- `references/design-approval.md`
- `references/blueprint.md`
- `references/reapproval.md`
- `references/execution-handoff.md`
- `references/skill-pressure-test.md`
