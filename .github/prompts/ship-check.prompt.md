---
description: "Run an rqmd release or handoff readiness pass covering verification, docs state, changelog quality, and remaining blockers."
name: "ship-check"
argument-hint: "Describe what is about to ship, or say what kind of final verification you want."
agent: "rqmd-dev"
---

Use the rqmd verification and release-readiness workflow for this task.

- Focus on final verification, changelog quality, requirements/doc sync, and any obvious release or handoff blockers.
- Prefer the installed rqmd verify and changelog workflows when they match the requested pass.
- Run the relevant summary checks and targeted validation before declaring the work ready.
- Call out blockers or residual risk plainly instead of smoothing them over.