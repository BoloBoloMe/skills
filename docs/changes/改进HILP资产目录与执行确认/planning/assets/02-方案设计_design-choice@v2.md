---
asset_id: hilp-asset-dir-exec-confirm-design-choice-v2
artifact_name: stage-3/design-choice
version: v2
state: approved
state_label: 已批准
owner_skill: hilp-design-approval
created_from: stage-1-2/requirements-and-facts@v1
last_event: human_approval_granted
last_decision: human-approval-design-choice-v2-2026-04-30
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/changes/改进HILP资产目录与执行确认/planning/assets/02-方案设计_design-choice@v2.md
asset_link: [02-方案设计_design-choice@v2.md](./02-方案设计_design-choice@v2.md)
---

# 方案设计与审批阶段

## 这个阶段要做什么
比较可行方案，按用户已选择的方案 A 重写推荐路径，并提交当前版本审批。

## 推荐方案
- 名称：共享 HILP 父目录 + planning / execution 子目录 + 执行计划轻量确认门。
- 核心思路：
  - 将新规划资产默认根目录改为 `docs/changes/<变更概述>/planning/`。
  - 将新执行资产默认根目录改为 `docs/hilp/execution/`。
  - 执行计划保存到 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - 两个文件夹共享 `docs/hilp/` 前缀；后缀分别为 `planning` 与 `execution`，直接区分计划资产和执行资产。
  - 规划 skill 继续维护 manifest、审核包、当前待审和当前已批准入口；执行 skill 只记录执行计划、HILP 绑定、禁止越界项、自检结果和确认提示。
  - 执行 skill 在写入执行计划后停止，输出“请确认是否执行该计划”；只有用户明确确认当前计划后，才进入 subagent、inline、TDD 或其他执行阶段。
- 为什么推荐：
  - 用户已选择方案 A，命名偏好明确。
  - 所有 HILP 相关资产集中在 `docs/hilp/` 下，便于查找与治理。
  - `planning` 与 `execution` 后缀满足计划资产和执行资产的区分要求。
  - 执行确认门保持轻量，不引入 planning 式状态机。

## 备选方案
### 方案 B：双根目录 `docs/hilp-planning/` 与 `docs/hilp-execution/`
- 核心思路：规划与执行分别使用两个顶层根目录。
- 优点：和当前历史 `docs/hilp/<变更概述>/` 隔离更清楚。
- 代价：HILP 资产分散在两个顶层目录；用户已明确选择共享父目录。
- 不选原因：不符合用户当前选择。

### 方案 C：保留 `docs/hilp/`，只新增 `docs/hilp-execution/`
- 核心思路：规划资产继续保存到旧 `docs/hilp/`，执行资产放入 `docs/hilp-execution/`。
- 优点：规划侧改动最小。
- 代价：规划文件夹名称不体现 planning，命名不对称。
- 不选原因：不充分满足“一个体现计划，一个体现执行”的要求。

## 关键取舍
- 正确性 / 安全性：执行计划写入后必须停止，不得在同一轮自动修改代码、派发 agent 或运行执行任务；确认必须绑定当前计划文件。
- 可回退性：不迁移旧资产，只更新新默认路径；旧 `docs/hilp/<变更概述>/` 历史资产仍可读取。
- 改动范围：需要更新 planning skill 中新资产默认路径和链接规则，更新 execution skill 中执行计划路径和计划后确认门。
- 可维护性：所有 HILP 资产集中在 `docs/hilp/` 下，按 `planning` 与 `execution` 分域管理。
- 未来扩展性：执行侧未来的审查记录、调试记录或完成报告可继续放在 `docs/hilp/execution/` 下按类型分目录。

## 需要用户决定什么
- 是否存在：无；用户已选择方案 A。
- 是否会阻止继续：无阻断项；但当前 v2 仍需明确审批后才能进入实施蓝图。
- 问题描述：请确认是否批准当前 v2 设计资产作为后续蓝图依据。
- 可选项：
  1. 批准 `stage-3/design-choice@v2`。
  2. 要求修订并说明新的命名或确认门要求。
- 建议：批准当前 v2。
- 默认路径：无；当前需等待明确批准。
- 用户是否已选择：已选择方案 A。
- 不得写成既定事实的内容：用户未明确批准当前 v2 前，不能进入实施蓝图或把 v2 当作已批准设计。

## 当前状态
- 中文状态名：已批准。
- 内部状态值：`approved`。
- 进入该状态的理由：用户明确批准 `stage-3/design-choice@v2`，批准决策记录为 `human-approval-design-choice-v2-2026-04-30`。

## 下一步
- 下一阶段：实施蓝图阶段。
- 继续前提：基于 `stage-3/design-choice@v2 [state=approved｜中文状态=已批准]` 生成确定、唯一、可审批的实施蓝图。
- 当前阻断项：无阻断项。
