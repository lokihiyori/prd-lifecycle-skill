# Sample Feature PRD

| Field | Value |
|---|---|
| PRD Version | v0.1.0 |
| Requirement Status | Draft |
| Product Owner | Product |
| Engineering | Engineering |
| Design | Design |
| Created | 2026-08-31 |
| Last Updated | 2026-08-31 |
| Target Release | MVP |
| Next Review | 2026-09-07 |
| Source of Truth | This file |

> Evidence legend: `[确认]` is input-backed; `[推断]` is unconfirmed; `[建议]` is proposed.

## 0. Current Action Snapshot

<!-- PRD-LIFECYCLE:NEXT-STEPS:START -->
| Action ID | Target ID | Recommended Action | Reason | Suggested Owner | Target Date | Completion Evidence |
|---|---|---|---|---|---|---|
| A-001 | Q-001 | Resolve scope | Gate for FR-CORE-001 | Product | 2026-09-07 | Decision record |
<!-- PRD-LIFECYCLE:NEXT-STEPS:END -->

## 1. Executive Summary

Build a source-backed answer flow for users.

## 8. User Stories and Use Cases

| ID | User Story | Priority | Evidence Class |
|---|---|---:|---|
| US-CORE-001 | As a user, I want a sourced answer, so that I can decide confidently. | P0 | `[确认]` |

### UC-CORE-001 — Generate an answer

The user submits a valid question, reviews sources, and can retry after a temporary failure. Maps to FR-CORE-001 and AC-CORE-001.

## 10. Functional Requirements

### FR-CORE-001 — Generate a source-backed answer

- AC-CORE-001 — A valid request returns an answer and evidence.

## 14. Non-Functional Requirements

| ID | Category | Requirement | Evidence | Priority |
|---|---|---|---|---:|
| NFR-SEC-001 | Security | Enforce authorization | Security test | P0 |

## 16. Dependencies, Risks, and Contradictions

<!-- PRD-LIFECYCLE:DEPENDENCY-REGISTER -->
| ID | Type | Blocking Level | Item | Status | Affects | Owner | Due Date | Notes / Evidence |
|---|---|---|---|---|---|---|---|---|
| Q-001 | Decision | Gate | Confirm launch scope | Open | FR-CORE-001 | Product | 2026-09-07 | Decision record required |

## 22. Traceability and Source Mapping

<!-- PRD-LIFECYCLE:TRACEABILITY -->
| Requirement ID | User Story / Use Case | Acceptance Criteria | Analytics | Dependencies | Source / Evidence Class |
|---|---|---|---|---|---|
| FR-CORE-001 | US-CORE-001; UC-CORE-001 | AC-CORE-001 | EV-CORE-001 | Q-001 | Product notes; `[确认]` |

## Appendix A. Delivery Tracker

<!-- PRD-LIFECYCLE:FUNCTIONAL-PROGRESS -->
| ID | Requirement | Priority | Delivery Status | Status Basis | Owner | Completion Date | Dependencies | Notes / Evidence |
|---|---|---:|---|---|---|---|---|---|
| FR-CORE-001 | Generate a source-backed answer | P0 | Not Started | Baseline confirmed by owner | Product | — | Q-001 | — |

<!-- PRD-LIFECYCLE:TECHNICAL-PROGRESS -->
| ID | Requirement | Priority | Delivery Status | Status Basis | Owner | Completion Date | Dependencies | Notes / Evidence |
|---|---|---:|---|---|---|---|---|---|
| TR-CORE-001 | Provide answer service | P0 | Not Started | Baseline confirmed by engineering | Engineering | — | — | — |

## Appendix B. Change History

<!-- PRD-LIFECYCLE:CHANGELOG -->
| Version | Date | Updated By | Change | Evidence |
|---|---|---|---|---|
| v0.1.0 | 2026-08-31 | Product | Initial draft | Product notes |
