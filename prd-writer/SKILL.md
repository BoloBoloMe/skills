---
name: prd-writer
description: professional prd creation, rewriting, review, and standardization for product requirements documents. use when the user asks to write a prd, generate product requirements, convert rough ideas or meeting notes into a prd, improve an existing prd, create acceptance criteria, define feature scope, write product flows, add metrics or tracking, or evaluate whether a prd is complete and actionable. supports chinese and english outputs, with mode routing, output length control, fact and assumption management, traceability, review verdict thresholds, prd type adaptation, non-functional requirements, and testable acceptance criteria.
---
# PRD Writer

## Core Behavior

Produce professional product requirements documents that align product, design, engineering, QA, data, operations, legal/compliance, security, and business stakeholders. Treat a PRD as a durable requirements asset: it should be clear enough to review, build, test, launch, instrument, and revisit after release.

Prioritize clarity, explicit scope, traceability, testability, measurable outcomes, and decision readiness over length. Adapt depth to the user's input and requested task. Never turn a thin idea into a long placeholder-filled document.

Default language: match the user's language. For Chinese requests, use professional Chinese product-management terminology and localized section titles while preserving stable IDs such as `FR-001`, `AC-001`, and `EVT-001`. Technical analytics field names may remain in English when they are implementation-facing. Keep verdict enums stable as `Ready`, `Needs revision`, and `Not ready`; in Chinese output, add the localized meaning on first use: `Ready（可进入下一阶段）`, `Needs revision（需修改）`, `Not ready（暂不可进入下一阶段）`.

## Execution Workflow

1. Identify the task type:
   - **Create PRD from scratch**: turn an idea, feature brief, business request, or meeting notes into a PRD.
   - **Improve existing PRD**: rewrite vague sections, add missing rules, clarify scope, strengthen traceability and acceptance criteria.
   - **Review PRD**: perform a decision-oriented audit using verdict thresholds and the quality checklist.
   - **Generate specific section**: produce only the requested section, such as user stories, flows, edge cases, tracking, or acceptance criteria.
2. If source material is provided or referenced, read/synthesize it first using `references/source-material-handling.md`: extract source-backed facts, decisions, assumptions, inferred recommendations, contradictions, and open questions. Do not choose Lite / Standard / Complex / Review until this extraction is complete.
3. Choose the output route before writing. Treat `references/prd-output-routing.md` as the routing source of truth for mode selection, output length, follow-up policy, template loading, table budget, and decision order.
4. Classify the PRD type and product shape. Use `references/prd-type-adapter.md` as the source of truth for product type modifiers and Complex escalation. When escalation is uncertain, follow its two-anchor rule.
5. Establish product context from available input and extracted source material:
   - product / feature name
   - target users, roles, scenarios, and affected surfaces
   - business or user problem
   - confirmed facts, assumptions, open questions, dependencies, constraints, launch timing, and known risks
6. Write or revise with explicit structure:
   - explain why the product change is needed
   - define goals, non-goals, and success metrics
   - specify what is in scope and out of scope
   - describe normal, branch, empty, loading, permission, failure, retry, partial-success, stale-data, and exception states when applicable
   - convert ambiguous language into observable product behavior and verifiable rules
   - add measurable metrics and instrumentation when the product behavior or success measurement needs data
   - link requirements to acceptance criteria, events, and metrics when using Standard or Complex PRD mode
7. Run the final quality pass before responding.

## Routing Decision Tree

Apply this order mechanically when the route is not explicit:

1. **Source material first**: if the user provides or references notes, tickets, existing PRDs, transcripts, research, design docs, dashboards, or connected-source content, extract source-backed facts and decisions before route selection.
2. **Review request**: if the user asks to review, audit, check readiness, or identify gaps, choose PRD Review and then select Quick / Standard / Deep depth.
3. **Single-section request**: if the user asks only for acceptance criteria, tracking, user stories, flows, scope, edge cases, risks, or NFRs, output only that section.
4. **Strategy-only input**: if the input is mainly market, business model, commercial goal, or positioning with no concrete product behavior, output a Product Strategy Clarification Brief.
5. **Sparse idea**: if input is too thin for Lite PRD, use Sparse Input Response Pattern; otherwise choose Lite PRD.
6. **Feature draft**: if users, problem, goal, and scope are available, choose Standard PRD.
7. **High-risk / cross-system check**: apply `prd-type-adapter.md`; use full Complex only when at least two escalation anchors apply or the user explicitly asks for full Complex.
8. **Table budget**: for Lite PRDs and Quick Reviews, default to bullets unless IDs, 3+ comparable items, or QA / data / risk review benefits justify a table.

## Routing Quick Reference

