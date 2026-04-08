---
name: rqmd-init
description: Initialize rqmd in a repository using the default chat-first flow, with heuristic routing between starter scaffold and legacy-style repository seeding.
argument-hint: Describe the repository, preferred requirements directory, ID prefix, whether to force legacy mode, and whether the AI chat flow should drive the interview.
user-invocable: true
metadata:
  guide:
    summary: Start rqmd with the unified init workflow, favoring the AI-chat flow and falling back to explicit compatibility paths when needed.
    workflow:
      - Start with the chat-first init command so the receiving AI can drive the grouped interview and preview the generated files.
      - Let rqmd choose between starter scaffold mode and legacy-style repository seeding unless the repository needs an explicit legacy override.
      - Review the generated requirements catalog and any suggested `/dev` and `/test` workflow skills before writing.
      - Apply only after explicit confirmation, then verify summaries and begin refining the generated requirements.
    examples:
      - rqmd-ai init --chat --json
      - rqmd-ai init --chat --json --legacy
      - rqmd-ai init --json --write --legacy --id-namespace RQMD
      - rqmd init
  legacy_init:
    default_requirements_dir: docs/requirements
    max_domain_files: 5
    max_issue_requirements: 5
    max_source_areas: 4
---

Use this skill when bringing rqmd into a repository for the first time and you want the product-default onboarding flow.

Workflow:
- Start with `rqmd-ai init --chat --json` or simply `rqmd init`.
- Paste the generated handoff prompt into your AI chat and let the chat agent run the grouped interview.
- Let init choose the setup strategy automatically unless the repository clearly needs `--legacy`.
- Review the generated requirements index, starter files, and any follow-up bundle skill previews before writing.
- Apply only after confirmation, then run `rqmd --verify-summaries --non-interactive` and start refining the generated requirements.

Constraints:
- Treat generated requirements as a starting point, not final truth.
- Keep `rqmd-init-legacy` available as a compatibility path during migration, but teach `rqmd-init` as the primary surface.
- Skills improve workflow discovery; shell and tool approvals may still be required.
