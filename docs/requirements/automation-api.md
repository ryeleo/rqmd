# Automation API Requirement

Scope: non-interactive updates, machine-friendly batch operations, and CI-friendly check behavior.

<!-- acceptance-status-summary:start -->
Summary: 10💡 11🔧 10✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-AUTOMATION-001: Check-only mode
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- Given docs may be out of sync
- When `--verify-summaries` is used
- Then no files are written
- And process exits non-zero if any summary changes would be required.

### RQMD-AUTOMATION-002: Single requirement update mode
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- Given requirement ID and status are provided
- When `--update-id` and `--update-status` are used
- Then only that requirement is updated
- And summary block for its file is refreshed.

### RQMD-AUTOMATION-003: Repeatable bulk set mode
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- Given multiple `--update REQUIREMENT-ID=STATUS` arguments
- When command runs
- Then each update is applied in argument order
- And command exits successfully when all updates succeed.

### RQMD-AUTOMATION-004: Batch updates via file
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- Given a JSONL/CSV/TSV update file
- When `--update-file` is used
- Then each row is parsed and applied
- And row-level validation errors include file and line context.

### RQMD-AUTOMATION-005: Batch row schema aliases
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- Given batch rows use `requirement_id`, `requirement_id`, `id`, `ac_id`, or `r_id`
- When parser reads rows
- Then any supported key is accepted for requirement identifier
- And status remains required.

### RQMD-AUTOMATION-006: Conflicting mode guardrails
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- Given user combines incompatible command modes
- When arguments are validated
- Then command fails fast with explicit message
- And no file writes are performed.

### RQMD-AUTOMATION-007: File scope disambiguation
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- Given duplicate requirement IDs might exist across files
- When user provides `--scope-file` scope
- Then update resolves only within that file
- And ambiguity errors are avoided.

### RQMD-AUTOMATION-008: Filtered tree output
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- Given `--status` with `--as-tree`
- When command runs in non-interactive mode
- Then tool prints grouped requirements tree by file
- And exits without opening interactive menus.

### RQMD-AUTOMATION-009: Summary table control
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- Given automation may not want console tables
- When `--no-table` is used
- Then summary table output is suppressed
- And command behavior otherwise remains unchanged.

### RQMD-AUTOMATION-010: JSON output for filtered status queries
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- Given machine consumers need parse-friendly output
- When `--as-json` is used in non-interactive command flows
- Then rqmd prints valid JSON for summary/check/set/filter-status modes
- And filter mode includes status, criteria_dir, total, and grouped requirements by file
- And rqmd exits without interactive prompts or tree formatting noise.

### RQMD-AUTOMATION-011: Empty filter JSON result
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a CI user
- I want `--as-json` filter queries with no matches to return `total: 0` and `files: []`
- So that zero-match runs are handled as valid outcomes without brittle parsing.

### RQMD-AUTOMATION-012: Stable JSON schema contract
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As an API consumer
- I want documented required JSON keys and value types per mode
- So that integrations are predictable and versioned when schema changes.

### RQMD-AUTOMATION-013: Deterministic JSON ordering
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a build engineer
- I want JSON arrays emitted in deterministic order
- So that repeated runs on unchanged inputs produce stable diffs.

### RQMD-AUTOMATION-014: Dry-run for mutation commands
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As an automation user
- I want dry-run behavior for write commands (`--update`, `--update-file`, `--update-priority`, `--seed-priorities`)
- So that I can preview exact changes before applying them.

### RQMD-AUTOMATION-015: Batch partial-failure report model
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As a CI maintainer
- I want per-row success/failure results in JSON and text batch modes
- So that retry logic can target only failed rows.

### RQMD-AUTOMATION-016: Exit code matrix
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a pipeline author
- I want explicit documented exit codes by outcome type
- So that pipeline control flow remains unambiguous.

### RQMD-AUTOMATION-017: Prompt suppression guarantee
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a headless runner
- I want non-interactive and JSON modes to never prompt
- So that jobs never hang waiting for input.

### RQMD-AUTOMATION-018: Migration mode automation contract
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a migration operator
- I want `--bootstrap --force-yes` and `--seed-priorities` to be idempotent, deterministic, and JSON-reportable
- So that migration steps are reliable in CI/CD workflows.

### RQMD-AUTOMATION-019: Unique-prefix argument/value abbreviations
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- As a CLI user
- I want unique minimal prefixes for long option names and enumerated values to be accepted (for example, `--filt V` -> `--status Verified`)
- So that fast terminal usage is supported without sacrificing determinism.
- So that ambiguous prefixes fail with a clear disambiguation error listing valid matches.

### RQMD-AUTOMATION-020: Ambiguous option-prefix error contract
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- As a CLI user
- I want ambiguous long-option prefixes to fail deterministically
- So that the error output lists candidate option names and recommended full invocations.

### RQMD-AUTOMATION-021: Ambiguous value-prefix error contract
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- As a CLI user
- I want ambiguous enumerated value prefixes (for example status values) to fail deterministically
- So that the error output lists candidate canonical values and recommended full values.

