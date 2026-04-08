# rqmd Agent Bundle

This folder contains a standard AI agent bundle installed by:

`rqmd-ai install`

Legacy equivalent:

`rqmd-ai --install-agent-bundle`

Presets:
- full (default): `.github/copilot-instructions.md`, `.github/agents/rqmd-dev.agent.md`, the bundled prompt suite under `.github/prompts/`, the rqmd workflow skills under `.github/skills/`, specialized full-preset agents under `.github/agents/`, and this README
- minimal: `.github/copilot-instructions.md`, `.github/agents/rqmd-dev.agent.md`, the bundled prompt suite under `.github/prompts/`, and the rqmd workflow skills under `.github/skills/`

Operational notes:
- Re-run is idempotent.
- Existing files are preserved unless `--overwrite-existing` is used.
- Prompts and skills improve workflow discovery and slash-command reuse, but they do not bypass terminal or tool approval prompts.
- The rqmd source repository also keeps a repo-local `rqmd-bundle-maintainer` agent for maintaining the bundle itself; `rqmd-ai install` does not install that self-maintenance agent into target workspaces.
- Bundle install also generates project-local `.github/skills/dev/SKILL.md` and `.github/skills/test/SKILL.md` scaffolds based on detected repository commands; review and customize them after install.

Useful commands:
- `rqmd-ai install`
- `rqmd-ai i --bundle-preset minimal --dry-run`
- `rqmd-ai --install-agent-bundle --bundle-preset minimal`

Installed prompts:
- `/go`: start or continue the standard rqmd implementation loop through `rqmd-dev`
- `/commit`: commit the current work with a well-structured git message
- `/commit-and-go`: keep going through one or more validated slices and create a clean git commit after each slice
- `/next`: pick the next highest-priority feasible rqmd slice and work it through validation
- `/refine`: refine existing requirements or shape new ones through focused discussion
- `/brainstorm`: turn loose ideas or notes into ranked rqmd proposals before implementation
- `/polish-docs`: run a focused documentation quality or sync pass for rqmd work
- `/refactor`: refactor code, docs, or other artifacts to improve readability, maintainability, or performance
- `/pin`: capture durable context or decision notes into a maintainable pinned note
- `/ship-check`: run a release or handoff readiness pass with verification and blocker review
- `/feedback`: send user-driven improvement feedback about rqmd via the telemetry service

Installed workflow skills:
- `/rqmd-brainstorm`
- `/rqmd-triage`
- `/rqmd-export-context`
- `/rqmd-implement`
- `/rqmd-status-maintenance`
- `/rqmd-docs`
- `/rqmd-doc-sync`
- `/rqmd-changelog`
- `/rqmd-pin`
- `/rqmd-bundle`
- `/rqmd-verify`
- `/rqmd-feedback`

Installed agents in the full preset:
- `rqmd-dev`: primary implementation and orchestration agent
- `rqmd-dev-longrunning`: priority-first implementation agent that keeps working through feasible backlog slices until it reaches a real stop condition
- `rqmd-dev-easy`: conservative implementation agent that prefers low-risk, high-confidence backlog wins first
- `rqmd-explore`: read-only codebase and requirement discovery agent
- `rqmd-requirements`: backlog, status, priority, and requirement-doc maintenance agent
- `rqmd-docs`: README, changelog, and requirement-doc sync agent

Recommended default:
- The recommended workflow is **brainstorm/refine with a high-power agent → hand off to a lower-power agent for implementation → repeat**.
- Use `/brainstorm` or `/refine` with a stronger model to shape requirements and explore trade-offs.
- When requirements are ready, the agent will offer a copy-paste-ready `/go` handoff prompt. Spawn a separate, cheaper agent session for the implementation work.
- Use `/go 10`-style numeric arguments when you want one prompt run to cover multiple validated slices without enabling automatic commits.
- Use `/commit-and-go 10` when you explicitly want the agent to commit each validated slice during a longer unattended run.
- Treat the extra full-preset agents as specialized or advanced modes when you want a materially different execution style.