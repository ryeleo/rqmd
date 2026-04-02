# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]
### Added

- Added proposed backlog requirements to continue moving shipped defaults toward a packaged-resource source of truth and to ensure legacy-init installs local schema guidance into generated requirement indexes for AI-friendly repository-local onboarding (RQMD-CORE-035, RQMD-AI-038).
- Added proposed backlog requirements for long-running and easy-first rqmd development agents, markdown catalog schema versioning, duplicate-ID repair, positional `rqmd ranked` grooming entry, and grapheme-safe emoji alignment in interactive menus; also cleaned the brainstorm and bug notes to point at tracked follow-up work (RQMD-AI-036, RQMD-AI-037, RQMD-CORE-033, RQMD-CORE-034, RQMD-SORTING-016, RQMD-INTERACTIVE-032).
- Added default `.rqmd.yml` scaffolding during `rqmd init --scaffold` and both rqmd-ai init apply paths so newly initialized repositories get an explicit root config with the selected requirements directory, ID prefix, and canonical status/priority catalogs for human and AI consumers (RQMD-CORE-032).
- Added rqmd-ai guidance that now prefers pairing a short user-story block with Given/When/Then acceptance bullets when both clarify a requirement, across the installed AI bundle and starter authoring templates (RQMD-AI-034).
- Added default markdown closeout guidance to the bundled `.github/copilot-instructions.md` template installed by `rqmd-ai init` and `rqmd-ai install`, preferring `# What got done`, `# Up next`, and `# Direction` with rendered requirement bodies in `Up next` instead of fenced code blocks (RQMD-AI-035).
- Added proposed backlog requirements for opening the current requirement in VS Code from the interactive UI, opening linked requirement references directly from interactive requirement detail views, and for first-class dual support of user-story plus Given/When/Then requirement blocks.
- Added an explicit interactive interview contract and ordered interview flow metadata to chat-mode `rqmd-ai` payloads so receiving agents are told to run a one-question-at-a-time multi-choice session with checked defaults and deferred recap behavior instead of summarizing answers after every question (RQMD-AI-033).
- Added stronger `rqmd-ai init` interview guidance for requirement ID prefixes by recommending a short project-specific key when one can be inferred, and added explicit default-checked selection metadata for suggested or recommended multi-select init choices (RQMD-AI-031, RQMD-AI-032).
- Added a unified `rqmd-ai init` entrypoint with `--chat` and `--legacy` support, plus a new bundled `rqmd-init` skill and copy/paste AI handoff prompts that guide the default onboarding flow through grouped interview questions before any write step (RQMD-AI-025, RQMD-AI-026, RQMD-AI-027, RQMD-AI-028, RQMD-AI-029, RQMD-AI-030).
- Added a chat-first `rqmd init` entrypoint that emits the same AI handoff contract as `rqmd-ai init --chat`, making guided onboarding the default public setup flow while keeping `--bootstrap` as a direct scaffold compatibility path (RQMD-CORE-029, RQMD-CORE-030).
- Added bundle-aware default `rqmd-ai` guide output that embeds packaged skill and agent definitions from `resources/bundle` when no workspace bundle is installed, while suppressing those embedded definitions and reporting active local files once the rqmd bundle is present (RQMD-AI-016, RQMD-AI-017, RQMD-AI-018).
- Added resource-backed brainstorm proposal title and ranking metadata so rqmd-ai brainstorm sorting/order guidance is no longer hard-coded in Python and can be tuned from the bundled skill definition.
- Added project-local `dev` and `test` skill scaffolding during `rqmd-ai install`, using detected repository commands as a reviewable starting point, and updated `rqmd-dev` guidance to rely on those generated skills when present (RQMD-AI-019, RQMD-AI-021).
- Added `rqmd-ai --workflow-mode init-legacy`, a bundled `rqmd-init-legacy` skill, and a first-pass legacy bootstrap flow that can preview or write a seeded requirements folder from repository structure, detected commands, and optional `gh` issue discovery (RQMD-AI-022, RQMD-AI-023, RQMD-AI-024).
- Added `rqmd-ai install --bootstrap-chat`, which exposes a structured interview payload for AI-guided bundle bootstrap, including inferred command questions, override answers, and generated `/dev` and `/test` skill previews before writing (RQMD-AI-020).
- Added duplicate requirement ID validation across rqmd and rqmd-ai plus a new `rqmd --next-id` allocator that emits the next sequential numeric ID for a single active namespace, using 3-digit minimum padding by default and continuing cleanly past `999` (RQMD-CORE-026, RQMD-CORE-027, RQMD-CORE-028).
- Added installable Copilot workflow skills for brainstorm planning, backlog triage, focused context export, implementation, status/priority maintenance, doc sync, history inspection, bundle management, and verification, plus specialized full-preset agents for requirements, docs, history, and bundle maintenance; the bundle/docs now ship those workflows while explicitly documenting that skills and agents do not bypass tool approval prompts.
- Added an optional `speedups` extra powered by `orjson`, and wired rqmd/rqmd-ai JSON export plus audit-log serialization through a native-acceleration helper with a pure-Python fallback (RQMD-CORE-025).
- Added `reqmd` and `reqmd-ai` as pre-release console-script aliases while keeping `rqmd` and `rqmd-ai` as the canonical command names, and documented the manual PyPI-check plus compatibility-window plan for any future rename decision (RQMD-PACKAGING-012).
- Added `rqmd-ai --workflow-mode brainstorm` as a read-only planning surface that parses brainstorm markdown into ranked requirement suggestions with recommended target docs, suggested IDs, canonical proposed status, and inferred priorities (RQMD-AI-014).

