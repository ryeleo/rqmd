# rqmd AI Contributor Instructions

Purpose:
- Keep requirement docs, summaries, and status lines synchronized.
- Prefer machine-readable workflows (`--json`) for automation.

Repository conventions:
- Requirements index: docs/requirements/README.md
- Domain docs: docs/requirements/*.md
- Verify-only pass: rqmd --verify-summaries --non-interactive

AI workflow defaults:
- Start with read-only context export via rqmd-ai.
- Propose updates before apply (`--update ...` without `--write`).
- Apply only after review with `--write`.
- For `rqmd-ai --json` workflows, run commands in the foreground and parse stdout as JSON while keeping stderr separate for diagnostics.
- On Windows shells, avoid mixing or reformatting streams when parsing JSON output; check the process exit code before JSON parsing.
- Keep the shared rqmd workflow shape recognizable across projects unless the repository intentionally overrides it.
- Preserve the requirement-first flow of context export -> requirements/docs updates -> preview -> apply -> verify instead of inventing ad hoc sequences for each repository.
- When drafting or editing requirement text, prefer a short user-story block (`As a ...`, `I want ...`, `So that ...`) plus Given/When/Then acceptance bullets when both add value.
- Treat the user-story and Given/When/Then sections as complementary views of the same requirement and keep them semantically aligned rather than letting one drift.
- For implementation work, use `rqmd-ai --workflow-mode implement` and take the highest-priority 1-3 proposed requirements at a time.
- After each implementation batch, make sure rqmd runs, summaries verify, tests pass, and priorities are re-checked before continuing.
- Use the same rqmd output conventions across projects where possible: concise markdown closeouts, consistent lifecycle emoji/labels, and the standard Info/Note/Warning block-quote style when callouts help readability.
- Prefer final markdown closeouts that use these exact sections in order:
	- `# What got done`
	- `# Up next`
	- `# Direction`
- Keep `What got done` concise and polished.
- Under `Up next`, include the full markdown bodies of the highest-priority proposed requirements as normal rendered markdown, not fenced code blocks.
- Under `Direction`, give a concrete next recommendation derived from the active backlog state.
- When the next step is implementation, include an explicit handoff suggestion in `Direction` — a copy-paste-ready `/rqmd-implement` prompt in a fenced code block that names the requirement IDs, batching order, and any dependency sequencing. This lets the user spawn a cheaper or faster implementation agent without re-explaining the context.
- The recommended rqmd multi-agent workflow is: **brainstorm/refine with a high-power agent → hand off to a lower-power agent for implementation → repeat**. Brainstorm, `/refine`, and `/next` work benefits from a stronger model that can reason about trade-offs and shape requirements. Implementation (`/go`, `/rqmd-implement`, `/commit-and-go`) is well-suited to a more cost-effective model focused on execution. Encourage users to spawn separate, cheaper agents for implementation batches rather than doing all work in one expensive session.
- If you customize statuses, keep lifecycle equivalents for Proposed, Implemented, Verified, Blocked, and Deprecated so the bundled AI workflows and examples still map cleanly onto your catalog.
- When referencing lifecycle states in prose, prefer consistent emoji plus label formatting such as `💡 Proposed`, `🔧 Implemented`, `✅ Verified`, `⛔ Blocked`, and `🗑️ Deprecated`, or their repository-local equivalents.
- Prefer the installed Copilot prompts and skills for repeatable workflows, such as `/go`, `/commit`, `/commit-and-go`, `/next`, `/refine`, `/brainstorm`, `/polish-docs`, `/refactor`, `/pin`, `/ship-check`, `/feedback`, `/rqmd-brainstorm`, `/rqmd-triage`, `/rqmd-export-context`, `/rqmd-implement`, `/rqmd-init`, `/rqmd-init-legacy`, `/rqmd-status-maintenance`, `/rqmd-docs`, `/rqmd-doc-sync`, `/rqmd-changelog`, `/rqmd-pin`, `/rqmd-bundle`, `/rqmd-verify`, `/rqmd-telemetry`, and `/rqmd-feedback`.
- The standard bundle install keeps `rqmd-dev` as the primary implementation agent, adds prompt entrypoints such as `/go` for common actions, and includes specialized agents for exploration, requirements, docs sync, history inspection, and optional advanced development modes. Use `--bundle-preset minimal` when you only want the lean bundle.
- Bundle install also scaffolds project-local `/dev` and `/test` skills based on detected repository commands so implementation agents have a concrete starting point for build, smoke, and validation workflows.
- Skills improve workflow discovery and reuse, but they do not bypass terminal/tool approval prompts.

AI output defaults:
- Keep outputs technical but user-friendly, written like a web article worth reading rather than a dump of internal notes.
- Use headings consistently: start at h1 and do not skip heading levels when headings improve the result.
- Prefer smaller sections over one oversized section.
- Introduce acronyms and jargon on first use, and add Info, Note, and Warning callouts when readers may need extra context.
- Prefer descriptive hyperlinks over raw pasted URLs.
- Use ordered or unordered lists to break up dense prose when they improve scanning.
- Use Info, Note, and Warning callouts deliberately to separate optional context, important reminders, and critical warnings.
- Use this exact markdown shape for callouts when examples or authored output need one: `> **ℹ️ Info:** ...`, `> **⚠️ Note:** ...`, `> **🚨 Warning:** ...`.

Useful commands:
- rqmd-ai install --json
- rqmd-ai i --json --bundle-preset minimal --dry-run
- rqmd-ai --json --workflow-mode implement
- rqmd-ai --json --dump-status proposed
- rqmd-ai --json --dump-id RQMD-CORE-001 --include-requirement-body
- rqmd-ai --json --update RQMD-CORE-001=implemented
- rqmd-ai --json --write --update RQMD-CORE-001=implemented
