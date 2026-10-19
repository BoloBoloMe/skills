# 编排日志 (tdd-as-orchestra)

- 权威输入: `EXECUTION.md`, `PRODUCT.md`, `TECHNICAL.md`, `DECISIONS.md`, `issues/ISSUE-*.md`.
- 主分支: `v2`. 工作树根: `/home/bolo/Workspace/skills/skills-v2.worktrees/`. 分支: `issue/<NN>`.
- 基线: 见 `BASELINE.md`. AFK 自主决定: 见 `UNAUTHORIZED_DECISIONS.md`.
- 演练记录: 各 `evidence/ISSUE-<NN>/`.

## 波次计划 (按 EXECUTION 任务图依赖)

- 波次 1: ISSUE-01, ISSUE-06, ISSUE-07, ISSUE-11, ISSUE-12 (均无依赖).
- 波次 2: ISSUE-02 (依赖 01), ISSUE-08 (依赖 07,06), ISSUE-13 (依赖 07,09 -> 待 09), ISSUE-09 (依赖 08).
  实际按依赖就绪逐个放行: 02 / 08 可并行, 其余候选随上游合入再放行.
- 后续: 03 -> 04 -> 05 -> 10 -> 14 -> 15; 08 -> 09 -> 13 -> 15.
- 已完成的波次在本文件追加记录, 每轮记录: ISSUE 集合, 合并结果, 勾选状态.

## 进度

- [x] 波次 1 派发: ISSUE-01, 06, 07, 11, 12
