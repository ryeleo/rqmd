# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed

- Added a dedicated `docs/requirements/bug-tracking.md` requirements domain and moved `RQMD-BUG-001` and `RQMD-BUG-002` into it so bug-tracking behavior is a first-class domain.
- Repurposed `docs/requirements/bugs.md` as the runtime bug backlog file for filed bug instances (separate from behavior requirements).

<a id="v0-2-4"></a>
## [0.2.4] - 2026-04-09

### Changed

- Repository cleanup after extension rollout: removed bundled `.github/agents`, `.github/prompts`, rqmd-managed skills, `copilot-instructions.md`, and `rqmd-bundle.json` from `.github/`, preserving only project-local `.github/skills/dev` and `.github/skills/test`.
- Removed entire `src/rqmd/resources/bundle/` from the Python package — the packaged bundle source (agents, prompts, skills, templates, preset manifests) is no longer shipped with the CLI, since the VS Code extension now owns that surface.
- `/next` prompt reworked to prefer planning and `/go` handoff over immediate implementation; now reminds users to commit before switching slices when the worktree is dirty.
- Agent-level worktree-health rule added to both `rqmd.agent.md` variants: check `git status` and recommend committing (or stashing) before handing off to the next slice.
- `RQMD-PACKAGING-015` marked ✅ Verified — `rqmd-ai` entrypoint fully removed.

### Added

- `scripts/rqmd-bundle-cleanup.sh` — portable cleanup script for removing rqmd-ai–installed bundle files from any project's `.github/`. Keeps `skills/dev/` and `skills/test/`; removes `agents/`, `prompts/`, rqmd-managed skills, `rqmd-bundle.json`, and `copilot-instructions.md` only when it was installed by rqmd (identified by rqmd header).

### Removed

- Removed `rqmd-ai` and `reqmd-ai` console-script entrypoints from `pyproject.toml`; `rqmd --json` remains the canonical machine-readable workflow surface.

<a id="v0-2-3"></a>
## [0.2.3] - 2026-04-09

### Added

- CLI `bug` command (`rqmd bug "title"`) to quickly generate a bug requirement boilerplate, append it to `docs/requirements/bugs.md`, and open VS Code at the new requirement (`RQMD-AI-061`).
- Improved `/bug` prompt for agents that leverages the `rqmd bug` CLI for reliable ID allocation and file creation, followed by drafting the bug body from chat context (`RQMD-AI-060`).
- New requirement proposals: domain-aware `rqmd bug <domain> "title"` with positional domain argument and tab completion (`RQMD-AI-063`); interactive `b` key for inline bug filing from the interactive session (`RQMD-INTERACTIVE-034`).

### Changed

- Primary agent renamed from `rqmd-dev` to `rqmd` across bundled agent file, all bundled prompts, both `agents/README.md` files, and telemetry skill examples (`RQMD-AI-056`). The old name implied a secondary tool; `rqmd` is the obvious default.
- Anti-hallucination rule added to all `rqmd.agent.md` variants: agents must never invent or calculate requirement IDs — always read `next_id` from `rqmd --json` output.

<a id="v0-2-2"></a>
## [0.2.2] - 2026-04-09

### Changed

- Release-tag preparation now uses `scripts/ensure_release_tag.py` (with `scripts/validate_release_tag.py` retained as a compatibility wrapper). The ensure script updates `pyproject.toml` `project.version` to match the release tag before build/publish.
- Stable release runs still enforce that `CHANGELOG.md` already contains a matching `## [x.y.z]` section before publish.

<a id="v0-2-1"></a>
## [0.2.1] - 2026-04-09

### Added

