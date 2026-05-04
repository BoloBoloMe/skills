# PRD Review Output Template

Use this file for PRD reviews. Choose Quick, Standard, or Deep Audit based on the user's request and risk level.

## Safe-use rules

Before final output, remove every placeholder row, bracket placeholder, and empty table row. If a field is unknown, either omit it or move it into Ambiguities / Decisions Needed with decision impact. For short Chinese reviews, use the lightweight Chinese quick review format instead of a heavy audit table.

## Verdict thresholds

Use `prd-quality-checklist.md` as the source of truth for Ready / Needs revision / Not ready thresholds, blocker taxonomy, dimension scoring anchors, and final gate rules. Release blockers override average score.

## Verdict localization

Use stable enums `Ready`, `Needs revision`, and `Not ready`. In Chinese reviews, write them with localized meaning on first use: `Ready（可进入下一阶段）`, `Needs revision（需修改）`, `Not ready（暂不可进入下一阶段）`.

## Quick review

```markdown
## Review Verdict
Ready / Needs revision / Not ready; add Chinese meaning on first use for Chinese reviews

## Top Blockers
1. State the issue and its impact

## Top Fixes
1. State the concrete fix

## Optional Rewrite
Rewrite the highest-risk section if useful.
```

## Chinese lightweight quick review

Use this for short PRDs, early ideas, or when the user asks for a quick Chinese review:

```markdown
## 结论
Ready / Needs revision / Not ready; add Chinese meaning on first use for Chinese reviews

## 主要问题
1. 写清问题及其影响

## 最小修复清单
1. 写清必须补齐的最小修改

## 建议改写
如有必要，改写最高风险片段。
```

## Standard review

```markdown
## Review Verdict
Ready / Needs revision / Not ready; add Chinese meaning on first use for Chinese reviews

## Release Blockers
| Issue | Impact | Why it blocks | Required fix | Owner |
|---|---|---|---|---|

## Must Fix Before Design / Development / Launch
| Stage | Issue | Impact | Recommended fix | Priority |
|---|---|---|---|---|

## Dimension Scores
| Dimension | Score | Status | Main issue | Fix suggestion |
|---|---:|---|---|---|
| Strategy and context | /10 |  |  |  |
| Scope control | /10 |  |  |  |
| Functional completeness | /10 |  |  |  |
| State and edge cases | /10 |  |  |  |
| Data and metrics | /10 |  |  |  |
| NFRs and risk | /10 |  |  |  |
| Testability | /10 |  |  |  |

## Ambiguities and Decisions Needed
| Area | Ambiguity | Decision needed | Decision owner | Impact if unresolved |
|---|---|---|---|---|

## Missing Edge Cases / NFRs
| Gap | Why it matters | Suggested requirement or AC |
|---|---|---|

## Recommended Rewrites
Provide improved sections or examples for the highest-risk gaps.

## Deferred Improvements
| Improvement | Why it can defer | Suggested timing |
|---|---|---|
```

## Deep audit additions

Add these sections after Standard review when the PRD is high-risk:

```markdown
## Traceability Audit
| Problem / goal | Requirement | AC | Event / metric | Gap |
|---|---|---|---|---|

## Launch Gate Assessment
| Gate | Status | Blocker | Owner | Required evidence |
|---|---|---|---|---|

## Risk Register Assessment
| Risk | Severity | Current mitigation | Gap | Required owner / action |
|---|---|---|---|---|

## Cross-Functional Owner Gaps
| Function | Missing review / owner | Why it matters |
|---|---|---|
```
