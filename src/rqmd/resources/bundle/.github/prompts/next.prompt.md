---
description: "Suggest the highest-priority feasible next slice, prefer handoff via /go, and keep worktree health explicit."
name: "next"
argument-hint: "Say 'next' to continue the backlog, or add a constraint such as 'easy-win', 'docs-only', or 'release-prep'."
agent: "rqmd"
---

Choose the next coherent slice, prioritize recommendation and handoff, and only implement immediately when the user asks.

- Prefer tracked requirements and the highest-priority feasible next item instead of asking the user to restate the backlog.
- If one clear next slice exists, recommend it and provide a copy-paste-ready `/go` prompt that names requirement IDs, batch order, and dependency sequencing.
- If priorities are ambiguous, run a short re-triage with the user and present the top options with trade-offs.
- Respect constraints in the argument: `easy-win` means low-risk quick wins, `docs-only` means documentation work, `release-prep` means polish and verification.
- Keep working-directory health explicit: remind the user to commit current work (or intentionally stash) before switching slices when the worktree is dirty.
- If the user asks to execute immediately, then run the selected slice through implementation and validation.
