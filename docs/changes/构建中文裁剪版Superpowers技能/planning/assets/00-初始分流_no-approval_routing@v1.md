---
asset_id: hilp-superpowers-skills-routing
artifact_name: stage-0/routing
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-router
created_from: original-task
last_event: none
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/构建中文裁剪版Superpowers技能/planning/assets/00-初始分流_no-approval_routing@v1.md
---

# 初始分流阶段

## 这个阶段要做什么
判断“根据 HILP 裁剪并中文化 Superpowers 技能包”应先补事实、先做方案选择，还是需要回看旧结论。

## 任务摘要
在仓库根目录新增 `superpowers-skills/`，基于 `裁剪superpowers.md` 的边界要求和 `superpowers/` 源仓内容，规划一个中文、裁剪后的 Superpowers 技能包；先按 HILP 阶段门控形成设计与蓝图，不直接越过审批进入实现。

## 分流判断
- 任务类型：行为变化型为主，即新增一个可供 agent 使用的技能包；行为保持型为次，即保留 Superpowers 执行纪律、TDD、review、worktree 等有效行为。
- 风险与治理强度：standard。该任务涉及多技能文档、触发语义、HILP 与 Superpowers 边界，不是单文件轻量改动；但不涉及运行时迁移、线上兼容窗口或高回滚成本。
- 建议采用的规格方式：行为规格为主，契约规格为辅。行为规格定义 HILP 接管设计审批后 Superpowers 只做执行层；契约规格定义各技能的触发条件、输入资产和禁止越界项。
- 建议采用的验证方式：文档结构检查、触发条件检查、HILP 边界覆盖检查、人工审阅清单。

## 需要用户知道的决策点
- 当前是否存在：无必须人工裁决；存在建议人工裁决，即是否采用“完整执行层技能包”而不是“最小保留包”。
- 是否会阻止继续：无阻断项。
- 原因：`裁剪superpowers.md` 已给出核心边界；仓库现状和 Superpowers 技能列表可被事实求证支撑后进入方案设计。

## 当前判断
- 是否需要先补证据：需要，必须读取 `裁剪superpowers.md` 与 `superpowers/` 的技能、文档和包结构后再设计。
- 是否需要先做现状刻画：需要。
- 是否存在旧结论失效或重审风险：无既有 HILP 资产或旧批准结论，按新规划任务进入。

## 下一步
- 下一阶段：需求对齐与事实求证阶段。
- 为什么进入这个阶段：需要把用户目标、裁剪边界、Superpowers 源仓事实和当前仓库落点分离记录，避免直接把原仓复制或把 HILP 已接管的审批环节重复引入。

## 暂时不能跳过的内容
不能跳过事实求证、方案设计与人工批准；不能直接创建 `superpowers-skills/` 正式内容。