| User request / input | Default route | Output behavior |
|---|---|---|
| One-sentence idea, early thought, or "write a simple PRD" | Lite PRD | <= 1,200 Chinese characters or equivalent; no more than 8 core sections. Include context, assumptions, scope, key requirements, edge cases, metrics, ACs, and top risks. Do not load the full template unless requested. |
| Feature brief with problem, users, and goals | Standard PRD | Use the main structure, but omit sections that cannot be meaningfully populated. Include simplified risk register. |
| Meeting notes or multi-stakeholder context | Standard or Complex PRD | Synthesize decisions, assumptions, open questions, and traceability. Load examples if output style is uncertain. |
| AI, permissions, compliance, payments, identity, data migration, platform, integration, or multi-system work | Standard + targeted high-risk sections by default; full Complex only by two-anchor rule | Use `prd-type-adapter.md` as the source of truth. If fewer than two Complex anchors apply and the risk is narrow, do not escalate to full Complex unless the user explicitly asks. |
| "Review this PRD" / "audit this" | PRD Review | Choose Quick, Standard, or Deep review depth. Use verdict thresholds. |
| "Only write acceptance criteria / tracking / user stories" | Single Section | Return only the requested section with IDs and testable language. |

## Output Tiers

### Lite PRD
Use for small changes, early ideas, low-risk experiments, or sparse input. Include only: executive summary, confirmed facts/assumptions/open questions, combined goals/non-goals/scope, key requirements, main states or edge cases, metrics if relevant, acceptance criteria, and risks/rollout notes. Target <= 1,200 Chinese characters or equivalent length, with no more than 8 numbered sections unless the user asks for more.

### Standard PRD
Use for normal product features requiring design, engineering, QA, metrics, and launch coordination. Use the default PRD structure selectively. Include requirement IDs, priority rationale, simplified risk register, event tracking when relevant, and acceptance criteria linked to requirements. Prefer 2,000-4,000 Chinese characters or equivalent length for first drafts; only expand sections with evidence, source material, or useful decision value.

### Complex PRD
Use for high-risk, cross-system, regulated, AI, platform, permission-heavy, migration, integration, or data-critical work only when the two-anchor rule in `references/prd-type-adapter.md` is met or the user explicitly requests full Complex output. Include a Review First summary, traceability matrix, full risk register, NFRs, permission matrix, data governance notes, rollout/rollback, and cross-functional review owners. If only one high-risk signal exists and it is narrow and well-contained, use Standard PRD with targeted high-risk sections. Unless the user explicitly requests a complete expanded document, start with a structured v0.1 that expands only the decision-critical sections.

## Review Depths

| Review depth | Use when | Output |
|---|---|---|
| Quick review | User asks for a quick check or the PRD is short. | Verdict, top blockers, top fixes, and optional rewrite sample. |
| Standard review | Default PRD review. | Verdict, blockers, stage-gated fixes, scores, ambiguities, missing edge cases/NFRs, rewrites, deferred items. |
| Deep audit | High-risk, launch-critical, compliance/security/data-heavy PRD. | Standard review plus traceability audit, launch gate, risk register assessment, and cross-functional owner gaps. |

Use `references/review-output-template.md` for formal reviews.

## Source and Connector Handling

When the user provides or references source material such as meeting notes, user feedback, an existing PRD, research notes, competitive analysis, design notes, tickets, internal documents, or connected-source content, use `references/source-material-handling.md` as the source of truth before route selection. Extract source-backed facts and decisions first, separate assumptions and inferred recommendations, preserve contradictions as open questions, then choose Lite / Standard / Complex / Review / Single Section / Strategy route. Avoid inventing exact data, compliance rules, metric baselines, or system constraints.

## Product Strategy Boundary

If the input is primarily strategy, market positioning, commercial goal, business model, or opportunity framing rather than product behavior, do not force a PRD. Return a product strategy clarification brief first with:

1. problem / opportunity hypothesis
2. target segment and scenario assumptions
3. strategy assumptions and evidence gaps
4. product behavior implications
5. key validation questions before PRD drafting

Proceed to a PRD only after there is enough product behavior, user scenario, or delivery scope to specify requirements.

## Sparse Input Response Pattern

When the input is too thin for even a Lite PRD, do not force a PRD. Return:

1. Draftable content
2. Assumptions
3. The 3 highest-impact open questions
4. Highest-risk missing decisions
5. Recommended next PRD section to write

## Fact, Assumption, Placeholder, and Follow-Up Rules

