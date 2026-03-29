# rqmd

Reusable requirements and acceptance-requirements workflow CLI.

rqmd: Human-readable + AI-readable requirements for Requirements Driven Development (RDD).

Project links:
- GitHub: https://github.com/example/rqmd
- PyPI: https://pypi.org/project/rqmd/

This package extracts the markdown status-tracking workflow used in this repository into a portable Python package that can be copied to other projects and eventually published to PyPI.

## What this tool does

- Scans requirement markdown files in a requirements directory.
- Uses `README.md` inside that directory as the requirements index.
- When `--docs-dir` is omitted, auto-detects the nearest viable requirement index from the current working path.
- Normalizes `- **Status:** ...` lines to canonical statuses.
- Parses requirement headers such as `### AC-FOO-001: Title` or `### R-FOO-001: Title`.
- Regenerates per-file summary blocks:

```md
<!-- acceptance-status-summary:start -->
Summary: 10💡 2🔧 3✅ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->
```

- Supports interactive status editing with keyboard navigation.
- Supports non-interactive updates for automation/agents.

Requirement bodies can be as short as a title plus status line, or include richer Given/When/Then acceptance detail under the same heading.

## Status model

- `💡 Proposed`
- `🧪 Pytested`
- `🚧 AI Blocked`
- `⏭️ AI Skipped`
- `🤖 AI Verified`
- `✅ Done`
- `🔄 Change Requested`
- `❌ Cancelled`
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
### AC-FEATURE-001: Core API endpoint
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
```

Priority is optional; requirements without a priority line parse successfully with `priority: None`.

Priority values are normalized case-insensitively, so `p0`, `P0`, `critical`, and `CRITICAL` all map to `🔴 P0 - Critical`.

## Install (local development)

From this folder:

```bash
uv sync
```

Install test dependencies:

```bash
uv sync --extra dev
```

Then run:

```bash
uv run rqmd --help
```

Module entrypoint:

```bash
uv run python -m rqmd --help
```

## Shell completion

rqmd uses Click dynamic completion and supports shell activation without maintaining static completion files.
Completion candidates stay in sync with live requirement docs, including positional target tokens (domain names, requirement IDs, and subsection names).

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

If you are running from a local clone during development, keep using `uv run rqmd` for execution; completion is provided by the installed `rqmd` console entrypoint.

Troubleshooting completion cache refresh:

- zsh: `rm -f ~/.zcompdump* && exec zsh`
- bash: open a new shell session after updating rc files
- fish: `exec fish` after updating config

## Core commands

Check summaries only:

```bash
uv run rqmd --verify-summaries
```

Interactive mode:

```bash
uv run rqmd
```

Open a specific domain file directly (absolute or repo-root-relative path):

```bash
uv run rqmd docs/requirements/interactive-ux.md
```

In non-interactive modes, a positional domain file path scopes operations to that file:

```bash
uv run rqmd docs/requirements/interactive-ux.md --update AC-EXAMPLE-001=verified
```

Interactive file and requirement menus now support:

- `s` to cycle sort columns
- `d` to toggle ascending/descending
- `r` to refresh/rescan while preserving the active sort
- `z` to undo the last recorded history step from a requirement action menu
- `y` to redo the next recorded history step from a requirement action menu
- `h` to open the paged history browser from a requirement action menu

Inside the history browser, selecting an entry opens a detail view where you can:

- press `c` to checkout the selected entry's branch
- press `l` to save a human-readable label for the selected entry's branch
- press `x` to discard the selected entry's alternate branch, with an option to save a label first
- press `p` to cherry-pick the selected commit onto the current branch
- press `r` to replay the selected entry's branch onto the current branch
- press `g` to run history gc with confirmation
- press `G` to run history gc with immediate prune

Long options also accept unique prefixes, so invocations such as `--proj`, `--docs`, and `--as-j` work when they resolve unambiguously.

History operations available in non-interactive mode include:

- `uv run rqmd --history`
- `uv run rqmd --timeline`
- `uv run rqmd --undo`
- `uv run rqmd --redo`
- `uv run rqmd --history-label-branch <branch-name> --history-branch-label <label>`
- `uv run rqmd --history-discard-branch <branch-name> --history-discard-save-label <label> --force-yes`
- `uv run rqmd --history-gc --force-yes`
- `uv run rqmd --history-gc --history-prune-now --force-yes`
- `uv run rqmd --history-checkout-branch <branch-name>`
- `uv run rqmd --history-cherry-pick <entry-index-or-ref> [--history-target-branch <branch-name>]`
- `uv run rqmd --history-replay-branch <branch-name> [--history-target-branch <branch-name>]`

`--history-gc` requires explicit confirmation because it runs maintenance against the hidden `.rqmd/history/rqmd-history` repository. Add `--history-prune-now` to expire reflogs and prune immediately instead of using Git's default grace period.

File lists now default to the `name` sort in descending order.

You can select a named sort strategy catalog for interactive mode:

```bash
uv run rqmd --sort-profile standard
uv run rqmd --sort-profile status-focus
uv run rqmd --sort-profile alpha-asc
```

Initialize docs scaffold (index + starter domain file):

```bash
uv run rqmd --bootstrap
```

`--bootstrap` prompts for a starter requirement key prefix (default: `REQ`; recommended to customize).
Scaffold content is sourced from repository-managed templates in `init-docs/README.md` and `init-docs/domain-example.md`.

Set one requirement non-interactively:

```bash
uv run rqmd --update-id AC-EXAMPLE-001 --update-status implemented
```

Update priorities non-interactively:

```bash
uv run rqmd --update-priority AC-EXAMPLE-001=p0
uv run rqmd --update-priority AC-EXAMPLE-001=critical --update-priority AC-EXAMPLE-002=medium
```

Batch updates can include `priority` fields, or combine `status` and `priority` in one row:

```json
{"id":"AC-EXAMPLE-001","priority":"p0"}
{"id":"AC-EXAMPLE-002","status":"implemented","priority":"medium"}
```

Interactive entry panels can start in priority mode:

```bash
uv run rqmd --focus-priority
```

Within an entry panel, press `t` to cycle status, priority, and flagged editing.

Regenerate summary blocks with priority aggregates included:

```bash
uv run rqmd --priority-rollup --no-walk
```

Filter by priority in tree, JSON, or interactive walk modes:

```bash
uv run rqmd --priority critical --as-tree
uv run rqmd --priority p1 --as-json --no-walk
```

Filter by subsection name with case-insensitive prefix matching:

```bash
uv run rqmd --sub-domain query --as-tree
uv run rqmd --sub-domain api --as-json --no-walk
```

Combine filters for slicing/dicing requirements:

- OR across different filter flags (`--status`, `--priority`, `--flagged`/`--no-flag`, `--has-link`/`--no-link`, `--sub-domain`)
- AND within the same flag when repeated

```bash
uv run rqmd --status proposed --priority p0 --as-tree
uv run rqmd --no-flag --as-json --no-walk
uv run rqmd --has-link --as-json --no-walk
uv run rqmd --status proposed --status implemented --as-json --no-walk
uv run rqmd --sub-domain query --sub-domain api --as-json --no-walk
```

Target an explicit worklist from CLI tokens or a reusable file:

```bash
uv run rqmd demo "Query API"
uv run rqmd --targets-file tmp/focus.txt --as-json --no-walk
```

`--targets-file` accepts `.txt`, `.conf`, or `.md` files with one-per-line or whitespace/comma-separated tokens, and supports `#` comments.

