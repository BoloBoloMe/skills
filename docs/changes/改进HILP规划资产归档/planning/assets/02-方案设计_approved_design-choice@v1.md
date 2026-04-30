---
asset_id: hilp-archive-design-choice
artifact_name: stage-3/design-choice
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-design-approval
created_from: stage-1-2/requirements-and-facts@v1 [state=archived｜中文状态=已归档]
last_event: Human Approval Granted
last_decision: human-approval-2026-04-28-hilp-archive-design-v1
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/changes/改进HILP规划资产归档/planning/assets/02-方案设计_approved_design-choice@v1.md
---

# 方案设计与审批阶段

## 这个阶段要做什么
比较可行方案，给出推荐路径，并明确哪些内容需要用户决定或批准。

## 批准记录
- 批准对象：`stage-3/design-choice@v1 [state=ready-for-approval｜中文状态=待审批]`
- 批准结果：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`
- 批准决策：`human-approval-2026-04-28-hilp-archive-design-v1`
- 用户批准语句：批准推荐方案，然后进入实施蓝图阶段。

## 已批准方案
- 名称：新增只读规划资产归档阶段。
- 核心思路：在执行交接成功后自动触发 `hilp-archive`，只生成版本化 `stage-7/archive-manifest@vN`，用阅读角色整理当前变更目录内资产；归档不修改任何上游资产、不移动文件、不生成 `CURRENT.md`、不新增规划判断。
- 批准理由：该方案直接解决阅读混乱，同时最小化对现有审批状态机、蓝图确定性纪律和执行交接门槛的影响。它把“文档怎么读”与“资产是否批准”分离，避免把最终批准资产错误改成 `archived`。

## 被拒绝方案
### 方案 A：只在执行交接中增加一个归档小节，不新增模块
- 不选原因：不能稳定解决多版本目录的长期阅读治理问题。

### 方案 B：新增归档阶段并移动旧文件到 archive 子目录
- 不选原因：用户已明确不希望移动文件；该方案也会改变既有资产路径。

### 方案 C：把所有非当前资产状态改为 `archived`
- 不选原因：用户已明确要求保持 approved；该方案会混淆资产审批状态与阅读活跃性。

## 批准边界
- 执行交接成功后自动归档。
- 归档失败不阻断执行交接。
- 归档只解决阅读混乱。
- 只治理当前变更目录。
- 外部引用只记录不治理。
- 不生成 `CURRENT.md`。
- 不移动文件。
- 不修改上游资产状态。
- 保持 `approved` 资产为 `approved`。
- 归档 manifest 自身无需审批，生成即已归档。
- 阅读角色以最终执行交接引用链为准。
- `needs-revision` 优先标为 `needs-revision-history`。
- 多候选最终链不唯一时归档失败。
- 旧 manifest 在新 manifest 中标为 `superseded`。
- 允许手动重新触发归档。
- 手动归档不要求刚完成执行交接。
- 成功时简短展示，失败时详细说明。

## 当前状态
- 中文状态名：已批准。
- 内部状态值：`approved`。
- 进入该状态的理由：用户明确批准当前具体设计资产版本。

## 下一步
- 下一阶段：实施蓝图阶段。
- 继续前提：实施蓝图必须完整覆盖批准边界，并通过确定性检查。
- 当前阻断项：无阻断项。
