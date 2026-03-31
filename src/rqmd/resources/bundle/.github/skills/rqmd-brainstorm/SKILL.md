---
name: rqmd-brainstorm
description: Turn brainstorm notes or loose ideas into ranked rqmd requirement proposals before implementation. Use for docs/brainstorm.md review, backlog grooming, requirement planning, and mapping ideas into docs/requirements/*.md with suggested IDs, statuses, and priorities.
argument-hint: Describe the brainstorm source and which requirement area it should likely affect.
user-invocable: true
metadata:
  guide:
    summary: Turn loose planning notes into ranked requirement proposals before implementation starts.
    workflow:
      - Start from raw planning notes such as docs/brainstorm.md or targeted requirement exports.
      - Promote brainstorm items into tracked requirement proposals with target docs, IDs, statuses, and priorities.
      - Keep the output read-only so requirement changes can be reviewed before any implementation work begins.
    examples:
      - rqmd-ai --json --workflow-mode brainstorm
      - rqmd-ai --json --dump-file ai-cli.md --include-domain-markdown
      - rqmd-ai --json --dump-status proposed
  brainstorm:
    default_target_file: ai-cli.md
    default_priority_rank: -1
    proposal_title:
      max_words: 10
      max_chars: 96
    proposal_sort:
      priority_source: runtime-catalog
    section_targets:
      - tokens: [ai workflow, agent, skill]
        target_file: ai-cli.md
      - tokens: [ux, interactive, ctrl + z]
        target_file: interactive-ux.md
      - tokens: [screen write, scroll]
        target_file: screen-write.md
      - tokens: [priority]
        target_file: priority.md
      - tokens: [filter, schema version]
        target_file: automation-api.md
      - tokens: [readme, rename key, external links, blocking]
        target_file: core-engine.md
      - tokens: [reqmd, rename, pypi]
        target_file: packaging.md
      - tokens: [debug why rqmd fails, desktop-verified, user story]
        target_file: portability.md
      - tokens: [performance, rust, native]
        target_file: core-engine.md
    priority_hints:
      - tokens: [critical, p0, must, crash, fails, regression]
        priority_rank: 0
      - tokens: [implement, workflow, agent, ai, summary, readme, blocking]
        priority_rank: 1
      - tokens: [priority, filter, link, schema, user story, screen]
        priority_rank: 2
---

Use this skill when the work starts as notes instead of tracked requirements.

Workflow:
- Export planning guidance with `uv run rqmd-ai --json --workflow-mode brainstorm`.
- Read the brainstorm source, usually `docs/brainstorm.md`.
- Cross-check existing backlog with `uv run rqmd-ai --json --dump-status proposed`.
- Convert viable ideas into tracked proposals with target requirement docs, suggested IDs, canonical `💡 Proposed` status, and priorities that follow the active project priority catalog.
- Update requirement docs, the requirements index, and `CHANGELOG.md` before code when the proposal changes shipped behavior or workflow.

Constraints:
- Do not skip requirement tracking and jump straight to code for net-new behavior.
- Keep the output read-only until requirement/doc changes are reviewed.
- Skills improve workflow discovery; shell and tool approvals may still be required.