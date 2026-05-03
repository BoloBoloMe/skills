---
name: human-in-loop-planning
description: 面向人在回路规划协议的总入口。用于把复杂变更、重构、迁移、调查、设计审批、蓝图编制、重审、执行交接和规划资产归档纳入同一状态机。适用于用户要求按 hilp 或人在回路流程规划任务、比较方案、补齐需求事实、处理旧批准被新事实推翻、生成已批准设计后的实施蓝图、交接已批准蓝图到执行层、整理已交接规划资产归档，或压测该协议本身。不要用于直接写代码或绕过人工决策；若只是普通问答且不需要阶段门控，不触发。
---

# 人在回路规划

## 概览

将本 Skill 作为一个整体规划协议使用，而不是 8 个独立 Skill 使用。`hilp-router`、`hilp-requirements-facts`、`hilp-design-approval`、`hilp-blueprint`、`hilp-reapproval`、`hilp-execution-handoff`、`hilp-archive` 和 `hilp-skill-pressure-test` 是协议内部的执行单元，详细规则放在 `references/` 下。

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
   - `references/execution-plan-contract.md`
   - `references/execution-unit-schema.md`
   - `references/verification-contract.md`
   - `references/context-packet.md`
   - `references/archive.md`
   - `references/skill-pressure-test.md`

蓝图或执行交接涉及 `execution_plan_contract`、并行资格、调度分组、文件域、共享状态或验证资源时，必须同时读取 `references/execution-plan-contract.md`，并以该契约约束蓝图输出、执行交接摘录和 HILE 只读复制边界。

蓝图或执行交接涉及 `execution_unit`、逐单元允许文件、验证或停止条件时，必须同时读取 `references/execution-unit-schema.md`，并以该契约约束蓝图输出和交接摘录；若同时存在 `execution_plan_contract`，`execution_unit` 只作为 `units[]` 内的单元字段来源，不作为顶层 contract。

蓝图或执行交接涉及 `must_haves`、Truths / Artifacts / Key Links、验证梯度或完成门槛时，必须同时读取 `references/verification-contract.md`；涉及 `context_packet`、当前单元上下文裁剪、前序摘要或明确忽略项时，必须同时读取 `references/context-packet.md`。

参考文件优先级固定为：`event-action-rules.md` > `handoff-contracts.md` > `routing-matrix.md` > 当前模块参考文件。

## 用户可见阶段名称

普通用户默认只需要知道“现在处于哪个阶段、这个阶段要解决什么、需要自己做什么”。因此输出时使用以下中文阶段名作为主表达：

- `hilp-router` → 初始分流阶段
- `hilp-requirements-facts` → 需求对齐与事实求证阶段
- `hilp-design-approval` → 方案设计与审批阶段
- `hilp-blueprint` → 实施蓝图阶段
- `hilp-reapproval` → 变更重审阶段
- `hilp-execution-handoff` → 执行交接阶段
- `hilp-archive` → 规划资产归档阶段
- `hilp-skill-pressure-test` → 协议压力测试阶段

内部模块名、事件名、`owner_skill`、`last_event`、`last_decision` 等字段默认只写入资产元数据或审计说明。只有用户要求调试协议、审查协议本身、追踪资产状态，或交接契约要求精确引用时，才在用户可见回答中展示这些内部字段。

## 资产落盘规则

所有已通过入口门槛的阶段都必须产出 Markdown 资产，并保存到当前项目目录下。实施蓝图阶段和执行交接阶段若未通过确定性检查，不得生成对应正式资产；只能由回退到的前置阶段记录阻断原因：

```text
项目根目录/docs/changes/变更概述/planning/
  manifest.md
  _current/
    当前待审.md
    当前已批准.md
  review-pack/
    <阶段前缀>-<artifact>@vN-review.md
  assets/
    <阶段前缀>-<阶段中文名>_<artifact>@vN.md
```

其中“变更概述”应使用本次任务的简短中文概括，例如 `改进HILP中文交互与资产落盘`。若无法确认项目根目录，必须先向用户确认保存位置；若写入失败，必须明确告知失败，不得声称资产已保存。

所有落盘 Markdown 资产、审核包、`manifest.md`、`_current/` 入口和用户可见回答中的文件引用，必须使用 Markdown 超链接格式 [显示文本](相对或绝对路径)，确保在 Markdown 预览视图中可点击跳转。优先使用相对当前 Markdown 文件的相对路径；无法确定相对路径时使用绝对路径。不得只给裸文件路径；若元数据或机器字段必须保留原始路径，必须在相邻字段或正文中补充同一文件的可点击链接。

