---
name: rqmd-verify
description: Verify rqmd requirement/documentation sync and post-change validation. Use after edits to re-run summary verification, targeted tests, full tests, and any final requirement-status checks before completion.
argument-hint: Describe what changed and whether you want targeted validation, a full verification pass, or both.
user-invocable: true
---

Use this skill when changes are already in progress and you need a disciplined finish pass.

Workflow:
- Re-run requirement summary verification with `uv run rqmd --verify-summaries --no-walk --no-table`.
- Run targeted tests for the touched area first.
- Run the full test suite with `uv run --extra dev pytest -q`.
- If work affected backlog state, re-check `uv run rqmd-ai --json --dump-status proposed` so priorities remain accurate.
- Call out any residual risk, missing validation, or requirement/doc drift before finishing.

Constraints:
- Prefer deterministic validation commands.
- Report clearly when validation could not be completed.
- Skills improve workflow discovery; shell and tool approvals may still be required.