# Portability Acceptance Criteria

Scope: cross-project operation, path configuration, and repo-agnostic behavior.

<!-- acceptance-status-summary:start -->
Summary: 5💡 5🔧 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### REQMD-PORTABILITY-001: Configurable repo root
- **Status:** 🔧 Implemented
- Given the target project is not the current directory
- When `--repo-root` is provided
- Then all file discovery and updates are scoped to that root
- And relative paths are resolved against it.

### REQMD-PORTABILITY-002: Configurable criteria directory
- **Status:** 🔧 Implemented
- Given criteria docs live outside default location
- When `--criteria-dir` is set
- Then markdown discovery uses that directory
- And supports absolute or repo-root-relative input.

### REQMD-PORTABILITY-003: Default conventions
- **Status:** 🔧 Implemented
- Given no portability flags are provided
- When command runs
- Then repo root defaults to current directory
- And criteria directory defaults to docs/requirements.

### REQMD-PORTABILITY-004: Stable relative source display
- **Status:** 🔧 Implemented
- Given criterion panels and updates are printed
- When output references file paths
- Then source paths are shown relative to repo root
- And remain readable across machines.

### REQMD-PORTABILITY-005: Non-project-specific assumptions
- **Status:** 🔧 Implemented
- Given this package is copied into another codebase
- When command is executed with valid docs structure
- Then tool behavior does not depend on Speed Steel VR-specific files
- And only AC markdown contract is required.

### REQMD-PORTABILITY-006: Optional future config file support
- **Status:** 💡 Proposed
- Given teams may want fewer CLI flags
- When a project config file is added in future
- Then defaults for repo root and criteria path can be declared centrally
- And command-line flags still override config values.

### REQMD-PORTABILITY-007: Status customization config location and precedence
- **Status:** 💡 Proposed
- Given teams want customizable status catalog metadata and colors
- When status customization is enabled
- Then the tool supports loading config from a project file at `.reqmd/status-catalog.json` by default
- And the tool supports explicit override via `--status-config <path>`
- And effective precedence is: CLI override file > project default file > built-in defaults
- And JSON is required initially, with YAML support optional for future extension.

### REQMD-PORTABILITY-008: Automatic requirements-dir search from current path
- **Status:** 💡 Proposed
- Given users run reqmd without an explicit `--criteria-dir`
- When reqmd scans from the current working path
- Then reqmd searches for viable requirements locations including `docs/requirements/`, `requirements/`, and `requirements.md`
- And the `docs/` prefix is optional rather than required
- And reqmd selects the best matching candidate deterministically
- And reqmd reports which path was selected.

### REQMD-PORTABILITY-009: Graceful startup errors for docs availability and permissions
- **Status:** 💡 Proposed
- Given reqmd cannot open requirements docs because files are missing or inaccessible
- When startup validation fails
- Then reqmd exits with a clear, actionable error message
- And the message distinguishes not-found conditions from permission-denied conditions
- And no partial interactive session is started.

### REQMD-PORTABILITY-010: One-time emoji strip and restore commands
- **Status:** 💡 Proposed
- Given a team prefers plain-text status labels for platform compatibility or readability
- When `--strip-status-emojis` is run once against the docs
- Then all emoji prefixes are removed from every status line across all criteria files
- And subsequent runs infer emoji-free mode from the absence of emojis in existing statuses and do not reintroduce them
- And summary blocks are regenerated without emoji characters.
- Given a team wants to restore emoji-prefixed statuses
- When `--restore-status-emojis` is run once against the docs
- Then the canonical emoji is prepended to every status line across all criteria files
- And subsequent runs resume normal emoji-inclusive behavior.
- And both operations are idempotent and produce no diff if already in the target mode.