新产生的正式阶段资产必须写入 `assets/`，文件名推荐格式：

```text
<阶段前缀>-<阶段中文名>_<artifact>@vN.md
```

审批标记和当前状态不再写入新资产文件名；必须由资产元数据、根目录 `manifest.md`、`review-pack/` 和 `_current/` 表达。旧命名资产不迁移、不重命名；历史兼容：旧 `docs/hilp/<变更概述>/` 与旧 `docs/hilp/planning/<变更概述>/` 历史资产仍可作为历史输入读取；兼容旧资产时可从资产元数据和文件名解析状态。

阶段前缀：

- `00`：初始分流阶段
- `01`：需求对齐与事实求证阶段
- `02`：方案设计与审批阶段
- `03`：实施蓝图阶段
- `04`：变更重审阶段
- `05`：执行交接阶段
- `06`：规划资产归档阶段
- `90`：协议压力测试阶段

根目录 `manifest.md` 是当前变更目录的 live manifest，是状态权威。它可以随资产状态变化更新，最小字段为：

```text
asset_id | artifact_name | version | asset_path | created_state | current_state | current_state_label | approval_marker | approval_marker_label | role | current_review_pack | supersedes | superseded_by | last_event | last_decision
```

其中 `asset_path`、`current_review_pack`、`supersedes`、`superseded_by` 中凡表示本地文件的位置，值必须是 Markdown 链接。

待审批资产必须同时生成审核包和当前待审入口，且三者在所有可见引用处都必须写成可点击链接：

- 正式资产：[阶段前缀-阶段中文名_artifact@vN.md](assets/阶段前缀-阶段中文名_artifact@vN.md)（示例为从变更目录根部引用）
- 审核包：[阶段前缀-artifact@vN-review.md](review-pack/阶段前缀-artifact@vN-review.md)（示例为从变更目录根部引用）
- 当前入口：[当前待审.md](_current/当前待审.md)（示例为从变更目录根部引用）

审核包必须保留审核尝试记录，最小字段为：

```text
review_pack_id | target_asset_ref | target_asset_path | target_version | previous_asset_ref | review_status | opened_at | closed_at | close_result | close_decision | change_summary | reviewer_action_required
```

其中 `target_asset_path` 中的本地文件位置必须是 Markdown 链接。

审核完成后不得删除审核包；必须将其关闭并保留。批准通过时，必须同步同一版本正式资产的 front matter 状态字段、正文 `asset_ref`、正文“当前状态”、正文“当前是否需要审批”、根目录 `manifest.md`、对应 review-pack、`_current/当前待审.md` 和 `_current/当前已批准.md`；审批状态变化不递增内容版本，也不得因状态变化改写新正式资产文件名。任一同步对象写入失败时，不得声称审批状态已完成，不得进入蓝图或执行交接。审核不通过时，更新同一版本正式资产自身状态摘要和 `manifest.md` 中对应版本的 `current_state=needs-revision｜中文状态=待修订`，关闭审核包；内容修订必须生成下一版本正式资产和新的审核包。

`_current/当前待审.md` 是唯一待审入口；`_current/当前已批准.md` 是当前有效批准集合入口。归档阶段不生成根目录 `CURRENT.md`，不移动正式资产，不覆盖 `_current/`；`_current/` 是资产管理工作入口，不属于归档阶段产出的 archive manifest。

## 路由决策树