### Changed

- Changed repeated positional requirement IDs such as `rqmd SSVR-0001 SSVR-0002` to use the focused multi-target selection flow instead of being intercepted by the legacy single-ID lookup shortcut.
- Changed shared interview group ordering, interaction-contract guidance, ID-prefix option copy, and bootstrap-chat, starter-init, and legacy-init interview labels, prompts, grouping, selection defaults, and option sets to load from packaged init YAML instead of hard-coded `rqmd-ai` Python dicts.
- Changed init strategy reason strings and legacy-init README note sections to load from packaged init templates instead of remaining inline `rqmd-ai` strings, continuing the packaged-resource migration for shipped onboarding copy.
- Changed init templates to live under `src/rqmd/resources/init/` as the single packaged source of truth, replacing the parallel `init-docs/` and `src/rqmd/init_docs/` directories and aligning init assets with the existing `resources/` layout.
- Changed scaffold prompt, completion, idempotent no-op, and empty-directory confirmation messages to load from packaged init templates via a shared CLI helper instead of repeating those strings inline across scaffold paths.
- Changed the `rqmd-ai init` chat handoff prompt body to render from packaged init templates, including the bundle-follow-up section and final verification steps, so another long shipped onboarding script is editable outside Python code.
- Changed the shared AI-chat handoff heading, preview-only notice, and `rqmd init` chat-first notice to load from packaged init message templates instead of being repeated inline across `rqmd` and `rqmd-ai`.
- Changed no-docs and missing-index startup guidance to load from packaged init message templates instead of duplicated inline CLI strings, extending the shared resource-backed path to more first-run user-facing text.
- Changed the default `.rqmd.yml` scaffold to render from an editable init template plus catalog placeholders instead of assembling the YAML layout entirely in Python, pushing another shipped init asset onto the packaged-resource path.
- Changed the remaining legacy-init seeded requirement document bodies for source-area, workflow, and issue-backlog files to load from editable init templates instead of embedded Python markdown builders, continuing the packaged-resource migration for shipped init content.
- Changed legacy-init README generation to use the same packaged requirements-index template as scaffold init, so init workflows now install a consistent schema-bearing requirements index instead of maintaining divergent README builders.
- Changed the built-in default status and priority catalogs to load from packaged YAML resources under `src/rqmd/resources/catalogs/`, and updated scaffold generation to consume those same resources so future default-catalog edits are data-driven instead of scattered across Python constants.
- Added `⚠️ Janky` as a built-in default status after `✅ Verified`, propagated the new six-status order through generated summaries, README sync rollups, scaffolds, and interactive status shortcuts so teams can mark verified-but-rough work without custom catalog setup.
- Changed the bare no-docs startup error to print a clearer first-time setup message that recommends the canonical `rqmd init` AI-driven onboarding flow while still surfacing `rqmd init --scaffold` as the manual compatibility path (RQMD-CORE-009).
- Changed the GitHub release publishing workflow to require a stable semver release tag that matches `project.version`, and switched PyPI publication to GitHub trusted publishing instead of a repository-stored API token (RQMD-PACKAGING-008).
- Added explicit `rqmd-ai --workflow-mode` guidance variants for `general`, `brainstorm`, and `implement`, including a proposal-batch implement loop that tells agents to work the highest-priority 1-3 proposed requirements at a time and re-run rqmd/tests/priority checks between batches (RQMD-AI-015).
- Added proposed requirement backlog entries for an AI brainstorm mode, proposal-batch implement mode, optional native acceleration hot paths, and a pre-release `ReqMD` rename/alias evaluation so those brainstorm items are now ranked in the tracked requirement set.
- Added lightweight terminal markdown rendering in requirement panels so criterion headings and bold inline labels display cleanly during interactive review without changing the underlying line-oriented markdown contract.
- Added explicit requirement-first AI workflow guidance to the README and AI CLI requirements, codifying the brainstorm -> requirements/docs -> preview -> apply -> verify loop for agent-assisted changes (RQMD-AI-013).
- Added terminology-neutral requirement document wording in scaffolded and generated indexes so teams can treat requirement markdown files as domains, user stories, feature areas, or other project-specific groupings without changing the parser contract (RQMD-PORTABILITY-019).
- Added positional status/priority filter tokens with filter-first precedence over requirement/domain lookup, deterministic prefix matching for IDs and domains, mixed filter-plus-target scoping such as `rqmd P1 core-engine`, and shell completion entries for positional filter values alongside IDs, domains, and subsection tokens (RQMD-AUTOMATION-035, RQMD-INTERACTIVE-027, RQMD-PACKAGING-011).

