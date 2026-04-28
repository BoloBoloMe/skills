---
asset_id: hilp-archive-routing
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
asset_path: D:/Workspace/skills/docs/hilp/改进HILP规划资产归档/00-初始分流_no-approval_routing@v1.md
---

# 初始分流阶段

## 这个阶段要做什么
判断“为 HILP 增加规划资产归档阶段”应先补事实、先做方案选择，还是需要回看旧结论。

## 任务摘要
为 `human-in-loop-planning` skill 增加执行交接后的自动规划资产归档环节，生成版本化 `archive-manifest@vN`，解决同一变更目录内多版本文档阅读混乱问题。

## 分流判断
- 任务类型：行为变化型。该变更会改变 HILP 工作流在执行交接后的用户可见输出和资产生成行为。
- 风险与治理强度：standard。该变更涉及主入口说明、交接契约、事件动作规则、新参考模块和输出纪律，属于跨规则文件的一致性修改，但不涉及兼容窗口、数据迁移或运行时回滚。
- 建议采用的规格方式：行为规格，叠加契约规格。
- 建议采用的验证方式：静态规则校验、协议压力测试样例、人工核对输出模板。

## 需要用户知道的决策点
- 当前是否存在：无。
- 是否会阻止继续：无阻断项。
- 原因：讨论阶段已明确归档的触发时机、范围、命名、失败处理、阅读角色和审批边界；剩余工作是形成可审批设计。

## 当前判断
- 是否需要先补证据：不需要。现有 HILP 规则文件和本次讨论结论足以支撑方案设计。
- 是否需要先做现状刻画：需要，已交给需求对齐与事实求证阶段记录现状与边界。
- 是否存在旧结论失效或重审风险：无。当前没有已批准的本变更设计资产被推翻。

## 下一步
- 下一阶段：需求对齐与事实求证阶段。
- 为什么进入这个阶段：需要先固化目标、范围、非目标、成功标准和现有规则事实，再进入方案审批。

## 暂时不能跳过的内容
- 不能直接进入实施蓝图阶段；必须先形成并获得明确批准的方案设计资产。
