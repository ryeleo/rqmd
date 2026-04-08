---
description: "Capture durable context, decisions, or quick-reference notes in a maintainable pinned note instead of leaving them in chat history."
name: "pin"
argument-hint: "Describe what should be pinned and, if known, where it should live."
agent: "rqmd-dev"
---

Capture something worth keeping in a durable repository note.

- Write the context, decision, or reminder as a readable note instead of leaving it buried in chat history.
- Default to `docs/pins/` when the right location is not obvious, but prefer a more specific home if one exists (e.g., an ADR folder, a design doc, or a project wiki).
- Keep the note concise, reviewable, and easy to rediscover later.
- If the pin collection or surrounding docs need cleanup, tidy them as part of the same pass.