### Changed

- Changed the recommended initialization vocabulary throughout the docs and bundle guidance to prefer `init` and the chat-first onboarding flow, while keeping `bootstrap`, `--bootstrap-chat`, and `init-legacy` as compatibility surfaces during transition.
- Changed rqmd and rqmd-ai docs, help text, and generated bundle guidance to prefer `--json` as the standard machine-readable output flag while keeping `--as-json` as a backward-compatible alias.
- Changed bootstrap-chat payloads for bundle install and `init-legacy` to expose grouped interview questions with multi-select suggestions, custom-answer prompts, skip support, recommended choices, detected-from hints, safe defaults, and answer-driven catalog generation.
- Changed `rqmd-ai install` to load bundle templates from packaged resource files under `src/rqmd/resources/bundle/` instead of embedding the bundle contents directly in code, so the shipped bundle can be edited as normal files and installed from package data.
- Added policy-aware history retention defaults and config overrides (`history_retention.retain_last`, `retain_days`, `max_size_kib`), and wired `rqmd --history-gc` to trim persisted history state before pack/prune maintenance while reporting the active policy in `--history` and `--history-gc` outputs (RQMD-UNDO-008).
- Added `rqmd --history-gc` with optional `--history-prune-now`, plus explicit confirmation and JSON/text reporting for safe maintenance of the hidden `rqmd-history` repository (progress toward RQMD-UNDO-007).
- Added interactive `g` and `G` history-browser actions for confirmed history gc and immediate-prune maintenance from the entry detail view (progress toward RQMD-UNDO-007).
- Added interactive `l` and `x` history-browser actions for saving named branch labels and discarding alternate branches, including an explicit chance to save a snapshot label before destructive branch removal (progress toward RQMD-UNDO-007).
- Added `rqmd --history-label-branch <name> --history-branch-label <label>` so automation can name alternate history branches without using the interactive browser (progress toward RQMD-UNDO-007).
- Added `rqmd --history-discard-save-label <label>` so non-interactive branch discard flows can preserve a named snapshot label in the same command before branch navigation is removed (progress toward RQMD-UNDO-007).
- Added `rqmd --history-gc-save-label <label>` plus matching interactive gc/prune save-label prompts so maintenance flows can preserve a named snapshot label before destructive history cleanup runs (progress toward RQMD-UNDO-007).
- Added proposed Vim-alignment requirements covering `j`/`k` vertical navigation defaults, richer Vim-style motions (`gg`, `G`, `Ctrl-U`, `Ctrl-D`), and `/`/`?` search with `n`/`N` repeat semantics in interactive mode.
- Added compact interactive footers with `:=help`, plus a shared help overlay that opens on `:` and toggles on invalid keys so full keymaps stay discoverable without long inline legends (RQMD-INTERACTIVE-026).
- Updated interactive requirement walks so status and priority edits keep the current requirement visible until the user explicitly presses next, and status-panel shifted-number priority shortcuts now update in place from the default status view instead of auto-advancing away (RQMD-INTERACTIVE-007).
- Updated the interactive status action menu to render those priority shortcuts as a visible aligned right-hand column, with the current priority marked in-place while status stays selected (RQMD-INTERACTIVE-007).
- Added a `v=code` action in interactive requirement detail menus that opens the current requirement in VS Code at its heading line when the `code` launcher is available, while keeping the interactive session active and reporting a graceful fallback otherwise (RQMD-INTERACTIVE-030).
- Added an `o=refs` action in interactive requirement detail menus that resolves local requirement references from the current entry and opens the selected linked requirement in a nested lookup flow, so users can jump to related requirements and return with `u` (RQMD-INTERACTIVE-031).
- Updated README-sync empty-state messaging to use requirement-document terminology consistently, avoiding a stale "requirement domains" message after the terminology-neutral indexing work (RQMD-PORTABILITY-019).
- Refined the interactive status menu's priority preview so the right-hand column is fixed-width and left-aligned within its own block, and so the active status highlight no longer overwrites the current-priority highlight (RQMD-INTERACTIVE-007).
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

