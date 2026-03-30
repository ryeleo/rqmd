# rqmd AI Contributor Instructions

Purpose:
- Keep requirement docs, summaries, and status lines synchronized.
- Prefer machine-readable workflows (`--as-json`) for automation.

Repository conventions:
- Requirements index: docs/requirements/README.md
- Domain docs: docs/requirements/*.md
- Verify-only pass: uv run rqmd --verify-summaries --no-walk --no-table

AI workflow defaults:
- Start with read-only context export via rqmd-ai.
- Propose updates before apply (`--update ...` without `--write`).
- Apply only after review with `--write`.
- For implementation work, use `rqmd-ai --workflow-mode implement` and take the highest-priority 1-3 proposed requirements at a time.
- After each implementation batch, make sure rqmd runs, summaries verify, tests pass, and priorities are re-checked before continuing.
- Prefer the installed Copilot skills for repeatable workflows such as `/rqmd-brainstorm`, `/rqmd-triage`, `/rqmd-export-context`, `/rqmd-implement`, `/rqmd-status-maintenance`, `/rqmd-doc-sync`, `/rqmd-history`, `/rqmd-bundle`, and `/rqmd-verify`.
- Skills improve workflow discovery and reuse, but they do not bypass terminal/tool approval prompts.

Useful commands:
- uv run rqmd-ai --as-json --workflow-mode implement
- uv run rqmd-ai --as-json --dump-status proposed
- uv run rqmd-ai --as-json --dump-id RQMD-CORE-001 --include-requirement-body
- uv run rqmd-ai --as-json --update RQMD-CORE-001=implemented
- uv run rqmd-ai --as-json --write --update RQMD-CORE-001=implemented
