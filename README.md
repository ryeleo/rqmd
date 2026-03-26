# ac-docs-cli

Reusable Acceptance Criteria documentation workflow CLI.

This package extracts the AC maintenance workflow used in this repository into a portable Python package that can be copied to other projects and eventually published to PyPI.

## What this tool does

- Scans AC markdown files in a criteria directory (default: `docs/acceptance-criteria`).
- Normalizes `- **Status:** ...` lines to canonical statuses.
- Regenerates per-file summary blocks:

```md
<!-- acceptance-status-summary:start -->
Summary: 10💡 2🔧 1💻 0🎮 3✅ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->
```

- Supports interactive status editing with keyboard navigation.
- Supports non-interactive updates for automation/agents.

## Status model

- `💡 Proposed`
- `🔧 Implemented`
- `💻 Desktop-Verified`
- `🎮 VR-Verified`
- `✅ Done`
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
uv run ac-cli --help
```

Module entrypoint:

```bash
uv run python -m ac_cli --help
```

## Core commands

Check summaries only:

```bash
uv run ac-cli --check
```

Interactive mode:

```bash
uv run ac-cli
```

Set one criterion non-interactively:

```bash
uv run ac-cli --set-criterion-id AC-EXAMPLE-001 --set-status implemented
```

Bulk set by repeated flags:

```bash
uv run ac-cli --set AC-EXAMPLE-001=implemented --set AC-EXAMPLE-002=desktop-verified
```

Batch set from file:

```bash
uv run ac-cli --set-file tmp/ac-updates.jsonl
```

Filter walk:

```bash
uv run ac-cli --filter-status proposed
```

Filter tree only:

```bash
uv run ac-cli --filter-status proposed --tree
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

## CI

This package includes a GitHub Actions workflow at `.github/workflows/pytest.yml`.

- Triggers on push and pull_request.
- Installs project dependencies with `uv sync --extra dev`.
- Runs `bash scripts/local-smoke.sh --skip-install`.

## Project portability

By default, the tool targets the current directory as repo root and reads from:

- `docs/acceptance-criteria/*.md`

You can override both:

```bash
uv run ac-cli --repo-root /path/to/project --criteria-dir docs/acceptance-criteria
```

`--criteria-dir` can be absolute or relative to `--repo-root`.

## Recommended docs recipe for projects

1. Keep a top-level index doc (example: `docs/acceptance-criteria.md`).
2. Keep domain files in `docs/acceptance-criteria/`.
3. Ensure each criterion has exactly one status line directly under the `### AC-...` header.
4. Run `uv run ac-cli --check` in CI to prevent stale summary blocks.
5. Use non-interactive `--set`/`--set-file` in automation.

## Packaging notes

- Package name: `ac-docs-cli`
- Console script entrypoint: `ac-cli`
- Source package: `src/ac_cli`

When ready for PyPI:

1. Choose final author/license metadata in `pyproject.toml`.
2. Build artifacts with `uv build`.
3. Upload using `uv publish`.
