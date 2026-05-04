# Source Material and Connector Handling

Use this reference whenever the user provides or references source material: meeting notes, transcripts, existing PRDs, research notes, competitive analysis, design docs, tickets/issues, support feedback, dashboards, internal documents, or files from connected sources.

## Intake order

1. Identify the source type and its reliability level.
2. Read the provided source material before drafting or reviewing.
3. Extract source-backed facts and decisions first.
4. Separate assumptions, inferred recommendations, unresolved contradictions, and open questions.
5. Choose the output route only after source extraction by applying the mechanical decision tree in `prd-output-routing.md`: Review, Single Section, Strategy Clarification Brief, Sparse fallback, Lite, Standard, or Complex.

## Source evidence map

Use `id-prefix-registry.md` for source-related prefixes such as `SRC-*`, `FACT-*`, `DEC-*`, `ASM-*`, and `TBD-*`. Use this structure internally, and include it in the PRD when source traceability materially affects scope, priority, risk, or review readiness.

| ID | Source / artifact | Source-backed fact or decision | Confidence | PRD impact |
|---|---|---|---|---|
| SRC-001 | Meeting notes / PRD / ticket / research | Confirmed detail | High / Medium / Low | Requirement, metric, risk, or open question affected |

## Fact and assumption separation

- Source-backed fact: explicitly present in the provided material.
- Decision: explicitly agreed, assigned, approved, or selected in the source material.
- Assumption: needed to draft but not confirmed by the source material.
- Inferred recommendation: a reasonable product recommendation derived from the source, but not yet a confirmed decision.
- Open question: unresolved, contradictory, missing, or decision-critical information.

Never present assumptions, inferred recommendations, metric baselines, compliance interpretations, security constraints, system behavior, legal requirements, or commercial targets as confirmed facts unless the source explicitly supports them.

## Connector-aware behavior

When connected-source content is available and the user asks to base work on it:

- Read the relevant document, ticket, transcript, or file before drafting.
- Cite or label source-backed facts when the final answer needs traceability.
- If source details conflict, preserve the conflict in Open Questions rather than silently choosing one.
- If a referenced source is inaccessible, say what could not be accessed and proceed only from available material with assumptions marked.
- Do not fabricate links, document titles, owners, metric values, launch dates, legal rules, or internal standards.

## Source-backed PRD output additions

For Standard or Complex PRDs derived from source material, include one of these depending on length:

### Compact source note

- Source-backed facts:
- Decisions:
- Assumptions:
- Open questions:

### Source traceability table

| PRD item | Source-backed basis | Assumption / gap | Impact if wrong |
|---|---|---|---|
| Requirement / metric / risk | Source detail | Unknown or inferred item | Design, engineering, QA, data, legal, launch impact |

## Contradiction handling

When sources disagree:

1. Do not resolve the contradiction silently.
2. State the conflicting claims neutrally.
3. Identify the decision owner if known.
4. Continue drafting only with a marked temporary assumption if the user requested a direct draft.

## Source quality notes

- User-provided meeting notes and transcripts are evidence, but may omit context or final decisions.
- Existing PRDs may be stale; use document content, not just metadata, to judge freshness.
- Support feedback is evidence of pain, not automatically evidence of priority or solution.
- Competitive analysis can inform options, but should not become a requirement unless the user confirms strategy.
- Analytics or dashboard screenshots should not be converted into exact metric targets unless the metric definition and baseline are explicit.

## Route-after-extraction rule

Do not decide Lite / Standard / Complex from a source-backed request until the source extraction is done. Source material can reveal hidden complexity, contradictions, missing decisions, or narrow scope that changes the route.
