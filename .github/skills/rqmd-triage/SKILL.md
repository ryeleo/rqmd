---
name: rqmd-triage
description: Review, rank, and select the next rqmd backlog slice from tracked requirements. Use for proposal triage, next-batch selection, backlog grooming, and deciding which 1-3 requirements should move next.
argument-hint: Describe the backlog area, status filter, or requirement domain you want to triage.
user-invocable: true
metadata:
  guide:
    summary: Review and narrow the next implementation slice from tracked proposed requirements.
    workflow:
      - Export the current proposal queue with --dump-status proposed.
      - Narrow broad backlogs with --dump-file, --dump-id, or targeted rqmd filters.
      - Pick the highest-value 1-3 items using priority, blocking relationships, and batch size.
    examples:
      - rqmd-ai --json --dump-status proposed
      - rqmd-ai --json --dump-file core-engine.md
      - rqmd --status proposed --priority p1 --json --no-walk
---

Use this skill when tracked requirements already exist and you need to decide what to work next.

Workflow:
- Export the current proposal queue with `rqmd-ai --json --dump-status proposed`.
- Narrow to a domain or requirement with `--dump-file`, `--dump-id`, or targeted rqmd filters when the backlog is broad.
- Rank candidates by priority, blocking relationships, and implementation batch size.
- Pick the highest-value 1-3 items for the next implementation slice.
- Re-check remaining priorities after each shipped batch so the queue stays accurate.

Constraints:
- Prefer tracked requirement proposals over scratch notes once backlog entries already exist.
- Keep selection logic explicit so future agents can understand why a batch was chosen.
- Skills improve workflow discovery; shell and tool approvals may still be required.