# PRD Type Adapter

Use this reference when the requested PRD type changes what must be included. Pick the closest type. If multiple types apply, combine their required sections without duplicating content. If a high-risk signal is narrow and well-contained, use a Standard PRD with targeted high-risk sections instead of automatically escalating to full Complex PRD.

## Type selection

| PRD type | Use when | Additional required content |
|---|---|---|
| New feature PRD | A new user-facing or admin-facing capability is being introduced. | user value, entry points, happy path, empty/loading/error states, launch metrics |
| Redesign PRD | An existing flow, page, or capability is being materially changed. | current vs proposed behavior, migration impact, backward compatibility, success/failure comparison |
| Admin / back-office PRD | Internal operations, moderation, support, CRM, CMS, finance ops, or workflow tooling. | role matrix, audit logs, bulk actions, filters/search, permission errors, operational KPIs |
| Growth experiment PRD | The work is an A/B test, onboarding change, conversion lever, lifecycle message, or pricing experiment. | hypothesis, population, variants, guardrail metrics, sample/rollout, stop criteria, experiment readout |
| Data / tracking PRD | The main deliverable is data collection, analytics, dashboarding, or reporting. | event spec, parameter dictionary, metric formula, source of truth, validation method, privacy review |
| AI feature PRD | The product uses model output, ranking, generation, recommendations, automation, or classification. | model role, user control, confidence/error handling, safety policy, eval metrics, fallback, human review |
| Platform capability PRD | The work creates reusable infrastructure, API, SDK, shared service, permissions, or workflow primitives. | consumers, interface contract, versioning, migration, SLAs, observability, deprecation strategy |
| Integration PRD | The work connects external or internal systems, APIs, partners, or webhooks. | data contract, auth, retry/idempotency, rate limits, failure handling, reconciliation, monitoring |
| Migration / refactor PRD | The user-visible goal depends on moving data, replacing systems, or changing architecture. | current/new state, migration phases, compatibility, validation, rollback, data integrity checks |
| Regulated / high-risk PRD | Legal, compliance, security, privacy, payments, finance, healthcare, identity, or minors are involved. | compliance owner, legal review, data retention/deletion, audit trail, abuse prevention, release gate |

## Complex escalation anchors

This section is the source of truth for Complex escalation. Escalate to full Complex PRD only when at least two anchors apply, or when the user explicitly asks for full Complex output:

1. multiple systems, teams, vendors, or external partners are involved
2. launch failure can cause legal, compliance, security, privacy, payment-risk, or data-integrity harm
3. rollback, migration, reconciliation, or compatibility is non-trivial
4. acceptance requires cross-functional signoff
5. core behavior depends on AI/model output, automation, ranking, external integration, or asynchronous data flow

If a high-risk signal is narrow and well-contained, use Standard PRD with targeted high-risk sections. Do not escalate to full Complex solely because a request mentions AI, permissions, compliance, payments, migration, integration, or platform work.

## Conditional must-have sections

- If the PRD involves user interaction, include page states and interaction rules.
- If the PRD changes data collection or reporting, include event tracking, metric definitions, and validation method.
- If the PRD affects permissions, include a permission matrix and unauthorized behavior.
- If the PRD affects money, identity, safety, privacy, or compliance, include risk register, auditability, and compliance review owner.
- If the PRD affects multiple systems, include dependencies, interface contracts, failure modes, and rollback.
- If the PRD ships behind a feature flag, include rollout cohort, monitoring window, and kill-switch behavior.


## Product shape modifiers

This section is the source of truth for product shape modifiers. Apply these modifiers in addition to the PRD type. They help tailor the PRD to delivery context and reduce generic output.

| Product shape | Add or emphasize |
|---|---|
| B2B SaaS | account/workspace model, roles and permissions, admin controls, audit logs, plan/billing effects, customer rollout |
| Consumer app | onboarding, empty states, notifications, platform/app-version behavior, privacy consent, retention and activation metrics |
| Internal tool | operational workflow, bulk actions, filters/search, escalation path, support runbook, role-based access, auditability |
| Payments / finance | identity/KYC, compliance owner, audit trail, reconciliation, risk controls, rollback constraints, customer notification |
| AI copilot / automation | model role, user control, confidence/fallback, evals, safety rules, human review, transparency copy, abuse cases |
| Developer product / API | API contract, auth, rate limits, versioning, error model, SDK/docs, backwards compatibility, deprecation plan |
| Data platform | data dictionary, lineage, quality checks, source of truth, privacy/sensitivity, retention/deletion, dashboard validation |

## Permission matrix pattern

| Role | Can view | Can create | Can edit | Can delete | Can approve | Denied-state behavior |
|---|---|---|---|---|---|---|

## Data dictionary pattern

| Field | Definition | Source | Type | Required | Retention | Sensitivity | Consumer |
|---|---|---|---|---|---|---|---|

## Experiment pattern

| Item | Definition |
|---|---|
| Hypothesis |  |
| Target population |  |
| Control |  |
| Variant(s) |  |
| Primary metric |  |
| Guardrail metrics |  |
| Exclusion rules |  |
| Stop criteria |  |
| Readout owner |  |

## AI feature pattern

| Area | Required detail |
|---|---|
| Model role | What the model decides, suggests, ranks, or generates |
| User control | Accept, reject, edit, undo, report, or override behavior |
| Failure modes | hallucination, irrelevant output, unsafe output, low confidence, latency, unavailability |
| Evaluation | offline eval, online metric, human review, sample quality checks |
| Safety | policy constraints, sensitive data handling, abuse cases, fallback behavior |
| Transparency | user-facing copy that explains AI involvement when needed |
