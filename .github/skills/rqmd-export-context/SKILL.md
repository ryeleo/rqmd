---
name: rqmd-export-context
description: Export focused rqmd and rqmd-ai context for prompts, reviews, and automation handoffs. Use for requirement slices by status, ID, file, or bounded domain markdown when an agent needs only the relevant context.
argument-hint: Describe which requirement slice or document context you need to export.
user-invocable: true
---

Use this skill when an agent needs precise context instead of the full repository.

Workflow:
- Start with `uv run rqmd-ai --as-json` for baseline guidance when needed.
- Export targeted slices with `uv run rqmd-ai --as-json --dump-status proposed`, `--dump-id <ID>`, or `--dump-file <domain>.md`.
- Include richer requirement text with `--include-requirement-body` when the body drives implementation.
- Include bounded domain rationale with `--include-domain-markdown --max-domain-markdown-chars <N>` when architecture notes matter.
- Prefer the smallest payload that still preserves stable IDs and requirement meaning.

Constraints:
- Keep exported context scoped and machine-readable by default.
- Avoid dumping whole domains when an ID- or status-level slice is enough.
- Skills improve workflow discovery; shell and tool approvals may still be required.