# rqmd

Reusable requirements and acceptance-requirements workflow CLI.

This package extracts the markdown status-tracking workflow used in this repository into a portable Python package that can be copied to other projects and eventually published to PyPI.

## What this tool does

- Scans requirement markdown files in a requirements directory.
- Uses `README.md` inside that directory as the requirements index.
- When `--requirements-dir` is omitted, auto-detects the nearest viable requirement index from the current working path.
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
- `🔧 Implemented`
- `✅ Verified`
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

## Core commands

Check summaries only:

```bash
uv run rqmd --check
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
uv run rqmd docs/requirements/interactive-ux.md --set AC-EXAMPLE-001=verified
```

Interactive file and requirement menus now support:

- `s` to cycle sort columns
- `d` to toggle ascending/descending
- `r` to refresh/rescan while preserving the active sort

File lists now default to the `name` sort in descending order.

You can select a named sort strategy catalog for interactive mode:

```bash
uv run rqmd --sort-strategy standard
uv run rqmd --sort-strategy status-focus
uv run rqmd --sort-strategy alpha-asc
```

Initialize docs scaffold (index + starter domain file):

```bash
uv run rqmd --init
```

`--init` prompts for a starter requirement key prefix (default: `REQ`; recommended to customize).
Scaffold content is sourced from repository-managed templates in `init-docs/README.md` and `init-docs/domain-example.md`.

Set one requirement non-interactively:

```bash
uv run rqmd --set-requirement-id AC-EXAMPLE-001 --set-status implemented
```

Update priorities non-interactively:

```bash
uv run rqmd --set-priority AC-EXAMPLE-001=p0
uv run rqmd --set-priority AC-EXAMPLE-001=critical --set-priority AC-EXAMPLE-002=medium
```

Batch updates can include `priority` fields, or combine `status` and `priority` in one row:

```json
{"id":"AC-EXAMPLE-001","priority":"p0"}
{"id":"AC-EXAMPLE-002","status":"implemented","priority":"medium"}
```

Interactive entry panels can start in priority mode:

```bash
uv run rqmd --priority-mode
```

Within an entry panel, press `t` to cycle status, priority, and flagged editing.

Regenerate summary blocks with priority aggregates included:

```bash
uv run rqmd --show-priority-summary --no-interactive
```

Filter by priority in tree, JSON, or interactive walk modes:

```bash
uv run rqmd --filter-priority critical --tree
uv run rqmd --filter-priority p1 --json --no-interactive
```

Filter by subsection name with case-insensitive prefix matching:

```bash
uv run rqmd --filter-sub-domain query --tree
uv run rqmd --filter-sub-domain api --json --no-interactive
```

Target an explicit worklist from CLI tokens or a reusable file:

```bash
uv run rqmd demo "Query API"
uv run rqmd --filter-ids-file tmp/focus.txt --json --no-interactive
```

`--filter-ids-file` accepts `.txt`, `.conf`, or `.md` files with one-per-line or whitespace/comma-separated tokens, and supports `#` comments.

Interactive file and requirement menus also expose `priority` as a sortable column via `s` / `d`.

Use a different ID prefix:

```bash
uv run rqmd --id-prefix R --set-requirement-id R-EXAMPLE-001 --set-status implemented
```

Bulk set by repeated flags:

```bash
uv run rqmd --set AC-EXAMPLE-001=implemented --set AC-EXAMPLE-002=verified
```

## AI CLI (rqmd-ai)

`rqmd-ai` is a companion command for AI-oriented workflows. It is read-only by default and supports prompt-context export, plan previews, and guarded apply mode.

Guidance mode:

```bash
uv run rqmd-ai --json
```

Export context for prompts:

```bash
uv run rqmd-ai --json --export-status proposed
uv run rqmd-ai --json --export-id RQMD-CORE-001 --include-body
uv run rqmd-ai --json --export-file ai-cli.md --include-domain-body --max-domain-body-chars 2000
```

Plan first, then apply explicitly:

```bash
uv run rqmd-ai --json --set RQMD-CORE-001=implemented
uv run rqmd-ai --json --apply --set RQMD-CORE-001=implemented
```

When apply mode runs, rqmd-ai appends a structured audit event to the local shared history backend at `.rqmd/history/rqmd-history/audit.jsonl`.

Batch set from file:

```bash
uv run rqmd --set-file tmp/ac-updates.jsonl
```

Allow custom prefixes such as `REQ-` in a repo:

```bash
uv run rqmd --id-prefix REQ --filter-status proposed --tree
```

Filter walk:

```bash
uv run rqmd --filter-status proposed
```

Filtered walk resume behavior (enabled by default):

- Uses persisted state so reruns continue at the last visited requirement.
- Disable with `--no-resume-filter`.
- Control storage location with `--state-dir`.

Examples:

```bash
uv run rqmd --filter-status implemented --state-dir system-temp
uv run rqmd --filter-status implemented --state-dir project-local
uv run rqmd --filter-status implemented --state-dir .rqmd/state
uv run rqmd --filter-status implemented --no-resume-filter
```