- First-class bug tracking — rqmd now parses `- **Type:** bug` and `- **Affects:** PROJ-XXX` metadata fields from requirement headers (`RQMD-CORE-041`, `RQMD-CORE-042`). Requirements default to `type: feature` when omitted, preserving backward compatibility.
- `--dump-type` CLI filter for `rqmd-ai` exports (`RQMD-AUTOMATION-039`). Composable with `--dump-status` for multi-axis filtering (e.g., `--dump-type bug --dump-status proposed`). Batch mode also supports the new `dump-type` query type.
- Packaged bug-report template (`RQMD-CORE-043`) with Steps to Reproduce / Expected / Actual / Root Cause sections. The `/brainstorm` and `/refine` prompts now detect defect descriptions and offer this template instead of the user-story + Given/When/Then shape.
- `/bug` prompt (`RQMD-AI-060`): type `/bug` in chat to instantly file a tracked bug requirement from conversation context. The agent drafts the requirement using the bug template, writes it directly to the appropriate domain file, and reports the new ID — zero-friction bug filing for frustrated developers.
- `rqmd-ai` query flags folded into the `rqmd` CLI (`RQMD-PACKAGING-014`): `--dump-status`, `--dump-type`, `--dump-id`, `--dump-file`, `--include-domain-markdown`, `--max-domain-markdown-chars`, `--write`, and `--batch` are now available on `rqmd` directly. Agents can call `rqmd --dump-status proposed` instead of `rqmd-ai --json --dump-status proposed`.
- `rqmd-vscode` extension scaffolded (`RQMD-PACKAGING-013`): the rqmd AI bundle (12 prompts, 16 skills, 2 agents) is now distributed as a VS Code extension via declarative `chatPromptFiles`, `chatSkills`, and `chatAgents` contribution points. No files are written to `.github/`; upgrading the bundle is a VS Code extension update.
- **"rqmd: Initialize Project"** command palette action added to the `rqmd-vscode` extension (`RQMD-PACKAGING-016`). Opens an integrated terminal running `rqmd init` and prompts the user to paste the output into Copilot Chat to complete guided project setup. Only project-specific files are written to `.github/`; shared rqmd defaults remain in the extension.


### Fixed

- Duplicate requirement IDs (`RQMD-CORE-041`–`043`, `RQMD-AUTOMATION-039`) caused by agents manually calculating the next ID instead of reading `next_id` from `rqmd-ai --json` output. Renumbered the duplicates to `RQMD-CORE-044`–`046` and `RQMD-AUTOMATION-040`.
- `next_id` guidance added to `copilot-instructions.md`, `/rqmd-brainstorm`, and `/rqmd-implement` skills so agents always allocate IDs from the JSON output rather than grepping markdown files.

### Deprecated

- `rqmd-ai` entrypoint now emits a `DeprecationWarning` on every invocation: *"rqmd-ai is deprecated. Use `rqmd --json` instead."* (`RQMD-PACKAGING-015`). The entrypoint still executes normally; the warning is informational only.

<a id="v0-2-0"></a>
## [0.2.0] - 2026-04-08

### Added

#### Telemetry

- Agent-facing telemetry infrastructure so AI agents can self-report workflow friction, improvement suggestions, and errors back to rqmd developers — implemented as a new `RQMD-TELEMETRY` requirement domain with a Postgres + MinIO local dev stack, a FastAPI gateway, a Python telemetry client, and an `/rqmd-telemetry` bundle skill that teaches agents when and how to submit events.
- Short-lived session tokens via gateway token exchange (`RQMD-TELEMETRY-012`). The client sends a public client ID to `POST /api/v1/token` and receives a short-lived Bearer token (1-hour TTL) cached in-process with transparent refresh. No plaintext API key is shipped in source.
- Gateway rate limiting (`RQMD-TELEMETRY-013`). In-memory sliding-window limiters protect event ingestion (60 req/min per-IP, 600 req/min global) and token exchange (10 req/min per-IP). Exceeded limits return `429 Too Many Requests` with a `Retry-After` header.
- Built-in production telemetry defaults — agents report friction out of the box without manual endpoint configuration. `RQMD_TELEMETRY_DISABLED=1` opts out entirely.
- `rqmd-ai telemetry` command for checking endpoint configuration and health.
- `rqmd-ai telemetry-test` command for verifying the telemetry pipeline end-to-end from any project.
- Command-discovery struggle reporting so agents explicitly report when `rqmd` or `rqmd-ai` cannot be invoked — tracked as a distinct high-severity telemetry event with the exact commands attempted and the fallback action taken.
- Azure single-VM telemetry deployment blueprint with Terraform provisioning, a GitHub Actions workflow, a production compose stack, systemd wiring, and backup/restore scripts.
- `feedback` event type added to `EventType` in `src/rqmd/telemetry.py` (`RQMD-TELEMETRY-015`).

#### Performance

