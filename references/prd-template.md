# Canonical Readable Living PRD Template

Use this reader-first shape as the default. Adapt irrelevant sections, but always retain document control, user stories, use cases, requirements, acceptance, open decisions, traceability, progress markers, and change history.

```markdown
# <Product / Feature> PRD

| Field | Value |
|---|---|
| PRD Version | v0.1.0 |
| Requirement Status | Draft |
| Product Owner | — |
| Engineering | — |
| Design | — |
| Created | YYYY-MM-DD |
| Last Updated | YYYY-MM-DD |
| Target Release | — |
| Next Review | — |
| Source of Truth | — |

> Evidence legend: `[确认]` is supported by supplied input; `[推断]` is reasonable but unconfirmed; `[建议]` is newly proposed. These labels do not indicate implementation or approval.

## 0. Current Action Snapshot

<!-- PRD-LIFECYCLE:NEXT-STEPS:START -->
| Action ID | Target ID | Recommended Action | Reason | Suggested Owner | Target Date | Completion Evidence |
|---|---|---|---|---|---|---|
| A-001 | Q-001 | Resolve the launch-scope decision | It gates the P0 journey | Product Owner | Before next review | Approved decision record |
<!-- PRD-LIFECYCLE:NEXT-STEPS:END -->

## 1. Executive Summary

One sentence: what are we building, for whom, and why now?

## 2. Background

- Current product state
- Why this need appeared now
- Relevant prior decisions or constraints

## 3. Problem Statement

| Dimension | Statement | Evidence Class |
|---|---|---|
| WHO | Who experiences the problem? | `[确认/推断]` |
| WHAT | What prevents the desired outcome? | `[确认/推断]` |
| WHEN | In which context or step does it happen? | `[确认/推断]` |
| WHY | Why is it worth solving now? | `[确认/推断]` |
| EVIDENCE | Research, analytics, tickets, observations, or source documents | `[确认]` or `待补充` |

## 4. Goals

| ID | Goal | Evidence Class |
|---|---|---|
| G-001 | <measurable product outcome> | `[确认/建议]` |

## 5. Non-Goals

Strategic problems or outcomes this initiative intentionally does not solve. Release-specific exclusions belong in §17.

## 6. Success Metrics

| ID | Type | Metric | Definition | Baseline | Target | Decision/Owner |
|---|---|---|---|---|---|---|
| KPI-001 | Primary | <metric> | <formula and population> | 待测 | 待决策 | Q-xxx |
| GUARD-001 | Guardrail | <metric> | <formula> | 待测 | 待决策 | Q-xxx |

## 7. Target Users, Roles, and Permissions

| Role / Persona | Need | Allowed Actions | Data Scope | Evidence Class |
|---|---|---|---|---|
| <role> | <need> | <actions> | <ownership/visibility> | `[确认/推断]` |

## 8. User Stories and Use Cases

### 8.1 User Stories

| ID | User Story | Priority | Evidence Class |
|---|---|---:|---|
| US-CORE-001 | As a <role>, I want <capability>, so that <outcome>. | P0 | `[确认/推断]` |

### 8.2 Use Cases

#### UC-CORE-001 — <Use-case name>

| Field | Content |
|---|---|
| Primary Actor | <role> |
| Preconditions | <required state> |
| Trigger | <event> |
| Main Flow | 1. ... 2. ... 3. ... |
| Alternate / Error Flows | <empty, invalid, permission, retry, recovery> |
| Result | <observable outcome> |
| Maps To | FR-CORE-001; AC-CORE-001–005 |

## 9. User Journey

Describe the shortest end-to-end journey and its failure/recovery branches. Use Mermaid only when branching or state change is materially clearer than prose.

## 10. Functional Requirements

### FR-CORE-001 — <Requirement name>

| Field | Content |
|---|---|
| Description | <observable product behavior> |
| Priority | P0 |
| Requirement Status | Draft |
| User Story / Use Case | US-CORE-001; UC-CORE-001 |
| Preconditions | <state> |
| Trigger | <event> |
| Expected Behavior | <normal behavior> |
| Dependencies | <IDs or —> |

Acceptance criteria:

- AC-CORE-001 — Normal flow: ...
- AC-CORE-002 — Validation/error: ...
- AC-CORE-003 — Permission: ...
- AC-CORE-004 — Duplicate/retry: ...
- AC-CORE-005 — Recovery: ...

## 11. AI Requirements

When applicable, define model behavior, grounding, evidence, confidence/uncertainty, fallback, hallucination handling, prompt injection, safety, evaluation, human review, model/version traceability, and prohibited behavior.

## 12. Edge Cases

| ID | Scenario | Expected Behavior | Mapped Requirement / AC |
|---|---|---|---|
| EC-001 | No data | <behavior> | FR-CORE-001 / AC-CORE-002 |

## 13. UX Requirements

Cover Figma/wireframe references, responsive behavior, accessibility interactions, loading, empty, error, permission-denied, partial-success, and recovery states.

## 14. Non-Functional Requirements

| ID | Category | Requirement | Measurement / Evidence | Priority |
|---|---|---|---|---:|
| NFR-PERF-001 | Performance | <requirement> | <measurement> | P0 |
| NFR-SEC-001 | Security | <requirement> | <review/test> | P0 |

Consider performance, security, privacy, accessibility, reliability, observability, and data lifecycle. Omit only when genuinely inapplicable and explain why.

## 15. Analytics

| Event ID | Event | Trigger | Required Properties | Metric / Requirement |
|---|---|---|---|---|
| EV-CORE-001 | <event_name> | <trigger> | <properties> | KPI-001 / FR-CORE-001 |

## 16. Dependencies, Risks, and Contradictions

<!-- PRD-LIFECYCLE:DEPENDENCY-REGISTER -->
| ID | Type | Blocking Level | Item | Status | Affects | Owner | Due Date | Notes / Evidence |
|---|---|---|---|---|---|---|---|---|
| Q-001 | Decision | Gate | <decision> | Open | FR-CORE-001 | Product Owner | Before next review | — |
| R-SEC-001 | Risk | Hard | <risk> | Open | FR-CORE-001 | Security | Before next review | — |

Use `Hard`, `Soft`, or `Gate`. Record contradictions as `C-*` and link them to a `Q-*` rather than silently choosing one side.

## 17. Out of Scope for This Release

List concrete capabilities deferred from the target release. Explain the difference from strategic Non-Goals when needed.

## 18. Rollout

| Phase | Audience / Percentage | Entry Criteria | Monitoring | Stop / Rollback Trigger | Owner |
|---|---|---|---|---|---|
| 1 | Internal | <criteria> | <metrics> | <trigger> | <owner> |

## 19. Release Acceptance

Define release blockers: P0 requirements and NFRs Verified, E2E passing, security/privacy/accessibility reviews, analytics validation, rollout and rollback readiness, product acceptance, and target-environment release evidence.

## 20. Open Questions

Keep one row per decision; its current status remains authoritative in §16.

| ID | Question | Affects |
|---|---|---|
| Q-001 | <question> | FR-CORE-001 |

## 21. Decision Log

| ID | Date | Decision | Reason | Owner | Replaces / Affects |
|---|---|---|---|---|---|
| D-001 | YYYY-MM-DD | <decision> | <reason> | <owner> | Q-001 |

## 22. Traceability and Source Mapping

<!-- PRD-LIFECYCLE:TRACEABILITY -->
| Requirement ID | User Story / Use Case | Acceptance Criteria | Analytics | Dependencies | Source / Evidence Class |
|---|---|---|---|---|---|
| FR-CORE-001 | US-CORE-001; UC-CORE-001 | AC-CORE-001–005 | EV-CORE-001 | Q-001 | <source>; `[确认]` |

## Appendix A. Delivery Tracker

### A.1 Functional Progress

<!-- PRD-LIFECYCLE:FUNCTIONAL-PROGRESS -->
| ID | Requirement | Priority | Delivery Status | Status Basis | Owner | Completion Date | Dependencies | Notes / Evidence |
|---|---|---:|---|---|---|---|---|---|
| FR-CORE-001 | <requirement> | P0 | Not Started | Baseline confirmed by owner | — | — | Q-001 | — |

### A.2 Technical Progress

<!-- PRD-LIFECYCLE:TECHNICAL-PROGRESS -->
| ID | Requirement | Priority | Delivery Status | Status Basis | Owner | Completion Date | Dependencies | Notes / Evidence |
|---|---|---:|---|---|---|---|---|---|
| TR-CORE-001 | <technical enabler> | P0 | Not Started | Baseline confirmed by engineering | — | — | — | — |

## Appendix B. Change History

<!-- PRD-LIFECYCLE:CHANGELOG -->
| Version | Date | Updated By | Change | Evidence |
|---|---|---|---|---|
| v0.1.0 | YYYY-MM-DD | <actor> | Initial normalized draft | <source> |
```

## Canonical values

- Requirement: `Draft / In Review / Approved / Deferred`
- Delivery: `Not Started / In Progress / Blocked / Reported Complete / Verified`
- Dependency blocking level: `Hard / Soft / Gate`
- Dependency state: `Open / In Progress / Resolved`

Marker-managed tables may use the English headers above or the supported Chinese equivalents. Do not alter marker comments.
