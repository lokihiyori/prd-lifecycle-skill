# PRD Lifecycle Skill

Create reader-friendly, evidence-aware PRDs and maintain their requirements, user stories, use cases, acceptance criteria, decisions, progress, and release history.

## Release evolution

| Release | Focus | Included in current v0.4 design |
|---|---|---|
| v0.2 | Reliability | Stable action/target IDs, individual decisions, no-op/version guards, source concurrency checks, validation |
| v0.3 | PRD quality | Status basis, Hard/Soft/Gate dependencies, NFR IDs, requirement-to-acceptance traceability |
| v0.4 | Comprehension | Reader-first template, mandatory user stories and use cases, compact action snapshot, complete appendix tracker |

## Example prompts

```text
Use $prd-lifecycle to turn these product notes into a Markdown PRD. Include user stories and detailed use cases for every P0 flow.
```

```text
Use $prd-lifecycle to update FR-SEARCH-001 to Reported Complete with PR #42 as evidence, then recommend the next unblocked work.
```

## Validation

```bash
python3 scripts/prd_validate.py Product_PRD_v0.4.0.md --strict
python3 -m unittest discover -s tests -v
```

Progress updates use `scripts/prd_progress.py`. Run `python3 scripts/prd_progress.py --help` for update and concurrency options.

Example update payload:

```json
{
  "updates": [
    {
      "id": "FR-SEARCH-001",
      "status": "Reported Complete",
      "status_basis": "Owner report with CI",
      "evidence": ["PR #42", "CI run #9001"]
    }
  ],
  "dependency_updates": [
    {
      "id": "Q-003",
      "status": "Resolved",
      "evidence": "Approved permission matrix"
    }
  ]
}
```
