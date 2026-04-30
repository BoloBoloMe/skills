---
asset_id: hilp-execution-capability-restoration-execution-handoff
artifact_name: stage-6/execution-handoff
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-execution-handoff
created_from: stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]
last_event: none
last_decision: human-approval-2026-04-29-approve-blueprint-package-v1
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/补回human-in-loop-execution能力/planning/assets/05-执行交接_no-approval_execution-handoff@v1.md
---

# 执行交接阶段

## 这个阶段要做什么

把已批准且通过确定性检查的蓝图封装成执行者可以遵守的边界、顺序、约束和验证承诺。

## 已保存资产

- 文件路径：`D:/Workspace/skills/docs/changes/补回human-in-loop-execution能力/planning/assets/05-执行交接_no-approval_execution-handoff@v1.md`
- asset_ref：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（内部状态值：`archived`）。
- 当前是否需要审批：无需审批；该交接绑定已批准蓝图包。

## 上游资产

- 已批准需求边界：本轮未单独生成 Stage 1/2 资产；事实基础来自 `docs/changes/构建中文裁剪版Superpowers技能/review/对比human-in-loop-execution与superpowers能力-2026-04-29 00-23-18.md` 和 `stage-3/design-choice@v1`。
- 已批准设计：`stage-3/design-choice@v1 [state=approved｜中文状态=已批准]`
- 已批准蓝图资产：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`
- 蓝图形式：分层蓝图包。
- 分层蓝图包 manifest：
  - `stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`，role: manifest。
  - `stage-4-5/blueprint-slice-entry-routing@v1 [state=approved｜中文状态=已批准]`，role: slice。
  - `stage-4-5/blueprint-slice-hard-disciplines@v1 [state=approved｜中文状态=已批准]`，role: slice。
  - `stage-4-5/blueprint-slice-planning-orchestration@v1 [state=approved｜中文状态=已批准]`，role: slice。
  - `stage-4-5/blueprint-slice-review-finishing@v1 [state=approved｜中文状态=已批准]`，role: slice。
  - `stage-4-5/blueprint-slice-meta-skill@v1 [state=approved｜中文状态=已批准]`，role: slice。
  - `stage-4-5/coverage-matrix@v1 [state=approved｜中文状态=已批准]`，role: coverage-matrix。
- 当前蓝图版本：v1。

## 执行范围

- 范围类型：整包。
- 改动切片：
  1. `entry-routing`：补强入口、路由、接收和 inline fallback 的执行边界。
  2. `hard-disciplines`：补强 TDD、完成前验证、系统化调试和测试 / 调试支持技术。
  3. `planning-orchestration`：补强执行计划、subagent 编排、并行 agent 和相关 prompt。
  4. `review-finishing`：补强代码审查、反馈处理、最终审查 prompt 和分支收尾。
  5. `meta-skill`：补强技能编写元纪律。
- 依赖顺序：先执行 `entry-routing`，再执行 `hard-disciplines`，再执行 `planning-orchestration`，再执行 `review-finishing`，最后执行 `meta-skill`，全部切片完成后执行覆盖矩阵验证。
- 禁止越界项：
  - 不修改 `superpowers/**`。
  - 不新增 `brainstorming`、`using-git-worktrees`、`using-superpowers` 独立入口。
  - 不复制 Superpowers 插件、hooks、commands、assets、历史 plans/specs、测试工程或上游贡献规则。
  - 不修改 HILP 规划协议文件，除本变更目录内规划资产外。
  - 不把需求、设计、审批或蓝图职责写入执行技能。
  - 不新增蓝图未列出的目标文件。

## 必须遵守的实现约束

- 接口约束：`human-in-loop-execution/SKILL.md` 的 frontmatter `name` 保持 `human-in-loop-execution`；`description` 只描述触发条件；不新增独立技能目录。
- 数据形状：所有 reference 和 prompt template 文件保持固定六段结构：适用时机、输入契约、执行规则、禁止事项、输出契约、检查清单。
- 错误处理：若补回内容需要新增执行技能入口、修改 `superpowers/`、补做需求 / 设计 / 接口 / 数据形状裁决，或验证命令失败，停止执行并回到 HILP 变更重审或实施蓝图阶段。
- 测试承诺：运行结构检查、禁止路径检查、入口边界检查和高风险能力关键词检查。

## 风险与验证

- 风险检查点：
  - 每个切片完成后检查目标文件仍保留固定结构。
  - 每个切片完成后检查新增内容包含 HILP asset_ref、禁止越界项、停止并回退条件。
  - 每个切片完成后检查未新增 Superpowers 被裁剪入口、插件、hooks、commands、assets、tests。
  - 全部切片完成后检查 `superpowers/` 无工作区改动。
- 发布 / 验证检查点：
  - 文本结构验证覆盖全部 reference 和 prompt template。
  - 关键词验证覆盖 TDD、调试、验证、subagent、审查、收尾、写技能。
  - prompt 验证覆盖实现、规格审查、质量审查、计划审查和最终代码审查 prompt。
  - 禁止路径验证覆盖 `superpowers/`。

## 执行模式

- 单代理。
- 选择原因：当前执行范围是确定的 Markdown 技能文档补强，文件边界清晰；当前环境未提供可实际派发 subagent 的 Task 工具，单代理按切片顺序执行最可控。

## 执行入口检查

- 确定性检查：已通过。
- 当前阻断项：无阻断项。
- 开始前必须确认：当前工作区为用户指定的执行工作区；执行者已读取本交接资产、已批准设计、已批准蓝图包和覆盖矩阵。
- 停止并回退条件：出现蓝图外文件需求、Superpowers 禁止路径变更、规划职责扩张、验证失败无法按蓝图修复、新事实推翻批准设计或蓝图、执行范围或执行模式需要改变。

## 规划资产归档

- 自动归档结果：已完成。
- 文件路径：`D:/Workspace/skills/docs/changes/补回human-in-loop-execution能力/planning/assets/06-规划资产归档_no-approval_archive-manifest@v1.md`
- asset_ref：`stage-7/archive-manifest@v1 [state=archived｜中文状态=已归档]`
- 当前是否需要审批：无需审批。
- 作用：标明本次变更的最终阅读入口、最终有效资产、历史过程资产和后续重审入口；不改变任何已批准资产状态。
