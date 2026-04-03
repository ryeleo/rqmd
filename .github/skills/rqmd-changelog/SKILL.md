---
name: rqmd-changelog
description: Keep CHANGELOG.md clear, human-led, and Keep a Changelog-aligned. Use when preparing Unreleased notes, tightening noisy release entries, or deciding which implementation details belong in the public changelog.
argument-hint: Describe the release slice, recent work, or changelog section that needs to be curated.
user-invocable: true
metadata:
  guide:
    summary: Curate CHANGELOG.md as a concise release narrative led by user-visible outcomes and human decisions.
    workflow:
      - Start from the shipped behavior, requirement updates, and recent user-directed changes.
      - Write the primary changelog bullets for end-user impact, release-relevant decisions, and notable workflow shifts.
      - Keep supporting AI implementation detail subordinate under a nested heading such as `AI Development` when it adds useful context.
    examples:
      - rqmd --verify-summaries --no-walk --no-table
      - rqmd-ai --json --dump-status proposed
      - rqmd-ai --json --workflow-mode implement
---

Use this skill when changelog quality matters as its own task, not just as a side effect of general docs sync.

Workflow:
- Update `CHANGELOG.md` under `Unreleased` before cutting a new version when the work has not shipped yet.
- Lead with human-directed decisions, user-visible behavior changes, and other release-relevant outcomes.
- When a bullet mainly records that a tracked requirement shipped, prefer wording like `Implemented RQMD-UNDO-008: size, retention, and compaction policy for persisted history` instead of `Updated requirement status to mark RQMD-UNDO-008 as Implemented ...`.
- Keep low-signal implementation detail out of the primary bullets; if the detail matters, group it under a nested `AI Development` heading instead of mixing it into the main narrative.
- Prefer concise bullets that a human reviewer can scan quickly during release prep.
- Keep the changelog aligned with the affected requirement docs, README guidance, and bundle workflow text when those surfaces changed too.

Constraints:
- Preserve Keep a Changelog structure.
- Do not turn the changelog into a commit log or exhaustive implementation diary.
- Include AI-enabling work only when it materially explains the shipped outcome or future maintenance path.
- Skills improve workflow discovery; shell and tool approvals may still be required.
