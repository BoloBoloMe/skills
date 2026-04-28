---
name: human-in-loop-planning
description: 面向人在回路规划协议的总入口。用于把复杂变更、重构、迁移、调查、设计审批、蓝图编制、重审和执行交接纳入同一状态机。适用于用户要求按 hilp 或人在回路流程规划任务、比较方案、补齐需求事实、处理旧批准被新事实推翻、生成已批准设计后的实施蓝图、交接已批准蓝图到执行层，或压测该协议本身。不要用于直接写代码或绕过人工决策；若只是普通问答且不需要阶段门控，不触发。
---

# 人在回路规划

## 概览

将本 Skill 作为一个整体规划协议使用，而不是 7 个独立 Skill 使用。`hilp-router`、`hilp-requirements-facts`、`hilp-design-approval`、`hilp-blueprint`、`hilp-reapproval`、`hilp-execution-handoff` 和 `hilp-skill-pressure-test` 是协议内部的执行单元，详细规则放在 `references/` 下。

本 Skill 的职责是在处理用户任务时，保持阶段门控、资产状态、审批边界和重审行为一致。对普通用户输出时，应优先使用中文阶段名称和任务相关内容，不默认暴露内部执行单元、事件名、状态机推导细节。

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

## 用户可见阶段名称

普通用户默认只需要知道“现在处于哪个阶段、这个阶段要解决什么、需要自己做什么”。因此输出时使用以下中文阶段名作为主表达：

- `hilp-router` → 初始分流阶段
- `hilp-requirements-facts` → 需求对齐与事实求证阶段
- `hilp-design-approval` → 方案设计与审批阶段
- `hilp-blueprint` → 实施蓝图阶段
- `hilp-reapproval` → 变更重审阶段
- `hilp-execution-handoff` → 执行交接阶段
- `hilp-skill-pressure-test` → 协议压力测试阶段

内部模块名、事件名、`owner_skill`、`last_event`、`last_decision` 等字段默认只写入资产元数据或审计说明。只有用户要求调试协议、审查协议本身、追踪资产状态，或交接契约要求精确引用时，才在用户可见回答中展示这些内部字段。

## 资产落盘规则

所有已通过入口门槛的阶段都必须产出 Markdown 资产，并保存到当前项目目录下。实施蓝图阶段和执行交接阶段若未通过确定性检查，不得生成对应正式资产；只能由回退到的前置阶段记录阻断原因：

```text
项目根目录/docs/hilp/变更概述/
```

其中“变更概述”应使用本次任务的简短中文概括，例如 `改进HILP中文交互与资产落盘`。若无法确认项目根目录，必须先向用户确认保存位置；若写入失败，必须明确告知失败，不得声称资产已保存。

文件名必须同时体现阶段和审批状态，推荐格式：

```text
<阶段前缀>-<阶段中文名>_<审批标记>_<artifact>@vN.md
```

阶段前缀：

- `00`：初始分流阶段
- `01`：需求对齐与事实求证阶段
- `02`：方案设计与审批阶段
- `03`：实施蓝图阶段
- `04`：变更重审阶段
- `05`：执行交接阶段
- `90`：协议压力测试阶段

审批标记：

- `no-approval`：无需审批，仅作为过程记录
- `needs-decision`：需要用户先做裁决
- `needs-approval`：可提交审批，但尚未批准
- `approved`：已明确批准
- `needs-revision`：需要修订
- `archived`：已归档

旧资产不迁移；本规则只影响新产生的资产。

## 路由决策树

