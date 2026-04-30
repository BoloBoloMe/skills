---
asset_id: hilp-topic-layered-asset-dir-execution-handoff-v1
artifact_name: stage-6/execution-handoff
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-execution-handoff
created_from: stage-4-5/implementation-blueprint@v1
last_event: execution_handoff_created
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/调整HILP资产目录为主题分层/planning/assets/05-执行交接_execution-handoff@v1.md
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
- 已批准需求边界：`stage-1-2/requirements-and-facts@v2 [state=archived｜中文状态=已归档]`；文件链接：[01-需求对齐与事实求证_requirements-and-facts@v2.md](./01-需求对齐与事实求证_requirements-and-facts@v2.md)
- 已批准设计：`stage-3/design-choice@v3 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v3.md](./02-方案设计_design-choice@v3.md)
- 已批准蓝图资产：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`；文件链接：[03-实施蓝图_implementation-blueprint@v1.md](./03-实施蓝图_implementation-blueprint@v1.md)
- 蓝图形式：单体蓝图。
- 分层蓝图包 manifest：无。
- 当前蓝图版本：v1。

## 执行范围
- 范围类型：整包。
- 改动切片：
  1. `planning-asset-root`：更新 `human-in-loop-planning` 的新 planning 资产默认目录为 `docs/changes/<变更概述>/planning/`。
  2. `execution-asset-root`：更新 `human-in-loop-execution` 的执行计划和执行资产目录为 `docs/changes/<变更概述>/execution/`。
  3. `review-result-root`：更新代码审查、协议审查、执行审查等审查结果文档目录为 `docs/changes/<变更概述>/review/`。
  4. `repository-readme`：更新仓库目录树、资料目录和维护约定。
- 依赖顺序：
  1. `planning-asset-root`
  2. `execution-asset-root`
  3. `review-result-root`
  4. `repository-readme`
- 禁止越界项：
  - 不得把 planning 的 `review-pack/` 移入 `review/`；`review-pack/` 仍属于 planning 资产。
  - 不得重命名技能目录、内部模块名、asset_ref 或 HILP 概念名称。
  - 不迁移、不删除旧 `docs/hilp/...`、`docs/changes/<变更概述>/review/...`、`docs/changes/<变更概述>/execution/plans/...` 历史资产。
  - 执行计划确认门保持不变：计划写入后仍必须等待用户确认。
  - 不修改蓝图文件范围之外的技能文档或业务代码。

## 必须遵守的实现约束
- 接口约束：
  - `human-in-loop-planning` 对外说明的新 planning 资产保存位置为 `docs/changes/<变更概述>/planning/`。
  - `human-in-loop-execution` 对外说明的新执行计划保存位置为 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - `code-review.md` 必须要求审查结果文档保存到 `docs/changes/<变更概述>/review/`，并输出可点击链接。
  - README 必须把共同父目录说明为 `docs/changes/`，而不是 `docs/hilp/` 或 `docs/changes/<变更概述>/review/`。
- 数据形状：
  - planning 资产根目录代码块：`项目根目录/docs/changes/变更概述/planning/`。
  - planning 元数据模板：`asset_path: <project-root>/docs/changes/<change-summary>/planning/assets/<file-name>.md`。
  - execution 计划保存路径：`docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - review 结果保存路径：`docs/changes/<变更概述>/review/<审查内容概括-yyyy-mm-dd HH-MM-SS>.md`。
  - planning 内部目录仍为 `manifest.md`、`_current/`、`review-pack/`、`assets/`。
- 错误处理：
  - 若实施时发现需修改文件范围外的技能文档，停止并回到 HILP 变更重审。
  - 若某处旧路径是历史兼容说明，保留并标注“历史兼容”；若是默认保存路径，必须替换为 `docs/changes/`。
  - 若发现必须改变 HILP 审批包生命周期才能实现路径要求，停止并回到 HILP 变更重审。
- 测试承诺：
  - 运行蓝图列出的四条 `rg` 验证命令。
  - 人工检查 planning 目标文件中 `review-pack/` 仍位于 planning 资产结构内。
  - 人工检查 execution 目标文件中执行计划确认门仍存在。
  - 人工检查 `code-review.md` 中审查结果路径为 `docs/changes/<变更概述>/review/`。

## 风险与验证
- 风险检查点：
  1. `review-pack/` 与 `review/` 语义不得混淆。
  2. 旧历史资产不得迁移、重命名或删除。
  3. 默认保存路径不得继续指向旧 `docs/hilp/planning/`、`docs/changes/<变更概述>/execution/plans/` 或 `docs/changes/<变更概述>/review/`。
  4. 执行确认门不得被绕过。
- 发布 / 验证检查点：
  1. 修改限定在 Markdown 文档。
  2. 新规则只约束新产生资产；历史资产保留原路径。
  3. 验证命令和人工检查全部通过后，才能声明执行完成。

## 执行模式
- 单代理。
- 选择原因：用户已明确选择单代理；本次修改集中于少量 Markdown 文档，且跨文件一致性要求高，单代理顺序执行可避免并行编辑冲突。

## 执行入口检查
- 确定性检查：已通过。
- 当前阻断项：无阻断项。
- 开始前必须确认：
  - 使用 `human-in-loop-execution` 接收本交接。
  - 先生成执行计划到 `docs/changes/<变更概述>/execution/plans/<yyyy-mm-dd>-<任务概括>.md`。
  - 执行计划写入后停止，等待用户明确确认当前计划。
  - 用户未确认当前计划前，不得修改目标文件、派发 agent、运行实现步骤或声明开始执行。
- 停止并回退条件：
  - 任一上游资产状态不再是已批准。
  - 执行计划需要新增蓝图外文件、接口或验证承诺。
  - 发现旧路径匹配项超出蓝图文件范围。
  - 发现必须改变 HILP 审批包生命周期。
  - 验证失败显示蓝图约束不充分。

## 规划资产归档
- 自动归档结果：已完成。
- 文件链接：[06-规划资产归档_archive-manifest@v1.md](./06-规划资产归档_archive-manifest@v1.md)
- asset_ref：`stage-7/archive-manifest@v1 [state=archived｜中文状态=已归档]`
- 当前是否需要审批：无需审批。
- 作用：标明本次变更的最终阅读入口、最终有效资产、历史过程资产和后续重审入口；不改变任何已批准资产状态。
