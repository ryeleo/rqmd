---
name: rqmd-init-legacy
description: Bootstrap rqmd in an existing repository by generating a reviewable first-pass requirements folder from the current codebase, developer workflows, and optional GitHub issue backlog.
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
      - rqmd-ai --json --workflow-mode init-legacy --show-guide
      - rqmd-ai --json --workflow-mode init-legacy
      - rqmd-ai --json --workflow-mode init-legacy --write --id-namespace RQMD
  legacy_init:
    default_requirements_dir: docs/requirements
    max_domain_files: 5
    max_issue_requirements: 5
    max_source_areas: 4
---

Use this skill when introducing rqmd into a repository that already has code, docs, and an existing backlog.

Workflow:
- Preview the bootstrap plan with `uv run rqmd-ai --json --workflow-mode init-legacy --bootstrap-chat`.
- If the repository uses a nonstandard requirements location, pass `--docs-dir` explicitly before applying.
- Let the workflow inspect repository structure and developer commands, and let it consult `gh issue list` when GitHub CLI is installed and authenticated.
- Use the grouped interview to choose catalog defaults, review inferred workflow commands, select starter domains, decide how to treat existing docs and tests, and capture custom notes.
- Review the generated `README.md`, workflow seed, domain seeds, and any issue-backlog seed before relying on them.
- Apply with `uv run rqmd-ai --json --workflow-mode init-legacy --write` only when the target requirements directory is empty.

Constraints:
- Treat generated requirements as a starting point, not authoritative truth.
- Keep the first write focused on a small, editable starter catalog rather than an exhaustive migration.
- Gracefully continue when `gh` is unavailable, unauthenticated, or the repository has no visible issues.
- Skills improve workflow discovery; shell and tool approvals may still be required.