Interactive file and requirement menus also expose `priority` as a sortable column via `s` / `d`.

Use a different ID prefix:

```bash
uv run rqmd --id-namespace R --update-id R-EXAMPLE-001 --update-status implemented
```

Bulk set by repeated flags:

```bash
uv run rqmd --update AC-EXAMPLE-001=implemented --update AC-EXAMPLE-002=verified
```

## AI CLI (rqmd-ai)

`rqmd-ai` is a companion command for AI-oriented workflows. It is read-only by default and supports prompt-context export, plan previews, and guarded apply mode.

Guidance mode:

```bash
uv run rqmd-ai --as-json
```

Export context for prompts:

```bash
uv run rqmd-ai --as-json --dump-status proposed
uv run rqmd-ai --as-json --dump-id RQMD-CORE-001 --include-requirement-body
uv run rqmd-ai --as-json --dump-file ai-cli.md --include-domain-markdown --max-domain-markdown-chars 2000
```

Plan first, then apply explicitly:

```bash
uv run rqmd-ai --as-json --update RQMD-CORE-001=implemented
uv run rqmd-ai --as-json --write --update RQMD-CORE-001=implemented
```

Install a standard AI agent/skill instruction bundle (minimal or full preset):

```bash
uv run rqmd-ai --as-json --install-agent-bundle --bundle-preset minimal --dry-run
uv run rqmd-ai --as-json --install-agent-bundle --bundle-preset full
uv run rqmd-ai --as-json --install-agent-bundle --bundle-preset full --overwrite-existing
```

