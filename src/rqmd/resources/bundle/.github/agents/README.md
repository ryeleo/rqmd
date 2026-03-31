# rqmd Agent Bundle

This folder contains a standard AI agent bundle installed by:

`rqmd-ai install`

Legacy equivalent:

`rqmd-ai --install-agent-bundle`

Presets:
- full (default): `.github/copilot-instructions.md`, `.github/agents/rqmd-dev.agent.md`, the rqmd workflow skills under `.github/skills/`, `.github/agents/rqmd-explore.agent.md`, `.github/agents/rqmd-requirements.agent.md`, `.github/agents/rqmd-docs.agent.md`, `.github/agents/rqmd-history.agent.md`, and this README
- minimal: `.github/copilot-instructions.md`, `.github/agents/rqmd-dev.agent.md`, and the rqmd workflow skills under `.github/skills/`

Operational notes:
- Re-run is idempotent.
- Existing files are preserved unless `--overwrite-existing` is used.
- Skills improve workflow discovery and slash-command reuse, but they do not bypass terminal or tool approval prompts.
- The rqmd source repository also keeps a repo-local `rqmd-bundle-maintainer` agent for maintaining the bundle itself; `rqmd-ai install` does not install that self-maintenance agent into target workspaces.

Useful commands:
- `rqmd-ai install`
- `rqmd-ai i --bundle-preset minimal --dry-run`
- `rqmd-ai --install-agent-bundle --bundle-preset minimal`

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

Installed agents in the full preset:
- `rqmd-dev`: primary implementation and orchestration agent
- `rqmd-explore`: read-only codebase and requirement discovery agent
- `rqmd-requirements`: backlog, status, priority, and requirement-doc maintenance agent
- `rqmd-docs`: README, changelog, and requirement-doc sync agent
- `rqmd-history`: timeline, history-ref, compare-refs, and recovery-planning agent