# ID Prefix Registry

Use this registry whenever the PRD, review, examples, or traceability matrix needs stable IDs. Do not invent additional prefixes unless the user or organization explicitly provides a convention. Keep IDs numeric and stable by default, for example `FR-001`, `AC-001`, and `RISK-001`.

## Allowed prefixes

| Prefix | Entity type | Use for | Should appear in |
|---|---|---|---|
| `PRB-*` | Problem / opportunity | User problem, business problem, opportunity, pain point | problem statements, traceability matrix |
| `GOAL-*` | Goal / objective | User, business, product, or metric objective | goals, metrics, traceability matrix |
| `SC-*` | Scenario | User scenario, use case, journey moment | scenario tables, traceability matrix |
| `FR-*` | Functional requirement | Product or system behavior the team must build | requirement tables, AC mapping |
| `BR-*` | Business rule | Policy, eligibility, calculation, conflict, or decision rule | business rules, traceability matrix |
| `NFR-*` | Non-functional requirement | Performance, reliability, security, privacy, accessibility, compliance, rollout, observability | NFR section, traceability matrix |
| `PERM-*` | Permission requirement | Role, access, authorization, denied-state behavior | permission matrix, AC mapping |
| `DATA-*` | Data rule | Data source, retention, deletion, masking, lineage, validation, consistency | data rules, data governance, traceability matrix |
| `EVT-*` | Analytics event | Instrumentation event and event parameters | tracking spec only; link from requirements or ACs when needed |
| `METRIC-*` | Metric definition | Success, guardrail, dashboard, or validation metric | metric definitions, traceability matrix |
| `AC-*` | Acceptance criterion | Testable acceptance criterion tied to requirement/rule/event validation | AC section, QA handoff |
| `RISK-*` | Risk | Product, technical, legal, security, data, payment, rollout, or operational risk | risk register only; link from requirements when needed |
| `FACT-*` | Source-backed fact | Confirmed fact from source material, user input, or cited document | facts/assumptions/open questions section |
| `DEC-*` | Decision | Explicit stakeholder decision from source material | source synthesis, decision log |
| `ASM-*` | Assumption | Assumption used to proceed when information is missing | facts/assumptions/open questions section |
| `TBD-*` | Open question | Decision, fact, owner, metric, or rule that must be confirmed | open questions, blockers |
| `DEP-*` | Dependency | Design, engineering, data, legal, vendor, API, or operational dependency | dependencies section |
| `EDGE-*` | Edge case | Boundary or exception case that must be handled | edge cases section, AC mapping |
| `SRC-*` | Source note | Evidence item extracted from a source document, meeting note, ticket, or connector | source synthesis only |
| `TC-*` | Regression test case | Golden prompt or validation case for this skill itself | `test-cases.md` only; not PRD output |

## Entity separation rules

- `FR-*` is for buildable product or system behavior.
- `EVT-*` is not a requirement. Put it in the tracking spec, then link it from a requirement, AC, metric, or traceability row.
- `RISK-*` is not a requirement. Put it in the risk register, then link it from affected requirements or launch gates.
- `DATA-*`, `PERM-*`, `BR-*`, and `NFR-*` are rule or constraint entities. They may be validated by ACs and traced to goals, but do not rename them as `FR-*` unless they describe buildable behavior.
- `FACT-*`, `DEC-*`, `ASM-*`, `TBD-*`, and `SRC-*` are planning/evidence entities. Do not treat them as implementation requirements.
- `TC-*` is only for skill regression tests. Do not use it in PRD output.

## Format rules

- Use three-digit numeric suffixes by default: `FR-001`, `FR-002`, `AC-001`.
- Preserve existing IDs when improving an existing PRD unless they are invalid or duplicated.
- Do not use subtype prefixes like `SAFE-*`, `NFR-SEC-*`, or `EVT-REG-*` unless the organization has already defined them.
- When an output only needs a small number of bullets and no traceability, IDs may be omitted except for acceptance criteria, events, or risks that need cross-reference.
