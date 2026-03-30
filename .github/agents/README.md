# rqmd Agent Bundle

This folder contains a standard AI agent bundle installed by:

`rqmd-ai --install-agent-bundle`

Presets:
- minimal: `.github/copilot-instructions.md`, `.github/agents/core.agent.md`, and the rqmd workflow skills under `.github/skills/`
- full: minimal + `.github/agents/Explore.agent.md` and this README

Operational notes:
- Re-run is idempotent.
- Existing files are preserved unless `--overwrite-existing` is used.
- Skills improve workflow discovery and slash-command reuse, but they do not bypass terminal or tool approval prompts.

Installed workflow skills:
- `/rqmd-brainstorm`
- `/rqmd-triage`
- `/rqmd-export-context`
- `/rqmd-implement`
- `/rqmd-status-maintenance`
- `/rqmd-doc-sync`
- `/rqmd-history`
- `/rqmd-bundle`
- `/rqmd-verify`
