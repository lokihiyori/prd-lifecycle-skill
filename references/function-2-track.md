# Function 2: PRD Progress Tracking and Update

## Required progress structure

The PRD must contain two separately readable tables: functional requirements and technical requirements. Use the canonical markers and columns in [prd-template.md](prd-template.md).

Required columns:

| Column | Rule |
|---|---|
| ID | Stable unique requirement ID; preferred update key |
| 需求项 | Human-readable title |
| 优先级 | P0 / P1 / P2 |
| 状态 | One of the five delivery statuses |
| 负责人 | Named person or role; use `—` when unknown |
| 完成日期 | Fill on `Reported Complete` or `Verified` |
| 依赖 | Requirement/decision IDs or a concise external dependency |
| 备注/证据 | PR, commit, test, design, decision, or explanation |

## Parse a conversational update

For input such as “我完成了 A、B、C 三项”:

1. Load the current authoritative PRD.
2. Match each item by exact ID first, then by a unique exact/near-exact title.
3. If a match is ambiguous, ask for that item only; continue with unambiguous items. The helper accepts an ID or a unique title match.
4. Set the status to `Reported Complete`, fill completion date, and fill owner from the actor when the owner is blank.
5. Use `Verified` only after comparing the supplied evidence with that requirement's acceptance criteria. The helper requires both evidence and `verification_confirmed: true`; that flag means the caller performed this comparison, not merely that a PR or CI link exists.
6. Append one changelog entry containing version, actor, time, affected IDs, old/new states, and evidence. Never overwrite history.
7. Bump Patch for progress-only changes. Use Minor when the update changes requirement meaning, priority, business rules, dependencies, or acceptance criteria.

The deterministic helper [scripts/prd_progress.py](../scripts/prd_progress.py) can update canonical Markdown tables, version metadata, next-step recommendations, and changelog. Use it when the PRD follows the template. Otherwise normalize the PRD first.

## Dependencies and blockers

- A requirement is blocked when its status is `Blocked`, its dependency cell names an unresolved Q/R/requirement ID, or it contains an unresolved external dependency such as “法务确认”.
- A requirement dependency is resolved only when it is `Verified`. A Q/R dependency is resolved only when the dependency register says `Resolved`.
- Normalize important external dependencies such as legal approval into a Q/R entry whenever possible.
- Do not recommend blocked work as “start now”. Recommend resolving the dependency itself, with owner, date, and expected evidence.

## Next-step recommendation order

Generate recommendations from unfinished, unblocked work in this order:

1. P0 before P1 before P2.
2. Within the same priority: `Reported Complete` needing verification, then `In Progress`, then `Not Started`.
3. Prefer items that unblock more downstream work.
4. Preserve stable document order as the final tie-breaker.

Recommended action by status:

- `Reported Complete`: verify the item using its required evidence.
- `In Progress`: continue the current item to its next explicit checkpoint.
- `Not Started`: start the item only when all dependencies are resolved.
- `Blocked`: recommend the dependency or decision, not the blocked item.
- `Verified`: do not recommend as implementation work.

Each recommendation includes ID, action, reason, suggested owner/role, target date, and expected evidence. The marker-managed recommendation table at the top is the authoritative “本周期可以直接开工” list; do not maintain a second action list.

## Permission and history

- Contributors may report progress, evidence, and blockers.
- Requirement owners may update delivery status for their items.
- Product owners approve requirement meaning, priority, scope, and product acceptance.
- QA/security reviewers verify items against agreed evidence.
- If the actor lacks authority for a requested change, record it as a proposed change rather than mutating the authoritative requirement.

Never hide conflicting simultaneous updates. If the current version changed since it was loaded, stop and reconcile against the latest version before writing.

## User-facing update summary

Return:

- Old and new PRD versions
- Updated IDs and state transitions
- Any updates not applied and why
- New or cleared blockers
- Updated actionable-now list
- Ranked next steps with reasons
