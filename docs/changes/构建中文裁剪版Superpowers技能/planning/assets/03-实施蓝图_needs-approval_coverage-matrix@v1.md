---
asset_id: hilp-superpowers-skills-coverage-matrix
artifact_name: stage-4-5/coverage-matrix
version: v1
state: ready-for-approval
state_label: 待审批
owner_skill: hilp-blueprint
created_from: stage-4-5/implementation-blueprint@v1
last_event: none
last_decision: none
approval_marker: needs-approval
approval_marker_label: 需审批
asset_path: D:/Workspace/skills/docs/changes/构建中文裁剪版Superpowers技能/planning/assets/03-实施蓝图_needs-approval_coverage-matrix@v1.md
blueprint_form: package-coverage-matrix
parent_blueprint: stage-4-5/implementation-blueprint@v1 [state=ready-for-approval｜中文状态=待审批]
---

# 覆盖矩阵

| 设计决策 / 需求承诺 | 改动切片 | 子蓝图 | 验证项 | 风险检查点 |
|---|---|---|---|---|
| 目录名采用 `human-in-loop-execution/` | 包结构与仓库登记 | `blueprint-slice-package-structure@v1` | `test -d human-in-loop-execution`; `grep -q '^name: human-in-loop-execution$' human-in-loop-execution/SKILL.md` | 检查不存在 `superpowers-skills` |
| 与 `human-in-loop-planning/` 形成规划 / 执行命名呼应 | 包结构与仓库登记 | `blueprint-slice-package-structure@v1` | `grep -q 'human-in-loop-planning' human-in-loop-execution/README.md` | README 不得描述为 Superpowers 完整 fork |
| 不要求仓库内 skill 自动发现 | 包结构与仓库登记 | `blueprint-slice-package-structure@v1` | `grep -q '用户.*安装' human-in-loop-execution/README.md` | README 不得声称自动发现 |
| 不保留 `using-git-worktrees` | 包结构与执行主协议 | `blueprint-slice-package-structure@v1`; `blueprint-slice-execution-protocol@v1` | `test ! -e human-in-loop-execution/skills/using-git-worktrees` | 执行入口只确认当前工作区，不创建 worktree |
| 不保留 `brainstorming` 与 spec approval | 执行主协议 | `blueprint-slice-execution-protocol@v1` | `test ! -e human-in-loop-execution/skills/brainstorming` | 执行文档不得生成 Superpowers design doc |
| 执行计划只能来自 HILP 已批准蓝图与执行交接 | 执行主协议 | `blueprint-slice-execution-protocol@v1` | `grep -q '执行交接' human-in-loop-execution/references/writing-plans.md` | 缺少 approved 资产时停止并回到 HILP |
| subagent prompt 必须携带 HILP 资产和禁止越界项 | 执行主协议；质量辅助与元技能 | `blueprint-slice-execution-protocol@v1`; `blueprint-slice-quality-and-meta@v1` | `grep -q '禁止越界项' human-in-loop-execution/references/prompt-templates/implementer-prompt.md` | subagent 不得重新设计或扩大范围 |
| TDD 铁律保留 | 执行主协议 | `blueprint-slice-execution-protocol@v1` | `grep -q '失败测试' human-in-loop-execution/references/test-driven-development.md` | 无失败测试不得写生产代码 |
| 代码审查与 review 反馈保留 | 执行主协议 | `blueprint-slice-execution-protocol@v1` | `grep -q 'Critical' human-in-loop-execution/references/code-review.md` | Critical 阻断，Important 先修 |
| 分支收尾保留但偏差回到 HILP 重审 | 执行主协议 | `blueprint-slice-execution-protocol@v1` | `grep -q '变更重审' human-in-loop-execution/references/finishing-branch.md` | 发现偏差或新事实不得直接收尾 |
| 系统调试保留且先根因后修复 | 质量辅助与元技能 | `blueprint-slice-quality-and-meta@v1` | `grep -q '根因' human-in-loop-execution/references/systematic-debugging.md` | 修复改变蓝图时回 HILP 重审 |
| 完成声明必须有新鲜验证证据 | 质量辅助与元技能 | `blueprint-slice-quality-and-meta@v1` | `grep -q '没有新鲜验证证据' human-in-loop-execution/references/verification-before-completion.md` | 不得无命令输出声称完成 |
| 并行 agent 受独立域和执行范围约束 | 质量辅助与元技能 | `blueprint-slice-quality-and-meta@v1` | `grep -q '互不' human-in-loop-execution/references/dispatching-parallel-agents.md` | 共享文件或顺序依赖时不得并行 |
| `writing-skills` 仅作为元技能 | 质量辅助与元技能 | `blueprint-slice-quality-and-meta@v1` | `grep -q '元技能' human-in-loop-execution/references/writing-skills.md` | 不得替代 HILP 方案审批 |
| 根 README 登记新技能包 | 包结构与仓库登记 | `blueprint-slice-package-structure@v1` | `grep -q 'human-in-loop-execution' README.md` | 不修改无关技能说明 |

## 覆盖结论
- 已批准设计决策全部有对应切片。
- 必要改动切片全部有验证项。
- 高风险点均有检查点。
- manifest 未遗漏子蓝图中的关键约束。

## 确定性检查
- 未确定项：无。
- 模糊表达：无。
- 分支待选方案：无。
- 需要执行者自行裁量的实现决策：无。