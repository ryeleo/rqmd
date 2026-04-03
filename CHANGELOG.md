# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added prompt-aware bundle support and a bundled prompt suite including `/go`, `/commit-and-go`, `/next`, `/brainstorm`, `/docs-pass`, `/pin`, and `/ship-check` so the installed rqmd AI experience can stay centered on one primary implementation agent with simpler slash-command entrypoints.
- Added workspace bundle provenance metadata at `.github/rqmd-bundle.json` so installed repositories can report which rqmd version and JSON schema version last generated their local bundle files.
- Added a visible project tooling metadata block for generated requirements indexes plus `rqmd --sync-index-metadata`, so interactive-only rqmd users can see and refresh the repository's recorded rqmd and JSON schema versions.
- Added explicit `rqmd-ai reinstall` and `rqmd-ai upgrade` commands for managed bundle lifecycle refreshes, including conservative upgrade protection for customized files.
- Added bundle-wide guidance for reliable `rqmd-ai --json` automation (foreground execution, stdout-only JSON parsing, separate stderr diagnostics), with Windows shell reliability called out explicitly.
- Added init-chat status-scheme selection so users can choose built-in default status sets (`canonical`, `lean`, `delivery`) or copy statuses from an existing project config path during bootstrap.

### Changed

- Reworked the README entrypoint with a clearer top-level install section and a short getting-started flow so first-time users can reach `rqmd init` or `rqmd --verify-summaries` faster.
- Reframed the bundled AI workflow surface toward a single-agent-first model where `rqmd-dev` stays primary, `/go` handles the most common “just continue” action, and specialized agents remain available as advanced modes.
- Documented a clearer bundle refresh workflow built around `rqmd --version`, `rqmd-ai --version`, `rqmd-ai --json`, `rqmd-ai upgrade`, and `rqmd-ai reinstall`.
- rqmd text-mode startup now warns when the requirements index metadata block is missing or records a different rqmd/schema version than the currently running tool.
- Made `rqmd-ai install` default to the single-agent-first minimal preset and slimmed the full preset so normal installs no longer add specialized agent variants by default.

## [0.1.0] - 2026-04-02

### Added

- Initial stable `rqmd` release with interactive and automation-friendly requirements workflows, chat-first onboarding, and a packaged AI bundle ready for real project use.
- Added an installable Copilot bundle with reusable workflow skills, specialized full-preset agents, and project-local `/dev` and `/test` scaffolding so AI-assisted work can stay close to each repository's actual commands and review loop.
- Added durable history, recovery, and planning workflows across `rqmd` and `rqmd-ai`, including branch-aware history inspection, detached reads, replay planning, and exportable reports.
- Added a practical pinning workflow for durable project context, including the `/rqmd-pin` skill, a default `docs/pins/` layout, and a starter example note in this repository.

### Changed

- Hardened release and packaging workflows with version/tag validation, trusted publishing guidance, and packaged-resource defaults so the shipped CLI and bundle are easier to maintain and release consistently.
- Reworked the documentation and AI guidance surface so README onboarding, changelog maintenance, docs quality, docs sync, shared rqmd workflow conventions, and more predictable AI output styling are clearer and more intentional.
- Standardized the bundled AI and docs guidance around one canonical Info/Note/Warning markdown pattern so authored outputs stay more predictable across agents, skills, and repository docs.
- Expanded the interactive and automation baseline with stronger navigation, JSON support, completion, history verification, and portability safeguards so `0.1.0` ships as a steadier foundation.

#### AI Development

- Added authored workflow skills for documentation quality, changelog curation, and durable note pinning through [RQMD-AI-039](docs/requirements/ai-cli.md#rqmd-ai-039), [RQMD-AI-040](docs/requirements/ai-cli.md#rqmd-ai-040), and [RQMD-AI-042](docs/requirements/ai-cli.md#rqmd-ai-042), so the bundle feels more like a real product surface and less like generic agent boilerplate.
- Added `rqmd-dev-longrunning` and `rqmd-dev-easy`, and codified a shared cross-project rqmd agent contract through [RQMD-AI-036](docs/requirements/ai-cli.md#rqmd-ai-036), [RQMD-AI-037](docs/requirements/ai-cli.md#rqmd-ai-037), and [RQMD-AI-041](docs/requirements/ai-cli.md#rqmd-ai-041).

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
- Switched the requirements index contract to in-directory `README.md` files and aligned scaffold generation, auto-detection, and repository docs around that layout.

#### AI Development

- Promoted and tracked the next backlog slice for long-running and easy-first development agents, requirement-schema follow-up, duplicate-ID repair, `rqmd ranked`, grapheme-safe alignment, and local schema guidance through [RQMD-AI-036](docs/requirements/ai-cli.md#rqmd-ai-036), [RQMD-AI-037](docs/requirements/ai-cli.md#rqmd-ai-037), [RQMD-AI-038](docs/requirements/ai-cli.md#rqmd-ai-038), [RQMD-CORE-033](docs/requirements/core-engine.md#rqmd-core-033), [RQMD-CORE-034](docs/requirements/core-engine.md#rqmd-core-034), [RQMD-CORE-035](docs/requirements/core-engine.md#rqmd-core-035), [RQMD-SORTING-016](docs/requirements/sorting.md#rqmd-sorting-016), and [RQMD-INTERACTIVE-032](docs/requirements/interactive-ux.md#rqmd-interactive-032).
- Refined the shipped AI authoring guidance around requirement-first implementation, dual user-story plus Given/When/Then drafting, concise closeouts, and explicit interview contracts through [RQMD-AI-013](docs/requirements/ai-cli.md#rqmd-ai-013), [RQMD-AI-014](docs/requirements/ai-cli.md#rqmd-ai-014), [RQMD-AI-015](docs/requirements/ai-cli.md#rqmd-ai-015), [RQMD-AI-031](docs/requirements/ai-cli.md#rqmd-ai-031), [RQMD-AI-032](docs/requirements/ai-cli.md#rqmd-ai-032), [RQMD-AI-033](docs/requirements/ai-cli.md#rqmd-ai-033), [RQMD-AI-034](docs/requirements/ai-cli.md#rqmd-ai-034), and [RQMD-AI-035](docs/requirements/ai-cli.md#rqmd-ai-035).
- Consolidated bundle and init assets under packaged resources so more of the shipped onboarding and bundle experience is editable without code changes.
- Deepened verification and implementation coverage for history, undo, interactive navigation, portability, and README sync, including delivered history-surface work such as [RQMD-UNDO-007](docs/requirements/undo.md#rqmd-undo-007) and [RQMD-UNDO-008](docs/requirements/undo.md#rqmd-undo-008).
