---
asset_id: hilp-asset-dir-exec-confirm-routing-v1
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
asset_path: D:/Workspace/skills/docs/changes/改进HILP资产目录与执行确认/planning/assets/00-初始分流_routing@v1.md
asset_link: [00-初始分流_routing@v1.md](./00-初始分流_routing@v1.md)
---

# 初始分流阶段

## 这个阶段要做什么
判断本次改进应先补事实、先做方案选择，还是需要回看旧结论。

## 任务摘要
改进仓库内人在回路规划与执行两个 skill：统一重命名规划资产与执行资产的输出文件夹，并要求执行层写完执行计划后先等待用户确认再真正执行。

## 分流判断
- 任务类型：行为变化型，兼有轻度结构治理调整；主要改变两个 skill 对资产落盘路径和执行启动门槛的用户可见行为。
- 风险与治理强度：standard。改动跨两个核心 skill，且会影响后续所有规划/执行资产位置与执行启动纪律，需要保留设计取舍和验证口径；未发现兼容窗口、数据迁移或高回滚成本信号。
- 建议采用的规格方式：行为规格 + 契约规格。资产路径是输出契约，执行确认是行为契约。
- 建议采用的验证方式：回归检查 + 文档契约扫描 + 一次模拟串联检查。

## 需要用户知道的决策点
- 当前是否存在：建议人工裁决。
- 是否会阻止继续：无阻断项。
- 原因：文件夹命名存在多种合理方案；可以先给出推荐方案并提交审批，用户通过或要求修订即可。

## 当前判断
- 是否需要先补证据：需要最小事实求证，确认现有路径和相关文档位置。
- 是否需要先做现状刻画：需要。
- 是否存在旧结论失效或重审风险：无；本次按新任务进入。

## 下一步
- 下一阶段：需求对齐与事实求证阶段。
- 为什么进入这个阶段：需要先固化现有资产路径、执行计划路径和影响面，再形成可审批设计。

## 暂时不能跳过的内容
不能跳过设计审批；命名方案和执行确认门槛需要用户看过并明确批准后，才能进入实施蓝图。
