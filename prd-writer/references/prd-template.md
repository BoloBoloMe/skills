# PRD Template v4

Use this as a section inventory for Standard and Complex PRDs, not as a literal final-output scaffold. Match the user's language. For Chinese requests, translate headings into professional Chinese PRD terms and keep ID formats stable. `Review First` is mandatory for Complex PRDs, optional for Standard PRDs when launch-critical, review-oriented, or user-requested, and omitted for Lite PRDs.

## Safe-use rules

- Do not copy this template wholesale into the final answer.
- Do not output unknown fields, empty tables, blank rows, blank owners, blank dates, blank field names, or placeholder labels.
- Prefer schema descriptions or filled mini-examples over empty scaffold tables.
- If information is unknown, omit the field or move it into Open Questions with decision impact.
- Only include sections that can be meaningfully populated, or explicitly capture missing decisions in the assumptions/open-questions table with decision impact.
- For sparse input or small changes, use `lite-prd-template.md` instead of this file.
- For review tasks, use `review-output-template.md` instead of this PRD template.
- Before final delivery, reduce tables to rows that add review value. Prefer bullets for early drafts unless stable IDs, QA validation, data validation, or risk review benefit from a table.
- Use `id-prefix-registry.md` for all ID prefixes. Keep `EVT-*` in event specs and `RISK-*` in risk registers; requirement tables may link to events or risks but should not use them as requirement rows.

## How to use the schemas below

Each section below gives either:

1. **Include when** guidance: when the section belongs in the output.
2. **Schema**: fields that may be included when known.
3. **Filled mini-example**: one realistic row or bullet that demonstrates the intended detail level.

Do not output the schema itself unless the user asks for a template. Convert it into a populated PRD using only known facts, explicit assumptions, and useful open questions.

---

# PRD: actual product or feature name

## Review First

**Include when:** Complex PRD, launch-critical Standard PRD, review-oriented draft, or explicit user request. Do not include in Lite PRDs.

**Schema:** launch decision/current recommendation; P0 scope; key unresolved decisions; top risks; required reviewers; next stage gate.

**Mini-example:**

- Launch decision: Needs revision before development because refund status copy and API enum mapping are unresolved.
- P0 scope: Show current refund status on order detail when a refund exists.
- Required reviewers: Product, Engineering, QA, Data, Support.
- Next stage gate: Design review after status enum and copy are confirmed.

## 0. Document Information

**Include when:** the PRD needs versioning, review ownership, lifecycle status, or cross-functional coordination.

**Schema:**

| Field | Use when | Example or rule |
|---|---|---|
| Version | The PRD will be reviewed or revised | v0.1 for first draft; v1.0 for approved baseline |
| Author | A real owner is known | Product manager name; omit if unknown |
| Created | A real creation date is needed | Use an actual date such as 2026-05-04; omit if unknown |
| Last updated | The document has multiple revisions | Use the actual update date only |
| Status | Lifecycle matters | Draft, In review, Approved, Launched |
| PRD tier | Routing decision matters | Standard or Complex |
| PRD type | Product-type rules apply | New feature, Growth experiment, Data, AI, Platform, Integration, Migration, Regulated |
| Stakeholders | Cross-functional review is required | Product, Design, Engineering, QA, Data, Operations, Legal, Security |

### Version History

**Include when:** there are real revisions to track.

**Schema:** version; date; owner; change summary.

**Mini-example:**

| Version | Date | Owner | Change |
|---|---|---|---|
| v0.2 | 2026-05-04 | Product owner | Added refund API enum assumptions and launch guardrails |

## 0.1 Confirmed Facts, Assumptions, and Open Questions

**Include when:** almost always. Keep facts, decisions, assumptions, dependencies, and open questions separate.

**Schema:** ID; type; content; current handling; decision impact; owner or confirmer if known.

**Mini-example:**

| ID | Type | Content | Current handling | Impact | Owner / confirmer |
|---|---|---|---|---|---|
| FACT-001 | Confirmed fact | Refund status is available from the order API | Use status in MVP | Enables refund progress module | Engineering |
| ASM-001 | Assumption | Refund ETA is unavailable for MVP | Do not show ETA copy | Prevents misleading user expectation | Product |
| TBD-001 | Open question | Final status enum and display copy are not confirmed | Block UI copy finalization | Affects QA cases and localization | Product + Engineering |

## 0.2 Executive Summary

**Include when:** always for Standard and Complex PRDs.

**Schema:** problem; proposed solution; primary users; expected impact; major risks or decisions; launch recommendation.

**Mini-example:**

