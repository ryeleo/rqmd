---
name: rqmd-bundle
description: Install, refresh, and explain the rqmd AI agent and skill bundle for a workspace. Use for onboarding repositories, previewing bundle changes, preserving customized files, and clarifying how skills relate to approval prompts.
argument-hint: Describe whether you want a dry-run preview, minimal/full install, overwrite behavior, or bundle customization.
user-invocable: true
---

Use this skill when the work is about Copilot instructions, agents, skills, or bundle installation rather than the application itself.

Workflow:
- Preview bundle changes with `uv run rqmd-ai --as-json --install-agent-bundle --bundle-preset minimal --dry-run`.
- Install the standard bundle with `uv run rqmd-ai --as-json --install-agent-bundle --bundle-preset full`.
- Use `--overwrite-existing` only when intentional replacement of workspace customization is desired.
- Keep generated bundle text and checked-in workspace copies aligned if the repository ships its own bundle source.
- Explain clearly that skills improve workflow discovery and slash-command reuse, but they do not bypass terminal or tool approval prompts.

Constraints:
- Preserve existing customized files unless overwrite is explicitly requested.
- Keep bundle changes consistent between installed templates and the repository copies that generate them.
- Skills improve workflow discovery; shell and tool approvals may still be required.