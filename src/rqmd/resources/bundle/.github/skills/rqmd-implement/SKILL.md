---
name: rqmd-implement
description: Implement the highest-priority proposed rqmd requirements in small validated batches. Use for multi-file code changes that must stay synchronized with docs/requirements, README, tests, and CHANGELOG entries.
argument-hint: Describe the requirement IDs or behavior to implement and the expected validation scope.
user-invocable: true
metadata:
  guide:
    summary: Work highest-priority proposed requirements in small validated batches.
    workflow:
      - Start by reviewing proposed requirements and choose the highest-priority 1-3 items for the next batch.
      - Update requirements, tests, and CHANGELOG entries as implementation details become concrete instead of deferring doc updates until the end.
      - Before taking the next batch, verify rqmd still runs, verify summaries, run the test suite, and re-check remaining proposal priorities.
    examples:
      - rqmd-ai --json --workflow-mode implement
      - rqmd-ai --json --dump-status proposed
      - rqmd --verify-summaries --no-walk --no-table
      - uv run --extra dev pytest -q
    batch_policy:
      max_items: 3
      selection_order: highest-priority proposed first
    validation_checks:
      - rqmd runs without startup errors
      - requirement summaries verify cleanly
      - full test suite passes
      - remaining proposal priorities are reviewed before continuing
---

Use this skill when a requirement is ready to move from proposal into implementation.

Workflow:
- Start with `rqmd-ai --json --workflow-mode implement`.
- Review the current proposal queue with `rqmd-ai --json --dump-status proposed`.
- Take the highest-priority 1-3 proposed requirements for the next batch.
- Update requirement docs, tests, README, and `CHANGELOG.md` as implementation details become concrete.
- Verify the result with `rqmd --verify-summaries --no-walk --no-table`, targeted tests, and then `uv run --extra dev pytest -q` before continuing.

Constraints:
- Keep changes focused and avoid broad unrelated refactors.
- Re-check remaining priorities before starting another batch.
- Skills improve workflow discovery; shell and tool approvals may still be required.