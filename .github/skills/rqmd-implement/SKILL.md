---
name: rqmd-implement
description: Implement the highest-priority proposed rqmd requirements in small validated batches. Use for multi-file code changes that must stay synchronized with docs/requirements, README, tests, and CHANGELOG entries.
argument-hint: Describe the requirement IDs or behavior to implement and the expected validation scope.
user-invocable: true
---

Use this skill when a requirement is ready to move from proposal into implementation.

Workflow:
- Start with `uv run rqmd-ai --as-json --workflow-mode implement`.
- Review the current proposal queue with `uv run rqmd-ai --as-json --dump-status proposed`.
- Take the highest-priority 1-3 proposed requirements for the next batch.
- Update requirement docs, tests, README, and `CHANGELOG.md` as implementation details become concrete.
- Verify the result with `uv run rqmd --verify-summaries --no-walk --no-table`, targeted tests, and then `uv run --extra dev pytest -q` before continuing.

Constraints:
- Keep changes focused and avoid broad unrelated refactors.
- Re-check remaining priorities before starting another batch.
- Skills improve workflow discovery; shell and tool approvals may still be required.