- Lazy import strategy for the rqmd package init so `rqmd-ai` and other non-interactive entry points skip eagerly importing the full interactive CLI module chain (`RQMD-CORE-037`). Measured: ~155ms → ~81ms (warm).
- In-process mtime+size-keyed parse cache so repeat `parse_requirements` and `read_text` calls skip re-parsing unchanged requirement files (`RQMD-CORE-038`). Measured 1.6× speedup on parse+body-extract paths.
- Non-interactive latency budget tests gating warm parse and single-ID lookup performance (`RQMD-CORE-039`).
- Multi-query `--batch` mode for `rqmd-ai` that reads a JSON array of query objects from stdin and executes them against one loaded catalog (`RQMD-AUTOMATION-038`). Measured 26% faster for 2 queries vs separate invocations, scaling linearly.

#### Bundle and AI workflow

- Prompt-aware bundle support and a bundled prompt suite including `/go`, `/commit-and-go`, `/next`, `/brainstorm`, `/polish-docs`, `/pin`, and `/ship-check`.
- Workspace bundle provenance metadata at `.github/rqmd-bundle.json`.
- Generated `agent-workflow.sh` scaffold during bundle install for machine-readable `preflight` and `validate` workflows.
- Visible project tooling metadata block for requirements indexes plus `rqmd --sync-index-metadata`.
- Explicit `rqmd-ai reinstall` and `rqmd-ai upgrade` commands for managed bundle lifecycle refreshes, with conservative upgrade protection for customized files.
- Bundle-wide guidance for reliable `rqmd-ai --json` automation, with Windows shell reliability called out explicitly.
- Init-chat status-scheme selection (`canonical`, `lean`, `delivery`) or copy-from-existing during bootstrap.
- Multi-agent workflow guidance across all rqmd AI surfaces — `copilot-instructions.md`, `/brainstorm`, `/refine` prompts, and the `rqmd-dev` agent now recommend brainstorming/refining with a high-power agent, then handing off to a cheaper agent for implementation via a copy-paste-ready `/go` prompt in the `Direction` closeout section.
- `/feedback` prompt (`RQMD-AI-053`): interactive user-driven improvement feedback session with iterative telemetry submission. Installed in `.github/prompts/` and the rqmd bundle.
- `/rqmd-feedback` skill (`RQMD-AI-054`): teaches agents the full feedback workflow — payload schema, valid categories, submission mechanics, and session lifecycle.
- GitHub issue creation from feedback sessions (`RQMD-AI-055`): the `/feedback` prompt now offers to file a `gh issue create --repo ryeleo/rqmd` when feedback is concrete enough, capturing the issue URL in telemetry.

### Changed

- Reworked the README entrypoint with a clearer install section and a short getting-started flow.
- Reframed the bundled AI workflow surface toward a single-agent-first model where `rqmd-dev` stays primary and `/go` handles the most common "just continue" action.
- Made `rqmd-ai install` default to the minimal preset so normal installs no longer add specialized agent variants.
- Simplified the core rqmd surface by removing history/time-machine and undo/redo CLI workflows from the 0.x track, deprecating the Time Machine and Undo requirement domains.
- Hardened interactive `screen_write` rendering on small terminals to prevent redraw overflow on wrapped lines (notably in Windows VS Code terminals).
- Updated `screen_write` redraws to clear terminal scrollback as well as the visible frame before each render.
- Updated PyPI publishing so stable versions ship from GitHub Releases while `rc` tags publish automatically on push.
- Requirement ID allocation is now per-domain: IDs use compound prefixes like `RQMD-CORE-041`, `RQMD-TELEMETRY-015` instead of a single global counter. `--id-namespace` accepts compound prefixes (e.g., `rqmd --next-id --id-namespace RQMD-CORE`), and `rqmd-ai --json` export includes a `next_id` field per domain file so agents can read the next available ID directly. Legacy init uses domain-scoped compound prefixes (`<PREFIX>-<SLUG>`, `<PREFIX>-WORKFLOW`, `<PREFIX>-ISSUE`).
- Project config files are no longer hidden (dot-prefixed): `rqmd.yml`, `rqmd.yaml`, and `rqmd.json` replace the previous `.rqmd.yml`, `.rqmd.yaml`, and `.rqmd.json` names. Project root auto-discovery and scaffold generation use the new names.

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

- Added a chat-first onboarding flow built around `rqmd init` and `rqmd-ai init`, with grouped interview prompts, preview-first handoff guidance, legacy-repo seeding support, and generated `rqmd.yml` scaffolding so new or existing repositories can adopt rqmd with less manual setup.
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
