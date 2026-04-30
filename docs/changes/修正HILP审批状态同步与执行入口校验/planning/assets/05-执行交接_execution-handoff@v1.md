---
asset_id: hilp-state-sync-intake-execution-handoff-v1
artifact_name: stage-6/execution-handoff
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-execution-handoff
created_from: stage-4-5/implementation-blueprint@v1
last_event: execution_handoff_created
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/修正HILP审批状态同步与执行入口校验/planning/assets/05-执行交接_execution-handoff@v1.md
asset_link: [05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md)
---

# 执行交接阶段

## 这个阶段要做什么

把已批准且通过确定性检查的蓝图封装成执行者可以遵守的边界、顺序、约束和验证承诺。

## 已保存资产

- 文件链接：[05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md)
- asset_ref：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（内部状态值：`archived`）。
- 当前是否需要审批：无需审批；执行交接绑定已批准蓝图，不重新审批。

## 上游资产

- 已批准需求边界：用户需求“按照方案 A+D 修正 HILP 审批状态同步与执行入口校验”。
- 已批准设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)。
- 已批准蓝图资产：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`；文件链接：[03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)。
- 蓝图形式：单体蓝图。
- 分层蓝图包 manifest：无。
- 当前蓝图版本：v1。

## 执行范围

- 范围类型：整包。
- 改动切片：
  1. planning 审批状态同步源头修复。
     - `human-in-loop-planning/SKILL.md`
     - `human-in-loop-planning/references/event-action-rules.md`
     - `human-in-loop-planning/references/handoff-contracts.md`
  2. execution 入口校验与恢复提示修复。
     - `human-in-loop-execution/references/hilp-handoff-intake.md`
  3. 语义收敛与自检。
     - 仅覆盖上述四个文件。
- 依赖顺序：
  1. 修改 `human-in-loop-planning/SKILL.md` 的审核完成规则。
  2. 修改 `human-in-loop-planning/references/event-action-rules.md` 的 Human Approval Granted 和审核生命周期规则。
  3. 修改 `human-in-loop-planning/references/handoff-contracts.md` 的审核生命周期和跨阶段资产引用规则。
  4. 修改 `human-in-loop-execution/references/hilp-handoff-intake.md` 的执行入口检查规则与固定恢复提示。
  5. 运行检索验证并报告结果。
- 禁止越界项：
  - 不新增脚本。
  - 不新增状态值或审批标记值。
  - 不新增完整方案 B 的统一状态一致性门文件。
  - 不正式引入方案 C 的新恢复事件模型。
  - 不迁移、不批量修复历史规划资产。
  - 不修改 `archive.md`、`blueprint.md`、`execution-handoff.md` 的完整入口门模型。
  - 不修改业务代码。

## 必须遵守的实现约束

- 接口约束：
  - `Human Approval Granted` 事件名保持不变。
  - `manifest.md` 仍是 live manifest 和索引权威。
  - 绑定性下游不得只信 manifest；必须核对实际资产文件自身状态。
  - execution 接收规则不得获得规划资产写权限；只阻断并提示回到 HILP。
- 数据形状：
  - 不新增状态值。
  - 不新增审批标记值。
  - 不新增目录结构。
  - 只修改 Markdown 规则文本。
- 错误处理：
  - planning 规则必须说明：任一同步对象写入失败时，不得声称审批状态已完成。
  - planning 规则必须说明：manifest 与资产文件状态不一致时，不得进入蓝图或执行交接。
  - execution 规则必须说明：状态不一致时，不得进入实现，不得自行修正规划资产。
- 测试承诺：
  - 使用 `rg` 检查新增规则关键词存在。
  - 使用 `rg` 检查旧歧义表述已被删除或改写。
  - 人工核对四个目标文件没有引入蓝图禁止项。

## 风险与验证

- 风险检查点：
  1. 不得把审批状态变化写成内容修订或要求递增版本。
  2. 不得否定 manifest 的索引权威，只补充实际资产文件交叉校验。
  3. 不得让 execution skill 直接修正规划资产。
  4. 不得把本轮 A+D 扩大成方案 B/C。
- 发布 / 验证检查点：
  1. 四个目标文件完成修改。
  2. 以下检索能看到新增规则：
     - `front matter`
     - `正文 asset_ref`
     - `当前状态`
     - `当前是否需要审批`
     - `审批状态一致性修复`
  3. 以下旧歧义不再以原含义存在：
     - `_current/当前已批准.md 只列当前仍有效的已批准资产集合，不改变正式资产正文`
     - `asset_ref 中的状态优先从根目录 manifest 读取`

## 执行模式

- 单代理。
- 选择原因：本次为四个 Markdown 规则文件的顺序编辑，跨文件一致性要求高，单代理执行可减少并行冲突。

## 执行入口检查

- 确定性检查：已通过。
- 当前阻断项：无阻断项。
- 开始前必须确认：
  - 使用 `human-in-loop-execution` 接收本交接。
  - 先生成执行计划到 `docs/changes/修正HILP审批状态同步与执行入口校验/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - 执行计划写入后停止，等待用户明确确认当前计划。
  - 用户未确认当前计划前，不得修改目标文件、派发 agent、运行实现步骤或声明开始执行。
- 停止并回退条件：
  - 任一上游资产状态不再是已批准。
  - 执行计划需要新增蓝图外文件、脚本、状态值或恢复事件模型。
  - 发现必须修改四个目标文件之外的 skill 文档。
  - 发现旧歧义需要通过方案 B/C 才能消除。
  - 验证失败显示蓝图约束不充分。

## 规划资产归档

- 自动归档结果：未完成。
- 失败原因：本次只完成执行交接资产落盘；尚未生成归档索引。
- 影响：执行交接资产本身不受影响；已批准设计和蓝图状态不变；本次失败只影响阅读索引生成，不阻断执行交接。
- 建议：如需闭环阅读索引，可重新触发规划资产归档。
