---
asset_id: hilp-asset-management-execution-handoff
artifact_name: stage-6/execution-handoff
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-execution-handoff
created_from: stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]
last_event: none
last_decision: human-approval-2026-04-29-hilp-asset-management-blueprint-v1
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/hilp/优化HILP资产管理/05-执行交接_no-approval_execution-handoff@v1.md
---

# 执行交接阶段

## 这个阶段要做什么

把已批准且通过确定性检查的蓝图封装成执行者可以遵守的边界、顺序、约束和验证承诺。

## 已保存资产

- 文件路径：`D:/Workspace/skills/docs/hilp/优化HILP资产管理/05-执行交接_no-approval_execution-handoff@v1.md`
- asset_ref：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（内部状态值：`archived`）
- 当前是否需要审批：无需审批；该交接绑定已批准蓝图。

## 上游资产

- 已批准需求边界：由 `stage-3/design-choice@v1` 中的需求边界与事实基础承载。
- 已批准设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`
- 已批准蓝图资产：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`
- 蓝图形式：单体蓝图。
- 分层蓝图包 manifest：无。
- 当前蓝图版本：v1。

## 执行范围

- 范围类型：整包。
- 改动切片：
  1. 修改资产根结构规则：`SKILL.md`、`references/handoff-contracts.md`。
  2. 修改稳定资产命名与状态权威规则：`SKILL.md`、`references/event-action-rules.md`、`references/handoff-contracts.md`。
  3. 修改审核包生命周期规则：`SKILL.md`、`references/event-action-rules.md`、`references/handoff-contracts.md`、`references/design-approval.md`、`references/blueprint.md`。
  4. 修改当前入口规则：`SKILL.md`、`references/handoff-contracts.md`、`references/archive.md`。
  5. 修改八个模块输出模板路径：`references/router.md`、`requirements-facts.md`、`design-approval.md`、`blueprint.md`、`reapproval.md`、`execution-handoff.md`、`archive.md`、`skill-pressure-test.md`。
  6. 修改归档与 live manifest 分工：`references/archive.md`、`references/event-action-rules.md`、`references/handoff-contracts.md`。
  7. 修改 lean 合并资产示例：`references/routing-matrix.md`。
- 依赖顺序：先总规则，再交接契约，再事件规则，再模块模板，再归档模块，最后路由矩阵示例。
- 禁止越界项：
  - 不迁移、不重命名、不移动 `docs/hilp/` 下既有历史规划资产。
  - 不修改 `human-in-loop-execution` skill。
  - 不改变审批语义：`ready-for-approval｜待审批` 仍不等于 `approved｜已批准`。
  - 不把归档阶段改造成业务推进阶段。
  - 不生成根目录 `CURRENT.md`。

## 必须遵守的实现约束

- 接口约束：
  - 新正式阶段资产路径统一为 `docs/hilp/<变更概述>/assets/<阶段前缀>-<阶段中文名>_<artifact>@vN.md`。
  - 待审批输出必须同时给出正式资产路径、审核包路径和 `_current/当前待审.md` 路径。
  - 跨阶段绑定引用继续使用 `asset_ref: <stage>/<artifact>@vN [state=<state>｜中文状态=<state_label>]`。
- 数据形状：
  - 变更目录包含 `manifest.md`、`_current/`、`review-pack/`、`assets/`。
  - live manifest 最小字段按蓝图定义实现。
  - review-pack 最小字段按蓝图定义实现。
- 错误处理：
  - 写入正式资产失败时不得声称已保存。
  - 写入 live manifest 失败时不得声称状态索引已更新。
  - 写入 review-pack 失败时不得声称已提交审核。
  - 写入 `_current/当前待审.md` 失败时必须报告审核入口更新失败。
- 测试承诺：执行蓝图中的三组 `rg` 检查，并人工核对核心文件。

## 风险与验证

- 风险检查点：
  - 新资产命名不能继续强制携带审批状态。
  - 旧资产兼容规则不能被删除。
  - live manifest 不能与归档 manifest 混淆。
  - `_current` 不能违反归档阶段“不生成 CURRENT.md”的边界。
- 发布 / 验证检查点：
  - 修改规则文件。
  - 运行蓝图指定 `rg` 检查。
  - 检查所有模块模板的待审批输出是否包含审核包与当前入口。
  - 检查归档模块仍不移动文件、不改上游资产状态。

## 执行模式

- 单代理。
- 选择原因：变更对象全部是 Markdown 规则文件，文件范围和验证命令已确定，单代理执行可保持上下文一致。

## 执行入口检查

- 确定性检查：已通过。
- 当前阻断项：无阻断项。
- 开始前必须确认：执行者只能按已批准蓝图修改列出的 HILP 规划 skill 规则文件。
- 停止并回退条件：
  - 发现必须修改蓝图未列出的文件。
  - 发现新资产结构与现有阶段门控发生不可调和冲突。
  - 发现需要新增未批准的状态或审批语义。
  - 发现执行中需要迁移历史资产。

## 规划资产归档

- 自动归档结果：已完成。
- 文件路径：`D:/Workspace/skills/docs/hilp/优化HILP资产管理/06-规划资产归档_no-approval_archive-manifest@v1.md`
- asset_ref：`stage-7/archive-manifest@v1 [state=archived｜中文状态=已归档]`
- 当前是否需要审批：无需审批。
- 作用：标明本次变更的最终阅读入口、最终有效资产、历史过程资产和后续重审入口；不改变任何已批准资产状态。
