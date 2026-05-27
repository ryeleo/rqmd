# rqmd

> **⚠️ Archived:** This project is no longer actively maintained.
> rqmd was a learning project in local-first requirements tracking — it was useful and fun to build, but AI agent tooling is evolving faster than I want to keep up with for a side project.
> The final release is **v0.4.0**. The PyPI package remains available but receives no updates.

`rqmd` is a *local-first* CLI tool for Requirements Driven Development (RDD).

> See also [Local-First Software: You Own Your Data, in spite of the Cloud](https://martin.kleppmann.com/papers/local-first.pdf)

Project links:
- [GitHub repository](https://github.com/ryeleo/rqmd)
- [PyPI package](https://pypi.org/project/rqmd/)

## Getting started

If you want the fastest path to a working rqmd setup:

1. Install `rqmd` with `uv`, `pipx`, or `pip`.
2. In a new or existing repository, run `rqmd init`.
3. Start managing requirements with `rqmd` interactively or via `--json` for scripting.

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
rqmd --version
```

> **ℹ️ Info:** `reqmd` remains available as a compatibility alias, but the primary supported command is `rqmd`.

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
- Supports non-interactive updates for automation and scripting.

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
$ rqmd --status implemented --as-tree -y
core-engine.md
	RQMD-CORE-001: Domain file discovery
	RQMD-CORE-011: Project scaffold initialization
interactive-ux.md
	RQMD-INTERACTIVE-007: Keep current requirement visible after update
```

### JSON mode is ready for automation and scripting

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

Project config can still override these built-ins with `rqmd.yml`, `rqmd.json`, or standalone status/priority catalog files.

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

When `orjson` is installed through the `speedups` extra, rqmd uses it for faster JSON export and audit-log serialization while preserving the existing JSON output shape (`schema`) and a pure-Python fallback when the extra is absent.

Then run:

```bash
rqmd --help
```

`reqmd` remains available as a compatibility alias, but the primary supported command is `rqmd`.

Module entrypoint:

```bash
python -m rqmd --help
```

Pre-release alias plan:

- `rqmd` remains the canonical package name and primary command for now.
- `reqmd` is shipped as a compatibility alias so teams can trial the shorter branding before any package regname decision.
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

### Open or scope to one file

Open a specific domain file directly (absolute or repo-root-relative path):

```bash
rqmd docs/requirements/interactive-ux.md
```

In non-interactive modes, a positional domain file path scopes operations to that file:

```bash
rqmd docs/requirements/interactive-ux.md --update RQ-001=verified
```

> **⚠️ Note:** History/time-machine and undo/redo workflows have been removed in the current 0.x simplification track. Use direct status updates (`rqmd --update ...`) or interactive status edits instead.

### Choose how interactive lists are ordered

File lists now default to the `name` sort in descending order.

You can select a named sort strategy catalog for interactive mode:

```bash
rqmd --sort-profile standard
rqmd --sort-profile status-focus
rqmd --sort-profile alpha-asc
```

### Start a new repository

Start rqmd in a new project:

```bash
rqmd init
```

`rqmd init` scaffolds your initial requirements directory, index file, and project config.

> **ℹ️ Info:** "Scaffold" and "bootstrap" both mean creating the initial requirements files and supporting config for a repo.

Direct scaffold path:

```bash
rqmd init --scaffold
```

`rqmd init --scaffold` is the direct starter scaffold path when you want immediate docs.
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
rqmd P1 Proposed --json -y
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
rqmd --priority-rollup -y
```

Filter by priority in tree, JSON, or interactive walk modes:

```bash
rqmd --priority critical --as-tree
rqmd --priority p1 --json -y
```

Filter by subsection name with case-insensitive prefix matching:

```bash
rqmd --sub-domain query --as-tree
rqmd --sub-domain api --json -y
```

Combine filters for slicing/dicing requirements:

- OR across different filter flags (`--status`, `--priority`, `--flagged`/`--no-flag`, `--has-link`/`--no-link`, `--sub-domain`)
- AND within the same flag when repeated

```bash
rqmd --status proposed --priority p0 --as-tree
rqmd --no-flag --json -y
rqmd --has-link --json -y
rqmd --status proposed --status implemented --json -y
rqmd --sub-domain query --sub-domain api --json -y
```

Target an explicit worklist from CLI tokens or a reusable file:

```bash
rqmd demo "Query API"
rqmd --targets-file tmp/focus.txt --json -y
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

## Machine-readable output (`rqmd --json`)

`rqmd --json` is the machine-readable surface for automation workflows. It is read-only by default and supports context export, plan previews, and guarded apply mode.

> **⚠️ Note:** Treat `rqmd --json` as preview-first. It stays read-only unless you explicitly add `--write`.

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

Recommended change loop for brainstorm-driven work:

1. Export focused context first with `rqmd --json` or a targeted `--dump-*` command.
2. Update tracked requirement docs, the requirement index, and `CHANGELOG.md` before code when the brainstorm changes product behavior or workflow.
3. Review the read-only plan preview from `rqmd --update ...`.
4. Apply explicitly with `--write` only after the preview matches the intended requirement/doc changes.
5. Finish with `rqmd --verify-summaries` and the test suite so requirement docs and shipped behavior stay aligned.

Guidance mode:

```bash
rqmd --json
rqmd --json --workflow-mode brainstorm
rqmd --json --workflow-mode implement
rqmd --json --workflow-mode init --show-guide
```

`--workflow-mode brainstorm` emits requirement-first planning guidance for turning notes into ranked proposals. `--workflow-mode implement` emits the execution loop for working the highest-priority proposed 1-3 items at a time, then re-checking `rqmd`, summaries, tests, changelog, and remaining priorities before the next batch.

Brainstorm mode can read `docs/brainstorm.md` by default or a custom markdown note file via `--brainstorm-file`, then emit ranked read-only proposal suggestions with recommended target requirement docs, suggested IDs, canonical `💡 Proposed` status, and inferred priorities.

Export context for prompts:

```bash
rqmd --json --dump-status proposed
rqmd --json --dump-id RQMD-CORE-001 --include-requirement-body
rqmd --json --dump-file my-domain.md --include-domain-markdown --max-domain-markdown-chars 2000
```

### Review a planned change before writing

Plan first, then apply explicitly:

```bash
rqmd --json --update RQMD-CORE-001=implemented
rqmd --json --write --update RQMD-CORE-001=implemented
```

That two-step flow is the safest way to use `rqmd --json`: inspect the preview first, then repeat the same command with `--write` only when the proposed change is correct.

> **⚠️ Note:** For reliable machine parsing on Windows and CI shells, run `rqmd --json` commands in the foreground and parse stdout only. Keep stderr separate for warnings/diagnostics and check the exit code before parsing.

The `init` interview also lets you choose a default status scheme (`canonical`, `lean`, or `delivery`) or copy a status catalog from an existing project path (for example another repository's `rqmd.yml`) before writing the new scaffold.

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

Filter as JSON for scripting:

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
rqmd --json -y
rqmd --verify-summaries --json -y
rqmd --update-id RQ-001 --update-status verified --json
rqmd --totals --json -y
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
rqmd --totals -y
```

Custom roll-up columns from CLI equations:

```bash
rqmd --totals --totals-map "C1=I+V" --totals-map "C2=P" -y
```

Custom roll-up columns from config (`.json`, `.yml`, `.yaml`):

```bash
rqmd --totals --totals-config rqmd.yml --json -y
```

Example project config for a repo that defines a custom status catalog and wants RQMD-ROLLUP-007 roll-up buckets:

```yaml

# rqmd.yml

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
2. project config (`rqmd.yml|rqmd.yaml` in `--project-root`)
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
- Triggers when a stable GitHub release is published, or when an `rc` tag such as `v0.1.0rcN` is pushed.
- Validates that the release tag is a stable semver tag or `rc` prerelease tag such as `v0.1.0rcN`, matching `project.version`.
- Builds with `python -m build` and publishes with GitHub Actions trusted publishing.

> **⚠️ Note:** "Trusted publishing" means GitHub Actions authenticates directly to PyPI using OpenID Connect (`id-token: write`) instead of storing a long-lived PyPI upload token in repository secrets.

## Project portability

By default, rqmd auto-discovers `--project-root` by searching from the current working directory upward.
The nearest ancestor with a supported marker wins.

Marker priority within each directory is deterministic:

1. `rqmd.yml`, `rqmd.yaml`, `rqmd.json`
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

To avoid repeating CLI flags across team members, use a single project config file at the project root: `rqmd.yml` (preferred).
Accepted extensions are `rqmd.yml`, `rqmd.yaml`, or `rqmd.json`.
`rqmd init --scaffold` and `rqmd init --write` now create `rqmd.yml` by default so the repository's requirements path, ID prefix, and canonical status/priority catalogs are explicit from day one.

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

CLI flags always override config file values. When `rqmd.yml` (or `rqmd.yaml` / `rqmd.json`) is present, rqmd loads it automatically; no additional flag is needed.

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
3. For a stable version, create and publish a GitHub Release with a matching tag such as `v0.1.0`.
4. For an internal release candidate, push a matching tag such as `v0.1.0rcN`; no GitHub Release is required.
5. Let `.github/workflows/publish-pypi.yml` publish through trusted publishing.
