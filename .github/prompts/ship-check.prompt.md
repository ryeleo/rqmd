---
description: "Run a release or handoff readiness pass covering verification, docs state, changelog quality, and remaining blockers."
name: "ship-check"
argument-hint: "Describe what is about to ship, or say what kind of final verification you want."
agent: "rqmd-dev"
---

Release-readiness check — verify the work is ready to ship.

- Focus on final verification: tests pass, docs are synchronized, changelog is accurate, and no obvious blockers remain.
- Run the project's smoke and validation commands before declaring the work ready.
- Check that README, CHANGELOG, and any requirement/status docs reflect the current shipped behavior.
- Call out blockers or residual risk plainly instead of smoothing them over.
- Summarize the ship-check result with a clear go / no-go and any recommended follow-ups.
