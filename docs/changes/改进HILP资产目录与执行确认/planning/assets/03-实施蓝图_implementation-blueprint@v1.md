---
asset_id: hilp-asset-dir-exec-confirm-implementation-blueprint-v1
artifact_name: stage-4-5/implementation-blueprint
version: v1
state: approved
state_label: 已批准
owner_skill: hilp-blueprint
created_from: stage-3/design-choice@v2
last_event: human_approval_granted
last_decision: human-approval-implementation-blueprint-v1-2026-04-30
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/changes/改进HILP资产目录与执行确认/planning/assets/03-实施蓝图_implementation-blueprint@v1.md
asset_link: [03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
---

# 实施蓝图阶段

## 这个阶段要做什么
把已批准的方案 A 转成可执行的改动切片、顺序、约束和验证检查点。

## 已保存资产
- 文件链接：[03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
- asset_ref：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`
- 蓝图形式：单体蓝图。
- 上游设计：`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v2.md](./02-方案设计_design-choice@v2.md)
- 当前状态：已批准（`approved`）。
- 当前是否需要审批：已审批通过。
- 审核包链接：[03-implementation-blueprint@v1-review.md](../review-pack/03-implementation-blueprint@v1-review.md)
- 当前待审入口：[当前待审.md](../_current/当前待审.md)

## 改动拓扑
- 改动切片：
  1. `planning-asset-root`：更新 `human-in-loop-planning` 的新规划资产默认根目录。
  2. `execution-plan-root`：更新 `human-in-loop-execution` 的执行计划保存根目录。
  3. `execution-confirmation-gate`：加入执行计划写入后的轻量用户确认门。
  4. `repository-readme`：更新仓库级目录说明和维护约定。
- 依赖顺序：
  1. 先实施 `planning-asset-root`，使规划层新资产根目录统一为 `docs/changes/<变更概述>/planning/`。
  2. 再实施 `execution-plan-root`，使执行层计划根目录统一为 `docs/changes/<变更概述>/execution/plans/`。
  3. 再实施 `execution-confirmation-gate`，使执行计划写入后停止并等待用户确认。
  4. 最后实施 `repository-readme`，使仓库说明与两个 skill 的规则一致。
- 风险检查点：
  1. 规划侧所有新资产保存路径文本只指向 `docs/changes/<变更概述>/planning/`。
  2. 执行侧所有执行计划路径文本只指向 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  3. 执行路由中从“执行计划阶段”进入 subagent 或 inline 执行阶段前，必须存在“用户已明确确认当前计划”的条件。
  4. 文档不得要求迁移旧 `docs/hilp/<变更概述>/` 历史资产。
- 发布检查点：
  1. 所有修改限定在 Markdown 文档，不创建、移动或删除历史资产目录。
  2. 修改完成后保留当前规划链已有资产路径不变；新规则只约束新产生的资产。
- 验证检查点：
  1. `rg -n "项目根目录/docs/hilp/变更概述|docs/human-in-loop-execution/plans|human-in-loop-execution/plans" human-in-loop-planning human-in-loop-execution README.md -g "*.md"` 输出为空。
  2. `rg -n "docs/hilp/planning|docs/hilp/execution/plans|用户明确确认当前计划|等待用户确认" human-in-loop-planning human-in-loop-execution README.md -g "*.md"` 输出包含规划路径、执行计划路径和确认门规则。
  3. `rg -n "没有计划先写执行计划；已有计划按 subagent 或 inline 执行" human-in-loop-execution -g "*.md"` 输出为空。
- 涉及模块 / 子系统 / 文件范围：
  - [human-in-loop-planning/SKILL.md](../../../../../human-in-loop-planning/SKILL.md)
  - [human-in-loop-planning/references/handoff-contracts.md](../../../../../human-in-loop-planning/references/handoff-contracts.md)
  - [human-in-loop-planning/references/event-action-rules.md](../../../../../human-in-loop-planning/references/event-action-rules.md)
  - [human-in-loop-execution/SKILL.md](../../../../../human-in-loop-execution/SKILL.md)
  - [human-in-loop-execution/references/execution-routing.md](../../../../../human-in-loop-execution/references/execution-routing.md)
  - [human-in-loop-execution/references/writing-plans.md](../../../../../human-in-loop-execution/references/writing-plans.md)
  - [human-in-loop-execution/references/executing-plans.md](../../../../../human-in-loop-execution/references/executing-plans.md)
  - [human-in-loop-execution/references/subagent-driven-development.md](../../../../../human-in-loop-execution/references/subagent-driven-development.md)
  - [README.md](../../../../../README.md)

## 分层蓝图包 manifest
- 使用条件：无。
- 包内资产清单：无。
- 切片索引：无。
- 跨切片依赖图 / 波次：无。
- 覆盖矩阵：无。
- 审批边界：单体蓝图 `stage-4-5/implementation-blueprint@v1`。

## 实现约束
- 数据形状：
  - 规划资产根目录文本统一为 `项目根目录/docs/hilp/planning/变更概述/`。
  - 规划资产元数据模板统一为 `asset_path: <project-root>/docs/hilp/planning/<change-summary>/assets/<file-name>.md`。
  - 执行计划路径文本统一为 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - 执行计划文件头保留既有字段 `HILP design asset_ref`、`HILP blueprint asset_ref`、`HILP execution handoff asset_ref`、`禁止越界项`、`目标`、`执行约束`，并新增一行 `执行确认状态: waiting-for-user-confirmation`。
- 接口约束：
  - `human-in-loop-planning` 对外说明的新资产保存位置为 `docs/changes/<变更概述>/planning/`；旧 `docs/hilp/<变更概述>/` 只作为历史资产读取来源。
  - `human-in-loop-execution` 对外说明的新执行计划保存位置为 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - `execution-routing.md` 的路由规则必须表达三段式顺序：没有计划先写执行计划；计划已写入但用户未确认时停在执行计划确认阶段；用户明确确认当前计划后才进入 subagent 或 inline 执行阶段。
  - `executing-plans.md` 与 `subagent-driven-development.md` 的输入契约必须要求用户已明确确认当前执行计划路径。
- 局部算法骨架：
  1. 在规划侧文档中把所有新资产默认路径替换为 `docs/changes/<变更概述>/planning/`，并保留“不迁移旧资产、旧资产仍可作为历史输入读取”的规则。
  2. 在执行侧文档中把计划路径替换为 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  3. 在执行路由中插入“执行计划确认阶段”，并把进入 subagent / inline 的前置条件改为用户明确确认当前计划。
  4. 在执行计划编写规则中要求计划写入后输出计划链接、自检结果、推荐执行方式和确认提示，然后停止。
  5. 在 README 中把目录树、技能说明、资料目录和维护约定同步到 `docs/hilp/planning/` 与 `docs/hilp/execution/`。
- 错误处理要求：
  - 若实现时发现目标文件中旧路径文本多于本蓝图列出的匹配项，停止执行并回到 HILP 变更重审。
  - 若执行确认门需要改变 HILP 规划审批语义，停止执行并回到 HILP 变更重审。
  - 若验证命令发现旧执行计划路径仍存在于目标文件，修正文档后重新运行验证命令。
- 测试承诺：
  - 运行三条 `rg` 验证检查命令。
  - 人工检查 `human-in-loop-execution/SKILL.md`、`references/execution-routing.md`、`references/writing-plans.md` 中的阶段顺序，确认计划写入后不会直接进入执行。
  - 人工检查 `human-in-loop-planning/SKILL.md`、`references/handoff-contracts.md`、`references/event-action-rules.md` 中的规划资产根路径一致。

## 确定性检查
- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。
- 分层蓝图包成员检查：无。

## 当前判断
- 当前是否可交接到执行层：是；蓝图已获用户明确批准，且确定性检查通过。
- 当前阻断项：无阻断项。
- 是否存在兼容 / 回滚约束：存在兼容约束；旧 `docs/hilp/<变更概述>/` 和 `docs/changes/<变更概述>/execution/plans/` 下已有历史文件不迁移、不删除，新规则只约束新产生的资产与计划。
- 当前状态：已批准（`approved`）。

## 下一步需要用户做什么
可进入执行交接阶段；执行层仍必须先生成执行计划并等待用户确认后再真正执行。
