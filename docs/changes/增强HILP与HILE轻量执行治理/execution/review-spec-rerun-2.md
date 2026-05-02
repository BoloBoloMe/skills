Spec compliant

## Review
- Correct: `human-in-loop-execution/SKILL.md:49` 明确在执行单个 `execution_unit` 前读取 `references/execution-unit-intake.md`；`human-in-loop-execution/SKILL.md:97` 在参考文件列表中列出该文件。
- Correct: `human-in-loop-planning/SKILL.md:29` 与 `human-in-loop-planning/SKILL.md:30` 在资源加载顺序中列出 `references/verification-contract.md` 与 `references/context-packet.md`；`human-in-loop-planning/SKILL.md:36` 明确相关场景必须同时读取二者；`human-in-loop-planning/SKILL.md:197` 与 `human-in-loop-planning/SKILL.md:198` 在参考文件列表中列出二者。
- Correct: `docs/changes/增强HILP与HILE轻量执行治理/execution/ledger.md:32` 如实记录用户要求“启用子代理依次执行各 execution_unit”，并记录实际单线程、未并行、未使用 worktree 自动化；`ledger.md:33` 说明该记录用于澄清 `subagent-worker` 与串行逐单元执行之间的歧义。
