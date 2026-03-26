# Roll-up Acceptance Criteria

Scope: status aggregation, per-file summary generation, and roll-up display output.

<!-- acceptance-status-summary:start -->
Summary: 2💡 0🔧 4✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-ROLLUP-001: Summary count generation per status
- **Status:** ✅ Verified
- Given requirement files contain canonical status lines
- When rqmd computes roll-up values
- Then counts are generated for each supported status in canonical order
- And roll-up values match current file content.

### RQMD-ROLLUP-002: Inline summary block lifecycle
- **Status:** ✅ Verified
- Given files may or may not include a summary block
- When rqmd processes files
- Then summary blocks are inserted or replaced idempotently
- And summary markers remain canonical.

### RQMD-ROLLUP-003: Summary table output control
- **Status:** ✅ Verified
- Given automation and humans have different output preferences
- When users toggle summary table options
- Then roll-up table output is shown or suppressed as requested
- And command behavior otherwise remains unchanged.

### RQMD-ROLLUP-004: Colored roll-up rendering in interactive menus
- **Status:** ✅ Verified
- Given interactive file selection displays aggregated roll-ups
- When roll-up text is rendered
- Then status-family color buckets are visually distinct
- And zebra/background styling remains legible.

### RQMD-ROLLUP-005: Cross-file/global roll-up report mode
- **Status:** 💡 Proposed
- Given teams need quick portfolio-level visibility
- When a global roll-up mode is added
- Then rqmd can output aggregate status totals across all domain files
- And optionally export structured machine-readable output.

### RQMD-ROLLUP-006: Project-configurable roll-up color knobs
- **Status:** 💡 Proposed
- Given projects may wish to control how roll-up colors are computed and rendered
- When a project-level status config file provides roll-up settings
- Then rqmd supports `rollup_mode` with values like `per_status`, `bucketed`, or `monochrome`, supports `bucket_map` to map statuses into roll-up buckets, and allows per-bucket `color` overrides
- And roll-up output follows these knobs consistently in interactive and non-interactive reports
- And invalid project roll-up settings produce clear validation messages referencing the config file path and offending keys.