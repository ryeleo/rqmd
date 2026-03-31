---
name: rqmd-brainstorm
description: Turn brainstorm notes or loose ideas into ranked rqmd requirement proposals before implementation. Use for docs/brainstorm.md review, backlog grooming, requirement planning, and mapping ideas into docs/requirements/*.md with suggested IDs, statuses, and priorities.
argument-hint: Describe the brainstorm source and which requirement area it should likely affect.
user-invocable: true
---

Use this skill when the work starts as notes instead of tracked requirements.

Workflow:
- Export planning guidance with `uv run rqmd-ai --json --workflow-mode brainstorm`.
- Read the brainstorm source, usually `docs/brainstorm.md`.
- Cross-check existing backlog with `uv run rqmd-ai --json --dump-status proposed`.
- Convert viable ideas into tracked proposals with target requirement docs, suggested IDs, canonical `💡 Proposed` status, and priorities.
- Update requirement docs, the requirements index, and `CHANGELOG.md` before code when the proposal changes shipped behavior or workflow.

Constraints:
- Do not skip requirement tracking and jump straight to code for net-new behavior.
- Keep the output read-only until requirement/doc changes are reviewed.
- Skills improve workflow discovery; shell and tool approvals may still be required.