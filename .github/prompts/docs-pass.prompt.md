---
description: "Run a focused documentation pass for rqmd work such as README polish, changelog cleanup, or doc sync after behavior changes."
name: "docs-pass"
argument-hint: "Describe the doc surface that needs a pass, or say what changed so the docs can be brought back in sync."
agent: "rqmd-dev"
---

Use the rqmd documentation workflow for this task.

- Focus on documentation quality, synchronization, and readability before considering broader implementation work.
- Prefer the installed rqmd docs, doc-sync, and changelog workflows when they match the requested pass.
- Keep requirement docs, README guidance, and CHANGELOG entries aligned with the shipped behavior.
- Make the smallest coherent documentation slice that improves discoverability and trust.
