# Automation API Requirement

Scope: non-interactive updates, machine-friendly batch operations, and CI-friendly check behavior.

<!-- acceptance-status-summary:start -->
Summary: 15💡 0🔧 10✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-AUTOMATION-001: Check-only mode
- **Status:** ✅ Verified
- Given docs may be out of sync
- When `--check` is used
- Then no files are written
- And process exits non-zero if any summary changes would be required.

### RQMD-AUTOMATION-002: Single requirement update mode
- **Status:** ✅ Verified
- Given requirement ID and status are provided
- When `--set-requirement-id` and `--set-status` are used
- Then only that requirement is updated
- And summary block for its file is refreshed.

### RQMD-AUTOMATION-003: Repeatable bulk set mode
- **Status:** ✅ Verified
- Given multiple `--set REQUIREMENT-ID=STATUS` arguments
- When command runs
- Then each update is applied in argument order
- And command exits successfully when all updates succeed.

### RQMD-AUTOMATION-004: Batch updates via file
- **Status:** ✅ Verified
- Given a JSONL/CSV/TSV update file
- When `--set-file` is used
- Then each row is parsed and applied
- And row-level validation errors include file and line context.

### RQMD-AUTOMATION-005: Batch row schema aliases
- **Status:** ✅ Verified
- Given batch rows use `requirement_id`, `criterion_id`, `id`, `ac_id`, or `r_id`
- When parser reads rows
- Then any supported key is accepted for requirement identifier
- And status remains required.

### RQMD-AUTOMATION-006: Conflicting mode guardrails
- **Status:** ✅ Verified
- Given user combines incompatible command modes
- When arguments are validated
- Then command fails fast with explicit message
- And no file writes are performed.

### RQMD-AUTOMATION-007: File scope disambiguation
- **Status:** ✅ Verified
- Given duplicate requirement IDs might exist across files
- When user provides `--file` scope
- Then update resolves only within that file
- And ambiguity errors are avoided.

### RQMD-AUTOMATION-008: Filtered tree output
- **Status:** ✅ Verified
- Given `--filter-status` with `--tree`
- When command runs in non-interactive mode
- Then tool prints grouped requirements tree by file
- And exits without opening interactive menus.

### RQMD-AUTOMATION-009: Summary table control
- **Status:** ✅ Verified
- Given automation may not want console tables
- When `--no-summary-table` is used
- Then summary table output is suppressed
- And command behavior otherwise remains unchanged.

### RQMD-AUTOMATION-010: JSON output for filtered status queries
- **Status:** ✅ Verified
- Given machine consumers need parse-friendly output
- When `--json` is used in non-interactive command flows
- Then rqmd prints valid JSON for summary/check/set/filter-status modes
- And filter mode includes status, criteria_dir, total, and grouped requirements by file
- And rqmd exits without interactive prompts or tree formatting noise.

### RQMD-AUTOMATION-011: Empty filter JSON result
- **Status:** 💡 Proposed
- As a CI user
- I want `--json` filter queries with no matches to return `total: 0` and `files: []`
- So that zero-match runs are handled as valid outcomes without brittle parsing.

### RQMD-AUTOMATION-012: Stable JSON schema contract
- **Status:** 💡 Proposed
- As an API consumer
- I want documented required JSON keys and value types per mode
- So that integrations are predictable and versioned when schema changes.

### RQMD-AUTOMATION-013: Deterministic JSON ordering
- **Status:** 💡 Proposed
- As a build engineer
- I want JSON arrays emitted in deterministic order
- So that repeated runs on unchanged inputs produce stable diffs.

### RQMD-AUTOMATION-014: Dry-run for mutation commands
- **Status:** 💡 Proposed
- As an automation user
- I want dry-run behavior for write commands (`--set`, `--set-file`, `--set-priority`, `--init-priorities`)
- So that I can preview exact changes before applying them.

### RQMD-AUTOMATION-015: Batch partial-failure report model
- **Status:** 💡 Proposed
- As a CI maintainer
- I want per-row success/failure results in JSON and text batch modes
- So that retry logic can target only failed rows.

### RQMD-AUTOMATION-016: Exit code matrix
- **Status:** 💡 Proposed
- As a pipeline author
- I want explicit documented exit codes by outcome type
- So that pipeline control flow remains unambiguous.

### RQMD-AUTOMATION-017: Prompt suppression guarantee
- **Status:** 💡 Proposed
- As a headless runner
- I want non-interactive and JSON modes to never prompt
- So that jobs never hang waiting for input.

### RQMD-AUTOMATION-018: Migration mode automation contract
- **Status:** 💡 Proposed
- As a migration operator
- I want `--init --yes` and `--init-priorities` to be idempotent, deterministic, and JSON-reportable
- So that migration steps are reliable in CI/CD workflows.

### RQMD-AUTOMATION-019: Unique-prefix argument/value abbreviations
- **Status:** 💡 Proposed
- As a CLI user
- I want unique minimal prefixes for long option names and enumerated values to be accepted (for example, `--filt V` -> `--filter-status Verified`)
- So that fast terminal usage is supported without sacrificing determinism.
- So that ambiguous prefixes fail with a clear disambiguation error listing valid matches.

### RQMD-AUTOMATION-020: Ambiguous option-prefix error contract
- **Status:** 💡 Proposed
- As a CLI user
- I want ambiguous long-option prefixes to fail deterministically
- So that the error output lists candidate option names and recommended full invocations.

### RQMD-AUTOMATION-021: Ambiguous value-prefix error contract
- **Status:** 💡 Proposed
- As a CLI user
- I want ambiguous enumerated value prefixes (for example status values) to fail deterministically
- So that the error output lists candidate canonical values and recommended full values.

### RQMD-AUTOMATION-022: JSON-formatted ambiguity errors
- **Status:** 💡 Proposed
- As an automation user
- I want ambiguity failures in `--json` mode to return a stable machine-readable error payload
- So that tools can branch on error type, inspect candidates, and auto-remediate input expansion.

### RQMD-AUTOMATION-023: Filter flagged requirements
- **Status:** 💡 Proposed
- As an automation user
- I want a `--filter-flagged` mode for non-interactive workflows
- So that flagged requirements can be listed, walked, or exported without relying on status changes.

### RQMD-AUTOMATION-024: JSON output for flagged items
- **Status:** 💡 Proposed
- As an automation user
- I want `--filter-flagged --json` to return flagged requirements in the same stable grouped structure used by other filter modes
- So that bots and scripts can consume focus lists consistently.

### RQMD-AUTOMATION-025: Direct flagged-state mutation
- **Status:** 💡 Proposed
- As an automation user
- I want to set flagged state directly with `--set-flagged REQUIREMENT-ID=true|false`
- So that workflows can mutate flagged state deterministically without requiring interactive mode.
- So that batch and CI jobs can manage flagged triage state using the same validation, ambiguity handling, and file-scope guardrails used by other mutation commands.
- So that `--set-file` rows can also include flagged-state mutation values with the same canonical true/false normalization and row-level error reporting guarantees.
- So that `--json` mutation runs return structured success/failure results for flagged updates consistent with the existing batch partial-failure model.
