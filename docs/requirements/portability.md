# Portability Requirement

Scope: cross-project operation, path configuration, and repo-agnostic behavior.

<!-- acceptance-status-summary:start -->
Summary: 5💡 7🔧 0✅ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->

### RQMD-PORTABILITY-001: Configurable repo root
- **Status:** 🔧 Implemented
- Given the target project is not the current directory
- When `--repo-root` is provided
- Then all file discovery and updates are scoped to that root
- And relative paths are resolved against it.

### RQMD-PORTABILITY-002: Configurable requirements directory
- **Status:** 🔧 Implemented
- Given requirements docs live outside default location
- When `--requirements-dir` is set
- Then markdown discovery uses that directory
- And supports absolute or repo-root-relative input.

### RQMD-PORTABILITY-003: Default conventions
- **Status:** 🔧 Implemented
- Given no portability flags are provided
- When command runs
- Then repo root defaults to current directory
- And requirements directory defaults to docs/requirements.

### RQMD-PORTABILITY-004: Stable relative source display
- **Status:** 🔧 Implemented
- Given requirement panels and updates are printed
- When output references file paths
- Then source paths are shown relative to repo root
- And remain readable across machines.

### RQMD-PORTABILITY-005: Non-project-specific assumptions
- **Status:** 🔧 Implemented
- Given this package is copied into another codebase
- When command is executed with valid docs structure
- Then tool behavior does not depend on Speed Steel VR-specific files
- And only AC markdown contract is required.

### RQMD-PORTABILITY-006: Optional future config file support
- **Status:** 💡 Proposed
- Given teams may want fewer CLI flags
- When a project config file is added in future
- Then defaults for repo root and requirements path can be declared centrally
- And command-line flags still override config values.

### RQMD-PORTABILITY-007: Status customization config location and precedence
- **Status:** 💡 Proposed
- Given teams want customizable status catalog metadata and colors
- When status customization is enabled
- Then the tool supports loading config from a project file at `.rqmd/status-catalog.json` or `.rqmd/status-catalog.yaml` by default
- And the tool supports explicit override via `--status-config <path>`
- And effective precedence is: CLI override file > project default file > user-level config > built-in defaults
- And both JSON and YAML are supported: detection is by file extension (`.json`, `.yml`, `.yaml`) with content-based sniffing as a fallback; parsed content is validated against a single canonical schema to ensure consistent behavior across formats.

### RQMD-PORTABILITY-008: Automatic requirements-dir search from current path
- **Status:** 🔧 Implemented
- Given users run rqmd without an explicit `--requirements-dir`
- When rqmd scans from the current working path
- Then rqmd searches for viable requirements index locations including `docs/requirements/README.md` and `requirements/README.md`
- And the `docs/` prefix is optional rather than required
- And rqmd selects the best matching candidate deterministically
- And rqmd reports which path was selected.

### RQMD-PORTABILITY-009: Graceful startup errors for docs availability and permissions
- **Status:** 🔧 Implemented
- Given rqmd cannot open requirements docs because files are missing or inaccessible
- When startup validation fails
- Then rqmd exits with a clear, actionable error message
- And the message distinguishes not-found conditions from permission-denied conditions
- And no partial interactive session is started.

### RQMD-PORTABILITY-010: One-time emoji strip and restore commands
- **Status:** 💡 Proposed
- Given a team prefers plain-text status labels for platform compatibility or readability
- When `--strip-status-emojis` is run once against the docs
- Then all emoji prefixes are removed from every status line across all requirements files
- And subsequent runs infer emoji-free mode from the absence of emojis in existing statuses and do not reintroduce them
- And summary blocks are regenerated without emoji characters.
- Given a team wants to restore emoji-prefixed statuses
- When `--restore-status-emojis` is run once against the docs
- Then the canonical emoji is prepended to every status line across all requirements files
- And subsequent runs resume normal emoji-inclusive behavior.
- And both operations are idempotent and produce no diff if already in the target mode.

### RQMD-PORTABILITY-011: Custom status schema in config file
- **Status:** 💡 Proposed
- Given teams need project-specific status taxonomies and display semantics
- When rqmd loads status configuration from file
- Then each custom status definition can specify `name`, `shortcode`, `emoji`, `color`, and `rollup_color`
- And parsing, normalization, interactive rendering, and roll-up display use the configured status metadata consistently
- And validation errors clearly identify missing or invalid status fields with actionable file/line context.

### RQMD-PORTABILITY-012: User-level config file for accessibility color overrides
- **Status:** 💡 Proposed
- Given users need terminal-friendly or accessibility-tuned colors across multiple projects
- When rqmd loads configuration
- Then rqmd supports a user-level config file at `~/.rqmd.config`
- And the user-level file can override color-related settings including zebra striping colors
- And precedence is: CLI options > project config > user config > built-in defaults
- And effective color settings are applied consistently in interactive and roll-up displays.

### RQMD-PORTABILITY-013: Project-configurable roll-up color knobs
- **Status:** 🗑️ Deprecated
- **Deprecated:** Superseded by RQMD-ROLLUP-007, which generalizes roll-up customization through declarative roll-up mappings/expressions and can represent color behavior within that model.
- Given projects may want consistent roll-up coloring across team tools and dashboards
- When a project-level status config file is present (e.g. `.rqmd/status-catalog.json`)
- Then the project config can include explicit roll-up color knobs such as `rollup_mode` (values: `per_status`|`bucketed`|`monochrome`), `bucket_map` to map statuses to roll-up buckets, and optional per-bucket `color` overrides
- And CLI flags can still override these knobs for ephemeral runs
- And roll-up rendering honors project-level knobs when present while falling back to user config and built-in defaults otherwise.