### RQMD-AUTOMATION-022: JSON-formatted ambiguity errors
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As an automation user
- I want ambiguity failures in `--as-json` mode to return a stable machine-readable error payload
- So that tools can branch on error type, inspect candidates, and auto-remediate input expansion.

### RQMD-AUTOMATION-023: Filter flagged requirements
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As an automation user
- I want a `--flagged` mode for non-interactive workflows
- So that flagged requirements can be listed, walked, or exported without relying on status changes.

### RQMD-AUTOMATION-024: JSON output for flagged items
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As an automation user
- I want `--flagged --as-json` to return flagged requirements in the same stable grouped structure used by other filter modes
- So that bots and scripts can consume focus lists consistently.

### RQMD-AUTOMATION-025: Direct flagged-state mutation
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As an automation user
- I want to set flagged state directly with `--update-flagged REQUIREMENT-ID=true|false`
- So that workflows can mutate flagged state deterministically without requiring interactive mode.
- So that batch and CI jobs can manage flagged triage state using the same validation, ambiguity handling, and file-scope guardrails used by other mutation commands.
- So that `--update-file` rows can also include flagged-state mutation values with the same canonical true/false normalization and row-level error reporting guarantees.
- So that `--as-json` mutation runs return structured success/failure results for flagged updates consistent with the existing batch partial-failure model.

### RQMD-AUTOMATION-026: Full domain-document JSON contract
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As an automation user when consuming `--as-json` outputs for domain-level workflows
- I want each domain entry to include all domain-document sections needed to reconstruct context, including `scope` and domain-level `body` aligned to RQMD-CORE-019
- So that machine consumers do not need to re-parse markdown to recover domain context beyond requirement rows.
- So that `--as-json` responses expose deterministic keys/order for domain metadata and preserve domain `body` content verbatim when present.

### RQMD-AUTOMATION-027: ReqID list input mode
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As a rqmd user when I want to target an explicit set of requirements
- I want a non-interactive/selection mode that accepts a CLI token list of requirement IDs and/or domain identifiers
- So that filtering and downstream operations can be scoped to exact IDs or whole domains instead of status or priority filters.
- So that domain tokens (filename, stem, or display name) are expanded deterministically to requirement IDs.
- So that list ordering is deterministic and duplicates are handled predictably.

### RQMD-AUTOMATION-028: ReqID list file parsing and comment support
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As a rqmd user when managing a reusable requirement worklist
- I want rqmd to accept a simple `.txt`/`.conf`/`.md` list file where requirement IDs, domain tokens, and subsection tokens may appear one-per-line or as comma/whitespace-separated tokens on any line
- So that teams can maintain lightweight worklists without strict CSV/JSONL schema overhead.
- So that `#` comment syntax is supported (line comments and trailing comments), and parsing ignores commented segments deterministically.
- So that this file-parser behavior is identical to positional/CLI token parsing for token forms, expansion, ordering, duplicate handling, and validation.
- So that subsection tokens are recognized by exact or case-insensitive prefix match and expand deterministically to all requirements in those subsections.

### RQMD-AUTOMATION-029: Filtered query by subsection
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As an automation user when filtering requirements within subsections
- I want a `--sub-domain <NAME>` flag to filter results by subsection
- So that similar to `--status`, only requirements matching the subsection name are included
- So that matching is case-insensitive prefix-based (e.g., `--sub-domain api` matches "API", "api-v1", etc.)
- So that subsection filtering works with `--as-tree`, `--as-json`, `--no-table`, and `--as-list` output modes
- So that in `--as-json` mode, filter context metadata includes the active `sub_domain` filter
- So that empty results are handled consistently with other filter modes.

### RQMD-AUTOMATION-030: Sub-domain metadata in JSON output
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As an automation consumer when processing JSON output
- I want each requirement entry to include a `sub_domain` field (string or null)
- So that metadata consumers can understand and reconstruct subsection structure
- So that domain-level JSON includes an optional `sub_sections` array listing available H2 section names and their requirement counts
- So that `--sub-domain` metadata in JSON output includes the filter name and matching count
- So that schema documentation clearly specifies the null-vs-absent distinction for `sub_domain` and `sub_sections`.

### RQMD-AUTOMATION-031: Minimal differentiable token matching for CLI args and values
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when typing commands quickly
- I want all CLI argument values that support enumerations/aliases to accept their smallest differentiable token**s** and shortcodes
- So that canonical labels are tokenized by whitespace-separated units and each unit is eligible for deterministic matching
- So that `🟡 P2 - Medium` is treated as exactly 4 tokens:
- `🟡`
- `P2`
- `-`
- `Medium`
- So that inputs like `--priority P2` resolve to the canonical configured priority label (for example `🟡 P2 - Medium`)
- So that inputs like `--priority M` resolve to the canonical configured priority label (for example `🟡 P2 - Medium`)
- So that inputs like `--priority H` resolve to the canonical configured priority label (for example `P1 - High`)
- So that inputs like `--status Ver` resolve to the canonical configured status label (for example `✅ Verified`)
- So that resolution is deterministic: unique prefixes are accepted, ambiguous prefixes fail with candidate lists, and unknown tokens return clear validation errors.
