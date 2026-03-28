# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added `extract_blocking_id()` to `req_parser.py`; `blocking_id` and `blocked_reason` fields now appear in JSON exports from `rqmd` and `rqmd-ai` when a requirement is blocked by a linked or bare requirement ID (RQMD-CORE-022).
- Added `parse_domain_priority_metadata()` to `req_parser.py`; `domain_priority` and `sub_section_priorities` fields now appear in JSON payloads when domain-level `**Priority:**` metadata is present (RQMD-PRIORITY-012).
- Added `--priorities-config` CLI option for loading a custom project priority catalog from a YAML or JSON file, mirroring the existing `--status-config` option (RQMD-PRIORITY-011).
- Added compact domain-notes pane to the interactive criterion panel in `status_update.py`: shows up to 3 lines of domain preamble body text with `…` truncation when more lines are present (RQMD-INTERACTIVE-018).
- Added interactive link-entry flow accessible via the `t` (toggle-field) key in all interactive loops; supports adding plain URL or `[label](url)` markdown links, optional label prompting for bare URLs, and numbered removal of existing links (RQMD-INTERACTIVE-022).
- Added theme-aware zebra-striping support with config override precedence, including `resolve_zebra_bg()` and threaded `zebra_bg` usage in interactive menus for accessibility-safe rendering (RQMD-INTERACTIVE-012).
- Added best-effort terminal theme detection with ordered precedence (CLI `--theme`, config override, macOS/GNOME probes, default fallback) via `detect_theme()` and wired CLI support for `--theme` (RQMD-INTERACTIVE-013).
- Added a project changelog following the Keep a Changelog format.
- Added README-index portability tests for automatic requirements discovery.
- Added deep scratch pagination corpus pages through page 23 for e2e coverage.
- Added first-class `--json` output for non-interactive summary/check/set/filter workflows to support machine-readable automation and AI triage.
- Added `schema_version` to JSON payload contracts across `rqmd` and `rqmd-ai`, with coverage tests for both CLIs.
- Added shell-completion activation and troubleshooting guidance for zsh, bash, and fish in README.
- Added requirement-level tests for status value-prefix resolution and ambiguous option-prefix candidate reporting.
- Added `rqmd-ai --install-agent-bundle` with minimal/full presets, dry-run preview, idempotent reruns, and optional overwrite behavior for existing instruction files.
- Added unknown-status compatibility tests and machine-readable JSON error payload coverage.
- Added `rqmd.readme_gen` module for RQMD-CORE-024: domain-to-README section generation with idempotent marker-based updates, status rollup summaries, and integration-ready API.
- Added comprehensive tests for README generation: domain summary extraction, section generation, marker-based updates, and idempotency validation.
- Added `--rename-id-prefix OLD=NEW` one-time bulk rename mode to rewrite requirement ID prefixes across domain files with conflict detection, dry-run/json output support, and per-file replacement summaries (RQMD-CORE-023).
- Added `--screen-write/--no-screen-write` with `screen_write` config support and precedence resolution (CLI > project config > user config > TTY default) for interactive rendering mode selection (RQMD-UI-002).

### Changed

- Switched requirements index layout from sibling requirements.md files to in-directory README.md files.
- Updated rqmd auto-detection to use docs/requirements/README.md and requirements/README.md.
- Updated scaffold generation to create README.md inside the requirements directory.
- Updated portability, core-engine, and README documentation to match the new requirements index contract.
- Updated bootstrap/index messaging with branded RDD tagline and direct GitHub/PyPI links.
- Updated README and requirements index status workflow documentation to the new ordered status catalog.
- Updated requirement statuses to mark `RQMD-CORE-017` and `RQMD-PACKAGING-010` as Implemented.
- Updated requirement status to mark `RQMD-AI-012` as Implemented.
- Updated requirement status to mark `RQMD-PORTABILITY-017` as Implemented.
- Updated requirement status to mark `RQMD-CORE-024` as Implemented (README auto-generation from domains).

## [0.1.0] - 2026-03-26

### Added

- Initial rqmd package release with interactive and automation-friendly requirements status workflows.