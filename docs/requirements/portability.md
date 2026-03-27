# Portability Requirement

Scope: cross-project operation, path configuration, and repo-agnostic behavior.

<!-- acceptance-status-summary:start -->
Summary: 2💡 3🔧 10✅ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->

### RQMD-PORTABILITY-001: Configurable repo root
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when the target project is not the current directory
- I want to pass `--project-root`
- So that all file discovery and updates are scoped to that root
- So that relative paths are resolved against it.

### RQMD-PORTABILITY-002: Configurable requirements directory
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when requirements docs live outside default location
- I want to set `--docs-dir`
- So that markdown discovery uses that directory
- So that it supports absolute or repo-root-relative input.

### RQMD-PORTABILITY-003: Default conventions
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when no portability flags are provided
- I want to run rqmd
- So that repo root defaults to current directory
- So that requirements directory defaults to docs/requirements.

### RQMD-PORTABILITY-004: Stable relative source display
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when requirement panels and updates are printed
- I want output to reference file paths
- So that source paths are shown relative to repo root
- So that they remain readable across machines.

### RQMD-PORTABILITY-005: Non-project-specific assumptions
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when this package is copied into another codebase
- I want to run the command against a valid docs structure
- So that tool behavior does not depend on Speed Steel VR-specific files
- So that only AC markdown contract is required.

### RQMD-PORTABILITY-006: Optional future config file support
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when teams may want fewer CLI flags
- I want an optional project config file
- So that defaults for repo root and requirements path can be declared centrally
- So that command-line flags still override config values.

### RQMD-PORTABILITY-007: Status customization config location and precedence
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when teams want customizable status catalog metadata and colors
- I want to enable status customization
- So that the tool supports loading config from a project file at `.rqmd/statuses.json` or `.rqmd/statuses.yml` by default
- So that the tool supports explicit override via `--status-config <path>`
- So that effective precedence is: CLI override file > project default file > user-level config > built-in defaults
- So that both JSON and YAML are supported: detection is by file extension (`.json`, `.yml`, `.yaml`) with content-based sniffing as a fallback; parsed content is validated against a single canonical schema to ensure consistent behavior across formats.

### RQMD-PORTABILITY-008: Automatic requirements-dir search from current path
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when users run rqmd without an explicit `--docs-dir`
- I want rqmd to scan from the current working path
- So that rqmd searches for viable requirements index locations including `docs/requirements/README.md` and `requirements/README.md`
- So that the `docs/` prefix is optional rather than required
- So that rqmd selects the best matching candidate deterministically
- So that rqmd reports which path was selected.

### RQMD-PORTABILITY-009: Graceful startup errors for docs availability and permissions
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when rqmd cannot open requirements docs because files are missing or inaccessible
- I want startup validation to fail fast
- So that rqmd exits with a clear, actionable error message
- So that the message distinguishes not-found conditions from permission-denied conditions
- So that no partial interactive session is started.

### RQMD-PORTABILITY-010: One-time emoji strip and restore commands
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when a team prefers plain-text status labels for platform compatibility or readability
- I want to run `--strip-status-icons` once against the docs
- So that all emoji prefixes are removed from every status line across all requirements files
- So that subsequent runs infer emoji-free mode from the absence of emojis in existing statuses and do not reintroduce them
- So that summary blocks are regenerated without emoji characters.
- As a rqmd user when a team wants to restore emoji-prefixed statuses
- I want to run `--restore-status-icons` once against the docs
- So that the canonical emoji is prepended to every status line across all requirements files
- So that subsequent runs resume normal emoji-inclusive behavior.
- So that both operations are idempotent and produce no diff if already in the target mode.

### RQMD-PORTABILITY-011: Custom status schema in config file
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when teams need project-specific status taxonomies and display semantics
- I want rqmd to load status configuration from file
- So that each custom status definition can specify `name`, `shortcode`, `emoji`, `color`, and `rollup_color`
- So that parsing, normalization, interactive rendering, and roll-up display use the configured status metadata consistently
- So that validation errors clearly identify missing or invalid status fields with actionable file/line context.

### RQMD-PORTABILITY-012: User-level config file for accessibility color overrides
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As a rqmd user when users need terminal-friendly or accessibility-tuned colors across multiple projects
- I want rqmd to load configuration
- So that rqmd supports a user-level config file at `~/.rqmd.config`
- So that the user-level file can override color-related settings including zebra striping colors
- So that precedence is: CLI options > project config > user config > built-in defaults
- So that effective color settings are applied consistently in interactive and roll-up displays.

### RQMD-PORTABILITY-014: Configurable state directory for persisted workflow state
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when teams may have different conventions for temporary/runtime files
- I want to run filtered interactive workflows with resume enabled
- So that rqmd supports `--session-state-dir` with explicit modes `system-temp` and `project-local`
- So that `--session-state-dir` also accepts a custom absolute or repo-root-relative path
- So that resume state persists under the selected directory without assuming any single repo layout.

### RQMD-PORTABILITY-013: Project-configurable roll-up color knobs
- **Status:** 🗑️ Deprecated
- **Priority:** 🟢 P3 - Low
- **Deprecated:** Superseded by RQMD-ROLLUP-007, which generalizes roll-up customization through declarative roll-up mappings/expressions and can represent color behavior within that model.
- As a rqmd user when projects may want consistent roll-up coloring across team tools and dashboards
- I want to provide a project-level status config file (e.g. `.rqmd/statuses.json`)
- So that the project config can include explicit roll-up color knobs such as `rollup_mode` (values: `per_status`|`bucketed`|`monochrome`), `bucket_map` to map statuses to roll-up buckets, and optional per-bucket `color` overrides
- So that CLI flags can still override these knobs for ephemeral runs
- So that roll-up rendering honors project-level knobs when present while falling back to user config and built-in defaults otherwise.

### RQMD-PORTABILITY-015: Upward project-root discovery
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when I run commands from nested subdirectories
- I want rqmd to discover project root by searching CWD and parent paths up to filesystem root
- So that root resolution follows git-like behavior and finds the nearest valid project context.
- So that discovery checks for any of `.rqmd.yml/.rqmd.yaml/.rqmd.json`, `requirements/`, or `docs/requirements/`.

### RQMD-PORTABILITY-016: Automated performance testing for large requirement datasets
- **Status:** 💡 Proposed
- **Priority:** 🔴 P0 - Critical
- As a rqmd team member ensuring tool responsiveness
- I want automated performance tests against large fuzzy requirement datasets
- So that latency guardrails defined in RQMD-UI-009 are enforced for interactive startup and render-sensitive paths as requirements evolve
- So that discovery, parsing, filtering, and interactive navigation performance are measured and tracked deterministically without introducing a second conflicting latency threshold definition
- So that test suite includes datasets of varying size (e.g., 100, 1000, 10000+ requirements) and complexity
- So that performance regressions trigger clear failures in CI before merging changes
- So that documented performance SLAs and benchmarks are available to users and operators.
