---
name: prd-lifecycle
description: Convert product notes or incomplete PRDs into readable, traceable, versioned PRDs with mandatory user stories and use cases, or update delivery progress, evidence, blockers, decisions, and release readiness. Do not use for technical design documents that contain no product requirements.
---

# PRD Lifecycle

Create and maintain a PRD that is easy for product, design, engineering, QA, and stakeholders to read while remaining a traceable source of truth.

## Route the request

- To create, normalize, or substantially review a PRD, read [references/function-1-normalize.md](references/function-1-normalize.md) and [references/prd-template.md](references/prd-template.md).
- To apply progress, evidence, blocker, owner, or decision updates, read [references/function-2-track.md](references/function-2-track.md).
- When both apply, normalize first and then update the normalized version.

Read every supplied source completely before classifying, modifying, or versioning it.

## Required product comprehension

1. Use the readable section order in the canonical template unless the user's established format is clearer.
2. Include both user stories (`US-*`) and use cases (`UC-*`) in every product PRD. Each P0 requirement must trace to at least one user story or use case and to explicit acceptance criteria.
3. Keep user stories outcome-focused. Put preconditions, triggers, normal flow, alternatives, errors, permissions, retries, and recovery in use cases and requirement acceptance criteria.
4. Keep `Non-Goals` strategic and `Out of Scope` release-specific; do not duplicate the same list under both.

## Shared invariants

1. Preserve evidence boundaries:
   - `[确认]`: directly supported by supplied input or evidence.
   - `[推断]`: reasonably inferred but unconfirmed.
   - `[建议]`: newly proposed.
   - `待决策 Q-xxx`: a material missing decision.
2. Never promote `[推断]`, `[建议]`, or a missing value into a confirmed requirement, target, implementation state, or approval.
3. Separate requirement maturity from delivery progress:
   - Requirement: `Draft / In Review / Approved / Deferred`.
   - Delivery: `Not Started / In Progress / Blocked / Reported Complete / Verified`.
   - `In Review` requires evidence that review has started. `Accepted` and `Released` are release gates.
4. Record the basis for each delivery status. Observed implementation, owner report, CI evidence, QA verification, and production evidence are not interchangeable.
5. A completion report moves work to `Reported Complete`; only evidence checked against acceptance criteria moves it to `Verified`.
6. Use stable individual IDs. Never use a range such as `Q-001–Q-010` as a tracked row.
7. Keep stable action IDs (`A-*`) separate from their target requirement, risk, or decision ID.
8. Classify dependencies as `Hard`, `Soft`, or `Gate`; only unresolved `Hard` or `Gate` dependencies automatically block delivery.
9. Keep product priority separate from security severity.
10. Do not propagate secrets, credentials, maintenance keys, or unnecessary internal addresses.
11. Give non-functional requirements stable `NFR-*` IDs when they affect acceptance or release.
12. Split substantial API, schema, infrastructure, telemetry, deployment, or workflow mechanics into companion specifications.

## Validation and delivery

- For canonical Markdown, run `scripts/prd_validate.py --strict` before delivery. Correct errors rather than bypassing validation.
- For progress updates, prefer `scripts/prd_progress.py`; supply the expected document version or SHA when concurrent edits are possible, then validate the output.
- Deliver the versioned PRD, classification and change summary, unresolved decisions, validation result, and every linked companion document.

## Versioning

- Major: product goal, core scope, or role model changes.
- Minor: requirements, priority, business rules, dependencies, user stories/use cases, or acceptance criteria materially change.
- Patch: progress, owner, evidence, dates, or non-substantive wording changes.
- Do not create a version when there is no effective change. Do not reuse or decrease a version number.

If the user has no established output preference, ask once whether they want Markdown, Word, or both. Reuse that preference later.
