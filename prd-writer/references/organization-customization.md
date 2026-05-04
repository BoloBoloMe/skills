# Organization Customization Entry Point

Use this file as the place to add team-specific PRD standards. If no organization-specific standard is supplied by the user, keep outputs generic and do not invent process owners, approval stages, metric names, or compliance rules.

## Customization areas

| Area | Examples of team-specific rules to add |
|---|---|
| PRD lifecycle | Draft, review, approved, in development, launched; required gates for each stage |
| Approval owners | Product, design, engineering, QA, data, security, legal, compliance, operations |
| Issue tracker mapping | Jira / Linear fields, epic/story/task mapping, priority labels, release labels |
| Experiment platform | Required hypothesis, sample sizing, guardrails, ramp plan, readout owner |
| Analytics conventions | Event naming, parameter naming, privacy levels, dashboard ownership, validation queries |
| Security and privacy | Data classification, retention/deletion, PII handling, audit log requirements |
| Launch management | Feature flag conventions, gray release policy, rollback criteria, monitoring windows |
| Design and QA handoff | Required design links, accessibility checks, QA test case format, regression scope |

## Use rules

- If the user provides an organization template, apply it after choosing the output route.
- If organization rules conflict with generic PRD guidance, follow the organization rule and note the override when it matters.
- If an organization rule is missing, mark the relevant owner or policy as `TBD-*` instead of inventing it.
- Do not claim legal, security, or compliance approval unless the source material explicitly says it is approved.

## Optional organization profile pattern

```markdown
# Organization PRD Profile

## Lifecycle states

## Required reviewers by PRD type

## Event naming and analytics validation

## Experiment standards

## Security / privacy / compliance gates

## Launch and rollback gates

## Issue tracker mapping
```
