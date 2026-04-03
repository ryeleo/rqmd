---
name: rqmd-verify
description: Verify rqmd requirement/documentation sync and post-change validation. Use after edits to re-run summary verification, targeted tests, full tests, and any final requirement-status checks before completion.
argument-hint: Describe what changed and whether you want targeted validation, a full verification pass, or both.
user-invocable: true
metadata:
  guide:
    summary: Run the finish-pass verification loop after edits land.
    workflow:
      - Re-run summary verification first.
      - Run targeted tests for the touched area.
      - Run the full test suite before calling the batch complete.
    examples:
      - rqmd --verify-summaries --no-walk --no-table
      - uv run --extra dev pytest tests/test_ai_cli.py -q
      - uv run --extra dev pytest -q
---

Use this skill when changes are already in progress and you need a disciplined finish pass.

Workflow:
- Re-run requirement summary verification with `rqmd --verify-summaries --no-walk --no-table`.
- Run targeted tests for the touched area first.
- Run the full test suite with `uv run --extra dev pytest -q`.
- If work affected backlog state, re-check `rqmd-ai --json --dump-status proposed` so priorities remain accurate.
- Call out any residual risk, missing validation, or requirement/doc drift before finishing.

Constraints:
- Prefer deterministic validation commands.
- Report clearly when validation could not be completed.
- Skills improve workflow discovery; shell and tool approvals may still be required.
