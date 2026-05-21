# 逐问澄清纪律

逐问澄清是 HITL 的强制流程纪律，但不是资产。仓库探索只能减少无效问题，不能替代盘问门禁。

## 规则

1. 每次最多只问一个问题。
2. design 前必须无情盘问计划的每个方面，直到双方对目标、范围、约束、方案分支、验证、风险、批准边界和执行分级达成共识。
3. 盘问必须沿设计树逐层推进：先锁定上游决策，再进入依赖它的下游分支；每个分支须逐一关闭，不能跳过仍影响后续决策的未知项。
4. 每个问题必须附带推荐答案和备选答案，以选项形式呈现，推荐程度越高排序越靠前；各项须说明优缺点、推荐理由，以及它会解锁或阻塞的下游决策。
5. 如果答案可以通过仓库、配置、测试、文档或已有资产探索得到，必须先探索再问，或记录为 `evidence-closed`；不得把可验证事实转嫁给用户，也不得把探索结果当作整棵设计树已关闭。
6. 只要存在影响范围、批准、验证、风险、设计分支或执行分级的阻断未知项，就不得写正式资产或请求固定命令。
7. 用户要求“别问了，直接继续”不能绕过阻断未知项。
8. 关闭 gate 必须逐项记录 `resolution_items`，每项包含 `question`、`resolution_type: human-confirmed|evidence-closed`、`resolution`、`evidence`；其中问题、结论和解释必须使用用户提出 HITL 请求时所用的主要语言。
9. `pre_execution_plan` 的 `resolution_items` 还必须包含 `resolution_id`、`unit_id`、`step_id`、`dependency_path`；`resolution_id` 固定格式为 `PEP-EU-001-S01-R001`，并作为 Plan / Runbook 中 `source_level_change_intent[].interrogation_refs` 的稳定引用。
10. 关闭 gate 必须记录固定命令 `关闭盘问: <gate> <asset_ref>`；仅填写 `status/evidence/closed_at` 不是有效关闭。
11. 不保存逐字 transcript。
12. 不生成 interrogation summary。
13. 不在 manifest 中记录 loop 完成事件；只维护 `interrogation_gates` 的状态、阻断未知项、逐项关闭依据、固定关闭命令和关闭时间。

## design 前设计树盘问顺序

1. 目标与验收：确认业务目标、成功标准、非目标和不可接受结果。
2. 事实与约束：优先探索仓库、配置、测试、文档和已有资产；只向用户询问探索后仍未知且阻断的内容。
3. 影响边界：确认允许文件、禁止文件、外部系统、数据/安全/兼容边界。
4. 方案分支：列出可行分支及依赖关系，一次只关闭一个分支决策。
5. 风险与回退：确认失败模式、停止条件、回退路径和重新批准触发条件。
6. 验证策略：确认自动验证、人工检查、证据格式和通过/失败判定。
7. 批准与执行分级：确认 tier、批准命令粒度、Plan/Runbook 要求和执行确认边界。

## pre_execution_plan 源码级盘问

生成 Plan / Runbook 前，必须以 `planning/blueprint@vN` 为上游输入，按以下顺序盘问用户直至关闭源码级变更意图，绝不允许尝试任何跳过此步骤的企图或者尝试，更不允许诱导用户跳过逐级盘问或者一次性询问所有问题：

1. 先按 `implementation_units[].dependencies` 的拓扑顺序遍历执行单元；每个 `unit_id` 固定格式为 `EU-001`。
2. 单元内按 `implementation_step_outline[]` 顺序遍历步骤；每个 `step_id` 固定格式为 `<unit_id>-S01`。
3. 若步骤声明 `depends_on`，只能收紧顺序：依赖步骤必须先被盘问关闭，不得引用同单元较晚步骤、非依赖单元步骤或自身。
4. 每个步骤至少形成一条 `resolution_items`，记录源码级变更意图、可接受行为、拒绝行为、文件/符号边界和证据。
5. `dependency_path` 表示当前问题发生时已满足的直接前置单元集合加当前单元，必须以当前 `unit_id` 结尾，并按拓扑顺序排列。
6. 如果盘问中发现需要新增、删除、重排 unit 或 step，或改变步骤语义，必须将 gate 标记为 blocked 并进入 reassessment；不得直接在 Plan / Runbook 中扩展步骤树。

## 适用位置

- 写 `planning/facts@vN` 前。
- 写 `planning/design@vN` 前，必须关闭并校验 `pre_design` gate。
- 写 `planning/blueprint@vN` 前，必须关闭并校验 `pre_blueprint` gate。
- 写 `planning/implementation-package@vN` 前的轻量核对。
- 最终 asset-check 通过后，生成 Plan / Runbook 前，必须关闭并校验 `pre_execution_plan` gate。
- standard Plan 或 strict Runbook 固定确认前。
- reassessment 中失败归因、影响范围或恢复路径不清时。

## 交接原则

如果交接发生在 loop 中途，接收 agent 不得假装知道未落盘问答。接收 agent 应读取 manifest、稳定资产和仓库证据，重新继续必要的逐问澄清。
