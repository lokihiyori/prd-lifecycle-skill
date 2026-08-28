# Function 1: Input File to Professional PRD

## Classify the input

Choose exactly one primary mode after reading the complete source.

| Input type | Signals | Required treatment |
|---|---|---|
| Unstructured material | Loose notes, meeting minutes, chat retelling, fragmented bullets, no recognizable document structure | Extract problem, users, goals, features, constraints, decisions, risks, and evidence. Build a complete first draft from the standard template. Mark every inferred or newly proposed element `[推断]` or `[建议]`. |
| Partial PRD | Existing headings or requirement-like structure, but missing scope, priorities, acceptance criteria, permissions, failure paths, metrics, or delivery tracking | Perform a gap analysis against the template, fill the gaps in a new version, and provide a brief “what changed” summary. Preserve source claims and mark additions by evidence class. |

If both appear, classify by the dominant content. Ask one focused question only when the classification would materially change the output.

## Normalize the source

1. Extract directly supported facts and retain their meaning.
2. Detect contradictions before choosing a solution. Assign `C-xxx`; do not silently pick one side.
3. Convert blocking unknowns into `Q-xxx` decisions with affected requirements, decision-owner role, due date, and status.
4. Restore a single glossary. Link disputed terms to their Q IDs.
5. Generate stable IDs:
   - `P-xxx` problems
   - `FR-<DOMAIN>-xxx` functional requirements
   - `TR-<DOMAIN>-xxx` technical requirements
   - `NFR-<DOMAIN>-xxx` non-functional requirements
   - `AC-<DOMAIN>-xxx` acceptance criteria
   - `R-<DOMAIN>-xxx` risks
   - `Q-xxx` decisions
   - `A-xxx` current-cycle actions
6. Separate roles from visibility scopes.
7. For each P0 requirement, add normal, error, permission, duplicate/retry, and recovery acceptance criteria when applicable.
8. Add a current-cycle execution dashboard containing work that does not depend on unresolved decisions.
9. Add concrete dates for the decisions blocking the most downstream work. If the company cadence is unknown, use “before the next review” and require a next-review date.
10. Add functional and technical implementation-progress tables using the canonical markers from the template.

## Gap analysis checklist

Check for:

- Document owner, version, target release, review date, and source of truth
- Problem evidence, goals, non-goals, and current scope
- Users, roles, visibility, permissions, and data ownership
- Core journey and failure/recovery paths
- Stable requirement IDs, priority, owner, status, and dependencies
- Measurable acceptance criteria for P0 items
- Security, privacy, accessibility, reliability, and data lifecycle
- AI allowed/prohibited behavior and traceability when AI is involved
- Success metrics with definitions; never invent baselines or targets
- Risks, contradictions, decisions, milestone dates, and release gates
- Glossary and source mapping

## Control uncertainty density

- Do not scatter dozens of anonymous `TBD` markers.
- Use Q IDs only for material decisions; group them in one table.
- Put executable, decision-independent work at the top so readers know what can start now.
- Use `[建议]` for reasonable improvements that do not claim approval.
- Do not create arbitrary dates for commitments. Label proposed planning dates and identify who must confirm them.

## Split large outputs

Create a companion Technical Spec when the source contains substantial API, database, task state, performance, telemetry, security implementation, or operations detail, or when the core PRD would become difficult to scan at roughly 500 lines or more.

Keep the PRD focused on product outcomes, business rules, scope, priority, acceptance, risk, and high-level progress. Preserve cross-references between split files.

## Format and deliver

If no preference is known, ask the user to choose Markdown, Word, or both. When Word is requested, use an available document-generation workflow and visually verify the result. When Markdown is requested, validate headings, tables, code fences, cross-references, filenames, and version metadata.

Output:

1. Versioned PRD.
2. Concise conversion summary including classification and major changes.
3. Source mapping identifying confirmed, inferred, and suggested material.
4. Technical Spec only when the split rule applies.

Before creating a new version, compare the new source with the source already used for the latest normalized version when available. Identical input with no rule/template change must reuse the current version.
