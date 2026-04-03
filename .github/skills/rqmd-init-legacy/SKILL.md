---
name: rqmd-init-legacy
description: Compatibility alias for the older legacy-repo init flow. Prefer rqmd-init unless you need to force legacy-style repository seeding explicitly.
argument-hint: Describe the repository, preferred requirements directory, ID prefix, and whether GitHub issues should be consulted when available.
user-invocable: true
metadata:
  guide:
    summary: Seed rqmd into a legacy repository by reviewing a generated first-pass requirements catalog before writing it.
    workflow:
      - Start from the current repository structure, commands, docs, and backlog instead of assuming a blank scaffold.
      - Preview the generated requirements index and starter domain files before writing anything.
      - Apply the bootstrap only into an empty requirements directory, then immediately refine the generated seeds.
    examples:
      - rqmd-ai init --chat --json --legacy
      - rqmd-ai init --chat --json --legacy --show-guide
      - rqmd-ai init --json --legacy --write --id-namespace RQMD
  legacy_init:
    default_requirements_dir: docs/requirements
    max_domain_files: 5
    max_issue_requirements: 5
    max_source_areas: 4
---

Use this skill when you explicitly need the old legacy-init behavior or are following older docs during the transition to `rqmd-init`.

Workflow:
- Prefer `rqmd-ai init --chat --json --legacy` for new usage; keep this skill for compatibility and explicit override cases.
- Preview the legacy-init plan with `rqmd-ai init --chat --json --legacy`.
- If the repository uses a nonstandard requirements location, pass `--docs-dir` explicitly before applying.
- Let the workflow inspect repository structure and developer commands, and let it consult `gh issue list` when GitHub CLI is installed and authenticated.
- Use the grouped interview to choose catalog defaults, review inferred workflow commands, inspect recommended choices and safe defaults, select starter domains, decide how to treat existing docs and tests, and capture custom notes.
- Review the generated `README.md`, workflow seed, domain seeds, and any issue-backlog seed before relying on them.
- Apply with `rqmd-ai init --json --legacy --write` only when the target requirements directory is empty.

Constraints:
- Treat generated requirements as a starting point, not authoritative truth.
- Keep the first write focused on a small, editable starter catalog rather than an exhaustive migration.
- Gracefully continue when `gh` is unavailable, unauthenticated, or the repository has no visible issues.
- Skills improve workflow discovery; shell and tool approvals may still be required.
