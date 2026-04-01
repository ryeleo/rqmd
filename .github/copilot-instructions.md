# rqmd AI Contributor Instructions

Purpose:
- Keep requirement docs, summaries, and status lines synchronized.
- Prefer machine-readable workflows (`--json`; `--as-json` remains supported) for automation.

Repository conventions:
- Requirements index: docs/requirements/README.md
- Domain docs: docs/requirements/*.md
- Verify-only pass: rqmd --verify-summaries --no-walk --no-table

AI workflow defaults:
- Start with read-only context export via rqmd-ai.
- Propose updates before apply (`--update ...` without `--write`).
- Apply only after review with `--write`.
- For implementation work, use `rqmd-ai --workflow-mode implement` and take the highest-priority 1-3 proposed requirements at a time.
- After each implementation batch, make sure rqmd runs, summaries verify, tests pass, and priorities are re-checked before continuing.
- Prefer final markdown closeouts that use these exact sections in order:
	- `# What got done`
	- `# Up next`
	- `# Direction`
- Keep `What got done` concise and polished.
- Under `Up next`, include the full markdown bodies of the highest-priority proposed requirements as normal rendered markdown, not fenced code blocks.
- Under `Direction`, give a concrete next recommendation derived from the active backlog state.
- If you customize statuses, keep lifecycle equivalents for Proposed, Implemented, Verified, Blocked, and Deprecated so the bundled AI workflows and examples still map cleanly onto your catalog.
- Prefer the installed Copilot skills for repeatable workflows such as `/rqmd-brainstorm`, `/rqmd-triage`, `/rqmd-export-context`, `/rqmd-implement`, `/rqmd-init`, `/rqmd-init-legacy`, `/rqmd-status-maintenance`, `/rqmd-doc-sync`, `/rqmd-history`, `/rqmd-bundle`, and `/rqmd-verify`.
- The standard bundle install includes specialized agents for exploration, requirements, docs sync, and history inspection. Use `--bundle-preset minimal` when you only want the lean bundle.
- Bundle install also scaffolds project-local `/dev` and `/test` skills based on detected repository commands so implementation agents have a concrete starting point for build, smoke, and validation workflows.
- This repository also keeps a local `rqmd-bundle-maintainer` agent for maintaining the bundle source itself; `rqmd-ai install` does not copy that self-maintenance agent into other workspaces.
- Skills improve workflow discovery and reuse, but they do not bypass terminal/tool approval prompts.

Useful commands:
- rqmd-ai install --json
- rqmd-ai i --json --bundle-preset minimal --dry-run
- rqmd-ai --json --workflow-mode implement
- rqmd-ai --json --dump-status proposed
- rqmd-ai --json --dump-id RQMD-CORE-001 --include-requirement-body
- rqmd-ai --json --update RQMD-CORE-001=implemented
- rqmd-ai --json --write --update RQMD-CORE-001=implemented