1. 如果用户是在测试、审查、验证或压力测试本协议本身，使用 `hilp-skill-pressure-test`。
2. 如果用户要求为已完成执行交接的规划链生成或重新生成规划资产归档，且没有新事实、失效、回滚、兼容窗口或必须人工裁决阻断既有路径，使用 `hilp-archive`。
3. 如果输入提到之前方案、旧判断、已批准结论、返工、重新看、推翻、新证据、运行中、已交接、已进入执行、治理变化、回滚、兼容窗口，或必须人工裁决阻断既有路径，先使用 `hilp-reapproval`。即使资产引用不完整，也按重审入口处理。
4. 如果这是没有既有资产、旧判断、当前阶段或重审语义的新规划任务，先使用 `hilp-router`。
5. 如果需求、范围、成功标准、当前行为、根因或影响面不清楚，使用 `hilp-requirements-facts`。
6. 如果目标、范围 / 非目标、成功标准、当前行为或证据基础、至少有界的影响面，以及不阻断方案比较的核心未知项都已建立，使用 `hilp-design-approval`。
7. 只有存在已批准的 Stage 3 设计资产，并且具备完整资产引用、owner_skill、人工批准授予（Human Approval Granted） 决策，且所有会影响实施蓝图的变量已经确定时，才使用 `hilp-blueprint`。若文件范围、接口、数据形状、验证口径、风险处理或执行边界仍未确定，必须先回到 `hilp-requirements-facts`、`hilp-design-approval` 或 `hilp-reapproval`。
8. 只有存在已批准的 Stage 4/5 蓝图资产或分层蓝图包、owner_skill、人工批准授予（Human Approval Granted） 决策、仍有效的上游已批准设计资产、确定性检查已通过，且没有未解决阻断项时，才使用 `hilp-execution-handoff`。执行模式、执行范围和禁止越界项未确定时，不得进入执行交接；分层蓝图包还要求主蓝图 / manifest 绑定的全部成员版本固定且已批准。
9. 执行交接成功落盘且入口检查为无阻断项后，自动尝试使用 `hilp-archive` 生成规划资产归档索引。归档失败不阻断执行交接，但必须报告失败原因。

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

从实施蓝图阶段开始，所有正式落盘资产必须是确定、唯一、可执行的，不得保留任何待定、可选、后续确认或执行时再判断的内容。该纪律同时约束实施蓝图阶段和执行交接阶段。大范围修改可使用分层蓝图包组织内容，但分层只改变阅读与审查结构，不降低确定性、覆盖性、审批绑定或交接入口要求。

以下内容一旦会影响实现路线、文件范围、接口形态、数据形状、算法骨架、错误处理、风险处理、验证口径、发布顺序、执行模式或禁止越界项，均视为未确定项：

- “待定”“可能”“视情况”“后续确认”“执行时再判断”“可选 A/B”“暂按”“大概”“原则上”等模糊表达。
- TODO、TBD、问号、空字段、占位符，或需要执行者补做规划判断的内容。
- 多个实现路径并列但未选择，或把风险处理留给执行者临场决定。

命中上述情况时，不得产出或批准 `stage-4-5/implementation-blueprint`，也不得产出 `stage-6/execution-handoff`；必须回退到能消除不确定性的前置阶段。若使用分层蓝图包，主蓝图 / manifest、全部子蓝图和覆盖矩阵必须作为一个固定版本集合通过确定性检查。执行交接阶段只能引用、摘录和封装已批准且通过确定性检查的蓝图或蓝图包，不得新增、修订或解释性扩展规划内容。

## 输出纪律

在本协议下输出任何响应时，必须：

1. 使用所选阶段参考文件中的输出模板，但用户可见标题应使用中文阶段名称。
2. 先说明当前阶段目的、已保存资产、当前结论和需要用户做什么。
3. 不默认展示内部模块名、事件推导、状态机计算过程或完整交接细节。
4. 若存在会影响用户行动的阻断项，必须用自然中文说明“缺什么、为什么不能继续、用户需要决定什么”。从实施蓝图阶段开始，阻断项不得写入正式蓝图或执行交接资产，只能触发回退说明。
5. 所有用户可见状态都必须优先给出中文状态名；涉及精确资产引用、审计或交接时，采用“内部值｜中文状态=中文名”的双写格式。
6. 只有交接契约允许时，才说明下一阶段；对普通用户写中文阶段名，对资产元数据保留内部标识。
7. 若输出会驱动下游工作，必须包含带版本、内部状态和中文状态名的资产引用，并写入项目目录下的阶段资产文件。
8. 所有需要人工审批、裁决或复核的资产，必须优先提供清爽、精炼的人类审核视图；机器字段、审计字段、状态账本、覆盖矩阵和执行单元明细应放入附录、折叠区或独立资产；完整 `execution_plan_contract` 必须抽离为 agent-only contract 资产，不得展开在实施蓝图正文或人类审核包中。
9. 所有用户可见文件引用必须是 Markdown 超链接；展示资产引用时同时给出 `asset_ref` 和对应文件链接。

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
- `references/execution-plan-contract.md`
- `references/execution-unit-schema.md`
- `references/verification-contract.md`
- `references/context-packet.md`
- `references/archive.md`
- `references/skill-pressure-test.md`
