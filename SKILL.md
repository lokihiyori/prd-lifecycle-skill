---
name: prd-lifecycle
description: Convert loose product notes or incomplete PRDs into professional versioned PRDs, and update living PRD implementation progress, changelogs, blockers, and next-step recommendations. Use when users ask to create, standardize, review, track, or update a PRD; do not use for technical design documents that contain no product requirements.
---

# PRD Lifecycle

Create and maintain a PRD as a traceable source of truth, not as a one-time rewrite.

## Route the request

- For notes, meeting records, chats, or an incomplete PRD that must become a professional PRD, read [references/function-1-normalize.md](references/function-1-normalize.md) and [references/prd-template.md](references/prd-template.md).
- For progress updates such as “完成了 A、B、C”, status tracking, changelog maintenance, or next-step recommendations, read [references/function-2-track.md](references/function-2-track.md).
- When the user requests both, normalize first, then apply the progress update to the normalized version.

Read every supplied source file completely before classifying or modifying it.

## Shared invariants

1. Preserve evidence boundaries:
   - `[确认]`: directly supported by the input or supplied evidence.
   - `[推断]`: reasonably inferred but not confirmed.
   - `[建议]`: newly proposed by the skill.
   - `待决策 Q-xxx`: a missing decision that materially changes scope, behavior, data, permission, or acceptance.
2. Never turn `[推断]`, `[建议]`, or a missing value into a confirmed requirement.
3. Separate the stable requirement definition from delivery progress. Use only:
   - Requirement status: `Draft / In Review / Approved / Deferred`.
   - Delivery status: `Not Started / In Progress / Blocked / Reported Complete / Verified`.
   - Treat `Accepted` and `Released` as release gates, not normal delivery statuses.
4. A user saying “完成了” moves an item to `Reported Complete`; move it to `Verified` only when the agreed evidence exists.
5. Keep product priority separate from security severity. A P2 operations feature can still have a P0 security risk.
6. Put the current actionable work in one authoritative execution dashboard. Risk, decision, and requirement sections link by ID instead of duplicating the same status text.
7. Do not propagate passwords, tokens, maintenance keys, secrets, or unnecessary internal addresses from the source into generated PRDs.
8. Keep product requirements in the PRD. Split substantial API, schema, infrastructure, performance, telemetry, or deployment material into a Technical Spec. Split update/approval mechanics into a workflow document.

## Output and versioning

- If the user has not indicated an output preference, ask once: Markdown, Word, or both. Reuse an established preference and do not ask again.
- Use filenames such as `<Product>_PRD_v1.2.0.md` or `.docx`.
- Major: product goal, core scope, or role model changes.
- Minor: requirements, priority, business rules, or acceptance criteria materially change.
- Patch: progress, owner, evidence, dates, or non-substantive text changes.
- If the input and normalized source are unchanged, do not create a fake version bump.

Deliver the new artifact plus a concise summary of classification, changes, unresolved decisions, and any companion documents. Use the environment's durable artifact workflow when files must be delivered.
