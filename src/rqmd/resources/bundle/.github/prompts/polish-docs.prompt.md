---
description: "Run a focused documentation pass — README polish, changelog cleanup, doc sync, or docstring alignment after behavior changes."
name: "polish-docs"
argument-hint: "Describe what changed or which doc surface needs a pass. Can target README, changelog, requirement docs, or code docstrings."
agent: "rqmd"
---

Use the rqmd documentation workflow for this task.

- Focus on documentation quality, synchronization, and readability before considering broader implementation work.
- Prefer the installed rqmd docs, doc-sync, and changelog workflows when they match the requested pass.
- Keep requirement docs, README guidance, and CHANGELOG entries aligned with shipped behavior.
- When polishing docs, also audit code docstrings in the touched area. Docstrings that contradict the shipped behavior or use stale parameter names are a documentation bug — fix them as part of the same pass.
- Make the smallest coherent documentation slice that improves discoverability and trust.
- If the pass reveals code that needs refactoring rather than just doc fixes, note it but keep this pass focused on docs. Use `/refactor` for the code side.