- Removed a stray duplicated import line in `workflows.py` that could break CLI startup and pytest collection with an `IndentationError`.
- Updated the documented canonical status workflow across the main README, requirements index, and generated init-doc templates to match the current five-status model: Proposed, Implemented, Verified, Blocked, Deprecated.
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
- Updated interactive menu navigation to add shared Vim-style list motions: `gg` jumps to the first list position, `G` jumps to the last, and `Ctrl-U`/`Ctrl-D` move by deterministic half-page steps while preserving refresh offset state.
- Updated requirement status to mark `RQMD-INTERACTIVE-024` as Implemented (Vim-style list motions and paging).
- Updated interactive menus to add shared Vim-style list search motions: `/` and `?` search the current list, while `n` and `N` repeat the last search in the same or opposite direction without disturbing sort/filter context.
- Updated requirement status to mark `RQMD-INTERACTIVE-025` as Implemented (Vim-style search and repeat navigation).
- Updated requirement status to mark `RQMD-INTERACTIVE-026` as Implemented (compact footer with full help menu).
- Updated requirement status to mark `RQMD-UNDO-007` as Implemented (history UI affordances and history-control command surface).
- Updated requirement status to mark `RQMD-UNDO-008` as Implemented (size, retention, and compaction policy for persisted history).
- Clarified the requirement action footer so `j/k/g/G` are labeled as outer requirement traversal (`next-ac`, `prev-ac`, `first-ac`, `last-ac`) rather than implying that the status action prompt participates in the shared searchable list contract.
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