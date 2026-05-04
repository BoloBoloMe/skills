# PRD Quality Checklist

Use this checklist when reviewing, improving, or finalizing a PRD. For formal reviews, return an audit-style verdict instead of general advice.

## 1. Strategy and Context

- The background explains the current situation, not just the requested solution.
- The user problem is concrete and tied to a scenario.
- Business impact is clear and not exaggerated beyond evidence.
- Confirmed facts, assumptions, open questions, source-backed decisions, and dependencies are separated.
- Goals are measurable or at least observable.
- Non-goals are explicit when scope can expand.

## 2. Scope Control

- In-scope and out-of-scope items are both explicit.
- Requirements are prioritized with P0 / P1 / P2 and rationale.
- Deferred work is marked as future scope, not hidden in vague language.
- Dependencies and constraints are documented with owners when known.
- The PRD tier is appropriate: Lite, Standard, or Complex.
- The output depth matches the input; small requests are not buried under a full template.
- If the input is primarily strategy, market positioning, business model, or commercial goal, recommend a product strategy clarification brief instead of forcing PRD structure.

## 3. User and Scenario Clarity

- User roles are defined.
- Primary and secondary scenarios are covered.
- User stories connect capability to value.
- Entry points, trigger conditions, and exit states are clear.
- Success outcomes are observable.

## 4. Functional Completeness

Each key function should include:

- purpose and user value
- affected surfaces
- display rules
- operation rules
- validation rules
- business rules
- data rules
- exception handling
- permission behavior
- acceptance criteria

## 5. State Coverage

Check for these states where applicable:

- default state
- empty state
- loading state
- success state
- failure state
- partial success state
- disabled state
- unauthenticated state
- unauthorized state
- offline / network timeout state
- duplicate action / repeated click state
- stale data / expired data state
- retry state
- rollback or recovery state

## 6. Edge Cases and Exceptions

Common omissions:

- user has no data
- user has too much data
- input format is invalid
- service timeout or API failure
- user repeats the same operation quickly
- permissions change mid-flow
- data changes after page load
- cross-platform behavior differs
- rollback or retry is required
- migration leaves partial or inconsistent data
- notification, email, webhook, or export is delayed or duplicated

## 7. Data, Analytics, and Governance

- Core success metrics are defined.
- Metric formulas are unambiguous.
- Event tracking includes event name, trigger, parameter types, required fields, privacy level, and validation method.
- Required dashboards or reporting needs are noted.
- Data source of truth is specified when relevant.
- Source-backed facts and assumptions from connected documents, tickets, transcripts, or research are labeled when they affect scope, risk, metrics, or launch readiness.
- Sensitive-data handling, retention, deletion, masking, and consent are considered.
- Tracking events map to the requirement or success metric they support.

## 8. Non-Functional Requirements

Check whether applicable areas are covered:

- performance
- reliability and retry behavior
- security and authorization
- privacy and data minimization
- compliance and auditability
- accessibility
- internationalization / localization
- compatibility
- observability
- rollout, gray release, kill switch, and rollback

## 9. Traceability and Testability

- P0/P1 requirements link to acceptance criteria.
- Acceptance criteria are scenario-based, observable, and deterministic where possible.
- QA can convert acceptance criteria into test cases.
- Business rules and data rules have corresponding test coverage where they affect user outcomes.
- Events and metrics map back to goals and requirements.

Weak example:
- The page experience is smooth.

Strong example:
- When the user clicks Submit Order, the button is disabled immediately and shows loading. Before the API returns, repeated submission is blocked. If the API does not return within 10 seconds, show the copy "Network error. Please try again later." and re-enable the button.

## 10. Cross-Functional Review

| Function | Review focus |
|---|---|
| Product | problem, goals, scope, priority, tradeoffs, success metrics |
| Design | user flow, states, copy, accessibility, interaction consistency |
| Engineering | feasibility, dependencies, data model, interface contract, rollout/rollback |
| QA | acceptance criteria, edge cases, state coverage, regression risk |
| Data | event spec, metric definitions, dashboard, data quality validation |
| Operations / Support | tooling, runbook, customer impact, support escalation |
| Legal / Compliance | policy, privacy, retention, audit, disclosures |
| Security | authorization, abuse, sensitive data, logging, rate limits |

## 11. Verdict Thresholds

Use these standards when giving a PRD review verdict:

| Verdict | Standard | Typical score pattern |
|---|---|---|
| Ready | No release blockers; P0 requirements have ACs; core scope, metrics, critical risks, rollout/rollback, and owners are clear enough for the next stage. | Most dimensions >= 8/10, and no blocker dimension below 7/10. |
| Needs revision | Direction is valid, but important gaps remain. The PRD can continue discussion, but must be revised before design, development, or launch as specified. | Mixed scores; one or more important dimensions 5-7/10. |
| Not ready | Problem, target user, goals, scope, P0 requirements, ACs, compliance/security/privacy, or launch viability is missing enough that next-stage work would be unsafe or wasteful. | Any critical dimension <= 4/10, or unresolved launch/safety blocker. |

