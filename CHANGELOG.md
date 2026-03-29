# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added

- Added `rqmd --history-gc` with optional `--history-prune-now`, plus explicit confirmation and JSON/text reporting for safe maintenance of the hidden `rqmd-history` repository (progress toward RQMD-UNDO-007).
- Added interactive `g` and `G` history-browser actions for confirmed history gc and immediate-prune maintenance from the entry detail view (progress toward RQMD-UNDO-007).
- Added interactive `l` and `x` history-browser actions for saving named branch labels and discarding alternate branches, including an explicit chance to save a snapshot label before destructive branch removal (progress toward RQMD-UNDO-007).
- Added `rqmd --history-label-branch <name> --history-branch-label <label>` so automation can name alternate history branches without using the interactive browser (progress toward RQMD-UNDO-007).
- Added `rqmd --history-discard-save-label <label>` so non-interactive branch discard flows can preserve a named snapshot label in the same command before branch navigation is removed (progress toward RQMD-UNDO-007).
- Added `rqmd --history-gc-save-label <label>` plus matching interactive gc/prune save-label prompts so maintenance flows can preserve a named snapshot label before destructive history cleanup runs (progress toward RQMD-UNDO-007).
- Added proposed Vim-alignment requirements covering `j`/`k` vertical navigation defaults, richer Vim-style motions (`gg`, `G`, `Ctrl-U`, `Ctrl-D`), and `/`/`?` search with `n`/`N` repeat semantics in interactive mode.
- Added a pytest timeout guard (`timeout = 30`) plus a startup requirement for `pytest-timeout`, so interactive regressions fail fast instead of silently hanging when the timeout plugin is missing from the local test environment.
- Updated local test and smoke-check commands to use `uv run --extra dev pytest ...`, matching the `pytest-timeout` requirement instead of relying on plain `uv run pytest`.
- Added explicit selected-row arrow markers in interactive menus so the current status, priority, or flagged choice is obvious on first render even before any further navigation (RQMD-INTERACTIVE-006).
- Added unique long-option prefix expansion in the top-level `rqmd` CLI wrapper, allowing unambiguous prefixes such as `--proj`, `--docs`, and `--as-j` while preserving deterministic ambiguity failures with candidate lists (RQMD-AUTOMATION-019).
- Added `z=undo`, `y=redo`, and `h=history` shortcuts to requirement action menus, plus a paged interactive history browser that surfaces commit, branch, and diff-summary metadata from the existing snapshot log (progress toward RQMD-UNDO-007).
- Added `rqmd --history-checkout-branch <name>` to restore the HEAD snapshot of a named alternate history branch through the main CLI, complementing the existing branch summaries in `--timeline` and branch-prune workflow in `--history-discard-branch` (progress toward RQMD-UNDO-007).
- Added `rqmd --history-cherry-pick <ref>` and `rqmd --history-replay-branch <branch>` with optional `--history-target-branch`, exposing replay/apply history controls through the main CLI for branch recovery workflows without dropping into internal APIs (progress toward RQMD-UNDO-007).
- Updated the interactive history selector to render a git-log-style one-line view with short commits, `HEAD -> branch` decorations, and date-ordered metadata so it reads more like `git log --graph --decorate --all --date-order --oneline` (progress toward RQMD-UNDO-007).
- Added interactive entry actions inside the history browser detail view so a selected history record can drive branch checkout, commit cherry-pick, and branch replay directly from the UI, with explicit confirmation for replay/apply paths (progress toward RQMD-UNDO-007).
- Added targeted pytest timeout markers to the interactive history and deep-paging regressions so accidental input loops fail quickly instead of hanging long local or agent-driven test runs.
- Fixed stray indentation in the screen-write precedence tests and rewrote the new history-browser action regressions to use deterministic stubs, restoring a clean timeout-enabled pytest run across the interactive suite and full repository.

