---
asset_id: hilp-asset-dir-exec-confirm-execution-handoff-v1
artifact_name: stage-6/execution-handoff
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-execution-handoff
created_from: stage-4-5/implementation-blueprint@v1
last_event: none
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/改进HILP资产目录与执行确认/planning/assets/05-执行交接_execution-handoff@v1.md
asset_link: [05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md)
---

# 执行交接阶段

## 这个阶段要做什么
把已批准且通过确定性检查的蓝图封装成执行者可以遵守的边界、顺序、约束和验证承诺。

## 已保存资产
- 文件链接：[05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md)
- asset_ref：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（`archived`）。
- 当前是否需要审批：无需审批；执行交接绑定已批准蓝图，不重新审批。

## 上游资产
- 已批准需求边界：[01-需求对齐与事实求证_requirements-and-facts@v1.md](./01-需求对齐与事实求证_requirements-and-facts@v1.md)
- 已批准设计：`stage-3/design-choice@v2 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v2.md](./02-方案设计_design-choice@v2.md)
- 已批准蓝图资产：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`；文件链接：[03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
- 蓝图形式：单体蓝图。
- 分层蓝图包 manifest：无。
- 当前蓝图版本：v1。

## 执行范围
- 范围类型：整包。
- 改动切片：
  1. `planning-asset-root`：更新 `human-in-loop-planning` 的新规划资产默认根目录。
  2. `execution-plan-root`：更新 `human-in-loop-execution` 的执行计划保存根目录。
  3. `execution-confirmation-gate`：加入执行计划写入后的轻量用户确认门。
  4. `repository-readme`：更新仓库级目录说明和维护约定。
- 依赖顺序：
  1. `planning-asset-root`
  2. `execution-plan-root`
  3. `execution-confirmation-gate`
  4. `repository-readme`
- 禁止越界项：
  - 不迁移、重命名或删除旧 `docs/hilp/<变更概述>/` 历史资产。
  - 不迁移、重命名或删除旧 `docs/changes/<变更概述>/execution/plans/` 历史计划。
  - 不改变 HILP 设计、蓝图、执行交接的审批语义。
  - 不引入 planning 式执行计划审批状态机。
  - 不修改本蓝图文件范围之外的技能文档或业务代码。

## 必须遵守的实现约束
- 接口约束：
  - `human-in-loop-planning` 新资产保存位置改为 `docs/changes/<变更概述>/planning/`。
  - `human-in-loop-execution` 新执行计划保存位置改为 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - `execution-routing.md` 必须表达三段式顺序：没有计划先写执行计划；计划已写入但用户未确认时停在执行计划确认阶段；用户明确确认当前计划后才进入 subagent 或 inline 执行阶段。
  - `executing-plans.md` 与 `subagent-driven-development.md` 的输入契约必须要求用户已明确确认当前执行计划路径。
- 数据形状：
  - 规划资产根目录文本：`项目根目录/docs/hilp/planning/变更概述/`。
  - 规划资产元数据模板：`asset_path: <project-root>/docs/hilp/planning/<change-summary>/assets/<file-name>.md`。
  - 执行计划路径文本：`docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - 执行计划文件头新增：`执行确认状态: waiting-for-user-confirmation`。
- 错误处理：
  - 目标文件中出现本交接未列出的旧路径匹配项时停止，并回到 HILP 变更重审。
  - 执行确认门需要改变 HILP 规划审批语义时停止，并回到 HILP 变更重审。
  - 验证命令发现旧执行计划路径仍存在于目标文件时，修正文档后重新运行验证命令。
- 测试承诺：
  - `rg -n "项目根目录/docs/hilp/变更概述|docs/human-in-loop-execution/plans|human-in-loop-execution/plans" human-in-loop-planning human-in-loop-execution README.md -g "*.md"` 输出为空。
  - `rg -n "docs/hilp/planning|docs/hilp/execution/plans|用户明确确认当前计划|等待用户确认" human-in-loop-planning human-in-loop-execution README.md -g "*.md"` 输出包含规划路径、执行计划路径和确认门规则。
  - `rg -n "没有计划先写执行计划；已有计划按 subagent 或 inline 执行" human-in-loop-execution -g "*.md"` 输出为空。
  - 人工检查执行计划阶段不会自动进入实现、派发 agent 或修改代码。

## 风险与验证
- 风险检查点：
  1. 规划侧所有新资产保存路径文本只指向 `docs/changes/<变更概述>/planning/`。
  2. 执行侧所有执行计划路径文本只指向 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  3. 执行路由进入 subagent 或 inline 前必须要求“用户已明确确认当前计划”。
  4. 文档不得要求迁移旧历史资产。
- 发布 / 验证检查点：
  1. 修改限定在 Markdown 文档。
  2. 运行三条 `rg` 验证命令。
  3. 人工检查规划路径、执行路径和执行确认门一致。

## 执行模式
- 单代理。
- 选择原因：当前仓库修改为同一组 Markdown 文档的顺序改动；先由执行层生成执行计划，计划经用户确认后由单代理按计划顺序执行，避免并行 agent 同时编辑相邻规则文本。

## 执行入口检查
- 确定性检查：已通过。
- 当前阻断项：无阻断项。
- 开始前必须确认：
  - 使用 `human-in-loop-execution` 接收本交接。
  - 先生成执行计划到 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - 执行计划写入后停止，等待用户明确确认当前计划。
  - 用户未确认当前计划前，不得执行文档修改、派发 agent、运行实现步骤或声明开始执行。
- 停止并回退条件：
  - 任一上游资产状态不再是已批准。
  - 执行计划需要新增蓝图外文件、接口或验证承诺。
  - 发现旧路径匹配项超出蓝图文件范围。
  - 用户要求改变命名方案或执行确认语义。
  - 验证失败显示蓝图约束不充分。

## 规划资产归档
- 自动归档结果：已完成。
- 文件链接：[06-规划资产归档_archive-manifest@v1.md](./06-规划资产归档_archive-manifest@v1.md)
- asset_ref：`stage-7/archive-manifest@v1 [state=archived｜中文状态=已归档]`
- 当前是否需要审批：无需审批。
- 作用：标明本次变更的最终阅读入口、最终有效资产、历史过程资产和后续重审入口；不改变任何已批准资产状态。
