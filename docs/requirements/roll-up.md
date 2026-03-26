# Roll-up Acceptance Criteria

Scope: status aggregation, per-file summary generation, and roll-up display output.

<!-- acceptance-status-summary:start -->
Summary: 1💡 0🔧 4✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### REQMD-ROLLUP-001: Summary count generation per status
- **Status:** ✅ Verified
- Given requirement files contain canonical status lines
- When reqmd computes roll-up values
- Then counts are generated for each supported status in canonical order
- And roll-up values match current file content.

### REQMD-ROLLUP-002: Inline summary block lifecycle
- **Status:** ✅ Verified
- Given files may or may not include a summary block
- When reqmd processes files
- Then summary blocks are inserted or replaced idempotently
- And summary markers remain canonical.

### REQMD-ROLLUP-003: Summary table output control
- **Status:** ✅ Verified
- Given automation and humans have different output preferences
- When users toggle summary table options
- Then roll-up table output is shown or suppressed as requested
- And command behavior otherwise remains unchanged.

### REQMD-ROLLUP-004: Colored roll-up rendering in interactive menus
- **Status:** ✅ Verified
- Given interactive file selection displays aggregated roll-ups
- When roll-up text is rendered
- Then status-family color buckets are visually distinct
- And zebra/background styling remains legible.

### REQMD-ROLLUP-005: Cross-file/global roll-up report mode
- **Status:** 💡 Proposed
- Given teams need quick portfolio-level visibility
- When a global roll-up mode is added
- Then reqmd can output aggregate status totals across all domain files
- And optionally export structured machine-readable output.