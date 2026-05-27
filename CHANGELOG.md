# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.4.0] - 2026-05-27

### Changed

- Project archived. This is the final release — no new features or bug fixes are planned.
- Updated `Development Status` PyPI classifier to `7 - Inactive`.
- Fixed project URLs in `pyproject.toml` (placeholder `github.com/example/rqmd` → `github.com/ryeleo/rqmd`).
- Updated README with archival notice.

## [0.3.1] - 2026-05-12

### Added

- [RQMD-TELEMETRY-018](docs/requirements/telemetry.md#L229): `scripts/telemetry-review.py` — internal standalone script (stdlib-only, not distributed) that fetches events from the gateway HTTP API using the cached session token and prints them as pretty-printed JSON.
Defaults to a 14-day window; pass an integer argument to override.
Pages automatically through results at the 500-event limit.
Exits non-zero with a human-readable error and fix hint on token/gateway failure.
Gateway URL overridable via `RQMD_TELEMETRY_URL` or `RQMD_TELEMETRY_ENDPOINT`.
- [RQMD-TELEMETRY-019](docs/requirements/telemetry.md#L260): `GET /api/v1/events` now accepts a `?since=<ISO-8601>` query parameter in the telemetry gateway; only events with `created_at >= since` are returned. Invalid values return HTTP 422.
- [RQMD-TELEMETRY-020](docs/requirements/telemetry.md#L273): `scripts/telemetry-tunnel.sh` now forwards `localhost:18080` to the gateway in addition to Postgres and MinIO ports; banner updated to list all four forwarded addresses.

### Changed

- `.github/prompts/telemetry-review.prompt.md`: query block replaced — psycopg2 Python snippet and credential env-var requirement removed; replaced with `python3 scripts/telemetry-review.py [DAYS]` one-liner.

## [0.3.0] - 2026-05-07

### Added

- [RQMD-TELEMETRY-017](docs/requirements/telemetry.md#L213): AI model identifier in telemetry events. `submit_event()` and `send_event()` now accept an optional `model_id: str | None` parameter. When provided, it is included as a top-level `model_id` field in the event payload so recurring friction patterns (e.g. hard-wrapping violations) can be correlated with specific models. Gateway: `model_id TEXT` column added to `telemetry_events` with a `CREATE INDEX` on the column; idempotent `ALTER TABLE ADD COLUMN IF NOT EXISTS` migration ensures existing databases are updated on next gateway restart. Gateway `EventCreate` model extended with `model_id` field; `feedback` added to the `event_type` Literal and DB CHECK constraint (fixing a silent schema gap from RQMD-TELEMETRY-015). `GET /api/v1/events` now returns `model_id` in each event record.
- `.github/skills/telemetry/SKILL.md` (rqmd-vscode): `model_id` added to the event field reference table with guidance on populating it from the agent's own system prompt or VS Code model context. Basic code example updated to show `model_id` usage.

- `.github/prompts/telemetry-review.prompt.md`: New `/telemetry-review` developer prompt — queries the telemetry Postgres DB (via tunnel), clusters events of ≥ 2 by category/root-cause, deduplicates against open requirements, and drafts accepted clusters as 💡 Proposed entries with a back-reference comment (RQMD-AI-FEEDBACK-006 [spec](../rqmd-vscode/docs/requirements/feedback.md#L86))
- [RQMD-TELEMETRY-016](docs/requirements/telemetry.md#L195): Client-side secrets and PII scrubbing before telemetry submission. All `send_event` / `submit_event` calls now pass freeform string fields through a three-layer pipeline — home-path normalisation pre-pass → `detect-secrets` (secret patterns) → `gitleaks stdin` (optional subprocess, best-effort) → `scrubadub` (PII redaction) — before the payload is serialised or transmitted. Any layer that raises is skipped with a WARNING; a total pipeline failure drops the event and logs ERROR rather than transmitting raw data. New module: `src/rqmd/scrubbing.py`. New dependencies: `detect-secrets>=1.4.0`, `scrubadub>=2.0.0`. Tests: `tests/test_telemetry_scrubbing.py`.

<a id="v0-2-11"></a>

## [0.2.11] - 2026-04-28

### Added

- [RQMD-CORE-057](docs/requirements/core-engine.md): `rqmd --refresh-index` — re-applies static boilerplate sections (install breadcrumb, How To Use, Schema Reference) from the current `init` template into an existing `docs/requirements/README.md`. Custom intro text, tooling metadata, extra sections, and the Requirement Documents listing are preserved. Supports `--dry-run`. Backed by new `refresh_requirements_index()` in `markdown_io.py` with sentinel-heading-based section detection. Covered by `tests/test_core_engine.py::test_RQMD_core_057_refresh_index_*`.

### Changed

- `.github/skills/dev/SKILL.md`: now leads with VS Code-native preference (per RQMD-EXT-090) — surfaces discovered `.vscode/tasks.json` labels (`Tunnel to Az TeleVM`, `Start Remote Admin Tools`, `SSH to Az TeleVM`) so the agent prefers `run_task` over raw shell when a label matches.
- `.github/skills/test/SKILL.md`: now leads with VS Code-native preference (per RQMD-EXT-090) — instructs the agent to prefer the `runTests` tool (Test Explorer) over `pytest -q` for focused runs, and reserves the canonical agent-workflow validate path for full-suite checks.
- `tests/test_release.py`, `tests/test_staleness.py`: import statements reformatted (no behavior change).

<a id="v0-2-10"></a>

## [0.2.10] - 2026-04-19

### Fixed

- [RQMD-BUG-005](docs/requirements/bugs.md#rqmd-bug-005): `rqmd init` (no flags) now runs the scaffold flow directly — no longer errors with "AI-guided init is no longer part of the CLI". Bare `rqmd init` is now identical to `rqmd init --scaffold`. Updated startup guidance messages to remove stale AI-driven onboarding references.
- [RQMD-BUG-006](docs/requirements/bugs.md#rqmd-bug-006): VS Code extension auto-install failure now captures subprocess stdout/stderr and logs it to the "rqmd bootstrap" output channel. The error notification includes a "Show Logs" button and references the channel for details, replacing the previous generic unactionable message.

### Removed

- Deleted `history.py` (975 lines) and all undo/redo/history integration points across `cli.py`, `workflows.py`, `status_update.py`, and 11 related tests. The RQMD-UNDO-* and RQMD-TIME-* features were already archived; this cleans up the dead code.
- Deprecated all RQMD-AI-001..011 requirements — the `rqmd-ai` entrypoint was never built; AI-facing capabilities are delivered via the rqmd VS Code extension's skill-based workflow. Archived `ai-cli.md` to `docs/requirements/archived/`. Relocated RQMD-AI-061/063 (`rqmd bug` features) to `bug-tracking.md`.

<a id="v0-2-9"></a>

## [0.2.9] - 2026-04-17

### Fixed

- [RQMD-BUG-004](docs/requirements/bugs.md#rqmd-bug-004): `--sync-index-metadata` is now idempotent — repeated runs no longer risk growing blank lines around the metadata section. Regex simplified to replace section content in-place without consuming surrounding whitespace.

### Added

- [RQMD-CORE-045](docs/requirements/core-engine.md#rqmd-core-045): `rqmd --staleness` — per-requirement staleness scoring based on git blame, grep cross-references, and configurable weighted signals. Includes `--staleness --json`, `--staleness --deprecated-only` (CI-friendly, exits non-zero), and `--staleness --explain`.
- [RQMD-CORE-052](docs/requirements/core-engine.md#rqmd-core-052): `rqmd --release-preflight` — machine-readable release readiness check. Validates CHANGELOG stamp, version-source agreement (auto-discovers `pyproject.toml`, `package.json`, etc.), and clean git working tree. Structured JSON output with `--json`; exit 0 on pass, 1 on fail.
- [RQMD-CORE-051](docs/requirements/core-engine.md#rqmd-core-051): Refreshed `docs/requirements/README.md` from the current `rqmd init` template — adds structured How To Use subsections, Schema Reference, install breadcrumb, and JSON contract docs.
- [RQMD-CORE-050](docs/requirements/core-engine.md#rqmd-core-050): `rqmd init` template now includes an install breadcrumb: `> **ℹ️ Info:** This index is managed by rqmd…`
- Filed [RQMD-BUG-003](docs/requirements/bugs.md#rqmd-bug-003): `--project-root .` resolves relative to `uv --directory` target instead of shell cwd, causing silent wrong-project processing in multi-root workspaces.

### Changed

- `.github/skills/release/SKILL.md`: rewrote preflight as explicit ordered steps; CHANGELOG stamping is now Step 1 with a hard-fail warning — tag must always land on the commit that contains the stamped changelog entry.

<a id="v0-2-8"></a>

## [0.2.8] - 2026-04-16

### Changed

- `README.md`: removed all AI/agent/Copilot/bundle references. README now describes rqmd strictly as a CLI tool; AI workflow integration is the domain of the rqmd VS Code extension.
- `pyproject.toml`: updated package description to match the CLI-only positioning.
- Archived fully-deprecated requirement domains: `undo.md` (11 RQMD-UNDO-*) and `time-machine.md` (10 RQMD-TIME-*) to `docs/requirements/archived/`. Updated README index and CHANGELOG cross-references.
- Pinned full history/undo removal scope (`docs/pins/history-removal-scope.md`) and seeded `docs/inbox.md` with `[tech-debt]` item for `/tech-debt-sweep` to consume.
- `.github/skills/release/SKILL.md`: added preflight step to bump prompt description versions via `rqmd-vscode/scripts/bump-prompt-versions.sh`.

<a id="v0-2-7"></a>

## [0.2.7] - 2026-04-15

### Added

- `docs/requirements/core-engine.md`: 💡 Proposed RQMD-CORE-045 (`rqmd --staleness`), RQMD-CORE-046 (exclude `archived/`), RQMD-CORE-047 (configurable decay curves).

<a id="v0-2-6"></a>

## [0.2.6] - 2026-04-14

### Added

- `.github/skills/release/SKILL.md`: per-repo `/release` skill with preflight checklist, paired-release contract, and pre-1.0.0 autonomous release policy. Registered in `agent-workflow.sh`.

### Removed

- `src/rqmd/ai_cli.py` (5 200+ lines): AI-guided init chat/interview flow, JSON context export (`--dump-status`, `--dump-id`, `--dump-type`, `--dump-file`), batch stdin query mode (`--batch`), AI plan/apply update mode (`--write --update`), and bundle install/management. All VS Code agent/skill/prompt bundle content has moved to the `rqmd-vscode` extension repo.
- CLI flags removed: `--batch`, `--dump-status`, `--dump-type`, `--dump-id`, `--dump-file`, `--include-requirement-body`/`--no-requirement-body`, `--include-domain-markdown`, `--max-domain-markdown-chars`, `--write`.
- `src/rqmd/resources/bundle/` directory and all shipped agent/skill/prompt/template files. Bundle content is now distributed exclusively via the `rqmd-vscode` VS Code extension.
- `pyproject.toml` `package-data` entries for `resources/bundle/**`.

<a id="v0-2-4"></a>

## [0.2.4] - 2026-04-10

### Added

- `- **Summary:**` field: requirements now carry an optional one-line summary parsed by the requirement engine and included in JSON exports. Pattern: `- **Summary:** <description>`.
- `SUMMARY_PATTERN` added to `constants.py`; `summary` and `summary_line` keys added to all parsed requirement dicts.
- `JSON_SCHEMA_VERSION` bumped to `1.1.0` — new `summary`/`summary_line` fields added to the requirement object schema (backward-compatible; existing requirements without a summary field parse with `summary: null`).
- `scripts/rqmd-bundle-cleanup.sh` — portable cleanup script for removing rqmd-ai–installed bundle files from any project's `.github/`. Keeps `skills/dev/` and `skills/test/`; removes `agents/`, `prompts/`, rqmd-managed skills, `rqmd-bundle.json`, and `copilot-instructions.md` only when it was installed by rqmd (identified by rqmd header).

### Changed

- All 16 requirement files (14 in rqmd-cli, 2 in rqmd-vscode) migrated from verbose `- As a... / - I want... / - So that...` user-story format to a single `- **Summary:** <description>` bullet. Given/When/Then acceptance criteria are preserved unchanged.
- `docs/schema.md` updated: `summary` and `summary_line` added to the Optional Metadata Fields table; full requirement example updated; schema version reference bumped to `1.1.0`.
- Repository cleanup after extension rollout: removed bundled `.github/agents`, `.github/prompts`, rqmd-managed skills, `copilot-instructions.md`, and `rqmd-bundle.json` from `.github/`, preserving only project-local `.github/skills/dev` and `.github/skills/test`.
- Removed entire `src/rqmd/resources/bundle/` from the Python package — the packaged bundle source (agents, prompts, skills, templates, preset manifests) is no longer shipped with the CLI, since the VS Code extension now owns that surface.
- `/next` prompt reworked to prefer planning and `/go` handoff over immediate implementation; now reminds users to commit before switching slices when the worktree is dirty.
- Agent-level worktree-health rule added to both `rqmd.agent.md` variants: check `git status` and recommend committing (or stashing) before handing off to the next slice.
- `RQMD-PACKAGING-015` marked ✅ Verified — `rqmd-ai` entrypoint fully removed.

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
- Deepened verification and implementation coverage for history, undo, interactive navigation, portability, and README sync, including delivered history-surface work such as [RQMD-UNDO-007](docs/requirements/archived/undo.md#rqmd-undo-007) and [RQMD-UNDO-008](docs/requirements/archived/undo.md#rqmd-undo-008).