1. 如果用户是在测试、审查、验证或压力测试本协议本身，使用 `hilp-skill-pressure-test`。
2. 如果输入提到之前方案、旧判断、已批准结论、返工、重新看、推翻、新证据、运行中、已交接、已进入执行、治理变化、回滚、兼容窗口，或必须人工裁决阻断既有路径，先使用 `hilp-reapproval`。即使资产引用不完整，也按重审入口处理。
3. 如果这是没有既有资产、旧判断、当前阶段或重审语义的新规划任务，先使用 `hilp-router`。
4. 如果需求、范围、成功标准、当前行为、根因或影响面不清楚，使用 `hilp-requirements-facts`。
5. 如果目标、范围 / 非目标、成功标准、当前行为或证据基础、至少有界的影响面，以及不阻断方案比较的核心未知项都已建立，使用 `hilp-design-approval`。
6. 只有存在已批准的 Stage 3 设计资产，并且具备完整资产引用、owner_skill、人工批准授予（Human Approval Granted） 决策，且所有会影响实施蓝图的变量已经确定时，才使用 `hilp-blueprint`。若文件范围、接口、数据形状、验证口径、风险处理或执行边界仍未确定，必须先回到 `hilp-requirements-facts`、`hilp-design-approval` 或 `hilp-reapproval`。
7. 只有存在已批准的 Stage 4/5 蓝图资产、owner_skill、人工批准授予（Human Approval Granted） 决策、仍有效的上游已批准设计资产、确定性检查已通过，且没有未解决阻断项时，才使用 `hilp-execution-handoff`。执行模式、执行范围和禁止越界项未确定时，不得进入执行交接。

不要把内部模块名当作真实的独立 Skill 调用。应在本 Skill 内部读取相应参考文件，并按该模块的输出模板完成响应。

## 资产与审批纪律

资产状态只允许以下六种，所有落盘文档和用户交互都必须给出对应中文状态名：

- `draft` → 草稿
- `ready-for-human-decision` → 待人工裁决
- `ready-for-approval` → 待审批
- `approved` → 已批准
- `needs-revision` → 待修订
- `archived` → 已归档

审批标记必须给出对应中文状态名：

- `no-approval` → 无需审批
- `needs-decision` → 待裁决
- `needs-approval` → 需审批
- `approved` → 已批准
- `needs-revision` → 待修订
- `archived` → 已归档

`ready-for-approval`（待审批）不是 `approved`（已批准）。只有明确的人工批准授予（Human Approval Granted） 才能把某个带版本的资产推进为 `approved`（已批准）。只有 `approved`（已批准）资产可以作为下游规划的绑定性输入。

人工批准授予（Human Approval Granted）必须明确批准当前具体资产版本。泛泛的“可以执行了”“差不多了”或“按这个来”不足以构成批准，除非上下文已经明确绑定到当前 `asset_ref`。

## 蓝图后确定性纪律

从实施蓝图阶段开始，所有正式落盘资产必须是确定、唯一、可执行的，不得保留任何待定、可选、后续确认或执行时再判断的内容。该纪律同时约束实施蓝图阶段和执行交接阶段。

以下内容一旦会影响实现路线、文件范围、接口形态、数据形状、算法骨架、错误处理、风险处理、验证口径、发布顺序、执行模式或禁止越界项，均视为未确定项：

- “待定”“可能”“视情况”“后续确认”“执行时再判断”“可选 A/B”“暂按”“大概”“原则上”等模糊表达。
- TODO、TBD、问号、空字段、占位符，或需要执行者补做规划判断的内容。
- 多个实现路径并列但未选择，或把风险处理留给执行者临场决定。

命中上述情况时，不得产出或批准 `stage-4-5/implementation-blueprint`，也不得产出 `stage-6/execution-handoff`；必须回退到能消除不确定性的前置阶段。执行交接阶段只能引用、摘录和封装已批准且通过确定性检查的蓝图，不得新增、修订或解释性扩展规划内容。

## 输出纪律

在本协议下输出任何响应时，必须：

1. 使用所选阶段参考文件中的输出模板，但用户可见标题应使用中文阶段名称。
2. 先说明当前阶段目的、已保存资产、当前结论和需要用户做什么。
3. 不默认展示内部模块名、事件推导、状态机计算过程或完整交接细节。
4. 若存在会影响用户行动的阻断项，必须用自然中文说明“缺什么、为什么不能继续、用户需要决定什么”。从实施蓝图阶段开始，阻断项不得写入正式蓝图或执行交接资产，只能触发回退说明。
5. 所有用户可见状态都必须优先给出中文状态名；涉及精确资产引用、审计或交接时，采用“内部值｜中文状态=中文名”的双写格式。
6. 只有交接契约允许时，才说明下一阶段；对普通用户写中文阶段名，对资产元数据保留内部标识。
7. 若输出会驱动下游工作，必须包含带版本、内部状态和中文状态名的资产引用，并写入项目目录下的阶段资产文件。

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
