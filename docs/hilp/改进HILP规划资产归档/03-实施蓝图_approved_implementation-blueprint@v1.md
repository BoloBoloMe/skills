---
asset_id: hilp-archive-implementation-blueprint
artifact_name: stage-4-5/implementation-blueprint
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v1 [state=approved｜中文状态=已批准]
last_event: Human Approval Granted
last_decision: human-approval-2026-04-28-hilp-archive-blueprint-v1
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/hilp/改进HILP规划资产归档/03-实施蓝图_approved_implementation-blueprint@v1.md
---

# 实施蓝图阶段

## 批准记录
- 批准对象：`stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]`
- 批准结果：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`
- 批准决策：`human-approval-2026-04-28-hilp-archive-blueprint-v1`
- 用户批准语句：批准 stage-4-5/implementation-blueprint@v1

## 已批准蓝图摘要
- 蓝图形式：单体蓝图。
- 上游设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`
- 实施范围：
  - `human-in-loop-planning/SKILL.md`
  - `human-in-loop-planning/references/event-action-rules.md`
  - `human-in-loop-planning/references/handoff-contracts.md`
  - `human-in-loop-planning/references/routing-matrix.md`
  - `human-in-loop-planning/references/execution-handoff.md`
  - `human-in-loop-planning/references/skill-pressure-test.md`
  - `human-in-loop-planning/references/archive.md`

## 改动切片
1. 主入口规则切片：更新总入口模块列表、资源加载、阶段名称、阶段前缀、路由决策树、参考文件和输出纪律。
2. 事件规则切片：新增执行交接完成后自动归档事件和失败不阻断交接规则。
3. 交接契约切片：新增 `hilp-archive` 关系、输入输出契约和禁止事项。
4. 路由矩阵切片：新增归档阶段名称和默认映射。
5. 执行交接切片：成功后追加自动归档摘要，失败时详细说明。
6. 归档模块切片：新增 `references/archive.md`。
7. 压力测试切片：补充归档相关测试场景。

## 实现约束
- 不移动文件。
- 不生成 `CURRENT.md`。
- 不修改上游资产状态。
- 保持 `approved` 资产为 `approved`。
- 归档只治理当前变更目录。
- 外部引用只记录为 `external-reference`。
- 归档 manifest 自身使用 `stage-7/archive-manifest@vN [state=archived｜中文状态=已归档]`。
- 文件名使用 `06-规划资产归档_no-approval_archive-manifest@vN.md`。
- 手动重新触发归档不要求刚完成执行交接，但必须基于有效执行交接资产。
- 归档失败不阻断执行交接。

## 确定性检查
- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：无。
- 检查结果：已通过。

## 当前状态
- 中文状态名：已批准。
- 内部状态值：`approved`。
- 当前阻断项：无阻断项。

## 下一步
- 下一阶段：执行交接阶段。
- 继续前提：执行交接只能摘录本蓝图，不能新增或修订规划内容。
