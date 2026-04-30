---
asset_id: hilp-asset-dir-exec-confirm-design-choice-v1
artifact_name: stage-3/design-choice
version: v1
state: needs-revision
state_label: 待修订
owner_skill: hilp-design-approval
created_from: stage-1-2/requirements-and-facts@v1
last_event: human_decision_recommended
last_decision: none
approval_marker: needs-revision
approval_marker_label: 待修订
asset_path: D:/Workspace/skills/docs/changes/改进HILP资产目录与执行确认/planning/assets/02-方案设计_design-choice@v1.md
asset_link: [02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
---

# 方案设计与审批阶段

## 这个阶段要做什么
比较可行方案，给出推荐路径，并明确哪些内容需要用户决定或批准。

## 推荐方案
- 名称：双根目录命名 + 执行计划轻量确认门。
- 核心思路：
  - 将新规划资产默认根目录改为 `docs/hilp-planning/<变更概述>/`。
  - 将新执行资产默认根目录改为 `docs/hilp-execution/`，执行计划保存到 `docs/hilp-execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - 两个根目录共享 `hilp-` 前缀；后缀分别为 `planning` 与 `execution`，直观区分规划资产和执行资产。
  - 规划 skill 继续维护 manifest、审核包、当前待审和当前已批准入口；执行 skill 只在计划文件中记录 HILP 绑定、禁止越界项、自检结果和“等待用户确认执行”的提示。
  - 执行 skill 在写入计划后停止，输出“请确认是否执行该计划”；只有用户明确确认当前计划后，才进入 subagent、inline、TDD 或后续执行阶段。
- 为什么推荐：
  - 符合用户要求的“共性 + 异性”：同为 `hilp-` 前缀，分别体现 planning 与 execution。
  - 改动面比共享父目录迁移更小，避免与既有 `docs/hilp/` 历史资产混淆。
  - 执行确认门足够轻量，不引入规划审批状态机，也不会让计划写完后自动执行。
  - 保持旧资产可读，新资产使用新默认路径，降低历史兼容风险。

## 备选方案
### 方案 A：共享父目录 `docs/hilp/planning/` 与 `docs/hilp/execution/`
- 核心思路：把规划与执行资产放到同一个 `docs/hilp/` 父目录下，用子目录区分 planning 和 execution。
- 优点：层级集中，HILP 资产都在同一父目录下。
- 代价：与当前 `docs/hilp/<变更概述>/` 历史布局冲突感较强；需要更多兼容说明，用户查找时容易混淆旧目录和新目录。
- 不选原因：本次需求强调两个 skill 的文件夹名称有共性也有异性；双根目录更直接，且不扰动旧 `docs/hilp/` 历史目录。

### 方案 B：保留 `docs/hilp/`，只新增 `docs/hilp-execution/`
- 核心思路：规划资产继续保存在 `docs/hilp/`，执行资产改到 `docs/hilp-execution/`。
- 优点：规划侧改动最小。
- 代价：规划与执行文件夹缺少对称后缀；`docs/hilp/` 不体现 planning，不能充分满足“一个体现计划，一个体现执行”。
- 不选原因：没有完整满足用户对命名共性和异性的期望。

## 关键取舍
- 正确性 / 安全性：执行计划写入后必须停止，不能在同一轮自动继续修改代码或派发 agent；确认必须绑定当前计划文件。
- 可回退性：不迁移旧资产，只更新新默认路径；发现问题可回退文档规则而不触碰历史资产。
- 改动范围：需要扫描并更新两个 skill 中所有新资产路径、执行计划路径和计划后执行规则；不改历史资产。
- 可维护性：`hilp-planning` / `hilp-execution` 命名语义稳定，比 `human-in-loop-*` 更短且与 HILP 资产引用一致。
- 未来扩展性：未来若执行侧产生审查报告、调试记录或完成报告，可继续放在 `docs/hilp-execution/` 下按类型分目录，不影响规划资产结构。

## 需要用户决定什么
- 是否存在：建议人工裁决。
- 是否会阻止继续：无阻断项；推荐路径可提交审批，但用户未批准前不得进入实施蓝图。
- 问题描述：是否接受新默认文件夹命名为 `docs/hilp-planning/` 与 `docs/hilp-execution/`，以及执行计划写完后的轻量确认门。
- 可选项：
  1. 批准推荐方案：使用 `docs/hilp-planning/` 与 `docs/hilp-execution/`。
  2. 改用共享父目录：`docs/hilp/planning/` 与 `docs/hilp/execution/`。
  3. 指定其他共同前缀和后缀。
- 建议：批准推荐方案。
- 默认路径：若用户只要求继续规划而未指定命名，后续蓝图按推荐方案展开；这不等于用户已批准。
- 用户是否已选择：未选择。
- 不得写成既定事实的内容：用户未明确批准前，不能声称最终命名已经确定，也不能进入实施蓝图。

## 当前状态
- 中文状态名：待修订。
- 内部状态值：`needs-revision`。
- 进入该状态的理由：用户选择方案 A，v1 推荐方案不再作为当前待审批版本；当前待审版本为 `stage-3/design-choice@v2 [state=ready-for-approval｜中文状态=待审批]`。

## 下一步
- 下一阶段：等待用户批准；批准后进入实施蓝图阶段。
- 继续前提：用户明确批准 `stage-3/design-choice@v1 [state=ready-for-approval｜中文状态=待审批]`，或要求修订并说明新命名偏好。
- 当前阻断项：无阻断项；但审批未完成，不能继续到实施蓝图。
