# PRD Lifecycle Skill

[![test](https://github.com/lokihiyori/prd-lifecycle-skill/actions/workflows/test.yml/badge.svg)](https://github.com/lokihiyori/prd-lifecycle-skill/actions/workflows/test.yml)
[![Python 3.11+](https://img.shields.io/badge/python-3.11%2B-blue)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green)](LICENSE)

An agent skill for turning raw product material into a **readable, traceable, versioned Product Requirements Document (PRD)** — and for keeping that PRD current as delivery progresses.

The skill enforces one core discipline: **never let an inference, a suggestion, or a completion report silently become a confirmed requirement or a verified result.** Every claim in the output carries an evidence class, requirement maturity is kept separate from delivery progress, and structural rules are checked by a deterministic validator rather than by trust.

---

## Table of contents

- [What it does](#what-it-does)
- [Why use it](#why-use-it)
- [How it works](#how-it-works)
- [Installation](#installation)
- [Usage](#usage)
- [The canonical PRD](#the-canonical-prd)
- [Core model](#core-model)
- [Scripts](#scripts)
- [Update payload format](#update-payload-format)
- [Validation rules](#validation-rules)
- [Repository layout](#repository-layout)
- [Release evolution](#release-evolution)
- [Development](#development)
- [Contributing](#contributing)
- [License](#license)

---

## What it does

The skill has two functions. It routes each request to one (or both, in order).

### 1. Normalize — build a readable living PRD

Takes unstructured input (meeting notes, chat logs, fragmented bullets) or a partial PRD and produces a complete document in reader-first order:

- Document control, executive summary, background, and a WHO / WHAT / WHEN / WHY / EVIDENCE problem statement.
- Goals, strategic non-goals, success metrics, target users, roles, and permissions.
- **Mandatory user stories (`US-*`) and use cases (`UC-*`)** placed *before* detailed requirements, so readers understand user value first.
- Functional requirements with explicit acceptance criteria, AI behavior, edge cases, UX states, non-functional requirements (`NFR-*`), analytics events, dependencies, rollout, and release gates.
- A traceability matrix linking every P0 requirement to a story/use case, acceptance criteria, analytics, and dependencies.
- A compact **action snapshot** at the top; full delivery-tracking tables in an appendix.

Every added statement is tagged by evidence class. Material unknowns become individual `Q-*` decision rows instead of guesses.

### 2. Track — maintain delivery, evidence, and decisions

Parses a conversational update (e.g. *"I finished FR-SEARCH-001, PR #42"*) and applies it deterministically:

- Moves user-reported completions to **`Reported Complete`** with `Owner report` as the basis — never straight to `Verified`.
- Promotes to **`Verified`** only when evidence has been checked against the mapped acceptance criteria and verification is explicitly confirmed.
- Resolves dependencies only with individual IDs and only against recorded evidence.
- Recomputes the ranked next-step / action snapshot, preserving stable `A-*` action IDs.
- Appends exactly one changelog row — history is never overwritten.
- Refuses no-op updates and version reuse or regression.
- Chooses the version bump automatically (Minor for semantic changes, Patch for progress-only changes).

---

## Why use it

| Problem in ad-hoc PRDs | How this skill addresses it |
|---|---|
| Inferences and proposals harden into "requirements" | Four evidence classes (`[确认]` / `[推断]` / `[建议]` / `待决策 Q-xxx`); promotion is forbidden |
| "Done" means different things to different people | Delivery status is separate from requirement maturity; a status **basis** is recorded for every row |
| A PR or green CI is treated as product acceptance | `Verified` requires evidence checked against acceptance criteria plus explicit confirmation |
| Requirements are unreadable walls of tables | Reader-first section order; stories and use cases come first; tracking tables move to an appendix |
| Blockers are vague | Dependencies are typed `Hard` / `Soft` / `Gate`; only unresolved `Hard`/`Gate` auto-block |
| Version numbers drift or lie | Deterministic bump rules; no-op and regression are rejected; filename and document version must agree |
| Concurrent edits clobber each other | Optional `--expected-version` / `--expected-sha256` guards abort on stale input |
| Secrets leak into shared docs | Credential, token, and internal-IP patterns fail validation and updates |

---

## How it works

```
Request
  │
  ├─ create / normalize / review ──▶ Function 1: Normalize
  │                                    references/function-1-normalize.md
  │                                    references/prd-template.md
  │
  ├─ progress / evidence / blocker ─▶ Function 2: Track
  │  / owner / decision update         references/function-2-track.md
  │                                    scripts/prd_progress.py
  │
  └─ both ─────────────────────────▶ Normalize first, then track the normalized version

Before delivery ─▶ scripts/prd_validate.py --strict
```

`SKILL.md` is the entry point the agent loads. It contains the routing logic, the shared invariants, and the versioning rules. The `references/` files are read on demand for each function. The `scripts/` are deterministic — the agent shells out to them rather than editing tables by hand, so structural guarantees hold regardless of the model.

---

## Installation

### Claude Code

Clone into your skills directory:

```bash
# project-level
git clone https://github.com/lokihiyori/prd-lifecycle-skill.git .claude/skills/prd-lifecycle

# or user-level
git clone https://github.com/lokihiyori/prd-lifecycle-skill.git ~/.claude/skills/prd-lifecycle
```

The skill is then available as `prd-lifecycle`. Verify with `/skills` or by asking Claude to *"use the prd-lifecycle skill"*.

### OpenAI / Codex-style agents

`agents/openai.yaml` provides the interface metadata (display name, short description, default prompt). Point your agent runtime at the repository root; it loads `SKILL.md` and invokes the skill as `$prd-lifecycle`.

### Requirements

- **Python 3.11+** on `PATH` (the scripts use no third-party packages).
- An agent host that supports file-based skills with a `SKILL.md` manifest.

---

## Usage

Invoke the skill by name and describe the task in natural language.

**Create a PRD from notes:**

```text
Use prd-lifecycle to turn these product notes into a Markdown PRD.
Include user stories and detailed use cases for every P0 flow.
```

**Fill gaps in an existing draft:**

```text
Use prd-lifecycle to review Product_PRD_v0.3.0.md, run a template gap analysis,
and produce a new version with a change summary.
```

**Apply a progress update and get the next step:**

```text
Use prd-lifecycle to set FR-SEARCH-001 to Reported Complete with PR #42 as evidence,
then recommend the next unblocked work.
```

**Resolve a decision:**

```text
Use prd-lifecycle to mark Q-003 Resolved (approved permission matrix attached)
and re-rank the action snapshot.
```

The skill delivers the versioned PRD, a classification / change summary, the list of unresolved decisions, the strict validator result, and any linked companion documents. If you have no stated format preference, it asks once (Markdown / Word / both) and reuses the answer.

---

## The canonical PRD

`references/prd-template.md` defines the reader-first document shape. Its structure:

| §  | Section | § | Section |
|---:|---|---:|---|
| 0 | Current Action Snapshot | 12 | Edge Cases |
| 1 | Executive Summary | 13 | UX Requirements |
| 2 | Background | 14 | Non-Functional Requirements |
| 3 | Problem Statement (WHO/WHAT/WHEN/WHY/EVIDENCE) | 15 | Analytics |
| 4 | Goals | 16 | Dependencies, Risks, Contradictions |
| 5 | Non-Goals (strategic) | 17 | Out of Scope for This Release |
| 6 | Success Metrics | 18 | Rollout |
| 7 | Target Users, Roles, Permissions | 19 | Release Acceptance |
| 8 | User Stories and Use Cases | 20 | Open Questions |
| 9 | User Journey | 21 | Decision Log |
| 10 | Functional Requirements | 22 | Traceability and Source Mapping |
| 11 | AI Requirements | A / B | Delivery Tracker / Change History (appendices) |

### Marker comments

The scripts locate tables by HTML-comment markers. **Do not edit or remove them.**

| Marker | Table |
|---|---|
| `<!-- PRD-LIFECYCLE:NEXT-STEPS:START -->` … `:END -->` | Current action snapshot |
| `<!-- PRD-LIFECYCLE:DEPENDENCY-REGISTER -->` | Dependencies / risks / contradictions |
| `<!-- PRD-LIFECYCLE:TRACEABILITY -->` | Traceability matrix |
| `<!-- PRD-LIFECYCLE:FUNCTIONAL-PROGRESS -->` | Appendix A.1 functional delivery |
| `<!-- PRD-LIFECYCLE:TECHNICAL-PROGRESS -->` | Appendix A.2 technical delivery |
| `<!-- PRD-LIFECYCLE:CHANGELOG -->` | Appendix B change history |

Marker-managed tables accept either the English headers or the supported Chinese equivalents; headers must match a known variant exactly.

---

## Core model

### Evidence classes

| Label | Meaning |
|---|---|
| `[确认]` | Directly supported by supplied input or evidence (input-backed — **not** "objectively true" or "implemented") |
| `[推断]` | Reasonably inferred but unconfirmed |
| `[建议]` | Newly proposed |
| `待决策 Q-xxx` | A material missing decision, tracked as an individual row |

`[推断]`, `[建议]`, and missing values are **never** promoted into a confirmed requirement, target, state, or approval.

### Requirement maturity vs. delivery progress

These are tracked independently.

```
Requirement maturity :  Draft ──▶ In Review ──▶ Approved ──▶ Deferred
                                  (needs evidence review started)

Delivery status      :  Not Started ──▶ In Progress ──▶ Blocked
                                    └──▶ Reported Complete ──▶ Verified
                                         (owner report)        (evidence vs. acceptance criteria)
```

Every delivery row also records a **status basis** — observed implementation, owner report, PR/commit, CI, QA verification, security review, or production evidence. These are not interchangeable.

### Dependency blocking levels

| Level | Effect |
|---|---|
| `Hard` | Work cannot proceed until resolved → auto `Blocked` |
| `Gate` | Implementation may proceed, but the item cannot pass the named approval / release gate → auto `Blocked` |
| `Soft` | Relevant, but does not by itself force `Blocked` |

Requirement dependencies resolve at `Verified`; decision / risk dependencies resolve at `Resolved` (with evidence).

### Stable IDs

Individual, never ranges: `P-*` `G-*` `NG-*` `US-*` `UC-*` `FR-*` `TR-*` `NFR-*` `AC-*` `EC-*` `EV-*` `R-*` `C-*` `Q-*` `D-*` `A-*`. A row such as `Q-001–Q-010` is rejected. Action IDs (`A-*`) are kept separate from their target requirement / risk / decision ID.

---

## Scripts

Both scripts are standalone (`python3 scripts/<name>.py --help`) and depend only on the standard library.

### `prd_validate.py`

Validates canonical Markdown structure, traceability, links, and safety.

```bash
python3 scripts/prd_validate.py Product_PRD_v0.4.0.md [--strict] [--json]
```

| Flag | Effect |
|---|---|
| `--strict` | Treat warnings as failures (exit 1) |
| `--json` | Emit `{"file", "valid", "errors", "warnings"}` |

Exit code is `0` when valid, `1` otherwise. Run it before every delivery and fix the errors rather than bypassing it.

### `prd_progress.py`

Deterministically applies progress and decision updates, bumps the version, refreshes the action snapshot, and appends a changelog row.

```bash
python3 scripts/prd_progress.py \
  --prd Product_PRD_v0.4.0.md \
  --updates updates.json \
  --output Product_PRD_v0.4.1.md \
  --actor "Jordan Lee" \
  [--date 2026-09-01] \
  [--bump auto|patch|minor|major] \
  [--new-version v0.4.1] \
  [--expected-version v0.4.0] \
  [--expected-sha256 <hex>] \
  [--recommend-limit 5]
```

| Flag | Required | Notes |
|---|:--:|---|
| `--prd` | ✓ | Input canonical Markdown PRD |
| `--updates` | ✓ | JSON file (see below) |
| `--output` | ✓ | New versioned path; **must differ** from the input |
| `--actor` | ✓ | Person or stable identifier recorded in the changelog |
| `--date` | | ISO date; defaults to today |
| `--bump` | | `auto` (default) picks Minor for semantic changes, Patch otherwise |
| `--new-version` | | Explicit `vX.Y.Z`; must strictly increase |
| `--expected-version` | | Abort unless the input is at this version |
| `--expected-sha256` | | Abort unless the input hash matches — use when another actor may edit concurrently |
| `--recommend-limit` | | Max next-step rows (default 5) |

On success it writes the new file atomically and prints a JSON summary (`old_version`, `new_version`, `transitions`, `recommendation_targets`, `input_sha256`, `unapplied`).

---

## Update payload format

`--updates` points at a JSON file with up to three arrays:

```json
{
  "updates": [
    {
      "id": "FR-SEARCH-001",
      "status": "Reported Complete",
      "status_basis": "Owner report with CI",
      "evidence": ["PR #42", "CI run #9001"],
      "completion_date": "2026-09-01",
      "owner": "Jordan Lee",
      "priority": "P0",
      "dependencies": "Q-003",
      "notes": "Behind feature flag search_v2"
    },
    {
      "id": "FR-SEARCH-002",
      "status": "Verified",
      "evidence": ["QA sign-off doc", "AC-SEARCH-001..005 checked"],
      "verification_confirmed": true
    }
  ],
  "dependency_updates": [
    {
      "id": "Q-003",
      "status": "Resolved",
      "evidence": "Approved permission matrix",
      "blocking_level": "Gate",
      "affects": "FR-SEARCH-001",
      "due_date": "2026-08-30"
    }
  ],
  "unapplied": [
    { "id": "FR-SEARCH-009", "reason": "No matching requirement in the PRD" }
  ]
}
```

Rules enforced by the script:

- A requirement update needs an `id` **or** a unique `title`. Ambiguous titles are reported, not guessed.
- `status: "Verified"` requires **both** `verification_confirmed: true` and non-empty `evidence`.
- `dependency_updates` accept only individual `Q-*` / `R-*` / `C-*` IDs; `status: "Resolved"` requires `evidence`.
- `status_basis` is auto-filled from the transition and `--actor` when omitted.
- `completion_date` is auto-set to the change date for `Reported Complete` / `Verified` and cleared on regressions.
- Multi-line evidence is flattened to `<br>` and pipes are escaped so tables stay well-formed.
- Credentials, tokens, and API-key patterns in the payload abort the update.
- A payload that produces no effective change is rejected ("refusing to create a fake version bump").
- A priority / dependency / blocking-level / affects change forces at least a Minor bump; forcing `--bump patch` over a semantic change is rejected.

---

## Validation rules

`prd_validate.py --strict` fails on:

- Missing or malformed marker tables, unexpected headers, wrong column counts.
- Invalid or duplicate requirement IDs; aggregate ID ranges (`Q-001–Q-010`).
- A delivery row missing its **status basis**.
- `Reported Complete` / `Verified` without a completion date.
- `Verified` without recorded evidence.
- `Blocked` without a dependency, or `Blocked` only by `Soft` dependencies.
- References to unknown dependency IDs; unknown action Target IDs; invalid or duplicate `A-*` IDs.
- No `US-*` user story or no `UC-*` use case anywhere in the document.
- A P0 functional requirement missing from the traceability matrix, or lacking a `US-*` / `UC-*` mapping or an `AC-*` mapping.
- Document / filename version mismatch (`_vX.Y.Z.md`).
- Possible credentials / secrets or internal network addresses (`10.x`, `192.168.x`, `172.16–31.x`).
- Broken relative links (`](./…)`).

Warnings (failures only under `--strict`): legacy table schemas without status basis / blocking level, legacy action-snapshot IDs, no `NFR-*` present.

---

## Repository layout

```
.
├── SKILL.md                          # Entry point: routing, invariants, versioning rules
├── agents/
│   └── openai.yaml                   # Interface metadata for Codex-style hosts
├── references/
│   ├── function-1-normalize.md       # How to normalize input into a living PRD
│   ├── function-2-track.md           # How to track delivery, evidence, decisions
│   └── prd-template.md               # Canonical reader-first PRD template
├── scripts/
│   ├── prd_validate.py               # Structural / traceability / safety validator
│   └── prd_progress.py               # Deterministic progress + versioning engine
├── tests/
│   ├── test_scripts.py               # 12 behavioral tests
│   └── fixtures/
│       └── Sample_PRD_v0.1.0.md       # Canonical fixture (passes --strict)
└── .github/workflows/test.yml        # CI: py_compile + unittest on 3.11
```

---

## Release evolution

| Release | Focus | What it added |
|---|---|---|
| **v0.2** | Reliability | Stable action / target IDs, individual decision rows, no-op and version guards, source concurrency checks, validation |
| **v0.3** | PRD quality | Status basis, `Hard` / `Soft` / `Gate` dependencies, `NFR-*` IDs, requirement-to-acceptance traceability |
| **v0.4** | Comprehension | Reader-first template, mandatory user stories and use cases, compact action snapshot, complete appendix tracker |

---

## Development

```bash
# compile-check the scripts
python3 -m py_compile scripts/prd_progress.py scripts/prd_validate.py

# run the test suite
python3 -m unittest discover -s tests -v

# validate the fixture
python3 scripts/prd_validate.py tests/fixtures/Sample_PRD_v0.1.0.md --strict
```

The tests cover: strict validation of the fixture, patch vs. minor bump selection, action-ID preservation, no-op rejection, `Verified`-needs-evidence, stale-input detection, dependency resolution unblocking a requirement, forced-patch rejection, version regression rejection, multi-line evidence safety, secret rejection, and aggregate-ID rejection.

CI (`.github/workflows/test.yml`) runs the compile check and the suite on every push to `main` and every pull request, on Python 3.11.

---

## Contributing

1. Fork and branch from `main`.
2. Keep the scripts dependency-free (standard library only) and compatible with Python 3.11+.
3. Add or update a test in `tests/test_scripts.py` for any behavior change.
4. Ensure `python3 -m unittest discover -s tests -v` and `prd_validate.py --strict` on the fixture both pass.
5. If you change the template structure or a marker, update `references/prd-template.md`, the validator, and this README together.

Issues and pull requests are welcome.

## License

Released under the [MIT License](LICENSE).
