# PRD Output Routing

Use this reference before writing when the input is sparse, ambiguous, high-risk, or likely to trigger overlong template output. If source material is present, extract source facts and decisions first, then use this file for routing.

## Mechanical decision tree

Use this order before applying the routing table:

1. If source material is present or referenced, load `source-material-handling.md`, read/extract facts and decisions, then route.
2. If the user asks for review/audit/readiness/gaps, choose PRD Review; select Quick / Standard / Deep after risk assessment.
3. If the user asks for a single section, output only that section.
4. If the input is strategy-only, output Product Strategy Clarification Brief.
5. If the input is sparse, choose Sparse fallback or Lite PRD.
6. If the input has problem, user, goal, and rough scope, choose Standard PRD.
7. Apply `prd-type-adapter.md`; upgrade to full Complex only when the two-anchor rule is met or user explicitly asks.
8. Apply table budget and final placeholder cleanup.

## Routing table

| User signal / input quality | Route | Load references | Target length | Required output |
|---|---|---|---|---|
| One-sentence idea with no background | Lite PRD | `lite-prd-template.md`; examples if style is uncertain | <= 1,200 Chinese characters or equivalent | Summary, assumptions/open questions, scope, 3-7 key requirements, main edge cases, 3-8 ACs, top risks |
| "简单 PRD", "快速写一版", "先出草案" | Lite PRD | `lite-prd-template.md` | <= 1,200 Chinese characters or equivalent | Same as above; do not include full 17-section template |
| Feature brief has user, problem, goal, and rough scope | Standard PRD | `prd-template.md`; `prd-type-adapter.md` if type-specific | 2,000-4,000 Chinese characters or equivalent for first draft | Default structure, selectively populated; simplified risk register |
| Meeting notes with decisions, owners, or multiple stakeholders | Standard PRD, Complex if high-risk | `prd-template.md`, examples | As needed, but avoid unpopulated sections | Decisions, open questions, requirements, traceability, ACs, risks |
| AI, compliance, payments, privacy, identity, minors, permissions, migration, platform, integration, or multi-system dependencies | Standard + targeted high-risk sections by default; full Complex only by two-anchor rule | `prd-template.md`, `prd-type-adapter.md`, quality checklist | Decision-critical depth first | `prd-type-adapter.md` is the source of truth. Escalate to full Complex only when at least two anchors apply or the user explicitly requests full Complex output. |
| User asks for only acceptance criteria, event tracking, user stories, scope, or edge cases | Single Section | relevant standard only | Section only | No full PRD; include assumptions if needed |
| User asks "review", "audit", "is this ready", or "what's missing" | PRD Review | `prd-quality-checklist.md`, `review-output-template.md` | Quick / Standard / Deep | Verdict, blockers, fixes, scores as appropriate |

## Output length and table budget

- Do not output a full Standard or Complex PRD from a single sentence unless the user explicitly asks for a full production PRD.
- Do not include empty sections, empty tables, blank rows, or placeholder labels in final output.
- If a section cannot be populated, either omit it or capture the missing decision in the open-questions table with impact.
- For Lite PRDs and Quick Reviews, default to compact bullets. Use tables only when there are 3 or more comparable items, stable IDs are needed, or QA / data / risk review clearly benefits from tabular structure.
- For Standard PRDs, include only tables that have meaningful content. A simplified table is better than a full empty template; bullets are acceptable for early drafts or low-risk sections.
- For Complex PRDs, include a Review First summary and all decision-critical high-risk controls; if the user did not ask for a complete expanded document, avoid expanding every low-signal table. Start with a structured v0.1 unless full expansion is requested.

## Product strategy boundary

If the input is mainly strategy, market positioning, business model, or commercial goal rather than concrete product behavior, route to a product strategy clarification brief instead of forcing a PRD. Include problem / opportunity hypothesis, target segment assumptions, strategy assumptions, product behavior implications, and validation questions.

Use `prd-examples.md` for the Strategy Clarification Brief example.

## Follow-up question policy

Ask at most 1-3 questions before producing output, and only when the answer changes direction, feasibility, major risk, or release readiness.

When the user asks for a draft immediately, proceed with assumptions. Put the unresolved decisions in this format:

| ID | Type | Open item | Current assumption | Decision impact | Suggested owner |
|---|---|---|---|---|---|
| TBD-001 | Open question |  |  |  |  |

## Template loading rules

- Treat templates as section inventories, not literal output scaffolds.
- Do not copy empty rows or placeholder text into the final PRD.
- Use `lite-prd-template.md` for sparse or small inputs.
- Use `prd-template.md` for Standard and Complex PRDs only when the user needs a full document or the context is rich enough.
- Use `review-output-template.md` for reviews instead of forcing PRD sections into a review answer.

## Complex route trigger anchors

Use `prd-type-adapter.md` as the source of truth for Complex escalation anchors. If only one high-risk signal exists and it is narrow and contained, choose Standard PRD plus targeted high-risk sections.

## Review depth routing

| Signal | Depth | Required contents |
|---|---|---|
| "quick review", short PRD, early draft | Quick | verdict, top blockers, top fixes, optional rewrite sample |
| normal PRD review | Standard | verdict, blockers, stage-gated fixes, scores, ambiguities, missing edge cases/NFRs, rewrites, deferred items |
| launch-critical, compliance/security/data-heavy, or user asks for deep audit | Deep audit | Standard review plus traceability audit, launch gate, risk register assessment, and cross-functional owner gaps |

## Product shape modifiers

Use `prd-type-adapter.md` as the source of truth for product shape modifiers. Do not duplicate or maintain separate shape-specific requirements here; apply that reference after choosing Lite, Standard, Complex, Review, or Single Section route.


## Sparse input fallback

When the input is too thin for even a Lite PRD, return this instead of forcing a PRD:

1. Draftable content
2. Assumptions
3. 3 highest-impact open questions
4. Highest-risk missing decisions
5. Recommended next PRD section to write

## Source material routing

When the input includes meeting notes, an existing PRD, user feedback, research notes, competitive analysis, design-copy notes, tickets, transcripts, or connected-source content, use `source-material-handling.md` before drafting or reviewing. Then choose Lite, Standard, Complex, Review, Single Section, or Strategy Clarification Brief.

## Length caps

| Route | Default length target |
|---|---|
| Sparse fallback | <= 800 Chinese characters or equivalent |
| Lite PRD | <= 1,200 Chinese characters or equivalent |
| Standard PRD | Prefer 2,000-4,000 Chinese characters or equivalent for first drafts |
| Complex PRD | Start with structured v0.1 unless full expansion is requested |
| Quick review | <= 1,000 Chinese characters or equivalent |

## Team maturity modifier

| Team context | Adaptation |
|---|---|
| Startup / early exploration | Reduce tables, highlight assumptions and next decisions. |
| Mature product team | Use Standard route with traceability for P0/P1 items. |
| Enterprise / regulated | Use full gate, owners, risk, NFR, compliance, and rollout controls. |
| Internal tooling | Emphasize workflow, permissions, audit logs, support, and operations. |
| Launch-critical | Emphasize blockers, rollback, observability, support readiness, and signoff. |

## Verdict localization

Use stable verdict enums for review state: `Ready`, `Needs revision`, `Not ready`. In Chinese output, show the localized meaning on first use: `Ready（可进入下一阶段）`, `Needs revision（需修改）`, `Not ready（暂不可进入下一阶段）`. Do not invent additional verdict states unless the user supplied a team-specific convention.
