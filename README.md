# rqmd

Reusable requirements and acceptance-criteria workflow CLI.

This package extracts the markdown status-tracking workflow used in this repository into a portable Python package that can be copied to other projects and eventually published to PyPI.

## What this tool does

- Scans requirement markdown files in a criteria directory.
- Uses `README.md` inside that directory as the requirements index.
- When `--criteria-dir` is omitted, auto-detects the nearest viable requirement index from the current working path.
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

Initialize docs scaffold (index + starter domain file):

```bash
uv run rqmd --init
```

`--init` prompts for a starter requirement key prefix (default: `REQ`; recommended to customize).

Set one criterion non-interactively:

```bash
uv run rqmd --set-criterion-id AC-EXAMPLE-001 --set-status implemented
```

Use a different ID prefix:

```bash
uv run rqmd --id-prefix R --set-criterion-id R-EXAMPLE-001 --set-status implemented
```

Bulk set by repeated flags:

```bash
uv run rqmd --set AC-EXAMPLE-001=implemented --set AC-EXAMPLE-002=verified
```

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

Filter tree only:

```bash
uv run rqmd --filter-status proposed --tree
```

Filter as JSON for automation/AI parsing:

```bash
uv run rqmd --filter-status proposed --json
```

Summary/check/set JSON examples:

```bash
uv run rqmd --json --no-interactive
uv run rqmd --check --json --no-interactive
uv run rqmd --set-criterion-id AC-EXAMPLE-001 --set-status verified --json
```

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

The test suite is organized to validate implemented acceptance-criteria behavior for:
- core engine parsing and summary sync
- interactive menu/color behavior
- non-interactive automation flows
- portability and packaging contracts

Detailed coverage mapping is documented in `docs/testing.md`.

## Changelog

Notable project changes are tracked in `CHANGELOG.md` using the Keep a Changelog format.

## CI

This package includes a GitHub Actions workflow at `.github/workflows/pytest.yml`.

- Triggers on push and pull_request.
- Installs project dependencies with `uv sync --extra dev`.
- Runs `bash scripts/local-smoke.sh --skip-install`.

## Project portability

By default, the tool targets the current directory as repo root and auto-detects requirement docs by scanning from the current working path.

Auto-detect preference is deterministic:

1. `docs/requirements/README.md`
2. `requirements/README.md`

You can override both:

```bash
uv run rqmd --repo-root /path/to/project --criteria-dir docs/requirements
```

`--criteria-dir` can be absolute or relative to `--repo-root`.
When auto-detection is used, rqmd reports which index path it selected.

Requirement header prefixes are configurable with `--id-prefix`.
When omitted, rqmd auto-detects prefixes by reading the selected `README.md` requirements index and linked domain docs when available.
If no prefixes are discovered, it falls back to `AC-`, `R-`, and `RQMD-`.

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

1. Choose final author/license metadata in `pyproject.toml`.
2. Build artifacts with `uv build`.
3. Upload using `uv publish`.
