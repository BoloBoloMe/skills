# Lite PRD Template

Use this for sparse input, simple changes, early ideas, or low-risk experiments. Do not expand it into a full Standard PRD unless the user asks for a full document.

## Safe-use rules

- Keep the final answer compact: <= 1,200 Chinese characters or equivalent, with no more than 8 numbered sections unless the user explicitly asks for more.
- Default to short bullets. Use tables only when at least one is true: there are 3 or more comparable items, stable IDs are needed, or QA / data / risk review clearly benefits from tabular structure.
- Delete any section that cannot be meaningfully populated.
- Before final output, remove every placeholder row, bracket placeholder, and empty table row. If a field is unknown, either omit it or move it into Open Questions with decision impact.
- Put missing information into assumptions/open questions with decision impact.

```markdown
# Lite PRD: {actual feature name}

## 1. Executive summary
- Problem:
- Proposed change:
- Primary user:
- Expected outcome:

## 2. Confirmed facts, assumptions, and open questions
- FACT/ASM/TBD items only as needed.
- Include decision impact for important assumptions or open questions.

## 3. Goals, non-goals, and scope
- Goals:
- Non-goals:
- In scope:
- Out of scope:

## 4. Key requirements
- FR-001:
- FR-002:

## 5. Main states and edge cases
- Default / success:
- Empty / disabled:
- Failure / retry:
- Permission / unauthorized:

## 6. Metrics / tracking
- Success metric:
- Guardrail metric:
- EVT links if tracking is needed:

## 7. Acceptance criteria
- AC-001:
- AC-002:

## 8. Risks and rollout notes
- Main risk:
- Mitigation:
- Rollout / rollback note:
```

## Sparse Input Fallback

Use this when the user gives less information than needed for a Lite PRD:

1. Draftable content
2. Assumptions
3. 3 highest-impact open questions
4. Highest-risk missing decisions
5. Recommended next PRD section to write
