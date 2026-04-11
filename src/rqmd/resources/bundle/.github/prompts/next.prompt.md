---
description: "Pick the highest-priority feasible next slice and work it through the standard validation loop."
name: "next"
argument-hint: "Say 'next' to continue the backlog, or add a constraint such as 'easy-win', 'docs-only', or 'release-prep'."
agent: "rqmd"
---

Choose the next coherent slice and work it through implementation and validation.

- Prefer tracked requirements and the highest-priority feasible next item instead of asking the user to restate the backlog.
- Re-triage briefly if the next best slice is ambiguous, then move into implementation without unnecessary back-and-forth.
- Respect constraints in the argument: `easy-win` means low-risk quick wins, `docs-only` means documentation work, `release-prep` means polish and verification.
- Keep the work validated in small batches with docs and CHANGELOG aligned when the changes warrant it.
- Surface blockers clearly if there is no safe or coherent next slice to take.
