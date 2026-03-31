---
name: rqmd-bundle
description: Install, refresh, and explain the rqmd AI agent and skill bundle for a workspace. Use for onboarding repositories, previewing bundle changes, preserving customized files, and clarifying how skills relate to approval prompts.
argument-hint: Describe whether you want a dry-run preview, minimal/full install, overwrite behavior, or bundle customization.
user-invocable: true
metadata:
  guide:
    summary: Preview or install the rqmd Copilot bundle while preserving workspace customizations by default.
    workflow:
      - Preview bundle changes first with a dry run.
      - Install the minimal or full preset intentionally.
      - Overwrite existing workspace customization files only when replacement is explicitly desired.
    examples:
      - rqmd-ai i --json --bundle-preset minimal --dry-run
      - rqmd-ai install --json
      - rqmd-ai install --json --bundle-preset full --overwrite-existing
---

Use this skill when the work is about Copilot instructions, agents, skills, or bundle installation rather than the application itself.

Workflow:
- Preview bundle changes with `uv run rqmd-ai i --json --bundle-preset minimal --dry-run`.
- For AI-guided onboarding, use `uv run rqmd-ai i --json --bundle-preset minimal --bootstrap-chat --dry-run` to get grouped interview prompts with multi-select suggestions, custom-answer prompts, skip support, recommended choices, safe defaults, and generated `/dev` and `/test` skill previews.
- Install the standard bundle with `uv run rqmd-ai install --json`.
- Repeat `--bootstrap-answer FIELD=VALUE` to select multiple commands or add custom answers when the inferred build, run, smoke, or test commands need correction before writing.
- Review the generated project-local `/dev` and `/test` skills after install and replace any weak command guesses with the repository's canonical workflows.
- Use `--overwrite-existing` only when intentional replacement of workspace customization is desired.
- Keep packaged bundle resources and checked-in workspace copies aligned if the repository ships its own bundle source.
- Explain clearly that skills improve workflow discovery and slash-command reuse, but they do not bypass terminal or tool approval prompts.

Constraints:
- Preserve existing customized files unless overwrite is explicitly requested.
- Keep bundle changes consistent between installed templates and the repository copies that generate them.
- Skills improve workflow discovery; shell and tool approvals may still be required.