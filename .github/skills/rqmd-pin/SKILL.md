---
name: rqmd-pin
description: Capture durable context, decisions, and quick-reference notes in a maintained home that stays easy to find across sessions. Use for project memory, decision logs, pinned reminders, and choosing where persistent notes should live.
argument-hint: Describe what should be pinned, whether it is a new note or an update, and where it currently lives if a location already exists.
user-invocable: true
metadata:
  guide:
    summary: Capture durable project context in a stable, reviewable home instead of leaving it buried in chat history.
    workflow:
      - Decide whether the note belongs in an existing nearby doc, a README section, or a dedicated `docs/pins/` area.
      - Prefer one focused note per topic, defaulting to `docs/pins/` when the best location is unclear.
      - Keep pin collections navigable with an index page and hand broader organization cleanup to `/rqmd-docs` when needed.
    examples:
      - rqmd-ai --json --dump-id RQMD-AI-042 --include-requirement-body
      - rqmd --verify-summaries --no-walk --no-table
      - rqmd-ai --json --dump-status proposed
---

Use this skill when important context should stay easy to find after the current conversation or implementation session ends.

Workflow:
- Decide whether the note belongs in an existing document, a small README section, or a dedicated `docs/pins/` folder.
- Default to `docs/pins/` with one markdown file per topic when the best location is unclear or when maintainability matters more than clever placement.
- When using `docs/pins/`, keep a lightweight `docs/pins/README.md` index and start new notes from a simple template such as `docs/pins/pin-template.md`.
- Give each pin a focused title and keep it readable, reviewable, and easy to update later.
- Link pins to the relevant requirements, docs, or implementation areas when those references make the note easier to trust or revisit.
- Add or update an index page when pin collections grow large enough that navigation would otherwise become sloppy.
- Use `/rqmd-docs` for follow-on cleanup when a growing pin area needs better structure, headings, or cross-linking.

Constraints:
- Do not let pinned notes replace the canonical requirement or changelog record when the information belongs there.
- Prefer stable, maintainable storage over burying durable notes in transient chat transcripts or scratch files.
- Keep the workflow flexible across repositories instead of forcing one storage layout everywhere.
- Skills improve workflow discovery; shell and tool approvals may still be required.