- Never invent exact business data, user research findings, compliance requirements, security constraints, model behavior, or system constraints as fact.
- Put uncertain content into a clearly marked confirmed-facts / assumptions / open-questions section near the top.
- Use `TBD` or `Needs confirmation` only with a reason and decision impact.
- Before final output, remove every placeholder row, bracket placeholder, and empty table row. If a field is unknown, either omit the field or move it into Open Questions with decision impact. Do not leave placeholder labels for description, date, field, owner, product name, or similar unknown fields.
- If input is sparse, output confirmed content, assumptions, open questions, and the highest-risk draft sections. Do not mechanically fill every section. For early exploration, prefer short bullets over tables unless the table improves reviewability, traceability, or QA execution.
- Ask follow-up questions only when a missing decision materially changes product direction, feasibility, risk, or launch readiness.
- Ask at most 1-3 high-leverage follow-up questions. If the user asks for a direct draft or revision, proceed with marked assumptions instead of blocking.
- For short PRDs under roughly 500 words and not high-risk, default to a Quick or Quick/Standard hybrid review unless the user asks for a full audit.

## Table Budget Rules

For Lite PRDs and Quick Reviews, default to short bullets. Use a table only when at least one condition is true: there are 3 or more comparable items, stable IDs are needed, or QA / data / risk review clearly benefits from tabular structure. For Standard and Complex outputs, include only tables with real content and review value; delete unused rows and avoid tables that merely restate prose.


## Default PRD Structure

Use this structure for full Standard and Complex PRDs unless the user asks for a different format. Load `references/prd-template.md` as a section inventory, not as a literal output scaffold. `Review First` is mandatory for Complex PRDs, optional for Standard PRDs only when launch-critical, review-oriented, or user-requested, and omitted for Lite PRDs.

0. Document information
0.1 Confirmed facts, assumptions, and open questions
0.2 Executive summary
1. Background, problem, and evidence
2. Goals and success metrics
3. Non-goals and scope boundaries
4. Product type, users, roles, and scenarios
5. Requirements scope and priority
6. Business process, flows, and state transitions
7. Functional details and business rules
8. Page, interaction, and state notes
9. Permissions, data rules, and governance
10. Edge cases and exception handling
11. Non-functional requirements
12. Data tracking, analytics, and metric definitions
13. Acceptance criteria
14. Requirements traceability matrix
15. Dependencies, risks, rollout, and rollback
16. Cross-functional review checklist
17. Appendix / links

## ID Prefix Registry and Traceability

Use `references/id-prefix-registry.md` as the source of truth for all allowed prefixes, including requirement IDs (`FR-*`, `BR-*`, `NFR-*`, `PERM-*`, `DATA-*`), acceptance criteria (`AC-*`), analytics events (`EVT-*`), metrics (`METRIC-*`), risks (`RISK-*`), source-backed facts (`FACT-*`), decisions (`DEC-*`), assumptions (`ASM-*`), open questions (`TBD-*`), dependencies (`DEP-*`), edge cases (`EDGE-*`), and source notes (`SRC-*`).

Use numeric stable IDs by default, such as `FR-001`, `NFR-001`, `AC-001`, and `EVT-001`. Do not introduce prefixes such as `SAFE-*`, subtype ID formats such as `NFR-SEC-*`, or organization-specific IDs unless the user or organization explicitly defines them.

Keep entity types separate: `FR-*` describes buildable product/system behavior, `EVT-*` belongs in tracking specs, and `RISK-*` belongs in risk registers. Requirement tables may link to related events or risks, but should not use `EVT-*` or `RISK-*` as requirement rows.

For Standard and Complex PRDs, preserve this chain where possible:

`Problem -> Goal -> Scenario -> Requirement -> Rule/NFR -> Acceptance Criterion -> Event -> Metric`

Use the traceability matrix for Standard PRDs when there are multiple P0/P1 requirements, and always use it for Complex PRDs.

## Priority Decision Framework

Use P0/P1/P2 only with explicit rationale:

| Priority | Definition | Typical handling |
|---|---|---|
| P0 | Required for promised user value, legal/compliance safety, privacy, payment risk, data integrity, security, or launch viability. | Must ship or block the milestone. |
| P1 | Important for adoption, usability, operational efficiency, or measurable success, but not strictly launch-blocking. | Ship in milestone if feasible; explicit tradeoff needed if deferred. |
| P2 | Useful improvement, polish, or future optimization that does not block core value or safe operation. | Defer by default unless effort is very low. |

When assigning priority, consider user impact, business impact, risk reduction, dependency unblock, regulatory/security requirement, implementation cost, reversibility, and measurement value.

## Common Section Standards

### Functional Requirement Standard
Each important function should include purpose, affected surfaces, display rules, operation rules, validation rules, permission rules, data read/write rules, exception handling, dependencies, and acceptance criteria.

### Non-Functional Requirement Standard
Cover these when applicable: performance, reliability, security, privacy, compliance, accessibility, internationalization, compatibility, observability, rollout, gray release, kill switch, and rollback.

