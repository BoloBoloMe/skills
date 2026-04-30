---
asset_id: hilp-topic-layered-asset-dir-implementation-blueprint-v1
artifact_name: stage-4-5/implementation-blueprint
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v3
last_event: human_approval_granted
last_decision: human-approval-implementation-blueprint-v1-2026-04-30
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/changes/调整HILP资产目录为主题分层/planning/assets/03-实施蓝图_implementation-blueprint@v1.md
asset_link: [03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
---

# 实施蓝图阶段

## 这个阶段要做什么
把已批准的 `docs/changes/` 方案转成可执行的改动切片、顺序、约束和验证检查点。

## 已保存资产
- 文件链接：[03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
- asset_ref：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`
- 蓝图形式：单体蓝图。
- 上游设计：`stage-3/design-choice@v3 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v3.md](./02-方案设计_design-choice@v3.md)
- 当前状态：已批准（`approved`）。
- 当前是否需要审批：已审批通过。
- 审核包链接：[03-implementation-blueprint@v1-review.md](../review-pack/03-implementation-blueprint@v1-review.md)
- 当前待审入口：[当前待审.md](../_current/当前待审.md)

## 改动拓扑
- 改动切片：
  1. `planning-asset-root`：更新 `human-in-loop-planning` 的新 planning 资产默认目录为 `docs/changes/<变更概述>/planning/`。
  2. `execution-asset-root`：更新 `human-in-loop-execution` 的执行计划和执行资产目录为 `docs/changes/<变更概述>/execution/`。
  3. `review-result-root`：更新代码审查、协议审查、执行审查等审查结果文档目录为 `docs/changes/<变更概述>/review/`。
  4. `repository-readme`：更新仓库目录树、资料目录和维护约定。
- 依赖顺序：
  1. 先实施 `planning-asset-root`，确保 planning 内部资产结构和元数据模板一致。
  2. 再实施 `execution-asset-root`，确保执行计划路径使用同一变更主题目录。
  3. 再实施 `review-result-root`，确保审查结果文档不再落到全局 `docs/changes/<变更概述>/review/`。
  4. 最后实施 `repository-readme`，同步仓库级说明。
- 风险检查点：
  1. 不得把 planning 的 `review-pack/` 移入 `review/`；`review-pack/` 仍属于 planning 资产。
  2. 不得重命名技能目录、内部模块名、asset_ref 或 HILP 概念名称。
  3. 不迁移、不删除旧 `docs/hilp/...`、`docs/changes/<变更概述>/review/...`、`docs/changes/<变更概述>/execution/plans/...` 历史资产。
  4. 执行计划确认门保持不变：计划写入后仍必须等待用户确认。
- 发布检查点：
  1. 所有修改限定在 Markdown 文档。
  2. 新规则只约束新产生资产；历史资产保留原路径。
- 验证检查点：
  1. `rg -n "docs/changes/<变更概述>/planning|docs/changes/<变更概述>/execution|docs/changes/<变更概述>/review" human-in-loop-planning human-in-loop-execution README.md -g "*.md"` 命中三类新路径。
  2. `rg -n "docs/human-in-loop-execution/plans|human-in-loop-execution/plans" human-in-loop-planning human-in-loop-execution README.md -g "*.md"` 无输出。
  3. `rg -n "docs/changes/<变更概述>/review/|docs/hilp/planning|docs/hilp/execution/plans" human-in-loop-planning human-in-loop-execution README.md -g "*.md"` 只允许在明确标注历史兼容的语句中命中；若命中默认保存路径则失败。
  4. `rg -n "review-pack.*review/|review/.*review-pack" human-in-loop-planning human-in-loop-execution README.md -g "*.md"` 不得出现要求把 `review-pack/` 放入 `review/` 的规则。
- 涉及模块 / 子系统 / 文件范围：
  - [human-in-loop-planning/SKILL.md](../../../../../human-in-loop-planning/SKILL.md)
  - [human-in-loop-planning/references/handoff-contracts.md](../../../../../human-in-loop-planning/references/handoff-contracts.md)
  - [human-in-loop-planning/references/event-action-rules.md](../../../../../human-in-loop-planning/references/event-action-rules.md)
  - [human-in-loop-execution/SKILL.md](../../../../../human-in-loop-execution/SKILL.md)
  - [human-in-loop-execution/references/writing-plans.md](../../../../../human-in-loop-execution/references/writing-plans.md)
  - [human-in-loop-execution/references/code-review.md](../../../../../human-in-loop-execution/references/code-review.md)
  - [README.md](../../../../../README.md)

## 分层蓝图包 manifest
- 使用条件：无；本次文件数量少且依赖线性，使用单体蓝图。
- 包内资产清单：无。
- 切片索引：无。
- 跨切片依赖图 / 波次：无。
- 覆盖矩阵：无。
- 审批边界：单体蓝图 `stage-4-5/implementation-blueprint@v1`。

## 实现约束
- 数据形状：
  - planning 资产根目录代码块统一为：`项目根目录/docs/changes/变更概述/planning/`。
  - planning 元数据模板统一为：`asset_path: <project-root>/docs/changes/<change-summary>/planning/assets/<file-name>.md`。
  - execution 计划保存路径统一为：`docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - review 结果保存路径统一为：`docs/changes/<变更概述>/review/<审查内容概括-yyyy-mm-dd HH-MM-SS>.md`。
  - planning 内部目录仍为 `manifest.md`、`_current/`、`review-pack/`、`assets/`。
- 接口约束：
  - `human-in-loop-planning` 对外说明的新 planning 资产保存位置为 `docs/changes/<变更概述>/planning/`。
  - `human-in-loop-execution` 对外说明的新执行计划保存位置为 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - `code-review.md` 必须要求审查结果文档保存到 `docs/changes/<变更概述>/review/`，并输出可点击链接。
  - README 必须把共同父目录说明为 `docs/changes/`，而不是 `docs/hilp/` 或 `docs/changes/<变更概述>/review/`。
- 局部算法骨架：
  1. 在 planning 三个目标文件中替换默认目录与 `asset_path` 模板，并补充历史兼容说明：旧 `docs/hilp/<变更概述>/`、`docs/changes/<变更概述>/planning/` 可兼容读取。
  2. 在 execution 两个目标文件中替换执行计划保存路径，不修改执行确认门。
  3. 在 `code-review.md` 增加审查结果保存路径、文件名时间戳格式和输出链接要求。
  4. 在 README 中把目录树改为 `docs/changes/<变更概述>/planning|execution|review`，同步技能说明、资料目录和维护约定。
- 错误处理要求：
  - 若实施时发现需修改文件范围外的技能文档，停止并回到 HILP 变更重审。
  - 若某处旧路径是历史兼容说明，保留并标注“历史兼容”；若是默认保存路径，必须替换为 `docs/changes/`。
  - 若发现必须改变 HILP 审批包生命周期才能实现路径要求，停止并回到 HILP 变更重审。
- 测试承诺：
  - 运行四条验证检查点中的 `rg` 命令。
  - 人工检查 planning 目标文件中 `review-pack/` 仍位于 planning 资产结构内。
  - 人工检查 execution 目标文件中执行计划确认门仍存在。
  - 人工检查 `code-review.md` 中审查结果路径为 `docs/changes/<变更概述>/review/`。

## 确定性检查
- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：无。

## 当前判断
- 当前是否可交接到执行层：否；蓝图已批准，但执行模式尚未由用户确定。
- 当前阻断项：无阻断项。
- 是否存在兼容 / 回滚约束：存在兼容约束；旧资产目录和旧审查报告目录不迁移、不删除，只作为历史兼容读取来源。
- 当前状态：已批准（`approved`）。

## 下一步需要用户做什么
请明确执行模式：人类开发者、单代理、多代理或暂不执行。执行模式确定后，才能进入执行交接阶段。
