# Issues found

## Review

- Correct: `human-in-loop-execution/SKILL.md` 已处理初审问题 1：资源加载顺序在 `human-in-loop-execution/SKILL.md:49` 要求执行单个 `execution_unit` 前读取 `references/execution-unit-intake.md`，参考文件清单在 `human-in-loop-execution/SKILL.md:94` 至 `human-in-loop-execution/SKILL.md:99` 列出 `references/execution-unit-intake.md`、`references/execution-ledger.md` 与 `references/unit-summary.md`。
- Correct: `docs/changes/增强HILP与HILE轻量执行治理/execution/ledger.md` 已处理初审问题 3：状态表仍如实记录 EU-001 至 EU-005 的 `subagent-worker` 执行方式（`ledger.md:24` 至 `ledger.md:28`），并在审查记录中说明用户要求“启用子代理依次执行各 execution_unit”、实际为单线程逐单元派发、未并行、未使用 worktree 自动化（`ledger.md:32` 至 `ledger.md:34`），未掩盖子代理、并行风险或 worktree 自动化。
- Blocker: `human-in-loop-planning/SKILL.md:185` 至 `human-in-loop-planning/SKILL.md:198` — 参考文件清单仍未列出 `references/verification-contract.md` 与 `references/context-packet.md`。虽然资源加载区已在 `human-in-loop-planning/SKILL.md:29` 至 `human-in-loop-planning/SKILL.md:30`、`human-in-loop-planning/SKILL.md:36` 加入读取规则，但用户复查项要求“已加载并列出”两者；当前只满足“已加载”，未满足“列出”。影响：入口文档的参考文件清单与加载规则不一致，后续维护者可能按清单核验时漏掉 verification contract 与 context packet。修复方向：在 `human-in-loop-planning/SKILL.md` 的 `## 参考文件` 清单中补充 `references/verification-contract.md` 与 `references/context-packet.md`。