- Problem: Users contact support because refund status is difficult to find after submitting a refund request.
- Proposed solution: Add a refund progress module to order detail when an order has an active or completed refund.
- Primary users: Consumers checking refund progress and support agents reducing status-related tickets.
- Expected impact: Lower refund-status support contacts and improve user self-service.
- Major decision: Final refund status enum and user-facing copy must be confirmed before development.

## 1. Background, Problem, and Evidence

### 1.1 Current Situation

**Schema:** current workflow; user pain; operational pain; existing workaround; known constraints.

### 1.2 User Problem / Opportunity

**Schema:** problem ID; affected user or segment; scenario; pain point or opportunity; evidence source; severity.

**Mini-example:**

| Problem ID | User / segment | Scenario | Pain point / opportunity | Evidence source | Severity |
|---|---|---|---|---|---|
| PRB-001 | Consumer with an active refund | Opens order detail after requesting refund | Cannot tell whether refund is pending, approved, or completed | Support ticket summary | High |

### 1.3 Business Impact

**Schema:** support cost, conversion, retention, compliance risk, operational efficiency, customer trust, or other business impact. Do not invent baselines.

### 1.4 Evidence and Source Notes

**Schema:** source; finding; confidence; limitation.

**Mini-example:**

| Source | Finding | Confidence | Limitation |
|---|---|---|---|
| Support meeting notes | Refund status confusion is a recurring user complaint | Medium | Ticket volume baseline was not provided |

## 2. Goals and Success Metrics

### 2.1 User Goals

**Schema:** what the user can understand, complete, avoid, or recover from.

### 2.2 Business Goals

**Schema:** measurable business outcome or directional business improvement. Mark baseline gaps as open questions.

### 2.3 Product Goals

**Schema:** goal ID; goal; related problem; success metric; target or direction; observation window.

**Mini-example:**

| Goal ID | Goal | Related problem | Success metric | Target / direction | Observation window |
|---|---|---|---|---|---|
| GOAL-001 | Help users self-serve refund progress | PRB-001 | Refund-status support contact rate | Decrease after launch | 14 days after rollout |

### 2.4 Guardrail Metrics

**Schema:** metric; why it matters; alert threshold or concern.

**Mini-example:**

| Metric | Why it matters | Alert threshold / concern |
|---|---|---|
| Refund page API error rate | Failed status loading can increase support contacts | Alert if materially higher than order-detail baseline |

## 3. Non-Goals and Scope Boundaries

### 3.1 In Scope

**Schema:** scope ID; item; priority; rationale.

**Mini-example:**

| Scope ID | Item | Priority | Rationale |
|---|---|---|---|
| SCOPE-001 | Display current refund status on order detail | P0 | Core user value and support reduction |

### 3.2 Out of Scope / Non-Goals

**Schema:** item; reason; future consideration.

**Mini-example:**

| Item | Reason | Future consideration |
|---|---|---|
| Refund ETA prediction | ETA is not available from API for MVP | Revisit after backend can provide reliable ETA |

## 4. Product Type, Users, Roles, and Scenarios

### 4.1 Product Type Notes

Use `references/prd-type-adapter.md` to add required sections for the selected PRD type.

### 4.2 User Roles

**Schema:** role ID; role; description; core need; permission level.

**Mini-example:**

| Role ID | Role | Description | Core need | Permission level |
|---|---|---|---|---|
| ROLE-001 | Consumer | Buyer viewing personal orders | Understand refund progress without contacting support | Own-order access only |

### 4.3 Scenarios

**Schema:** scenario ID; scenario; user motivation; trigger; expected outcome; priority.

**Mini-example:**

| Scenario ID | Scenario | User motivation | Trigger | Expected outcome | Priority |
|---|---|---|---|---|---|
| SC-001 | User checks refund after submitting a request | Confirm refund state | Opens order detail with active refund | Sees current refund status and next step copy | P0 |

### 4.4 User Stories

**Schema:** role; capability; value. Use only when it clarifies scenario value.

**Mini-example:**

- As a consumer, I want to see the current refund status on order detail so that I do not need to contact support for basic progress updates.

## 5. Requirements Scope and Priority

### 5.1 Functional Requirements

**Schema:** requirement ID; module; requirement; priority; priority rationale; related scenario; notes; optional related event/risk IDs.

**Mini-example:**

| Requirement ID | Module | Requirement | Priority | Priority rationale | Related scenario | Notes |
|---|---|---|---|---|---|---|
| FR-001 | Order detail | Show refund progress module when an order has an active or completed refund | P0 | Required for promised user value | SC-001 | Link to EVT-001 for impression tracking |

