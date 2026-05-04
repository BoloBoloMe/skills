# PRD Writer Regression Test Cases

Use these cases to validate routing, required elements, and prohibited output after editing the skill. These are golden prompt checks, not executable unit tests. A future executable harness can convert each row into prompt + assertions.

## Golden prompt matrix

| Case ID | Golden prompt | Expected route | Must include | Must not include |
|---|---|---|---|---|
| TC-001 Sparse idea | `给订单列表加一个批量导出按钮。` | Lite PRD or Sparse fallback depending on requested depth | assumptions or open questions; <= 8 numbered sections; core requirements; ACs if enough behavior is inferable | full 17-section PRD; empty tables; bracket placeholders |
| TC-002 Strategy-only | `我们要进军高端企业市场，提高 ARR，帮我写 PRD。` | Product Strategy Clarification Brief | opportunity hypothesis; target segment assumptions; validation questions before PRD | invented functional requirements; fake roadmap; fake ARR baseline |
| TC-003 AI feature | `Write a PRD for an AI assistant that summarizes tickets and suggests replies.` | Standard + targeted high-risk sections by default; Complex only if >= 2 anchors apply or user explicitly asks | model role; human control; safety/fallback; eval metrics; no auto-send assumption marked as assumption if not sourced; route rationale | auto-send behavior as fact; missing safety/fallback; `SAFE-*` prefix; full Complex caused only by the AI label |
| TC-004 Narrow permission change | `Allow workspace admins to export audit logs.` | Standard PRD + targeted permission/security sections | permission matrix; denied-state behavior; audit/logging; ACs | full Complex PRD unless >=2 anchors apply; legal approval claim without source |
| TC-005 Short PRD review | `Review: Add phone signup and improve conversion.` | Quick review or Quick/Standard hybrid | verdict; top blockers; minimal fixes | heavy traceability audit; full PRD rewrite unless requested |
| TC-006 Payment automation | `Deep audit this PRD for automatic refunds.` | Deep audit | payment-risk blocker checks; reconciliation; rollback; owner gaps; launch gate | Ready verdict if reconciliation/security/data integrity unresolved |
| TC-007 Data tracking only | `只补注册漏斗埋点，包括打开注册页、提交手机号、验证码通过、注册成功。` | Single Section or Data / tracking PRD | event spec; parameter privacy; validation method; ACs linked as event validation | treating `EVT-*` rows as functional requirements |
| TC-008 Meeting notes | `Support says users cannot find refund status. Eng says status exists but ETA does not. Data wants click tracking.` | Standard PRD | FACT/DEC/ASM/TBD separation; no ETA in MVP unless sourced; event tracking | source-backed facts mixed with recommendations; invented ETA |
| TC-009 Source contradiction | `Doc A says export limit is 5,000; support notes say users need 20,000.` | Source synthesis then PRD or review | contradiction as open question; decision impact; owner suggestion | silently choosing one limit as fact |
| TC-010 Migration/refactor | `Replace the legacy search index while keeping behavior unchanged.` | Standard + migration sections or Complex if >=2 anchors apply | current/new state; validation; rollback; DATA rules; risk register | `RISK-*` inside functional requirement table; no rollback path |

## Required global checks

- Source-backed requests extract facts and decisions before route selection.
- Review First appears in Complex PRDs, launch-critical/review-oriented Standard PRDs, or when requested; it does not appear in Lite PRDs.
- No final output contains placeholder labels for owner, date, description, product name, or blank table rows.
- No final output contains undefined prefixes such as `SAFE-*` or subtype IDs such as `NFR-SEC-*` unless the user supplied that convention.
- Lite PRD outputs use no more than 8 numbered sections.
- Quick reviews prefer bullets; tables are used only when they improve comparison or traceability.
- `EVT-*` appears in tracking/event specs, not as a functional requirement row.
- `RISK-*` appears in risk registers, not as a functional requirement row.
- Full Complex PRD is used only when the two-anchor rule in `prd-type-adapter.md` is met or the user explicitly requests full Complex output.

## Suggested manual evaluation rubric

| Check | Pass condition |
|---|---|
| Route correctness | Output route matches expected route and explains assumptions when route is ambiguous. |
| Entity separation | Requirements, events, metrics, risks, facts, assumptions, and open questions are not mixed. |
| Table budget | Lightweight cases use bullets by default and only use tables for clear review value. |
| Safety of facts | Unsourced exact data, compliance rules, system constraints, and owners are not invented. |
| Final cleanup | No empty scaffold, placeholder, or unexplained TBD remains. |
