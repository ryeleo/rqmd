---
description: "Pick the highest-priority feasible next rqmd slice and work it through the standard validation loop."
name: "next"
argument-hint: "Say 'next' to continue the backlog, or add a short constraint such as easy-win, docs-only, or release-prep."
agent: "rqmd-dev"
---

Use the standard rqmd implementation loop, but start by choosing the next coherent slice.

- Prefer tracked requirements and the highest-priority feasible next item instead of asking the user to restate the backlog.
- Re-triage briefly if the next best slice is ambiguous, then move into implementation.
- Keep the work requirement-first, validated in small batches, and aligned with README and CHANGELOG updates when needed.
- Surface blockers clearly if there is no safe or coherent next slice to take.