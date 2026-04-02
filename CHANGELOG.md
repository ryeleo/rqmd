# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.1.0] - 2026-04-02

### Added

- Added a dedicated `/rqmd-changelog` bundle skill and tracked AI workflow requirement so changelog curation is treated as a first-class authored workflow instead of a generic docs-sync afterthought.
- Added a dedicated `/rqmd-docs` bundle skill and tracked AI workflow requirement so documentation quality work has an authored workflow for structure, readability, jargon handling, callouts, and page organization beyond simple drift correction.
- Added full-preset `rqmd-dev-longrunning` and `rqmd-dev-easy` agent variants so the shipped bundle can offer either long-running priority-first execution or conservative easy-wins execution without abandoning the shared rqmd workflow contract.
- Added a dedicated `/rqmd-pin` bundle skill so important project context, decisions, and quick-reference notes can be kept easy to find across sessions instead of disappearing into chat history.
- Added a concrete `docs/pins/` default shape with a lightweight index page and starter note template so the pin workflow has an obvious first place to land in this repository.
- Added a first example pinned note under `docs/pins/` to make the default pin workflow concrete in this repository.

### Changed

- Changed changelog guidance to prefer concise user-facing highlights first, with optional nested `AI Development` detail when supporting implementation context is worth keeping.
- Narrowed `/rqmd-doc-sync` toward synchronization work, and moved broader documentation-quality guidance into `/rqmd-docs` so docs craft and docs alignment are no longer conflated.
- Implemented `RQMD-AI-041`: a shared cross-project rqmd agent contract covering requirement-first sequencing, standard closeout headings, consistent lifecycle formatting, and Info/Note/Warning callout conventions.
- Implemented `RQMD-AI-036` and `RQMD-AI-037` by shipping long-running and easy-first development agent variants in the full bundle preset and documenting how they differ from the default `rqmd-dev` agent.
- Implemented `RQMD-AI-042` by shipping an authored `rqmd-pin` workflow that defaults durable notes toward maintainable pin locations and hands larger note-organization cleanup to `/rqmd-docs`.

## [0.1.0rc3] - 2026-04-02

### Changed

- Hardened release prep by moving release-tag validation into `scripts/validate_release_tag.py` and syntax-checking repository Python scripts during the local smoke path.
- Reduced prerelease churn by switching docs and tests to generic `rcN` examples or the live `project.version` instead of a hard-coded prerelease number.
- Reworked the README into a clearer landing page with stronger command-group headings, more rendered output examples, and a proposal for splitting longer-form docs into GitHub Pages.

#### AI Development

- Added a clearer preview-first AI CLI section in the README so bundle-driven workflows stay discoverable during release preparation.

## [0.1.0rc1] - 2026-04-01
### Added

- Added a chat-first onboarding flow built around `rqmd init` and `rqmd-ai init`, with grouped interview prompts, preview-first handoff guidance, legacy-repo seeding support, and generated `.rqmd.yml` scaffolding so new or existing repositories can adopt rqmd with less manual setup.
- Added an installable Copilot bundle with reusable workflow skills and specialized agents, plus project-local `/dev` and `/test` skill scaffolding so AI-assisted work can stay closer to the repository's actual commands and review loop.
- Added richer history and recovery tooling across `rqmd` and `rqmd-ai`, including persistent undo/redo, branch-aware history, detached historical views, replay and cherry-pick planning, timeline filtering, and exportable history reports.
- Added stronger interactive and automation support, including duplicate-ID validation and next-ID allocation, machine-readable JSON output, custom priority-catalog loading, shell-completion improvements, external-link editing, and broader interactive navigation/search/history affordances.
- Added optional native JSON speedups through `orjson`, plus prerelease command aliases `reqmd` and `reqmd-ai` while the project evaluates a possible future rename.

### Changed

- Made rqmd more portable and release-ready by treating `readline` as optional for Windows-style environments, documenting trusted publishing, supporting `rc` prerelease tags, and matching the GitHub release flow to `project.version`.
- Moved more shipped onboarding, catalog, and bundle guidance into packaged resources so defaults and templates are edited as normal files instead of scattered Python strings.
- Standardized the public workflow language around `init`, chat-first onboarding, preview-first AI guidance, and `--json` as the preferred machine-readable flag while preserving compatibility surfaces where needed.
- Expanded the default status and interaction model with `⚠️ Janky`, clearer first-run guidance, richer interactive menus, and better requirement-doc terminology across scaffolded and generated content.

#### AI Development

- Promoted and tracked the next backlog slice for long-running and easy-first development agents, markdown schema versioning, duplicate-ID repair, `rqmd ranked`, grapheme-safe menu alignment, and local schema guidance in generated requirement indexes (RQMD-AI-036, RQMD-AI-037, RQMD-CORE-033, RQMD-CORE-034, RQMD-SORTING-016, RQMD-INTERACTIVE-032, RQMD-AI-038, RQMD-CORE-035).
- Refined the shipped AI authoring guidance around user-story plus Given/When/Then drafting, concise markdown closeouts, requirement-first implement loops, and explicit interview contracts for chat-mode onboarding and bundle bootstrap (RQMD-AI-013, RQMD-AI-014, RQMD-AI-015, RQMD-AI-031, RQMD-AI-032, RQMD-AI-033, RQMD-AI-034, RQMD-AI-035).
- Consolidated bundle and init assets under packaged resources, including resource-backed skill definitions, init templates, message text, starter guidance, and bundle-install output, so more of the shipped AI experience is editable without code changes (RQMD-AI-016 through RQMD-AI-030).
- Deepened verification and implementation coverage for history, undo, time-machine, screen-write, interactive navigation, portability, JSON export, README sync, and other foundational capabilities that shipped alongside the rc1 milestone.

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