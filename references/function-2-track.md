# Function 2: Track PRD Delivery and Decisions

## Canonical tracking structure

Use the marker-managed tables in [prd-template.md](prd-template.md). The canonical progress columns are:

| Column | Rule |
|---|---|
| ID | Stable `FR-*` or `TR-*` ID |
| 需求项 | Human-readable title |
| 优先级 | P0 / P1 / P2 |
| 交付状态 | One of the five delivery statuses |
| 状态依据 | Observation, owner report, PR/commit, CI, QA, security review, or production evidence |
| 负责人 | Named person or role; `—` when unknown |
| 完成日期 | Fill on `Reported Complete` or `Verified` |
| 依赖 | Individual requirement, `Q-*`, `R-*`, or concise external dependency |
| 备注/证据 | Evidence or explanation |

The helper remains compatible with legacy tables using `状态` and no `状态依据`, but new documents use the canonical columns.

## Parse a conversational update

For input such as “我完成了 A、B、C”:

1. Load the authoritative PRD and, when concurrency is possible, record its version or SHA.
2. Match exact ID first and then a unique exact/near-exact title. Ask only about ambiguous items and continue with unambiguous items.
3. Move a user-reported completion to `Reported Complete`, fill the date and actor when appropriate, and state `Owner report` as the basis.
4. Move to `Verified` only after evidence has been compared with the mapped acceptance criteria. A PR or passing CI alone is not automatically product verification.
5. Update dependencies only with individual IDs. A `Resolved` decision or risk requires evidence.
6. Preserve stable `A-*` action IDs while separately updating their target IDs.
7. Append one changelog row; never overwrite history.
8. Refuse no-op updates and version reuse/regression.
9. Use Minor for priority, dependency, requirement, use-case, or acceptance changes; use Patch for progress-only changes.

Prefer [scripts/prd_progress.py](../scripts/prd_progress.py). Use `--bump auto`; provide `--expected-version` or `--expected-sha256` when another actor may edit the source. Validate the output with [scripts/prd_validate.py](../scripts/prd_validate.py).

## Dependencies and blockers

- `Hard`: work cannot proceed until resolved.
- `Gate`: implementation may proceed, but the item cannot pass the named approval or release gate.
- `Soft`: relevant dependency that does not automatically change delivery to `Blocked`.
- Requirement dependencies resolve at `Verified`; decision/risk dependencies resolve at `Resolved`.
- A requirement explicitly marked `Blocked` without a dependency must produce an action to clarify the blocker.

## Next-step ranking

Rank unfinished work by:

1. P0, then P1, then P2.
2. `Reported Complete`, then `In Progress`, then `Not Started`.
3. Dependencies that unblock the most downstream items.
4. Stable document order.

Aggregate all downstream requirements when recommending a decision or risk. Do not present one arbitrary dependent as if it were the only reason.

Each action has a stable `A-*` ID plus a target ID, action, reason, owner, date, and evidence. The marker-managed snapshot is authoritative; do not maintain a second current-action list.

## Permission and history

- Contributors report progress, evidence, and blockers.
- Requirement owners update delivery state.
- Product owners approve meaning, priority, scope, user stories/use cases, and product acceptance.
- QA/security reviewers verify against agreed acceptance evidence.
- Unauthorized changes are recorded as proposals, not authoritative mutations.

If the loaded source version or SHA no longer matches, stop and reconcile before writing.

## User-facing summary

Return old/new versions, effective transitions, unapplied changes with reasons, new or cleared blockers, current actions, ranked next steps, and validation status.