- Added detached historical export browsing to `rqmd-ai` via `--history-ref`, allowing point-in-time inspection of prior requirement snapshots by history index or commit ref without mutating the current working tree (RQMD-TIME-001).
- Added detached historical view safety guards for `rqmd-ai --history-ref`, explicitly rejecting `--write` and `--update` mutation paths while in historical export mode to preserve read-only detached behavior (RQMD-TIME-003).
- Added branch-aware historical timeline in the history backend: automatically creates recovery branches when undoing and making divergent edits, with full DAG reconstruction and branch tracking in state metadata (RQMD-TIME-002).
- Added historical activity context in `rqmd-ai` history exports, including neighboring entry pointers and per-requirement before/after status deltas for the selected history entry (RQMD-TIME-004).
- Added `--compare-refs` to `rqmd-ai` for point-in-time diff views between any two history refs; supports `A..B` and `A B` syntax with entry indices, commit hashes, `head`, `current`, and `latest` keywords; returns structured JSON with status transitions, added/removed requirements, and cumulative summary counters (RQMD-TIME-005).
- Added stable history identifiers (`hid:<commit>`) in `rqmd-ai` historical payloads (`history_source`, compare refs, and neighbors), and support for resolving those identifiers in `--history-ref` and `--compare-refs` for durable deep links (RQMD-TIME-008).
- Added `rqmd-ai --history-report` for exportable temporal reports in both JSON (`--as-json`) and text form, covering single detached historical states (`--history-ref`) and point-to-point comparison ranges (`--compare-refs`) with summary counters and per-requirement details (RQMD-TIME-009).
- Added timeline query filters in `rqmd --timeline` for branch, actor, command, file path, requirement ID, transition token, and ISO-8601 date ranges, with enriched node metadata (`changed_requirement_ids`, `status_transitions`) to support machine-readable navigation in long-lived histories (RQMD-TIME-007).
- Added `rqmd-ai --history-action` read-only previews for `restore`, `replay`, and `cherry-pick` planning workflows, including action-step metadata and diff-style impact summaries before any write paths are used (RQMD-TIME-006).
- Added a temporal verification matrix test suite covering branch graph reconstruction, detached historical reads, point-to-point diffs, replay previews, and stable identifier resolution across multi-file branching fixtures (RQMD-TIME-010).
- Added `rqmd --history` non-interactive history-log API output (text + JSON) including entry-indexed commits, stable IDs, branch metadata, head cursor, and undo/redo availability for automation flows (RQMD-UNDO-009).
- Added `rqmd --undo` and `rqmd --redo` non-interactive catalog restoration commands backed by persistent snapshot history, including automatic baseline capture on the first rqmd mutation (RQMD-UNDO-001).
- Added persistent hidden `.rqmd/history/rqmd-history` git-backed catalog snapshots plus on-disk cursor state (v2.0) with branch tracking for durable undo/redo recovery and branch-aware history across process restarts (RQMD-UNDO-005, RQMD-TIME-002).
- Added restart-durability regression coverage for undo history persistence, validating that entries, cursor state, snapshot materialization, and undo/redo behavior survive `HistoryManager` reinitialization (RQMD-UNDO-002).
- Added an undo verification matrix suite covering history log output, branch-aware timeline views, replay preview planning, and restart-based undo checks across multi-file divergent history fixtures (RQMD-UNDO-010).
- Added explicit rqmd-ai apply audit linkage to `rqmd-history` commits, including per-update history entry metadata (`entry_index`, commit, stable `hid:` identifier, timestamp, command, branch) in both API payloads and persisted audit events for deterministic undo/audit cross-referencing (RQMD-UNDO-011).
- Added structured history delta payloads to persisted `rqmd-history` entries and `rqmd --history --as-json` output, including per-file numstat summaries (`additions`, `deletions`, `files_changed`) alongside existing provenance metadata for audit and timeline consumers (RQMD-UNDO-006).
- Added priority undo/history semantics coverage: priority-only updates are recorded as first-class `set-priority` history operations, and combined status+priority updates are captured atomically as a single `update-requirement` history entry with undo/redo restoration behavior (RQMD-PRIORITY-008).
- Added UI-010 renderer verification coverage with a dedicated row-diff helper (`compute_row_diff`) and tests covering changed-row detection, row removal semantics, and integration behavior across both TTY screen-write and non-TTY fallback paths for CI stability (RQMD-UI-010).
- Added UI-008 terminal resize handling in interactive menus by wiring SIGWINCH lifecycle management (install on TTY entry, consume pending resize markers, restore previous handler on exit) with regression tests to ensure resize events preserve stable rendering and selection flow (RQMD-UI-008).
- Added UI-007 contrast-preserving redraw safeguards: vetted zebra background accessibility checks, CLI-level colorized redraw gating, and fallback to plain non-colorized menu rendering when background contrast cannot be trusted (RQMD-UI-007).
- Added UI-009 adaptive performance heuristics with a dedicated render-mode controller using smoothed latency windows (median/p95), hysteresis thresholds, and cooldown-based anti-thrashing transitions between `screen-write` and `append` rendering modes, including regression tests for sustained-latency degrade/recover behavior (RQMD-UI-009).
- Added UNDO-003 branching history support with automatic recovery branch creation on divergence, new `HistoryManager` methods (`checkout_branch`, `cherry_pick`, `replay_branch`, `label_branch`, `discard_branch`, `get_branches`), branch head tracking in state metadata, and comprehensive regression tests for branch navigation, preservation of alternate timelines, and replay workflows (RQMD-UNDO-003).
- Added `rqmd --history-discard-branch <name>` as a dedicated non-interactive history mode for pruning alternate branches, with explicit confirmation enforcement (`--force-yes`) for automation-safe destructive operations and JSON/text result payloads (RQMD-UNDO-004).
- Added scratch frontend QA assets under `test-corpus/scratch/`: a new mixed-metadata edge-case corpus page (`requirements/page-24-edge-cases.md`) and a task-oriented manual validation guide (`QA-frontend-checklist.md`) for interactive rendering, resize behavior, filters, and history/confirmation smoke checks.
- Added portability hardening for user-facing compatibility failures to avoid raw Python traceback output in normal CLI flows, including catalog-safe roll-up rendering with custom status taxonomies and regression coverage for interactive startup behavior (RQMD-PORTABILITY-018).

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
- Added full-screen ANSI redraw behavior for interactive menus when `--screen-write` is enabled or configured; includes clear + home cursor escapes on each render and pagination for snappy, stable visual updates without scrollback artifacts (RQMD-UI-001).
- Added `--screen-write/--no-screen-write` with `screen_write` config support and precedence resolution (CLI > project config > user config > TTY default) for interactive rendering mode selection (RQMD-UI-002).
- Added automatic fallback to scrolling/append-style output for non-TTY environments (scripts, CI, piped output, file redirects); screen-write mode respects `sys.stdout.isatty()` check to ensure no ANSI escapes in non-interactive contexts (RQMD-UI-003).
- Added reserved footer region for standardized legend and transient notification messages in interactive menus; `footer_legend` parameter allows custom key-mapping displays (e.g., `d=[asc|dsc]`) that reliably persist across renders and pagination without shifting menu content (RQMD-UI-006).
- Added stable cursor/selection position maintenance across pagination and re-renders in interactive menus; `selected_option_index` parameter with optional `selected_option_bg` highlighting ensures predictable focus across n/p key navigation and page transitions (RQMD-UI-005).