### 5.2 Business Rules

**Schema:** rule ID; rule; applies to; priority or conflict handling; related requirement.

**Mini-example:**

| Rule ID | Rule | Applies to | Priority / conflict handling | Related requirement |
|---|---|---|---|---|
| BR-001 | Do not display refund ETA unless the backend provides a confirmed ETA field | Refund progress module | Prevents misleading copy | FR-001 |

### 5.3 Data Rules

**Schema:** data rule ID; object or field; read rule; write rule; retention or deletion rule; source of truth; related requirement.

**Mini-example:**

| Data Rule ID | Object / field | Read rule | Write rule | Retention / deletion | Source of truth | Related requirement |
|---|---|---|---|---|---|---|
| DATA-001 | refund_status | Read from order API response | No client-side write | Follow existing order data retention | Order service | FR-001 |

## 6. Business Process, Flows, and State Transitions

### 6.1 Main Flow

**Schema:** ordered steps from entry point to completion. Include only real steps.

**Mini-example:**

1. User opens order detail.
2. System checks whether the order has refund data.
3. If refund data exists, system displays refund progress module with current status and explanatory copy.
4. User can read status or tap help entry if further action is needed.

### 6.2 Branch Flows

**Schema:** branch ID; trigger; system behavior; user-visible result; related requirement.

**Mini-example:**

| Branch ID | Trigger | System behavior | User-visible result | Related requirement |
|---|---|---|---|---|
| BRANCH-001 | Order has no refund | Hide refund progress module | Order detail remains unchanged | FR-002 |

### 6.3 State Transition

**Schema:** current state; trigger or condition; system behavior; next state; event or log.

**Mini-example:**

| Current state | Trigger / condition | System behavior | Next state | Event / log |
|---|---|---|---|---|
| Refund pending | API returns approved status | Update module copy and progress indicator | Refund approved | EVT-002 status_viewed |

## 7. Functional Details and Business Rules

### 7.1 Functional module details

**Include when:** a module requires detailed display, operation, validation, or exception rules.

#### 7.1.1 Purpose and User Value

**Schema:** what the module does and why the user or business needs it.

#### 7.1.2 Display Rules

**Schema:** when the component appears, hides, changes copy, disables controls, or shows warnings.

#### 7.1.3 Operation Rules

**Schema:** action; preconditions; system response; failure handling; related AC.

**Mini-example:**

| Action | Preconditions | System response | Failure handling | Related AC |
|---|---|---|---|---|
| Open order detail | User owns the order and refund data exists | Render refund progress module above support entry | If refund API fails, hide module and show fallback support entry | AC-001 |

#### 7.1.4 Validation Rules

**Schema:** field or object; validation rule; error copy; blocking behavior.

**Mini-example:**

| Field / object | Validation rule | Error copy | Blocking? |
|---|---|---|---|
| refund_status | Must map to an approved display state | Show generic refund-in-progress copy when enum is unknown | Non-blocking for page load |

#### 7.1.5 Exception Rules

**Schema:** exception; trigger; system handling; user copy; recovery path.

**Mini-example:**

| Exception | Trigger | System handling | User copy | Recovery path |
|---|---|---|---|---|
| Unknown refund status enum | API returns unmapped status | Use generic status display and log enum value | Your refund is being processed | Add enum mapping after backend confirmation |

## 8. Page, Interaction, and State Notes

### 8.1 Affected Surfaces

**Schema:** surface; entry point; user action; notes.

**Mini-example:**

| Surface | Entry point | User action | Notes |
|---|---|---|---|
| Order detail page | Orders list or notification deep link | View refund status | Module appears only for orders with refund data |

### 8.2 Interaction Notes

**Schema:** click behavior, disabled behavior, copy behavior, accessibility behavior, and navigation behavior.

### 8.3 Page / Component States

**Use a state table only when at least three states need explicit behavior. Otherwise use bullets.**

**Schema:** state; visual behavior; user actions; system behavior; copy.

**Filled mini-example:**

| State | Visual behavior | User actions | System behavior | Copy |
|---|---|---|---|---|
| Default | Refund module shows current status and progress label | User can read status or open help | Data is read from order API | Refund is being processed |
| Empty | Refund module is hidden | No refund-specific action | System confirms no refund data exists | No refund copy shown |
| Failure | Module is hidden and support entry remains visible | User can contact support | API failure is logged for monitoring | Need help with this order? |

## 9. Permissions, Data Governance, and Auditability

### 9.1 Permission Matrix

**Schema:** role; allowed actions; denied-state behavior. Include create/edit/delete/approve columns only when those actions exist.

