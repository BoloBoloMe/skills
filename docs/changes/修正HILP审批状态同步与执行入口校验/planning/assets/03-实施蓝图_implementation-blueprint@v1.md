---
asset_id: hilp-state-sync-intake-blueprint-v1
artifact_name: stage-4-5/implementation-blueprint
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v1
last_event: human_approval_granted
last_decision: human-approval-implementation-blueprint-v1-2026-04-30
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/changes/修正HILP审批状态同步与执行入口校验/planning/assets/03-实施蓝图_implementation-blueprint@v1.md
asset_link: [03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
---

# 实施蓝图阶段

## 这个阶段要做什么

把已批准的方案 A+D 转成可执行的文档改动切片、顺序、约束和验证检查点。

## 已保存资产

- 文件链接：[03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
- asset_ref：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`
- 蓝图形式：单体蓝图。
- 上游设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
- 当前状态：已批准（内部状态值：`approved`）
- 当前是否需要审批：已批准；可进入执行交接阶段。
- 审核包：[03-implementation-blueprint@v1-review.md](../review-pack/03-implementation-blueprint@v1-review.md)（已关闭）
- 当前已批准入口：[当前已批准.md](../_current/当前已批准.md)

## 改动拓扑

### 改动切片

1. planning 审批状态同步源头修复。
   - 文件：`human-in-loop-planning/SKILL.md`
   - 文件：`human-in-loop-planning/references/event-action-rules.md`
   - 文件：`human-in-loop-planning/references/handoff-contracts.md`
   - 目标：批准通过时，规则必须明确同步目标资产自身 front matter、正文状态摘要、manifest、review-pack、`_current/当前待审.md`、`_current/当前已批准.md`。
2. execution 入口校验与恢复提示修复。
   - 文件：`human-in-loop-execution/references/hilp-handoff-intake.md`
   - 目标：执行入口必须读取实际设计 / 蓝图资产文件，核对 front matter、正文 `asset_ref`、执行交接引用和 manifest 状态；不一致时阻断并输出固定恢复建议。
3. 语义收敛与自检。
   - 文件范围：上述四个文件。
   - 目标：消除“只信 manifest”“不改变正式资产正文”造成的歧义，保留 manifest 作为索引权威而非唯一状态来源。

### 依赖顺序

1. 先修改 planning 源头规则，确保审批状态变化的写入对象完整。
2. 再修改 handoff 契约，确保跨阶段读取规则不再只依赖 manifest。
3. 再修改 execution 接收规则，固化入口阻断和恢复提示。
4. 最后运行检索验证，确认关键规则文本存在且旧歧义被收敛。

### 风险检查点

- 风险 1：把状态同步写成内容修订，导致误增版本。控制：明确“审批状态变化不递增内容版本，但必须同步同一版本资产的状态元数据与状态摘要”。
- 风险 2：把 manifest 权威完全否定，破坏索引用途。控制：明确“manifest 是索引权威，但绑定性下游必须核对实际资产文件状态”。
- 风险 3：execution skill 误修改规划资产。控制：execution 入口只阻断并提示回到 HILP，不在执行 skill 中修正规划资产。

### 发布检查点

1. 完成四个目标文件修改。
2. 运行文本检索验证。
3. 提供变更摘要和验证结果。
4. 等待用户决定是否进入执行交接或直接执行文档修改。

### 验证检查点

- `rg -n "front matter|正文.*asset_ref|当前状态|当前是否需要审批|manifest|review-pack|当前待审|当前已批准" human-in-loop-planning/SKILL.md human-in-loop-planning/references/event-action-rules.md human-in-loop-planning/references/handoff-contracts.md`
- `rg -n "读取实际|front matter|正文.*asset_ref|manifest|状态不一致|审批状态一致性修复" human-in-loop-execution/references/hilp-handoff-intake.md`
- `rg -n "不改变正式资产正文|asset_ref.*优先从根目录.*manifest" human-in-loop-planning/references/event-action-rules.md human-in-loop-planning/references/handoff-contracts.md`

### 涉及模块 / 子系统 / 文件范围

- `human-in-loop-planning/SKILL.md`
- `human-in-loop-planning/references/event-action-rules.md`
- `human-in-loop-planning/references/handoff-contracts.md`
- `human-in-loop-execution/references/hilp-handoff-intake.md`

## 分层蓝图包 manifest

单体蓝图，无分层蓝图包。

## 实现约束

### 数据形状

- 不新增状态值。
- 不新增审批标记值。
- 不新增规划资产目录。
- 不新增脚本文件。
- 仅修改 Markdown 规则文本。

### 接口约束

- `Human Approval Granted` 规则必须保留原有事件名。
- `manifest.md` 仍是 live manifest 和索引权威。
- 下游绑定推进必须同时要求资产文件自身状态一致。
- execution 接收规则不得获得规划资产写权限；只能阻断并给出回退建议。

### 局部算法骨架

1. 在 planning 审批规则中增加“批准通过原子同步对象清单”。
2. 在审核生命周期规则中补充目标资产 front matter 与正文状态摘要同步。
3. 在跨阶段引用规则中把“优先从 manifest 读取”改为“先读取 manifest 定位，再核对资产文件自身状态”。
4. 在 execution intake 规则中增加实际文件校验步骤和固定失败恢复提示。
5. 用检索命令确认关键规则均已落入目标文件。

### 错误处理要求

- 任一同步对象写入失败时，planning 不得声称审批状态已完成。
- manifest 与资产文件状态不一致时，planning 不得进入蓝图或执行交接。
- execution 入口发现状态不一致时，不得进入实现，不得自行修正规划资产。

### 测试承诺

- 使用 `rg` 检查新增规则关键词是否存在。
- 使用 `rg` 检查旧歧义表述是否已被删除或改写。
- 人工核对四个目标文件没有引入新状态值、脚本要求或超出方案 A+D 的范围。

## 确定性检查

- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：无，当前为单体蓝图。

## 当前判断

- 当前是否可交接到执行层：是。当前蓝图已批准，上游设计仍为已批准，确定性检查通过。
- 当前阻断项：无阻断项。
- 是否存在兼容 / 回滚约束：无代码兼容约束；文档修改可通过版本控制回退。
- 当前状态：已批准（内部状态值：`approved`）。

## 下一步需要用户做什么

当前蓝图版本已获用户明确批准，可进入执行交接阶段：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`。
