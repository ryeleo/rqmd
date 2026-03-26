# Automation API Acceptance Criteria

Scope: non-interactive updates, machine-friendly batch operations, and CI-friendly check behavior.

<!-- acceptance-status-summary:start -->
Summary: 0💡 0🔧 10✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### REQMD-AUTOMATION-001: Check-only mode
- **Status:** ✅ Verified
- Given docs may be out of sync
- When `--check` is used
- Then no files are written
- And process exits non-zero if any summary changes would be required.

### REQMD-AUTOMATION-002: Single criterion update mode
- **Status:** ✅ Verified
- Given criterion ID and status are provided
- When `--set-criterion-id` and `--set-status` are used
- Then only that criterion is updated
- And summary block for its file is refreshed.

### REQMD-AUTOMATION-003: Repeatable bulk set mode
- **Status:** ✅ Verified
- Given multiple `--set AC-ID=STATUS` arguments
- When command runs
- Then each update is applied in argument order
- And command exits successfully when all updates succeed.

### REQMD-AUTOMATION-004: Batch updates via file
- **Status:** ✅ Verified
- Given a JSONL/CSV/TSV update file
- When `--set-file` is used
- Then each row is parsed and applied
- And row-level validation errors include file and line context.

### REQMD-AUTOMATION-005: Batch row schema aliases
- **Status:** ✅ Verified
- Given batch rows use `criterion_id`, `id`, or `ac_id`
- When parser reads rows
- Then any supported key is accepted for criterion identifier
- And status remains required.

### REQMD-AUTOMATION-006: Conflicting mode guardrails
- **Status:** ✅ Verified
- Given user combines incompatible command modes
- When arguments are validated
- Then command fails fast with explicit message
- And no file writes are performed.

### REQMD-AUTOMATION-007: File scope disambiguation
- **Status:** ✅ Verified
- Given duplicate criterion IDs might exist across files
- When user provides `--file` scope
- Then update resolves only within that file
- And ambiguity errors are avoided.

### REQMD-AUTOMATION-008: Filtered tree output
- **Status:** ✅ Verified
- Given `--filter-status` with `--tree`
- When command runs in non-interactive mode
- Then tool prints grouped criteria tree by file
- And exits without opening interactive menus.

### REQMD-AUTOMATION-009: Summary table control
- **Status:** ✅ Verified
- Given automation may not want console tables
- When `--no-summary-table` is used
- Then summary table output is suppressed
- And command behavior otherwise remains unchanged.

### REQMD-AUTOMATION-010: JSON output for filtered status queries
- **Status:** ✅ Verified
- Given machine consumers need parse-friendly output
- When `--json` is used in non-interactive command flows
- Then reqmd prints valid JSON for summary/check/set/filter-status modes
- And filter mode includes status, criteria_dir, total, and grouped criteria by file
- And reqmd exits without interactive prompts or tree formatting noise.