Filter tree only:

```bash
uv run rqmd --filter-status proposed --tree
```

Filter as JSON for automation/AI parsing:

```bash
uv run rqmd --filter-status proposed --json
```

Filter JSON includes requirement body content and line metadata by default:

```bash
uv run rqmd --filter-status proposed --json
```

Use compact output without bodies:

```bash
uv run rqmd --filter-status proposed --json --no-body
```

Summary/check/set JSON examples:

```bash
uv run rqmd --json --no-interactive
uv run rqmd --check --json --no-interactive
uv run rqmd --set-requirement-id AC-EXAMPLE-001 --set-status verified --json
uv run rqmd --rollup --json --no-interactive
```

### JSON contract (stable keys)

When `--json` is used, top-level keys are stable by mode:

- `summary`: `mode`, `criteria_dir`, `changed_files`, `totals`, `files`, `ok`
- `check`: `mode`, `criteria_dir`, `changed_files`, `totals`, `files`, `ok`
- `set` / `set-priority` / `set-flagged`: `mode`, `criteria_dir`, `changed_files`, `totals`, `files`, `updates`
- `filter-status`: `mode`, `status`, `criteria_dir`, `total`, `files`
- `filter-priority`: `mode`, `priority`, `criteria_dir`, `total`, `files`
- `filter-flagged`: `mode`, `flagged`, `criteria_dir`, `total`, `files`
- `filter-sub-domain`: `mode`, `sub_domain`, `criteria_dir`, `total`, `files`
- `filter-targets`: `mode`, `targets`, `criteria_dir`, `total`, `files`
- `rollup`: `mode`, `criteria_dir`, `file_count`, `totals`, optional `rollup_source`, optional `rollup_columns`
- `init`: `mode`, `criteria_dir`, `starter_prefix`, `created_files`, `created_count`
- `init-priorities`: `mode`, `criteria_dir`, `default_priority`, `changed_files`, `changed_count`

Filter payloads return `files` ordered by path and requirement entries ordered by requirement ID.
By default, filter JSON includes `body.markdown` and line metadata; pass `--no-body` to omit bodies.
Each requirement entry includes `sub_domain` (string or `null`), and each file entry includes `sub_sections` with subsection names and requirement counts.

### Exit codes

RQMD uses this exit-code matrix for automation:

- `0`: Success (including successful no-op runs)
- `1`: Validation or contract failure (for example `--check` found out-of-sync summaries, invalid input, missing docs, ambiguity, or other `ClickException` errors)
- `130`: Interrupted by user (`Ctrl+C`)

Explicit global roll-up totals:

```bash
uv run rqmd --rollup --no-interactive
```

Custom roll-up columns from CLI equations:

```bash
uv run rqmd --rollup --rollup-map "C1=I+V" --rollup-map "C2=P" --no-interactive
```

Custom roll-up columns from config (`.json`, `.yml`, `.yaml`):

```bash
uv run rqmd --rollup --config .rqmd.yml --json --no-interactive
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

1. `--rollup-map` CLI equations
2. project config (`.rqmd.yml|.rqmd.yaml` in `--repo-root`)
3. user config (`~/.config/rqmd/rollup.json|yaml|yml`)
4. built-in canonical status totals

## Tests

Run full pytest suite from this folder:

```bash
uv run pytest
```

Run a specific test module:

```bash
uv run pytest tests/test_core_engine.py
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

By default, rqmd auto-discovers `--repo-root` by searching from the current working directory upward.
The nearest ancestor with a supported marker wins.

Marker priority within each directory is deterministic:

1. `.rqmd.yml`, `.rqmd.yaml`, `.rqmd.json`
2. `docs/requirements/`
3. `requirements/`

If no marker is found, rqmd falls back to current working directory.
When auto-discovery is used, rqmd reports the discovered root and source marker.

Passing explicit `--repo-root` bypasses auto-discovery.

When `--requirements-dir` is omitted, rqmd auto-detects requirement docs by scanning from the current working path.

Auto-detect preference is deterministic:

1. `docs/requirements/README.md`
2. `requirements/README.md`

You can override both:

```bash
uv run rqmd --repo-root /path/to/project --requirements-dir docs/requirements
```

`--requirements-dir` can be absolute or relative to `--repo-root`.
When auto-detection is used, rqmd reports which index path it selected.

Filtered walkthrough resume state is configurable with `--state-dir`:

- `system-temp` (default): OS temp directory.
- `project-local`: `<repo-root>/tmp/rqmd`.
- custom path: absolute or relative to `--repo-root`.

Requirement header prefixes are configurable with `--id-prefix`.
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
4. Run `uv run rqmd --check` in CI to prevent stale summary blocks.
5. Use non-interactive `--set`/`--set-file` in automation.

## Packaging notes

- Package name: `rqmd`
- Console script entrypoint: `rqmd`
- Source package: `src/rqmd`

When ready for PyPI:

1. Follow semantic versioning policy in `docs/SEMVER.md`.
2. Build artifacts with `uv build`.
3. Publish via GitHub release workflow or upload manually using `uv publish`.
