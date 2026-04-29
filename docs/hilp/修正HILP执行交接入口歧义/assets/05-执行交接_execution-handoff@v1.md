---
asset_id: fix-hilp-execution-handoff-intake-ambiguity-execution-handoff
artifact_name: stage-6/execution-handoff
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-execution-handoff
created_from: stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]
last_event: none
last_decision: none
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/hilp/修正HILP执行交接入口歧义/assets/05-执行交接_execution-handoff@v1.md
asset_link: [05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md)
---

# 执行交接阶段

## 这个阶段要做什么

把已批准且通过确定性检查的 v2 蓝图封装成单代理执行者可以遵守的边界、顺序、约束和验证承诺。

## 已保存资产

- 文件链接：[05-执行交接_execution-handoff@v1.md](./05-执行交接_execution-handoff@v1.md)
- asset_ref：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（内部状态值：`archived`）
- 当前是否需要审批：无需审批；该交接绑定已批准设计和已批准蓝图。

## 上游资产

- 已批准需求边界：本轮边界来自压力测试审查和后续重审，目标为修正 HILP 执行交接入口歧义并纳入本变更目录表格渲染校验。
- 已批准设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`；文件链接：[02-方案设计_design-choice@v1.md](./02-方案设计_design-choice@v1.md)
- 已批准蓝图资产：`stage-4-5/implementation-blueprint@v2 [state=approved｜中文状态=已批准]`；文件链接：[03-实施蓝图_implementation-blueprint@v2.md](./03-实施蓝图_implementation-blueprint@v2.md)
- 蓝图形式：单体蓝图。
- 分层蓝图包 manifest：无。
- 当前蓝图版本：v2。

## 执行范围

- 范围类型：整包。
- 改动切片：
  1. `hilp-asset-table-rendering`：验证并保留本变更目录 review-pack 表格列数修复。
  2. `skill-entry-description`：修正 `human-in-loop-execution/SKILL.md` 的 frontmatter description、入口前提和 HILP 绑定纪律。
  3. `handoff-intake-contract`：修正 `human-in-loop-execution/references/hilp-handoff-intake.md` 的输入契约、执行规则、禁止事项和检查清单。
- 依赖顺序：先确认 HILP 资产表格列数，再修改 `SKILL.md`，再修改 `hilp-handoff-intake.md`，最后运行全部验证命令。
- 禁止越界项：
  - 不修改 `human-in-loop-planning/**` 源文件。
  - 不修改 `human-in-loop-execution/references/execution-routing.md`。
  - 不修改 `human-in-loop-execution/references/writing-plans.md`。
  - 不修改除本交接列明的 2 个 execution skill 文件之外的 skill 源文件。
  - 不修改其他 `docs/hilp/**` 历史变更目录。
  - 不修改 `docs/review/**`。
  - 不改变已批准设计和蓝图的语义。

## 必须遵守的实现约束

- 接口约束：不新增 skill 文件，不新增 frontmatter 字段，不改变 execution skill 的阶段体系。
- 数据形状：两个目标 execution 文件保持现有 Markdown 结构；当前变更目录 Markdown 表格必须满足表头、分隔行、数据行列数一致。
- 错误处理：目标字符串不存在、需要扩大源文件范围、需要修改 `execution-routing.md`、或验证失败无法在蓝图范围内修复时，停止并回到 HILP 变更重审阶段。
- 测试承诺：执行 v2 蓝图列出的五条验证命令，并报告退出码和关键输出摘要。

## 风险与验证

- 风险检查点：
  - 不把执行交接资产自身改成必须批准的资产。
  - 不放宽设计资产和蓝图资产必须 `approved｜中文状态=已批准` 的门槛。
  - 不放宽执行范围、禁止越界项、停止并回退条件。
  - 表格修复只治理当前变更目录，不触碰其他历史变更目录。
- 发布 / 验证检查点：
  - `handoff has been approved` 在 `human-in-loop-execution/SKILL.md` 中不再出现。
  - “执行交接资产自身不要求”在两个目标 execution 文件中均出现。
  - `owner_skill=hilp-execution-handoff` 在两个目标 execution 文件中均出现。
  - `git diff -- human-in-loop-planning` 无输出。
  - 当前变更目录 Markdown 表格列数校验输出 `markdown table columns ok`。

## 执行模式

- 单代理。
- 选择原因：本轮执行范围只有 2 个 execution skill Markdown 文件和当前变更目录资产表格校验，依赖顺序线性，单代理最可控。

## 执行入口检查

- 确定性检查：已通过。
- 当前阻断项：无阻断项。
- 开始前必须确认：执行者已读取本交接资产、已批准设计 v1、已批准蓝图 v2 和 v2 验证命令。
- 停止并回退条件：
  - 需要修改蓝图未列文件。
  - 需要改变 planning 侧源文件规则。
  - 需要修改 `execution-routing.md` 或其他 execution reference 文件。
  - 目标字符串不存在且无法按蓝图做最小替换。
  - 验证失败且修复会扩大范围。
  - 新事实推翻已批准设计或蓝图。

## 规划资产归档

- 自动归档结果：已完成。
- 文件链接：[06-规划资产归档_archive-manifest@v1.md](./06-规划资产归档_archive-manifest@v1.md)
- asset_ref：`stage-7/archive-manifest@v1 [state=archived｜中文状态=已归档]`
- 当前是否需要审批：无需审批。
- 作用：标明本次变更的最终阅读入口、最终有效资产、历史过程资产和后续重审入口；不改变任何已批准资产状态。