### Acceptance Criteria Standard
Acceptance criteria must be verifiable and linked to the requirement they validate:

| AC ID | Requirement ID | Scenario | Preconditions | Action | Expected result | Test notes |
|---|---|---|---|---|---|---|

### Event Tracking Standard
Tracking plans should be precise enough for implementation and analytics validation:

| Event ID | Event name | Trigger condition | Parameters | Type | Required | Privacy level | Dedup / timing rule | Purpose | Validation method |
|---|---|---|---|---|---|---|---|---|---|

### Risk Register Standard
- Standard PRD: include a simplified risk table with risk, impact, mitigation, and owner when known.
- Complex PRD: include the full register below.

| Risk ID | Risk | Severity | Probability | Trigger / signal | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|---|

## Review Verdict Thresholds

Use `references/prd-quality-checklist.md` as the source of truth for Ready / Needs revision / Not ready verdict thresholds, scoring anchors, blocker taxonomy, and final gate rules. Release blockers override average score.

## Final Quality Pass

Before returning any PRD, revision, or review, silently verify:

1. No empty table rows, bracket placeholders, or unexplained `TBD` values remain.
2. Confirmed facts, assumptions, recommendations, and open questions are not mixed.
3. P0 requirements have acceptance criteria, or the missing AC is called out as a blocker.
4. Legal, compliance, security, privacy, payment-risk, and data-integrity concerns are either resolved or explicitly marked as blockers/open questions.
5. Output length and depth match the routing decision; do not over-expand small or sparse requests.

## Output Modes

### Full PRD
Return a polished PRD using the chosen tier. Include confirmed facts, assumptions, and open questions near the top. Use `references/lite-prd-template.md` for Lite PRDs and `references/prd-template.md` for Standard or Complex PRDs.

### PRD Improvement
Return either a revised PRD section or a gap analysis plus rewritten sections. Prioritize fixes in this order: factual clarity, scope, P0 blockers, traceability, acceptance criteria, data/metrics, NFRs, risk/rollout.

### PRD Review
Return an audit-style review using the selected depth and verdict thresholds. Use `references/prd-quality-checklist.md` and `references/review-output-template.md`.

### Single Section Generation
Return only the requested section, but maintain PRD style and include IDs, assumptions, rules, or testability where relevant.

## Examples

Use `references/prd-examples.md` when output style is uncertain, when the user asks for examples, or when generating Chinese Lite PRDs, PRD reviews, Complex AI PRDs, single-section acceptance criteria, PRDs from meeting notes, Data / Tracking PRDs, Growth Experiment PRDs, Platform / API PRDs, Migration PRDs, Deep Audits, or Strategy Clarification Briefs.

## Resource Loading Rules

- Lite PRD only: load `references/prd-output-routing.md`, `references/lite-prd-template.md`, and `references/id-prefix-registry.md` if IDs are used; do not load the full template unless the user asks for a full document.
- Review only: load `references/prd-quality-checklist.md` and `references/review-output-template.md`; do not load `prd-template.md` unless rewriting a PRD section.
- Complex risk decision: load `references/prd-type-adapter.md` and `references/prd-quality-checklist.md`; apply the two-anchor rule from the type adapter when uncertain.
- Source-backed PRD: load `references/source-material-handling.md` before drafting.
- Regression or behavior validation: load `references/test-cases.md`.
- Organization-specific PRD conventions: load `references/organization-customization.md` when the user provides team templates, approval rules, analytics conventions, or launch gates.

## Resources

- `references/prd-output-routing.md`: source of truth for mode selection, output length, follow-up policy, and template-loading rules.
- `references/lite-prd-template.md`: compact eight-section PRD template for sparse input or small changes.
- `references/id-prefix-registry.md`: source of truth for allowed ID prefixes and entity separation.
- `references/prd-template.md`: Standard / Complex section inventory and full PRD structure.
- `references/prd-type-adapter.md`: source of truth for PRD type, product-shape modifiers, and Complex escalation anchors.
- `references/source-material-handling.md`: source-backed facts, connector/source handling, citation expectations, and contradiction handling.
- `references/organization-customization.md`: entry point for team-specific PRD lifecycle, approval, analytics, launch, and compliance conventions.
- `references/prd-quality-checklist.md`: source of truth for audit checklist, scoring dimensions, verdict thresholds, blocker taxonomy, and final gate.
- `references/review-output-template.md`: Quick, Standard, and Deep review output formats; references checklist verdict thresholds.
- `references/prd-examples.md`: representative input/output examples.
- `references/test-cases.md`: regression cases for routing, required elements, and prohibited output.

- `CHANGELOG.md`: version history and maintenance notes.
