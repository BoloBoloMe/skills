---
name: scheme-review-brief-en
description: generate a complete english solution review brief from human-in-loop-planning and human-in-loop-execution asset packages. use when the user provides hilp or hile planning, execution, handoff, manifest, review-pack, runbook, verification, audit, or related assets and asks for a final solution review brief, review memo, meeting brief, or decision-readiness summary. this skill reads the asset package thoroughly, preserves fact and source traceability, fills every section of the english review template, marks missing evidence explicitly, and outputs only the final brief content.
---

# English Solution Review Brief Generator

## Objective

Turn user-provided `human-in-loop-planning` and `human-in-loop-execution` asset packages into a complete English Solution Review Brief that can be used directly in a review meeting. The output must be the final brief body only, with no process notes, plan, or explanatory preface.

## Role Boundary

This skill only interprets assets and generates a review brief. Do not start a new HILP/HILE protocol, and do not create or modify planning assets, execution assets, manifests, approval records, handoff records, runbooks, plans, or verification records.

When the `human-in-loop-planning` and `human-in-loop-execution` skills are available and their semantics are needed, read each relevant `SKILL.md` first, then read the shortest necessary reference path. Use those skills only to interpret asset structure, lifecycle state, approval/confirmation semantics, versioning, boundaries, gates, and verification evidence. Do not escalate this task into a new planning or execution workflow.

## Input

The user will usually provide one or more HILP/HILE asset packages, folders, archives, links, or pasted documents. Identify and read as many of these assets as available:

- HILP planning manifest, phase-01 requirements/facts, phase-02 design-choice, phase-03 implementation-blueprint, phase-04 reapproval, phase-05 execution-handoff, review-pack, audit trail, and archive index.
- HILE execution manifest, handoff intake, runbook, plan, execution unit, allowed files, ledger, unit summary, verification record, completion review, and failure forensics review.
- Supporting materials such as background notes, design discussions, requirements, decision records, test results, logs, changed-file lists, and human reviewer notes.

When the package is large, prioritize the manifest/current pointers, review packs, approved design and blueprint, current execution handoff, execution plan/runbook, verification records, and completion/failure reviews. Do not rely only on filenames or metadata; use document content to confirm facts, versions, and states.

## Workflow

1. Inventory the asset package and create a mental source index: filename, asset type, version, lifecycle state, whether it is current, and its relationship to the solution.
2. Read the planning assets using HILP semantics: background, goals, facts, assumptions, in-scope items, out-of-scope items, solution choice, alternatives, implementation blueprint, dependencies, and re-review conditions.
3. Read the execution assets using HILE semantics: execution tier, runbook/plan, affected files or modules, execution units, allowed-files boundary, verification evidence, failure/blocker/completion state.
4. Cross-check planning against execution: confirm whether the execution plan still matches the approved design and blueprint; flag new facts, boundary changes, changed validation criteria, blockers, and re-review triggers.
5. Map evidence into the brief template. Fill every section. If information is missing, write “no explicit evidence found in the asset package” and state the impact instead of leaving placeholders.
6. Output the final English brief. Do not output the analysis process, do not ask the user for additional confirmation, and do not add extra text before or after the brief.

## Extraction Rules

- “Key facts” must be source-backed facts that affect solution choice or execution boundaries.
- “Current assumptions” must be unproven premises that the solution depends on.
- “In scope” and “Out of scope / unchanged items” should come first from the HILP blueprint, handoff, allowed files, prohibited/stop conditions, and review packs.
- “Current solution and key tradeoffs” should come first from the design-choice, implementation-blueprint, reapproval record, and review packs.
- “Implementation plan” should come first from the implementation-blueprint, execution handoff, runbook, plan, and execution units.
- “Acceptance approach” should come first from the verification contract, verification record, completion review, tests, logs, and comparison evidence.
- “Risks, open questions, and re-review triggers” should synthesize HILP risks, HILE failure forensics, stop conditions, unverified items, residual risks, and blockers.
- “Meeting conclusion” may be checked as ready to proceed only when the assets support that conclusion. If evidence is insufficient, check “Pause progress” or “Requires re-review” and explain why.

## Source and Uncertainty Rules

Every important conclusion must be traceable to a source. If the environment supports file citations or links, preserve clickable sources in the body or appendix. If it does not, use stable file paths, document titles, section names, or asset versions.

Do not invent links, versions, owners, dates, states, or verification results. Missing information must be explicitly marked. Do not write “should pass” or “looks fine” as verified fact. Treat validation as verified only when the assets contain a command, timestamp, result, or equivalent evidence.

## Output Format

Always use the complete structure in `references/brief-template-cn.md`. You may add rows as needed, but do not remove main sections. Do not leave placeholder text. The final output must start with this title:

`# Solution Review Brief: Solution Name`

If the assets do not contain a clear solution name, use the most specific change name, handoff name, manifest slug, or topic. If still unclear, use “Unnamed Solution”.
