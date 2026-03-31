---
name: rqmd-status-maintenance
description: Safely update requirement statuses, priorities, and focused worklists with rqmd and rqmd-ai. Use for planned status transitions, priority triage, filter-driven maintenance, and guarded requirement doc mutations.
argument-hint: Describe the requirement IDs, desired status or priority updates, and whether you want preview-only or apply mode.
user-invocable: true
---

Use this skill when the task is primarily about requirement metadata rather than product code.

Workflow:
- Preview requirement changes first with `uv run rqmd-ai --json --update ID=STATUS`.
- Apply only after review with `uv run rqmd-ai --json --write --update ID=STATUS`.
- Use `uv run rqmd --update-priority ID=p1` or repeated `--update-priority` flags for priority maintenance.
- Use rqmd filters such as `--status`, `--priority`, `--flagged`, `--has-link`, or positional tokens to build focused maintenance worklists.
- Re-run summary verification after any requirement mutation.

Constraints:
- Keep status and priority changes aligned with the actual code and test state.
- Prefer machine-readable preview/apply flows for multi-update maintenance.
- Skills improve workflow discovery; shell and tool approvals may still be required.