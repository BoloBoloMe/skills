---
asset_id: hilp-superpowers-skills-design-choice
artifact_name: stage-3/design-choice
version: v3
state: approved
state_label: 已批准
owner_skill: hilp-design-approval
created_from: stage-reapproval/reapproval-decision@v2
last_event: human-approval-granted
last_decision: human-approval-2026-04-28-human-in-loop-execution-design-v3
approval_marker: approved
approval_marker_label: 已批准
asset_path: D:/Workspace/skills/docs/hilp/构建中文裁剪版Superpowers技能/02-方案设计_approved_design-choice@v3.md
replaces: stage-3/design-choice@v2 [state=needs-revision｜中文状态=待修订]
---

# 方案设计与审批阶段

## 审批结论
用户已明确批准：`02-方案设计_needs-approval_design-choice@v3`，采用 `human-in-loop-execution` 作为目录名。

## 已批准方案
在仓库根目录构建 `human-in-loop-execution/`：一个中文化、受 `human-in-loop-planning/` 执行交接约束的执行层技能包。它来源于 Superpowers 的裁剪和汉化，但不使用 `superpowers-skills` 命名，不保留 Superpowers 的设计审批入口，不假设仓库内技能会被 agents 自动发现，也不保留 `using-git-worktrees`。

## 已批准边界
- `human-in-loop-planning/` 负责规划治理：需求事实、方案比较、人工审批、实施蓝图、执行交接。
- `human-in-loop-execution/` 负责执行纪律：执行计划拆分、subagent 或 inline 执行、TDD、代码审查、根因调试、完成前验证、分支收尾和技能编写元纪律。
- 不纳入 `brainstorming`。
- 不纳入 `using-git-worktrees`。
- 不纳入原始 `using-superpowers` 的全局强制入口模式。
- 不复制 Superpowers design doc / spec approval gate。
- 不复制源仓插件分发、hooks、commands、assets、历史 plans/specs、测试仓库和上游贡献规则。
- 不要求仓库内 skill 被 agents 自动发现；真实使用时由用户触发安装。

## 下游输入引用
```text
asset_ref: stage-3/design-choice@v3 [state=approved｜中文状态=已批准]
owner_skill: hilp-design-approval
source_event: human-approval-2026-04-28-human-in-loop-execution-design-v3
last_decision: human-approval-2026-04-28-human-in-loop-execution-design-v3
summary: create human-in-loop-execution as HILP-bound Chinese execution skill package
```
