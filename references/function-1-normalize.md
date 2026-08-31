# Function 1: Normalize Input into a Readable Living PRD

## Classify the input

Choose one primary mode after reading the complete source.

| Input type | Signals | Treatment |
|---|---|---|
| Unstructured material | Notes, meeting records, chats, fragmented bullets | Extract problems, users, evidence, goals, constraints, decisions, risks, and candidate behavior. Build a first draft and mark every addition by evidence class. |
| Partial PRD | Existing requirements or headings, but missing stories, use cases, scope, permissions, failures, acceptance, metrics, or tracking | Preserve source meaning, perform a template gap analysis, and create a new version with a concise change summary. |

Ask a focused question only when the answer would materially change scope or output. Otherwise create explicit `Q-*` decisions.

## Normalize in reader order

Use [prd-template.md](prd-template.md) as the default order:

1. Start with document control, an executive summary, background, and a WHO/WHAT/WHEN/WHY/EVIDENCE problem statement.
2. Separate goals, strategic non-goals, metrics, target users, roles, permissions, and release-specific out-of-scope items.
3. Add user stories and use cases before detailed requirements so readers understand user value and behavior first.
4. Add the core journey, functional requirements, AI behavior, edge cases, UX, NFRs, analytics, dependencies, rollout, release gates, questions, decisions, traceability, progress, and history.
5. Keep the top action snapshot short. Put complete functional and technical progress tables in the appendix.

## Evidence and status rules

- `[确认]` means input-backed, not objectively true or implemented. State this in the document legend.
- Default newly normalized requirement maturity to `Draft`. Use `In Review` only when supplied evidence shows that review has begun.
- Do not infer active work merely from a visible page or endpoint. When implementation evidence exists but delivery is not verified, record the conservative delivery state and state basis explicitly, such as `Observed implementation; acceptance unverified`.
- Do not invent baselines, dates, owners, or numeric targets. A proposed target may appear only as `[建议]` and must remain unapproved until a named decision closes it.

## Mandatory user stories and use cases

Generate stable IDs:

- `US-<DOMAIN>-xxx` for user stories.
- `UC-<DOMAIN>-xxx` for use cases.

Every PRD must contain both. For each core flow and every P0 requirement:

1. Link at least one `US-*` or `UC-*`.
2. Write the user story as: `As a <role>, I want <capability>, so that <outcome>.`
3. Define a use case with actor, preconditions, trigger, main flow, alternate/error flows, permissions, result, and mapped `FR-*` / `AC-*` IDs.
4. Do not invent persona demographics, motivation, or research evidence. Use a role label and mark inferred needs.
5. Reuse one story or use case across requirements when it genuinely represents the same user outcome; do not create artificial one-to-one duplication.

## Requirements and traceability

Generate stable individual IDs:

- `P-*`, `G-*`, `NG-*`, `US-*`, `UC-*`, `FR-*`, `TR-*`, `NFR-*`, `AC-*`, `EC-*`, `EV-*`, `R-*`, `C-*`, `Q-*`, `D-*`, and `A-*`.
- Do not create aggregate tracked rows such as `Q-001–Q-012`.
- Separate roles from visibility and data ownership.
- For each P0 requirement, cover normal, validation/error, permission, duplicate/retry, and recovery behavior when applicable.
- Add a traceability row connecting each P0 requirement to a story/use case, acceptance criteria, analytics, and dependencies.

## Dependency and uncertainty control

- Detect contradictions before selecting a solution. Assign `C-*` and link them to decisions.
- Convert material unknowns into individual `Q-*` rows with affected IDs, decision owner role, due date, and status.
- Mark dependencies `Hard`, `Soft`, or `Gate`. Only `Hard` and `Gate` should force `Blocked`.
- Keep executable, decision-independent work in the action snapshot.
- Give the most consequential blockers concrete dates. If cadence is unknown, require a next-review date rather than inventing one.

## NFR, AI, metrics, and analytics

- Add stable NFRs for applicable performance, security, privacy, accessibility, reliability, observability, and data-lifecycle requirements.
- For AI products, define allowed behavior, grounding, evidence, uncertainty, fallback, hallucination handling, prompt injection, safety, evaluation, and human review.
- Define metric formulas and event mappings. Leave unknown baselines and targets as `待测` / `待决策`.
- Treat zero-tolerance security or privacy targets as proposed until approved unless the input already establishes them.

## Split large outputs

Create a companion Technical Spec when implementation detail is substantial or the PRD becomes difficult to scan. Create a separate Delivery Tracker when progress tables dominate the product narrative. Keep linked files in the delivered bundle and validate the links.

## Required output

1. Versioned PRD.
2. Concise classification and conversion summary.
3. Source mapping for confirmed, inferred, and suggested material.
4. Companion specifications when the split rule applies.
5. Strict validator result.

Before versioning, compare the input and rules with the latest normalized source. Reuse the current version when nothing effectively changed.