### Changed

- Updated the scratch QA checklist with a step-by-step undo/history UX walkthrough covering `h` history browsing, `z` undo, `y` redo, git-style history rows, branch divergence setup, and branch checkout verification.
- Updated requirement status to mark `RQMD-AUTOMATION-019` as Implemented (unique option-name/value prefix abbreviations now supported in `rqmd`).
- Updated human-readable `rqmd --history` output to include reason text and compact diff summaries (`+additions/-deletions`, changed-file count) for each entry, bringing the text mode closer to the existing JSON metadata surface (progress toward RQMD-UNDO-007).

- Updated requirement status to mark `RQMD-TIME-005` as Implemented (compare historical points via `--compare-refs`).
- Updated requirement status to mark `RQMD-TIME-003` as Implemented (detached historical view mode via `--history-ref`).
- Updated requirement status to mark `RQMD-TIME-008` as Implemented (stable historical identifiers and deep-linkable refs).
- Updated requirement status to mark `RQMD-TIME-009` as Implemented (exportable temporal state and comparison reports via `--history-report`).
- Updated requirement status to mark `RQMD-TIME-007` as Implemented (timeline filters and queryable navigation in `--timeline`).
- Updated requirement status to mark `RQMD-TIME-006` as Implemented (restore/replay/cherry-pick preview planning via `--history-action`).
- Updated requirement status to mark `RQMD-TIME-010` as Implemented (temporal verification coverage matrix).
- Updated requirement status to mark `RQMD-UNDO-009` as Implemented (programmatic history listing via `rqmd --history`).
- Updated requirement status to mark `RQMD-UNDO-002` as Implemented (persistent history durability across restart/recovery flows).
- Updated requirement status to mark `RQMD-UNDO-010` as Implemented (undo/history verification matrix coverage).
- Updated requirement status to mark `RQMD-UNDO-011` as Implemented (unified undo and audit capture cross-referencing through `rqmd-history`).
- Updated requirement status to mark `RQMD-UNDO-006` as Implemented (history metadata, provenance, and delta payload coverage).
- Updated requirement status to mark `RQMD-UNDO-004` as Implemented (interactive/non-interactive confirmation guardrails for history-destructive branch discard actions).
- Updated requirement status to mark `RQMD-PRIORITY-008` as Implemented (undo/history semantics for priority-only and combined mutations).
- Updated requirement status to mark `RQMD-UI-010` as Implemented (renderer diff-engine and terminal-path test coverage in CI).
- Updated requirement status to mark `RQMD-UI-008` as Implemented (SIGWINCH resize reflow handling in interactive screen-write flows).
- Updated requirement status to mark `RQMD-UI-007` as Implemented (contrast-preserving redraw validation with safe color fallback).
- Updated requirement status to mark `RQMD-UI-009` as Implemented (smoothed latency heuristics with hysteresis and cooldown mode-transition guardrails).
- Updated interactive refresh flow to preserve current pagination context in file/requirement menus by carrying page metadata through refresh events instead of resetting to page 1.
- Updated interactive sort cycling behavior to follow a deterministic left-to-right ring aligned with visible sort columns.
- Updated file/requirement selection rendering to surface priority visuals directly in list rows and sortable header columns (explicit `priority` column label and per-row priority emoji markers).
- Updated scratch frontend checklist to prioritize manual interactive/tree QA commands and move JSON-heavy checks into optional automation spot checks.
- Updated requirement status to mark `RQMD-PORTABILITY-018` as Implemented (user-facing compatibility errors without uncaught Python stack traces in normal CLI use).
- Updated the CLI entrypoint safety behavior so unexpected uncaught internal exceptions render as a single friendly error line by default, while `-v/--detailed` preserves traceback re-raise behavior for debugging.
- Updated interactive navigation to make `j`/`k` the primary keyboard next/prev controls in paged menus and requirement walkthroughs, while keeping arrow-key navigation intact and removing `n`/`p` as vertical-navigation aliases.
- Updated requirement status to mark `RQMD-INTERACTIVE-023` as Implemented (`j`/`k` Vim-style vertical navigation defaults).
- Fixed a `--screen-write` regression where adaptive render-mode fallback could override an explicit CLI request; explicit `--screen-write` now forces full-screen redraw for that run, and render-mode state is reset at CLI startup.
- Fixed interactive requirement-action rendering so full requirement panels remain visible during status/priority/flagged/link prompts under screen-write redraws, restoring the colored rule, source/domain notes, and requirement body instead of dropping to a terse menu-only prompt.

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