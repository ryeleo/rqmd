---
name: rqmd-doc-sync
description: Synchronize rqmd requirement docs, summaries, README guidance, and changelog entries after behavior changes. Use when shipped behavior is already understood and the main task is to close documentation drift.
argument-hint: Describe what changed and which docs or requirement files need alignment.
user-invocable: true
metadata:
  guide:
    summary: Close documentation drift after a behavior change without turning the task into a broader writing or restructure pass.
    workflow:
      - Update the affected requirement docs first.
      - Keep README, changelog, and bundle guidance aligned with the shipped behavior.
      - Hand broader readability, structure, or page-splitting work to `/rqmd-docs` when needed.
      - Re-run summary verification before finishing.
    examples:
      - rqmd --verify-summaries --no-walk --no-table
      - rqmd-ai --json --dump-id RQMD-CORE-001 --include-requirement-body
      - rqmd-ai --json --workflow-mode implement
---

Use this skill when code changes are done and the main remaining task is alignment, not documentation craft.

Workflow:
- Update the affected requirement docs in `docs/requirements/*.md`.
- Keep `docs/requirements/README.md`, top-level `README.md`, and `CHANGELOG.md` aligned with shipped behavior.
- Use `/rqmd-docs` instead when the real task is improving structure, headings, jargon explanations, or splitting long pages.
- If work changed AI workflows or onboarding, update `.github/copilot-instructions.md` and any installed bundle text as needed.
- Re-run `rqmd --verify-summaries --no-walk --no-table`.
- Call out any remaining drift or docs that still need manual judgment.

Constraints:
- Treat requirement markdown as product surface, not optional notes.
- Prefer small doc updates tied directly to shipped behavior.
- Skills improve workflow discovery; shell and tool approvals may still be required.
