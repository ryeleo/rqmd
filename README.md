# rqmd

`rqmd` is a CLI tool for Requirements Driven Development (RDD).

Works great with AI assisted workflows, but also fully functional as a standalone CLI for teams who want to keep AI out of their requirements process.

Project links:
- [GitHub repository](https://github.com/example/rqmd)
- [PyPI package](https://pypi.org/project/rqmd/)

## Getting started

If you want the fastest path to a working rqmd setup:

1. Install `rqmd` with `uv`, `pipx`, or `pip`.
2. In a new or existing repository, run `rqmd-ai init`.
3. Install the rqmd AI bundle if you want the prompt and skill shortcuts in chat.

Main prompt shortcuts after bundle install:

- `/go`: start or continue the standard rqmd implementation loop
- `/commit-and-go`: checkpoint existing related work if needed, then keep going and create a clean commit after each validated slice
- `/next`: pick the highest-priority feasible next slice and work it through validation
- `/brainstorm`: turn loose ideas or notes into ranked rqmd proposals before implementation
- `/docs-pass`: run a focused documentation quality or sync pass
- `/pin`: capture durable context or decision notes into a maintainable pinned note
- `/ship-check`: run a release or handoff readiness pass and call out blockers

> **ℹ️ Info:** `/go 10` means work through up to 10 validated slices before stopping. `/commit-and-go 10` means do the same thing, but create a clean git commit after each validated slice.

## Install

Recommended with `uv`:

```bash
uv tool install rqmd
```

With `pipx`:

```bash
pipx install rqmd
```

With `pip`:

```bash
python -m pip install rqmd
```

Then verify the install:

```bash
rqmd --help
rqmd-ai --help
```

> **ℹ️ Info:** `reqmd` and `reqmd-ai` remain available as compatibility aliases, but the primary supported commands are `rqmd` and `rqmd-ai`.

## What this tool does

- Scans requirement markdown files in a requirements directory.
- Uses `README.md` inside that directory as the requirements index.
- When `--docs-dir` is omitted, auto-detects the nearest viable requirement index from the current working path.
- Normalizes `- **Status:** ...` lines to the built-in standard status labels that rqmd writes back to disk.
- Parses requirement headers such as `### RQ-001: Title` or `### FOOBAR-001: Title`.
- Regenerates per-file summary blocks:

```md
<!-- acceptance-status-summary:start -->
Summary: 10💡 2🔧 3✅ 0⚠️ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->
```

Rendered:

> Summary: 10💡 2🔧 3✅ 0⚠️ 0⛔ 1🗑️

- Supports interactive status editing with keyboard navigation.
- Supports non-interactive updates for automation/agents.

Requirement bodies can be as short as a title plus status line, or include richer detail under the same heading. When both are useful, prefer pairing a short user story (`As a ...`, `I want ...`, `So that ...`) with Given/When/Then acceptance bullets.

> **ℹ️ Info:** In this README, "canonical" just means the normalized built-in value rqmd uses internally and writes back out, such as `✅ Verified` instead of a looser input like `verified`.

## What rqmd looks like

> **ℹ️ Info:** The examples below are representative outputs from the CLI. They are meant to show the shape and feel of rqmd in real use.

### Summary blocks stay readable in Git diffs and PRs

```md
<!-- acceptance-status-summary:start -->
Summary: 10💡 2🔧 3✅ 0⚠️ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->
```

Rendered:

> Summary: 10💡 2🔧 3✅ 0⚠️ 0⛔ 1🗑️

### Tree output is fast to scan during triage

```text
$ rqmd --status implemented --as-tree --no-walk --no-table
core-engine.md
	RQMD-CORE-001: Domain file discovery
	RQMD-CORE-011: Project scaffold initialization
interactive-ux.md
	RQMD-INTERACTIVE-007: Keep current requirement visible after update
```

### JSON mode is ready for automation and AI tooling

```json
{
	"mode": "filter-status",
	"schema_version": "1.0.0",
	"status": "💡 Proposed",
	"criteria_dir": "docs/requirements",
	"total": 3,
	"files": [
		{
			"path": "core-engine.md",
			"requirements": [
				{
					"id": "RQMD-CORE-033",
					"title": "Versioned requirement markdown schema and migration path",
					"status": "💡 Proposed"
				}
			]
		}
	]
}
```

## Status model

The built-in default status and priority catalogs ship as packaged YAML resources under `src/rqmd/resources/catalogs/`, so changing the shipped defaults no longer requires touching multiple Python tables.

> **ℹ️ Info:** A "catalog" here is just the list of allowed status or priority values, plus their labels and emoji.

- `💡 Proposed`
- `🔧 Implemented`
- `✅ Verified`
- `⚠️ Janky`
- `⛔ Blocked`
- `🗑️ Deprecated`

## Priority model (optional field)

Requirements can optionally include a `**Priority:**` line alongside the status line. When present, priority metadata supports sorting, filtering, and priority-aware summaries.

Default priority levels:

- `🔴 P0 - Critical`
- `🟠 P1 - High`
- `🟡 P2 - Medium`
- `🟢 P3 - Low`

Example requirement with priority:

```md
### RQ-001: Core API endpoint
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
```

Rendered:

> ### RQ-001: Core API endpoint
> - **Status:** 🔧 Implemented
> - **Priority:** 🔴 P0 - Critical

Priority is optional; requirements without a priority line parse successfully with `priority: None`.

Priority values are normalized case-insensitively, so `p0`, `P0`, `critical`, and `CRITICAL` all map to `🔴 P0 - Critical`.

Project config can still override these built-ins with `.rqmd.yml`, `.rqmd.json`, or standalone status/priority catalog files.

## Development install (from source)

From this folder:

```bash
uv sync
```

Install test dependencies:

```bash
uv sync --extra dev
```

Install optional native JSON acceleration:

```bash
uv sync --extra speedups
```

When `orjson` is installed through the `speedups` extra, rqmd and rqmd-ai use it for faster JSON export and audit-log serialization while preserving the existing JSON output shape (`schema`) and a pure-Python fallback when the extra is absent.

Then run:

```bash
rqmd --help
```

`reqmd` and `reqmd-ai` remain available as compatibility aliases, but the primary supported commands are `rqmd` and `rqmd-ai`.

Module entrypoint:

```bash
python -m rqmd --help
```

Pre-release alias plan:

- `rqmd` remains the canonical package name and primary command for now.
- `reqmd` and `reqmd-ai` are shipped as compatibility aliases so teams can trial the shorter branding before any package regname decision.
- Any future package-name rename should happen only after a manual PyPI availability check and a documented compatibility window for existing `rqmd` users.

## Shell completion

rqmd uses Click dynamic completion and supports shell activation without maintaining static completion files.
Completion candidates stay in sync with live requirement docs, including positional target tokens (domain names, requirement IDs, and subsection names) plus positional status/priority filter values such as `Proposed` and `P1`.

> **ℹ️ Info:** "Dynamic completion" means the shell asks rqmd for suggestions at completion time, instead of relying on a pre-generated completion file that can go stale.

zsh activation (add to `~/.zshrc`):

```bash
eval "$(_RQMD_COMPLETE=zsh_source rqmd)"
```

bash activation (add to `~/.bashrc`):

```bash
eval "$(_RQMD_COMPLETE=bash_source rqmd)"
```

fish activation (add to `~/.config/fish/config.fish`):

```fish
_RQMD_COMPLETE=fish_source rqmd | source
```

If you are running from a local clone during development without installing the console script, use `python -m rqmd`; completion is provided by the installed `rqmd` console entrypoint.

Troubleshooting completion cache refresh:

- zsh: `rm -f ~/.zcompdump* && exec zsh`
- bash: open a new shell session after updating rc files
- fish: `exec fish` after updating config

## Core commands

The command surface is broad, so the easiest way to learn it is by job to be done.

### Check whether your docs are in sync

Check summaries only:

```bash
rqmd --verify-summaries
```

This is the safest first command to run in an existing repo. It tells you whether the generated summary blocks still match the underlying requirement statuses.

### Open the interactive review UI

Interactive mode:

```bash
rqmd
```

Interactive file and requirement menus now support:

- `j` and `k` for next/previous vertical movement alongside arrow keys
- `gg` to jump to the first visible list position and `G` to jump to the last
- `Ctrl-U` and `Ctrl-D` for predictable half-page movement in paged menus
- `/` and `?` to search forward or backward within the current interactive list
- `n` and `N` to repeat the last list search in the same or opposite direction
- compact default footers with `:=help` instead of always showing the full key legend inline
- `:` to open the full help surface from interactive menus
- invalid or unmapped keys to playfully toggle the help surface open and closed without losing context
- `s` to cycle sort columns
- `d` to toggle ascending/descending
- `r` to refresh/rescan while preserving the active sort
- `z` to undo the last recorded history step from a requirement action menu
- `y` to redo the next recorded history step from a requirement action menu
- `h` to open the paged history browser from a requirement action menu

### Open or scope to one file

Open a specific domain file directly (absolute or repo-root-relative path):

```bash
rqmd docs/requirements/interactive-ux.md
```

In non-interactive modes, a positional domain file path scopes operations to that file:

```bash
rqmd docs/requirements/interactive-ux.md --update RQ-001=verified
```

### Recover, inspect, and maintain history

Inside the history browser, selecting an entry opens a detail view where you can:

- press `c` to checkout the selected entry's branch
- press `l` to save a human-readable label for the selected entry's branch
- press `x` to discard the selected entry's alternate branch, with an option to save a label first
- press `p` to cherry-pick the selected commit onto the current branch
- press `r` to replay the selected entry's branch onto the current branch
- press `g` to run history gc with confirmation
- press `G` to run history gc with immediate prune

Both interactive gc actions can optionally save a human-readable label on the current history branch before maintenance runs.

> **⚠️ Note:** `gc` here means garbage collection: cleanup of old history data and Git internals, not Python memory cleanup.

> **ℹ️ Info:** `checkout`, `cherry-pick`, and `replay` are Git operations. In short: `checkout` switches to another branch state, `cherry-pick` reapplies one specific change, and `replay` reapplies a sequence of changes.

History retention now uses a conservative default policy of retaining the last 1000 entries or the last 90 days of history metadata before running pack/prune maintenance. You can override that policy in project or user config with a top-level `history_retention` object:

```json
{
	"history_retention": {
		"retain_last": 500,
		"retain_days": 30,
		"max_size_kib": 2048
	}
}
```

`retain_last` and `retain_days` decide which persisted history entries remain navigable after `--history-gc`; `max_size_kib` records when the hidden history repo has crossed a size threshold so maintenance reports can surface it alongside the pack/prune result.

Long options also accept unique prefixes, so invocations such as `--proj`, `--docs`, and `--as-j` work when they resolve unambiguously.

History operations available in non-interactive mode include:

- `rqmd --history`
- `rqmd --timeline`
- `rqmd --undo`
- `rqmd --redo`
- `rqmd --history-label-branch <branch-name> --history-branch-label <label>`
- `rqmd --history-discard-branch <branch-name> --history-discard-save-label <label> --force-yes`
- `rqmd --history-gc --history-gc-save-label <label> --force-yes`
- `rqmd --history-gc --force-yes`
- `rqmd --history-gc --history-prune-now --force-yes`
- `rqmd --history-checkout-branch <branch-name>`
- `rqmd --history-cherry-pick <entry-index-or-ref> [--history-target-branch <branch-name>]`
- `rqmd --history-replay-branch <branch-name> [--history-target-branch <branch-name>]`

`--history-gc` requires explicit confirmation because it runs maintenance against the hidden `.rqmd/history/rqmd-history` repository. Add `--history-prune-now` to expire reflogs (Git's internal reference history) and prune immediately instead of using Git's default grace period.

> **🚨 Warning:** History cleanup and branch-discard commands are destructive maintenance operations. Read the prompt carefully before confirming them, especially if you have not saved a branch label first.

### Choose how interactive lists are ordered

File lists now default to the `name` sort in descending order.

You can select a named sort strategy catalog for interactive mode:

```bash
rqmd --sort-profile standard
rqmd --sort-profile status-focus
rqmd --sort-profile alpha-asc
```

### Start a new repository

Start rqmd in a new project with the default chat-first flow:

```bash
rqmd init
```

`rqmd init` prints a copy/paste handoff prompt for your AI chat. That chat then runs `rqmd-ai init --chat --json`, asks the grouped interview questions, previews the generated files, and applies the bootstrap only after confirmation.

> **ℹ️ Info:** "Scaffold" and "bootstrap" both mean creating the initial requirements files and supporting config for a repo. This README uses "scaffold" for the direct file-generation path and "chat-first onboarding" for the AI-guided path.

Direct scaffold compatibility path:

```bash
rqmd init --scaffold
```

`rqmd init --scaffold` is the direct starter scaffold path when you want immediate docs without the chat-first onboarding flow.
Scaffold content is sourced from repository-managed templates in `src/rqmd/resources/init/README.md` and `src/rqmd/resources/init/domain-example.md`.

### Allocate or update requirement IDs from the CLI

Allocate the next sequential numeric requirement ID for the active namespace:

```bash
rqmd --id-namespace TEAM --next-id
rqmd --id-namespace TEAM --next-id --json
```

`--next-id` respects the active key prefix, uses at least 3 digits of zero-padding by default, and continues past `999` as `1000`, `1001`, and higher.

Set one requirement non-interactively:

```bash
rqmd --update-id RQ-001 --update-status implemented
```

Update priorities non-interactively:

```bash
rqmd --update-priority RQ-001=p0
rqmd --update-priority RQ-001=critical --update-priority RQ-002=medium
```

Batch updates can include `priority` fields, or combine `status` and `priority` in one row:

```json
{"id":"RQ-001","priority":"p0"}
{"id":"RQ-002","status":"implemented","priority":"medium"}
```

### Filter the catalog quickly

Use positional filters for fast narrowing without explicit flags:

```bash
rqmd all
rqmd P1 Proposed --json --no-walk --no-table
rqmd Proposed core-engine
```

`rqmd all` opens a whole-catalog overview ordered by newest requirement ID first. When positional status and priority filters are combined, rqmd narrows across both families, so `rqmd P1 Proposed` returns only proposed P1 requirements. Remaining positional tokens are then resolved as requirement IDs, domain tokens, or subsection tokens.

> **ℹ️ Info:** A "positional filter" is a filter value passed as a plain argument like `P1` or `Proposed`, instead of a named flag like `--priority p1`.

### Work inside a focused requirement panel

Interactive entry panels can start in priority mode:

```bash
rqmd --focus-priority
```

Within an entry panel, press `t` to cycle status, priority, and flagged editing.

When the entry panel is on status, rqmd also shows a right-hand priority column so the current priority and available shifted number-row shortcuts such as `!`/`@`/`#`/`$`/`%`/`^`/`&`/`*` stay visible while you review statuses. That column is rendered as its own aligned block, and its current-priority highlight remains separate from the active status-row highlight so both states stay readable at once. Those shortcuts set the first configured priorities immediately and keep focus on the current requirement until you explicitly move on with down arrow or `j`.

From any requirement detail panel, press `o` to inspect linked local requirement references that rqmd can resolve from the current entry. Selecting one opens that linked requirement in a nested detail view, and pressing `u` there returns you to the originating requirement.

From the same detail panel, press `v` to open the current requirement in VS Code at the requirement heading line. If the `code` launcher is unavailable, rqmd reports that cleanly and keeps you in the current interactive context.

### Show priority-aware and grouped totals

Regenerate summary blocks with priority aggregates included:

```bash
rqmd --priority-rollup --no-walk
```

Filter by priority in tree, JSON, or interactive walk modes:

```bash
rqmd --priority critical --as-tree
rqmd --priority p1 --json --no-walk
```

Filter by subsection name with case-insensitive prefix matching:

```bash
rqmd --sub-domain query --as-tree
rqmd --sub-domain api --json --no-walk
```

Combine filters for slicing/dicing requirements:

- OR across different filter flags (`--status`, `--priority`, `--flagged`/`--no-flag`, `--has-link`/`--no-link`, `--sub-domain`)
- AND within the same flag when repeated

```bash
rqmd --status proposed --priority p0 --as-tree
rqmd --no-flag --json --no-walk
rqmd --has-link --json --no-walk
rqmd --status proposed --status implemented --json --no-walk
rqmd --sub-domain query --sub-domain api --json --no-walk
```

Target an explicit worklist from CLI tokens or a reusable file:

```bash
rqmd demo "Query API"
rqmd --targets-file tmp/focus.txt --json --no-walk
```

`--targets-file` accepts `.txt`, `.conf`, or `.md` files with one-per-line or whitespace/comma-separated tokens, and supports `#` comments.

Interactive file and requirement menus also expose `priority` as a sortable column via `s` / `d`.

Use a different ID prefix:

```bash
rqmd --id-namespace R --update-id R-EXAMPLE-001 --update-status implemented
```

Bulk set by repeated flags:

```bash
rqmd --update RQ-001=implemented --update RQ-002=verified
```

## AI CLI (rqmd-ai)

`rqmd-ai` is a companion command for AI-oriented workflows. It is read-only by default and supports prompt-context export, plan previews, and guarded apply mode.

> **⚠️ Note:** Treat `rqmd-ai` as preview-first. It stays read-only unless you explicitly add `--write`.

### Preview guidance and plan payloads

Representative guide output looks like this:

```json
{
	"workflow_mode": "implement",
	"mode": "guide",
	"read_only": true,
	"next_step": "Review the preview, then add --write only when the plan matches your intent."
}
```

### Export focused context

Recommended AI change loop for brainstorm-driven work:

1. Export focused context first with `rqmd-ai --json` or a targeted `--dump-*` command.
2. Update tracked requirement docs, the requirement index, and `CHANGELOG.md` before code when the brainstorm changes product behavior or workflow.
3. Review the read-only plan preview from `rqmd-ai --update ...`.
4. Apply explicitly with `--write` only after the preview matches the intended requirement/doc changes.
5. Finish with `rqmd --verify-summaries` and the test suite so requirement docs and shipped behavior stay aligned.

Guidance mode:

```bash
rqmd-ai --json
rqmd-ai --json --workflow-mode brainstorm
rqmd-ai --json --workflow-mode implement
rqmd-ai init --chat --json
rqmd-ai --json --workflow-mode init --show-guide
```

`--workflow-mode brainstorm` emits requirement-first planning guidance for turning notes into ranked proposals. `--workflow-mode implement` emits the execution loop for working the highest-priority proposed 1-3 items at a time, then re-checking `rqmd`, summaries, tests, changelog, and remaining priorities before the next batch. `rqmd-ai init --chat` is the preferred onboarding entrypoint: it routes between starter scaffold mode and legacy-style repository seeding, emits a copy/paste AI handoff prompt, and keeps `--workflow-mode init-legacy` available only as a compatibility surface.

By default, `rqmd-ai --json` now includes the packaged prompt, skill, and agent definitions from `resources/bundle` when the rqmd bundle is not installed in the workspace. If the bundle is already installed, the guide payload stays concise and reports the active local definition files instead of duplicating the packaged content.

> **ℹ️ Info:** In this section, a "bundle" means the installable set of Copilot instructions, skills, and agents that rqmd can scaffold into a repository.

Brainstorm mode can read `docs/brainstorm.md` by default or a custom markdown note file via `--brainstorm-file`, then emit ranked read-only proposal suggestions with recommended target requirement docs, suggested IDs, canonical `💡 Proposed` status, and inferred priorities.

Export context for prompts:

```bash
rqmd-ai --json --dump-status proposed
rqmd-ai --json --dump-id RQMD-CORE-001 --include-requirement-body
rqmd-ai --json --dump-file ai-cli.md --include-domain-markdown --max-domain-markdown-chars 2000
```

### Review a planned change before writing

Plan first, then apply explicitly:

```bash
rqmd-ai --json --update RQMD-CORE-001=implemented
rqmd-ai --json --write --update RQMD-CORE-001=implemented
```

That two-step flow is the safest way to use `rqmd-ai`: inspect the preview first, then repeat the same command with `--write` only when the proposed change is correct.

### Install the Copilot bundle

Install a standard AI prompt/agent/skill instruction bundle (minimal or full preset):

```bash
rqmd-ai --json --install-agent-bundle --bundle-preset minimal --dry-run
rqmd-ai --json --install-agent-bundle --bundle-preset full
rqmd-ai --json --install-agent-bundle --bundle-preset full --overwrite-existing
```

Bundle installs are idempotent by default and preserve existing customized instruction files unless `--overwrite-existing` is explicitly passed.

> **ℹ️ Info:** "Idempotent" means you can run the same install command again without duplicating files or changing already-correct output.

Bundle install also scaffolds project-local `.github/skills/dev/SKILL.md` and `.github/skills/test/SKILL.md` files based on detected repository commands. Treat those as a starting point: review and tighten the generated build, smoke, and validation commands so future `rqmd-dev` runs can rely on them instead of guessing.

The default bundle shape is now single-agent-first: `rqmd-dev` stays the main implementation agent, the bundled prompts provide the main slash-command entrypoints for common rqmd actions, and the extra full-preset agents stay available as specialized modes when you intentionally want a different execution style.

Bundle installation can also be driven through a structured chat-style preview with `rqmd-ai install --json --bundle-preset minimal --chat --dry-run`. That payload now includes grouped interview questions, multi-select command suggestions, custom-answer prompts, skip support, detected command sources, recommended choices, safe defaults, and preview content for the generated `/dev` and `/test` skills. Repeat `--answer FIELD=VALUE` to select multiple suggestions or add custom commands before writing.

### Use rqmd-ai for new-project onboarding

New-project flow: run `rqmd init`, paste the output into your AI chat, let that chat drive `rqmd-ai init --chat --json`, review the generated requirements catalog and any suggested bundle skill setup, and then start refining the resulting requirements docs.

Legacy-style repository seeding can still be previewed with `rqmd-ai init --chat --json --legacy`. The grouped interview covers catalog setup, developer workflows, repository understanding, backlog handling, and review notes, and its options include recommended choices, detected-from hints, and safe defaults. The generated starter catalog seeds a requirements index, developer workflow requirements, repository-area seed files, and an issue backlog file when `gh issue list` succeeds.

Installed prompt shortcuts:

- `/go`: start or continue the standard rqmd implementation loop; `/go 10` means work through up to 10 validated slices before stopping
- `/commit-and-go`: work through one or more validated slices and create a clean git commit after each slice; `/commit-and-go 10` means keep going for up to 10 validated committed slices
- `/next`: pick the highest-priority feasible next slice and work it through validation
- `/brainstorm`: turn loose ideas or notes into ranked rqmd proposals before implementation
- `/docs-pass`: run a focused documentation quality or sync pass
- `/pin`: capture durable context or decision notes into a maintainable pinned note
- `/ship-check`: run a release or handoff readiness pass and call out blockers

The installed bundle also includes Copilot skills for `/rqmd-brainstorm`, `/rqmd-triage`, `/rqmd-export-context`, `/rqmd-implement`, `/rqmd-init`, `/rqmd-init-legacy`, `/rqmd-status-maintenance`, `/rqmd-docs`, `/rqmd-doc-sync`, `/rqmd-changelog`, `/rqmd-history`, `/rqmd-pin`, `/rqmd-bundle`, and `/rqmd-verify` so teams can reuse the core planning, backlog selection, context export, implementation, unified init, compatibility legacy bootstrap, documentation-quality, docs-sync, changelog-authoring, history, pinning durable project context, bundle-management, and verification loops without rewriting those instructions in every workspace. Prompts and skills help with discovery and consistency, but they do not auto-approve terminal commands or bypass Copilot tool approval prompts.

For repositories that use `/rqmd-pin`, a practical default is `docs/pins/README.md` as a lightweight index plus one markdown file per topic started from `docs/pins/pin-template.md`.

The full bundle preset also installs specialized agents for exploration, requirement maintenance, docs sync, history investigation, and the `rqmd-dev-longrunning` and `rqmd-dev-easy` implementation variants so teams can opt into a different working style without losing the shared rqmd workflow contract.

Bundle workflows assume the core lifecycle states remain representable in your status catalog. Custom labels are fine, but if you want `rqmd-ai` guidance, examples, and installed skills to work well out of the box, keep lifecycle equivalents for `💡 Proposed`, `🔧 Implemented`, `✅ Verified`, `⛔ Blocked`, and `🗑️ Deprecated`.

When apply mode runs, rqmd-ai appends a structured audit event to the local shared history backend at `.rqmd/history/rqmd-history/audit.jsonl` (JSON Lines, one JSON object per line).

Batch set from a JSON Lines (`.jsonl`) file:

```bash
rqmd --update-file tmp/ac-updates.jsonl
```

Allow custom prefixes such as `REQ-` in a repo:

```bash
rqmd --id-namespace REQ --status proposed --as-tree
```

Filter walk:

```bash
rqmd --status proposed
```

Filtered walk resume behavior (enabled by default):

- Uses persisted state so reruns continue at the last visited requirement.
- Disable with `--no-resume-walk`.
- Control storage location with `--session-state-dir`.

Examples:

```bash
rqmd --status implemented --session-state-dir system-temp
rqmd --status implemented --session-state-dir project-local
rqmd --status implemented --session-state-dir .rqmd/state
rqmd --status implemented --no-resume-walk
```

Filter tree only:

```bash
rqmd --status proposed --as-tree
```

Filter as JSON for automation/AI parsing:

```bash
rqmd --status proposed --json
```

Filter JSON includes requirement body content and line metadata by default:

```bash
rqmd --status proposed --json
```

Use compact output without bodies:

```bash
rqmd --status proposed --json --no-requirement-body
```

Summary/check/set JSON examples:

```bash
rqmd --json --no-walk
rqmd --verify-summaries --json --no-walk
rqmd --update-id RQ-001 --update-status verified --json
rqmd --totals --json --no-walk
```

### JSON contract (stable keys)

When `--json` is used, top-level keys are stable by mode.
All JSON payloads include `schema_version` (current value: `1.0.0`) and follow semantic versioning (`major.minor.patch`).

> **ℹ️ Info:** `schema_version` is the version of the machine-readable JSON structure, not the package release version.

- `summary`: `mode`, `schema_version`, `criteria_dir`, `changed_files`, `totals`, `files`, `ok`
- `check`: `mode`, `schema_version`, `criteria_dir`, `changed_files`, `totals`, `files`, `ok`
- `set` / `set-priority` / `set-flagged`: `mode`, `schema_version`, `criteria_dir`, `changed_files`, `totals`, `files`, `updates`
- `filter-status`: `mode`, `schema_version`, `status`, `criteria_dir`, `total`, `files`
- `filter-priority`: `mode`, `schema_version`, `priority`, `criteria_dir`, `total`, `files`
- `filter-flagged`: `mode`, `schema_version`, `flagged`, `criteria_dir`, `total`, `files`
- `filter-sub-domain`: `mode`, `schema_version`, `sub_domain`, `criteria_dir`, `total`, `files`
- `filter-combined`: `mode`, `schema_version`, `filters`, `criteria_dir`, `total`, `files`
- `filter-targets`: `mode`, `schema_version`, `targets`, `criteria_dir`, `total`, `files`
- `rollup`: `mode`, `schema_version`, `criteria_dir`, `file_count`, `totals`, optional `rollup_source`, optional `rollup_columns`
- `init`: `mode`, `schema_version`, `criteria_dir`, `starter_prefix`, `created_files`, `created_count`
- `init-priorities`: `mode`, `schema_version`, `criteria_dir`, `default_priority`, `changed_files`, `changed_count`

Filter payloads return `files` ordered by path and requirement entries ordered by requirement ID.
By default, filter JSON includes `body.markdown` and line metadata; pass `--no-requirement-body` to omit bodies.
Each requirement entry includes `sub_domain` (string or `null`), and each file entry includes `sub_sections` with subsection names and requirement counts.

### Exit codes

RQMD uses this exit-code matrix for automation:

- `0`: Success (including successful no-op runs)
- `1`: Validation or contract failure (for example `--verify-summaries` found out-of-sync summaries, invalid input, missing docs, ambiguity, or other `ClickException` errors)
- `130`: Interrupted by user (`Ctrl+C`)

Explicit global roll-up totals (combined totals from multiple statuses):

```bash
rqmd --totals --no-walk
```

Custom roll-up columns from CLI equations:

```bash
rqmd --totals --totals-map "C1=I+V" --totals-map "C2=P" --no-walk
```

Custom roll-up columns from config (`.json`, `.yml`, `.yaml`):

```bash
rqmd --totals --totals-config .rqmd.yml --json --no-walk
```

Example project config for a repo that defines a custom status catalog and wants RQMD-ROLLUP-007 roll-up buckets:

```yaml
# .rqmd.yml
statuses:
	- name: Proposed
		shortcode: P
		emoji: "💡"
	- name: Implemented
		shortcode: I
		emoji: "🔧"
	- name: Desktop-Verified
		shortcode: DV
		emoji: "💻"
	- name: VR-Verified
		shortcode: VV
		emoji: "🎮"
	- name: Done
		shortcode: D
		emoji: "✅"
	- name: Blocked
		shortcode: B
		emoji: "⛔"
	- name: Deprecated
		shortcode: X
		emoji: "🗑️"

rollup_map:
	Proposed: [proposed]
	Build-Ready: [implemented, desktop-verified]
	Complete: [vr-verified, done]
	Parked: [blocked, deprecated]
```

That example yields these roll-up families:

- `Blocked + Deprecated` roll up together in `Parked`
- `Implemented + Desktop-Verified` roll up together in `Build-Ready`
- `VR-Verified + Done` roll up together in `Complete`

When no CLI map/config is passed, rqmd resolves roll-up mappings with this precedence:

> **ℹ️ Info:** A "roll-up" is a combined total such as grouping multiple statuses into one higher-level bucket like `Build-Ready` or `Complete`.

1. `--totals-map` CLI equations
2. project config (`.rqmd.yml|.rqmd.yaml` in `--project-root`)
3. user config (`~/.config/rqmd/rollup.json|yaml|yml`)
4. built-in status totals

## Tests

Run full pytest suite from this folder:

```bash
uv run --extra dev pytest
```

Run a specific test module:

```bash
uv run --extra dev pytest tests/test_core_engine.py
```

One-command shell smoke check (no make required):

```bash
bash scripts/local-smoke.sh
```

The test suite is organized to validate implemented acceptance-requirements behavior for:
- core engine parsing and summary sync
- interactive menu/color behavior
- non-interactive automation flows
- portability and packaging contracts

Detailed coverage mapping is documented in `docs/testing.md`.

## Changelog

Notable project changes are tracked in `CHANGELOG.md` using the Keep a Changelog format.

## CI

> **ℹ️ Info:** CI means continuous integration: the automated checks that run in GitHub Actions on pushes, pull requests, and releases.

This package includes GitHub Actions workflows:

- `.github/workflows/pytest.yml`
- Triggers on push and pull_request.
- Installs project dependencies with `uv sync --extra dev`.
- Runs `bash scripts/local-smoke.sh --skip-install`.

- `.github/workflows/publish-pypi.yml`
- Triggers when a GitHub release is published.
- Validates that the release tag is a stable semver tag or `rc` prerelease tag such as `v0.1.0rcN`, matching `project.version`.
- Builds with `python -m build` and publishes with GitHub Actions trusted publishing.

> **⚠️ Note:** "Trusted publishing" means GitHub Actions authenticates directly to PyPI using OpenID Connect (`id-token: write`) instead of storing a long-lived PyPI upload token in repository secrets.

## Project portability

By default, rqmd auto-discovers `--project-root` by searching from the current working directory upward.
The nearest ancestor with a supported marker wins.

Marker priority within each directory is deterministic:

1. `.rqmd.yml`, `.rqmd.yaml`, `.rqmd.json`
2. `docs/requirements/`
3. `requirements/`

If no marker is found, rqmd falls back to current working directory.
When auto-discovery is used, rqmd reports the discovered root and source marker.

Passing explicit `--project-root` bypasses auto-discovery.

When `--docs-dir` is omitted, rqmd auto-detects requirement docs by scanning from the current working path.

Auto-detect preference is deterministic:

1. `docs/requirements/README.md`
2. `requirements/README.md`

You can override both:

```bash
rqmd --project-root /path/to/project --docs-dir docs/requirements
```

`--docs-dir` can be absolute or relative to `--project-root`.
When auto-detection is used, rqmd reports which index path it selected.

Filtered walkthrough resume state is configurable with `--session-state-dir`:

- `system-temp` (default): OS temp directory.
- `project-local`: `<repo-root>/tmp/rqmd`.
- custom path: absolute or relative to `--project-root`.

Requirement header prefixes are configurable with `--id-namespace`.
When omitted, rqmd auto-detects prefixes by reading the selected `README.md` requirements index and linked domain docs when available.
If no prefixes are discovered, it falls back to `AC-`, `R-`, and `RQMD-`.

> **ℹ️ Info:** An "ID namespace" here just means the leading identifier family such as `RQMD-`, `REQ-`, or `TEAM-`.

### Project configuration file

To avoid repeating CLI flags across team members, use a single project config file at the project root: `.rqmd.yml` (preferred).
Accepted extensions are `.rqmd.yml`, `.rqmd.yaml`, or `.rqmd.json`.
`rqmd init --scaffold` and `rqmd-ai init --write` now create `.rqmd.yml` by default so the repository's requirements path, ID prefix, and canonical status/priority catalogs are explicit from day one.

Example:

```yaml
{
	requirements_dir: docs/requirements
	id_prefix: PROJ
	sort_strategy: status-focus
	state_dir: project-local
}
```

Supported keys:

- `requirements_dir`: Default requirements directory (relative to repo root)
- `id_prefix`: Default ID prefix for requirement headers
- `sort_strategy`: Default sort strategy for interactive mode (standard, status-focus, alpha-asc)
- `state_dir`: Default state directory for filtered walk resume (system-temp, project-local, or custom path)

CLI flags always override config file values. When `.rqmd.yml` (or `.rqmd.yaml` / `.rqmd.json`) is present, rqmd loads it automatically; no additional flag is needed.

## Recommended docs recipe for projects

1. Keep an index doc at `docs/requirements/README.md` or `requirements/README.md`.
2. Keep domain files in that same directory.
3. Ensure each requirement has exactly one status line directly under the `### <PREFIX>-...` header.
4. Run `rqmd --verify-summaries` in CI to prevent stale summary blocks.
5. Use non-interactive `--update`/`--update-file` in automation.

## Packaging notes

- Package name: `rqmd`
- Console script entrypoint: `rqmd`
- Source package: `src/rqmd`

When ready for PyPI:

1. Follow semantic versioning policy in `docs/SEMVER.md`.
2. Follow the release checklist in `docs/releasing.md`.
3. Create and publish a GitHub Release with a matching tag such as `v0.1.0` or `v0.1.0rcN`.
4. Let `.github/workflows/publish-pypi.yml` publish through trusted publishing.
