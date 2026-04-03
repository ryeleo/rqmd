---
name: rqmd-export-context
description: Export focused rqmd and rqmd-ai context for prompts, reviews, and automation handoffs. Use for next-batch proposal slices, single-requirement deep dives, or bounded domain markdown when an agent needs only the relevant context.
argument-hint: Describe whether you need next-batch proposals, one requirement, or bounded domain context.
user-invocable: true
metadata:
  guide:
    summary: Default read-only rqmd-ai workflow for context export, preview, and guarded apply.
    workflow:
      - Export context with --dump-id/--dump-status/--dump-file.
      - Draft updates using --update ID=STATUS without --write to preview.
      - Apply only after review by adding --write.
    examples:
      - rqmd-ai --json --dump-status proposed
      - rqmd-ai --json --dump-id RQMD-CORE-001 --include-requirement-body
      - rqmd-ai --json --dump-file ai-cli.md --include-domain-markdown
      - rqmd-ai --json --dump-status proposed --history-ref 0
      - rqmd-ai --update RQMD-CORE-001=implemented
      - rqmd-ai --update RQMD-CORE-001=implemented --write
---

Use this skill when an agent needs precise context instead of the full repository.

Workflow:
- Start with `rqmd-ai --json` for baseline guidance when needed.
- For next-batch implementation handoffs, export `rqmd-ai --json --dump-status proposed` and then keep the slice narrowed to the highest-priority 1-3 requirements under discussion.
- For a single requirement under active work, export `rqmd-ai --json --dump-id <ID> --include-requirement-body` so the implementation context includes the full body and stable metadata.
- For architecture or domain rationale, export `rqmd-ai --json --dump-file <domain>.md --include-domain-markdown --max-domain-markdown-chars <N>` with a strict size limit.
- Prefer one requirement, one proposal slice, or one bounded domain at a time instead of a broad multi-domain dump.

Constraints:
- Keep exported context scoped and machine-readable by default.
- Avoid dumping the whole backlog when a next-batch proposal slice is enough.
- Avoid dumping whole domains when an ID-level export plus bounded domain markdown is enough.
- Skills improve workflow discovery; shell and tool approvals may still be required.
