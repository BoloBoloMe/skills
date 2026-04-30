---
asset_id: hilp-superpowers-skills-execution-handoff
artifact_name: stage-6/execution-handoff
version: v1
state: archived
state_label: 已归档
owner_skill: hilp-execution-handoff
created_from: stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]
last_event: none
last_decision: human-approval-2026-04-28-blueprint-package-v1
approval_marker: no-approval
approval_marker_label: 无需审批
asset_path: D:/Workspace/skills/docs/changes/构建中文裁剪版Superpowers技能/planning/assets/05-执行交接_no-approval_execution-handoff@v1.md
---

# 执行交接阶段

## 这个阶段要做什么
把已批准且通过确定性检查的蓝图封装成执行者可以遵守的边界、顺序、约束和验证承诺。

## 已保存资产
- 文件路径：`D:/Workspace/skills/docs/changes/构建中文裁剪版Superpowers技能/planning/assets/05-执行交接_no-approval_execution-handoff@v1.md`
- asset_ref：`stage-6/execution-handoff@v1 [state=archived｜中文状态=已归档]`
- 当前状态：已归档（内部状态值：`archived`）。
- 当前是否需要审批：无需审批；该交接绑定已批准蓝图包。

## 上游资产
- 已批准需求边界：`stage-1-2/requirements-and-facts@v1 [state=archived｜中文状态=已归档]`
- 已批准设计：`stage-3/design-choice@v3 [state=approved｜中文状态=已批准]`
- 已批准蓝图资产：`stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`
- 蓝图形式：分层蓝图包。
- 分层蓝图包 manifest：
  - `stage-4-5/implementation-blueprint@v1 [state=approved｜中文状态=已批准]`，role: manifest。
  - `stage-4-5/blueprint-slice-package-structure@v1 [state=approved｜中文状态=已批准]`，role: slice。
  - `stage-4-5/blueprint-slice-execution-protocol@v1 [state=approved｜中文状态=已批准]`，role: slice。
  - `stage-4-5/blueprint-slice-quality-and-meta@v1 [state=approved｜中文状态=已批准]`，role: slice。
  - `stage-4-5/coverage-matrix@v1 [state=approved｜中文状态=已批准]`，role: coverage-matrix。
- 当前蓝图版本：v1。

## 执行范围
- 范围类型：整包。
- 改动切片：
  1. 创建 `human-in-loop-execution/` 包结构、`SKILL.md`、包 README，并更新仓库根 `README.md`。
  2. 创建执行主协议 reference 文件：入口检查、路由、计划拆分、subagent 执行、inline fallback、TDD、代码审查和分支收尾。
  3. 创建质量辅助与元技能 reference 文件：系统调试、完成前验证、并行 agent、技能编写，以及 prompt/reference 支撑文件。
- 依赖顺序：先创建目录和入口文档，再写主执行协议，再写质量辅助与元技能，最后更新根 README 并运行验证命令。
- 禁止越界项：
  - 不创建 `superpowers-skills/`。
  - 不修改 `superpowers/`。
  - 不修改 `human-in-loop-planning/`。
  - 不修改 `cz-sdk-windows-build/`。
  - 不创建 `using-git-worktrees`、`brainstorming` 或原始 `using-superpowers` 独立入口。
  - 不复制插件、hooks、commands、assets、历史 plans/specs、源仓测试目录和上游贡献规则。
  - 不声称仓库内 skill 会被 agents 自动发现。
  - 不新增蓝图未列出的文件。

## 必须遵守的实现约束
- 接口约束：`human-in-loop-execution/SKILL.md` 是单一顶层入口；内部 references 是执行单元，不作为独立 skill 入口。
- 数据形状：reference 文件统一包含“适用时机、输入契约、执行规则、禁止事项、输出契约、检查清单”。
- 错误处理：若发现 `human-in-loop-execution/` 已存在、根 README 无法定位插入区域、或需要新增蓝图未列文件，停止执行并回到 HILP 变更重审或实施蓝图阶段。
- 测试承诺：执行后运行蓝图列出的文件存在性、禁止路径、frontmatter 和关键字 grep 检查。

## 风险与验证
- 风险检查点：
  - 命名必须是 `human-in-loop-execution/`。
  - 不得恢复被裁剪掉的设计审批能力。
  - 所有执行链路必须绑定 HILP 执行交接资产。
  - 完成声明必须有新鲜验证证据。
- 发布 / 验证检查点：
  - 创建文件后检查目录结构。
  - 更新根 README 后检查只登记新技能包，不修改无关说明。
  - 运行蓝图 manifest 中的验证命令。

## 执行模式
- 单代理。
- 选择原因：当前执行范围是确定的 Markdown 技能包创建与 README 修改，文件边界清晰；当前环境未提供可实际派发 subagent 的 Task 工具，单代理顺序执行最可控。

## 执行入口检查
- 确定性检查：已通过。
- 当前阻断项：无阻断项。
- 开始前必须确认：执行者只能按本交接资产和已批准蓝图包修改列出的文件。
- 停止并回退条件：发现需要改变目录名、恢复 worktree/brainstorming/using-superpowers 入口、修改蓝图未列出的既有技能、或需要新增未批准文件时，停止执行并回到 HILP 变更重审阶段。

## 规划资产归档
- 自动归档结果：已完成。
- 文件路径：`D:/Workspace/skills/docs/changes/构建中文裁剪版Superpowers技能/planning/assets/06-规划资产归档_no-approval_archive-manifest@v1.md`
- asset_ref：`stage-7/archive-manifest@v1 [state=archived｜中文状态=已归档]`
- 当前是否需要审批：无需审批。
- 作用：标明本次变更的最终阅读入口、最终有效资产、历史过程资产和后续重审入口；不改变任何已批准资产状态。