Bundle installs are idempotent by default and preserve existing customized instruction files unless `--overwrite-existing` is explicitly passed.

When apply mode runs, rqmd-ai appends a structured audit event to the local shared history backend at `.rqmd/history/rqmd-history/audit.jsonl`.

Batch set from file:

```bash
uv run rqmd --update-file tmp/ac-updates.jsonl
```

Allow custom prefixes such as `REQ-` in a repo:

```bash
uv run rqmd --id-namespace REQ --status proposed --as-tree
```

Filter walk:

```bash
uv run rqmd --status proposed
```

Filtered walk resume behavior (enabled by default):

- Uses persisted state so reruns continue at the last visited requirement.
- Disable with `--no-resume-walk`.
- Control storage location with `--session-state-dir`.

Examples:

```bash
uv run rqmd --status implemented --session-state-dir system-temp
uv run rqmd --status implemented --session-state-dir project-local
uv run rqmd --status implemented --session-state-dir .rqmd/state
uv run rqmd --status implemented --no-resume-walk
```

Filter tree only:

```bash
uv run rqmd --status proposed --as-tree
```

Filter as JSON for automation/AI parsing:

```bash
uv run rqmd --status proposed --as-json
```

Filter JSON includes requirement body content and line metadata by default:

```bash
uv run rqmd --status proposed --as-json
```

Use compact output without bodies:

```bash
uv run rqmd --status proposed --as-json --no-requirement-body
```

Summary/check/set JSON examples:

```bash
uv run rqmd --as-json --no-walk
uv run rqmd --verify-summaries --as-json --no-walk
uv run rqmd --update-id AC-EXAMPLE-001 --update-status verified --as-json
uv run rqmd --totals --as-json --no-walk
```

### JSON contract (stable keys)

When `--as-json` is used, top-level keys are stable by mode.
All JSON payloads include `schema_version` (current value: `1.0.0`) and follow semantic versioning (`major.minor.patch`).

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

Explicit global roll-up totals:

```bash
uv run rqmd --totals --no-walk
```

Custom roll-up columns from CLI equations:

```bash
uv run rqmd --totals --totals-map "C1=I+V" --totals-map "C2=P" --no-walk
```

Custom roll-up columns from config (`.json`, `.yml`, `.yaml`):

```bash
uv run rqmd --totals --totals-config .rqmd.yml --as-json --no-walk
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

1. `--totals-map` CLI equations
2. project config (`.rqmd.yml|.rqmd.yaml` in `--project-root`)
3. user config (`~/.config/rqmd/rollup.json|yaml|yml`)
4. built-in canonical status totals

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

This package includes GitHub Actions workflows:

- `.github/workflows/pytest.yml`
- Triggers on push and pull_request.
- Installs project dependencies with `uv sync --extra dev`.
- Runs `bash scripts/local-smoke.sh --skip-install`.

- `.github/workflows/publish-pypi.yml`
- Triggers when a GitHub release is published.
- Builds with `uv build` and publishes with `uv publish` using `PYPI_API_TOKEN`.

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
uv run rqmd --project-root /path/to/project --docs-dir docs/requirements
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

### Project configuration file

To avoid repeating CLI flags across team members, use a single project config file at the project root: `.rqmd.yml` (preferred).
Accepted extensions are `.rqmd.yml`, `.rqmd.yaml`, or `.rqmd.json`.

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
4. Run `uv run rqmd --verify-summaries` in CI to prevent stale summary blocks.
5. Use non-interactive `--update`/`--update-file` in automation.

## Packaging notes

- Package name: `rqmd`
- Console script entrypoint: `rqmd`
- Source package: `src/rqmd`

When ready for PyPI:

1. Follow semantic versioning policy in `docs/SEMVER.md`.
2. Build artifacts with `uv build`.
3. Publish via GitHub release workflow or upload manually using `uv publish`.