**Mini-example:**

| Role | Allowed actions | Denied-state behavior |
|---|---|---|
| Consumer | View refund status for own orders | Hide module for orders the user cannot access |
| Support agent | View refund status for assigned support cases | Show permission error if account scope does not match |

### 9.2 Audit and Logging

**Schema:** action; whether a log is required; log fields; retention rule; reviewer or consumer.

**Mini-example:**

| Action | Log required? | Log fields | Retention | Reviewer / consumer |
|---|---|---|---|---|
| User views refund module | Yes | user_id hash, order_id hash, refund_status, timestamp | Follow analytics retention policy | Data team |

### 9.3 Privacy / Sensitive Data

**Schema:** data; sensitivity; collection purpose; retention; deletion or masking rule; review owner.

**Mini-example:**

| Data | Sensitivity | Collection purpose | Retention | Deletion / masking | Review owner |
|---|---|---|---|---|---|
| order_id | Internal identifier | Join refund module events to order context | Follow existing analytics retention | Hash or tokenize in analytics | Privacy owner |

## 10. Edge Cases and Exception Handling

**Schema:** case ID; scenario; trigger; expected handling; user impact; related AC.

**Mini-example:**

| Case ID | Scenario | Trigger | Expected handling | User impact | Related AC |
|---|---|---|---|---|---|
| EDGE-001 | Refund status changes after page load | API status updates while user is viewing order detail | Refresh status on next page load or manual refresh | User may see stale status until refresh | AC-004 |

## 11. Non-Functional Requirements

**Do not output a full generic NFR checklist. Include only NFRs relevant to the product risk, launch gate, or user experience.**

**Schema:** NFR ID; area; requirement; target or rule; validation method; owner if known.

**Filled mini-examples:**

| NFR ID | Area | Requirement | Target / rule | Validation method | Owner |
|---|---|---|---|---|---|
| NFR-001 | Performance | Refund module must not materially slow order detail rendering | Keep page load within existing order-detail performance budget | Compare before/after page performance metrics | Engineering |
| NFR-002 | Reliability | Refund status fetch failure must not block order detail page | Hide module and keep core order detail usable | Simulate API timeout and verify fallback behavior | Engineering |
| NFR-003 | Privacy | Analytics events must not expose raw order identifiers | Hash or tokenize order identifiers before analytics ingestion | Data QA validates event payload sample | Data / Privacy |

## 12. Data Tracking, Analytics, and Metric Definitions

### 12.1 Event Tracking

**Schema:** event ID; event name; trigger condition; parameters; type; required flag; privacy level; dedup or timing rule; purpose; validation method.

**Mini-example:**

| Event ID | Event name | Trigger condition | Parameters | Type | Required | Privacy level | Dedup / timing rule | Purpose | Validation method |
|---|---|---|---|---|---|---|---|---|---|
| EVT-001 | refund_progress_impression | Refund module becomes visible on order detail | order_id_hash, refund_status, user_role | impression | Yes | Internal identifier, hashed | Emit once per page load | Measure module reach | Validate event in staging and analytics table |

### 12.2 Metric Definitions

**Schema:** metric ID; metric; formula; source event or table; segment; observation window; owner if known.

**Mini-example:**

| Metric ID | Metric | Formula | Source event / table | Segment | Observation window | Owner |
|---|---|---|---|---|---|---|
| METRIC-001 | Refund-status support contact rate | Refund-status contacts divided by orders with refunds | Support tickets and order refund table | Orders with active refunds | 14 days after rollout | Support analytics |

### 12.3 Dashboard / Reporting

**Schema:** dashboard or report; owner; users; refresh cadence; launch validation need.

**Mini-example:**

| Dashboard / report | Owner | Users | Refresh cadence | Launch validation need |
|---|---|---|---|---|
| Refund progress adoption dashboard | Data owner | Product, Support, Engineering | Daily | Confirm impressions, click-through, and support contact trend |

## 13. Acceptance Criteria

**Schema:** AC ID; requirement ID; scenario; preconditions; action; expected result; test notes.

**Mini-example:**

| AC ID | Requirement ID | Scenario | Preconditions | Action | Expected result | Test notes |
|---|---|---|---|---|---|---|
| AC-001 | FR-001 | User views order with active refund | User owns the order and refund_status is pending | Open order detail | Refund progress module is visible with pending-status copy | Verify module visibility and copy mapping |

## 14. Requirements Traceability Matrix

**Use when:** multiple P0/P1 requirements exist, or always for Complex PRDs.

