---
name: rqmd-docs
description: Improve repository documentation quality using authored standards for readability, structure, jargon handling, and page organization. Use when docs need more than simple drift correction.
argument-hint: Describe which documentation pages need improvement and whether the work is about structure, clarity, jargon, callouts, or splitting long pages.
user-invocable: true
metadata:
  guide:
    summary: Improve documentation quality as a first-class workflow, not just a sync pass.
    workflow:
      - Start from the active documentation standards and the audience for the page.
      - Improve headings, page structure, hyperlinks, jargon explanations, and list formatting so the doc is faster to scan and easier to trust.
      - Split oversized pages into smaller linked pages or index pages when that meaningfully improves navigation.
    examples:
      - rqmd --verify-summaries --no-walk --no-table
      - rqmd-ai --json --dump-id RQMD-AI-040 --include-requirement-body
      - rqmd-ai --json --dump-status proposed
---

Use this skill when the documentation itself needs better writing, structure, or organization rather than only post-change alignment.

Workflow:
- Use headings consistently: start at h1 and do not skip heading levels.
- Prefer many smaller pages over one oversized page; create brief index pages when splitting large content improves navigation.
- Introduce acronyms and jargon on first use, and add Info-style callouts when readers may need extra context.
- Prefer descriptive hyperlinks over raw pasted URLs.
- Use ordered or unordered lists to break up dense prose when they improve scanning.
- Use Info, Note, and Warning callouts deliberately to separate optional context, important reminders, and critical warnings.
- Keep documentation technical but user-friendly, written like a web article worth reading rather than a dump of internal notes.
- Never include secrets in documentation or code examples.

Callout examples:

> **ℹ️ Info:** `rqmd --verify-summaries --no-walk --no-table` only verifies summary blocks and does not rewrite requirement files.

> **⚠️ Note:** If a page introduces `rqmd-ai` before `rqmd`, expand the acronym on first use and explain the relationship once rather than assuming prior context.

> **🚨 Warning:** Do not paste tokens, credentials, or internal-only URLs into repository documentation, even in examples.

Use that exact callout shape when you need one; avoid mixing in all-caps or multiple icon variants unless a repository already standardized on them.

Constraints:
- Do not use this skill when the real task is only keeping docs aligned with a known behavior change; use `/rqmd-doc-sync` for that.
- Keep requirement docs, README guidance, and bundle text consistent with shipped behavior when you improve them.
- Prefer focused improvements over needless rewrites, but do restructure or split pages when readability is clearly suffering.
- Skills improve workflow discovery; shell and tool approvals may still be required.