Release blockers override average score. A PRD with any unresolved legal, compliance, security, privacy, payment-risk, or data-integrity blocker is not Ready even if the average score is high.

## 12. Dimension Scoring Anchors

Use these anchors to calibrate 0-10 scores consistently:

| Dimension | 9-10 | 6-8 | 3-5 | 0-2 |
|---|---|---|---|---|
| Strategy and context | Problem, evidence, user, business impact, and decision context are explicit. | Direction is clear, but evidence or impact is incomplete. | Solution exists, but problem, user, or context is vague. | No usable strategy context. |
| Scope control | In-scope, out-of-scope, priorities, dependencies, and deferred work are explicit. | Main scope is clear, but boundaries or priority rationale are incomplete. | Scope is partial and likely to cause delivery ambiguity. | Scope is absent or contradictory. |
| Functional completeness | Key behavior, rules, states, permissions, and dependencies are specified. | Core behavior is present, but secondary rules or states are missing. | Requirements are broad and hard to build from. | No actionable functional requirements. |
| State and edge cases | Normal, branch, failure, permission, retry, and boundary states are covered where applicable. | Main happy path is covered, but several states are missing. | Edge cases are mostly implicit. | No meaningful state or exception handling. |
| Data and metrics | Metrics, event specs, source of truth, validation, and privacy handling are clear. | Metrics or events exist, but formulas, validation, or governance are incomplete. | Data plan is vague or only names high-level metrics. | No usable measurement or data plan. |
| NFRs and risk | Relevant performance, reliability, security, privacy, compliance, rollout, and risk controls are covered. | Major risks are identified, but owners or mitigations are incomplete. | Risk/NFR coverage is shallow. | High-risk areas are ignored. |
| Testability | P0/P1 requirements map to deterministic ACs that QA can convert to tests. | Most core ACs exist, but some are ambiguous or incomplete. | ACs are generic or not tied to requirements. | No testable acceptance criteria. |

## 13. Blocker Taxonomy

| Category | Meaning | Typical treatment |
|---|---|---|
| Release blocker | Prevents safe launch or violates legal/security/data integrity expectations. | Must fix before launch; often Not ready. |
| Must fix before design | Missing problem, user, scenario, scope, or key UX state decision. | Resolve before design starts or finalizes. |
| Must fix before development | Missing P0 requirement, business rule, interface dependency, data rule, or AC. | Resolve before implementation. |
| Must fix before launch | Missing metric validation, rollout/rollback, support readiness, compliance signoff, or monitoring. | Resolve before release. |
| Can defer | Improves completeness but does not block the next decision. | Track as future scope or follow-up. |

## 14. Review Depth

| Depth | Use when | Required output |
|---|---|---|
| Quick review | User asks for a fast pass or PRD is very short. | Verdict, top blockers, top fixes, optional rewrite. |
| Standard review | Default review mode. | Verdict, blockers, stage-gated fixes, dimension scores, ambiguities, missing edge cases/NFRs, rewrites, deferred items. |
| Deep audit | High-risk, compliance/security/data-heavy, or launch-critical PRD. | Standard review plus traceability audit, launch gate, risk register, and cross-functional owner gaps. |

## 15. Audit Review Format

Use `review-output-template.md` for exact output templates. For Standard reviews, include:

1. Review Verdict
2. Release Blockers
3. Must Fix Before Design / Development / Launch
4. Dimension Scores
5. Ambiguities and Decisions Needed
6. Missing Edge Cases / NFRs
7. Recommended Rewrites
8. Deferred Improvements

## 16. Final Quality Pass

Before delivering a PRD or PRD review, check:

- no empty table rows, bracket placeholders, or unexplained `TBD` values remain
- confirmed facts, assumptions, recommendations, and open questions are separated
- P0 requirements have acceptance criteria or are marked as blockers
- high-risk items have owners or explicit decision dependencies
- output depth matches the request and input complexity
- source-backed facts, assumptions, inferred recommendations, and open questions are not mixed

## 17. Final Gate

A PRD is **Ready** only when all launch-blocking questions are answered, P0 requirements have acceptance criteria, critical risks have owners, and success measurement is defined. Otherwise use **Needs revision** or **Not ready** with explicit blockers.

## 18. Table Budget and Readability

- Lite PRDs and Quick Reviews should default to bullets. Use tables only when there are 3 or more comparable items, stable IDs are needed, or QA / data / risk review clearly benefits.
- Standard and Complex reviews may use tables for blockers, scores, traceability, and launch gates, but omit empty tables and low-signal rows.
- Early exploration should prioritize guidance and decision clarity over audit density.