**Schema:** problem; goal; scenario; requirement ID; rule or NFR ID; AC ID; event ID; success metric.

**Mini-example:**

| Problem | Goal | Scenario | Requirement ID | Rule / NFR ID | AC ID | Event ID | Success metric |
|---|---|---|---|---|---|---|---|
| PRB-001 | GOAL-001 | SC-001 | FR-001 | BR-001 / NFR-002 | AC-001 | EVT-001 | METRIC-001 |

## 15. Dependencies, Risks, Rollout, and Rollback

### 15.1 Dependencies

**Schema:** dependency ID; dependency; type; owner if known; needed by; risk if delayed.

**Mini-example:**

| Dependency ID | Dependency | Type | Owner | Needed by | Risk if delayed |
|---|---|---|---|---|---|
| DEP-001 | Confirmed refund status enum mapping | Engineering | Order API owner | Design finalization and QA test cases | Incorrect copy or missing edge cases |

### 15.2 Risk Register

**Schema:** risk ID; risk; severity; probability; trigger or signal; impact; mitigation; owner if known; status.

**Mini-example:**

| Risk ID | Risk | Severity | Probability | Trigger / signal | Impact | Mitigation | Owner | Status |
|---|---|---|---|---|---|---|---|---|
| RISK-001 | Unknown refund status displays misleading copy | High | Medium | API returns unmapped enum | User trust and support contacts worsen | Use generic fallback copy and log unknown enum | Product + Engineering | Open |

### 15.3 Launch and Gray Release

**Schema:** launch method; cohort; monitoring window; success gate; stop or rollback trigger; rollback owner; communication plan. Omit unknown fields or move them to Open Questions.

**Mini-example:**

| Item | Plan |
|---|---|
| Launch method | Feature flag to 10 percent of eligible traffic before full rollout |
| Monitoring window | First 48 hours for errors; 14 days for support contact trend |
| Stop / rollback trigger | Refund module API error rate materially exceeds baseline |
| Communication plan | Inform support team before rollout with status-copy reference |

## 16. Cross-Functional Review Checklist

**Use when:** Standard or Complex PRD requires explicit signoff. Do not include blank reviewer rows.

**Schema:** function; real reviewer or required owner role; must-review areas; status; notes.

**Mini-example:**

| Function | Reviewer / owner role | Must review | Status | Notes |
|---|---|---|---|---|
| Product | Product owner | goals, scope, priority, copy decisions | Pending | Confirm enum-to-copy mapping |
| Engineering | Order API owner | feasibility, dependencies, fallback behavior | Pending | Confirm status enum and error handling |
| QA | QA owner | ACs, edge cases, regression risk | Pending | Build tests from AC and EDGE rows |
| Data | Data owner | events, metrics, dashboard validation | Pending | Validate EVT-001 and METRIC-001 |

## 17. Appendix / Links

**Include only real links or known references. Do not output empty link bullets.**

**Schema:** design file; API/interface documentation; data dashboard; research/source notes; related documents.

**Mini-example:**

- Source notes: Support meeting summary from 2026-05-01.
- API reference: Order API refund status enum documentation, if available to the user.

---

## Chinese heading guide

Use these localized headings when the user writes in Chinese:

| English | Chinese |
|---|---|
| Document Information | 文档信息 |
| Confirmed Facts, Assumptions, and Open Questions | 已确认事实、假设与待确认事项 |
| Executive Summary | 执行摘要 |
| Background, Problem, and Evidence | 背景、问题与依据 |
| Goals and Success Metrics | 目标与成功指标 |
| Non-Goals and Scope Boundaries | 非目标与范围边界 |
| Product Type, Users, Roles, and Scenarios | 产品类型、用户角色与场景 |
| Requirements Scope and Priority | 需求范围与优先级 |
| Business Process, Flows, and State Transitions | 业务流程与状态流转 |
| Functional Details and Business Rules | 功能详情与业务规则 |
| Page, Interaction, and State Notes | 页面、交互与状态说明 |
| Permissions, Data Governance, and Auditability | 权限、数据治理与可审计性 |
| Edge Cases and Exception Handling | 边界条件与异常处理 |
| Non-Functional Requirements | 非功能需求 |
| Data Tracking, Analytics, and Metric Definitions | 数据埋点、分析与指标定义 |
| Acceptance Criteria | 验收标准 |
| Requirements Traceability Matrix | 需求追踪矩阵 |
| Dependencies, Risks, Rollout, and Rollback | 依赖、风险、上线与回滚 |
| Cross-Functional Review Checklist | 跨职能评审清单 |
| Appendix / Links | 附录 / 链接 |
