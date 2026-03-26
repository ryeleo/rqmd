# Roll-up Acceptance Criteria

Scope: status aggregation, per-file summary generation, and roll-up display output.

<!-- acceptance-status-summary:start -->
Summary: 0💡 1🔧 5✅ 0⛔ 1🗑️
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
- **Status:** ✅ Verified
- Given teams need quick portfolio-level visibility
- When a global roll-up mode is added
- Then rqmd can output aggregate status totals across all domain files
- And optionally export structured machine-readable output.

### RQMD-ROLLUP-006: Project-configurable roll-up color knobs
- **Status:** 🗑️ Deprecated
- **Deprecated:** Superseded by RQMD-ROLLUP-007 which provides a more general `rollup_map`/`rollup_equations` mechanism for defining roll-up columns and mappings; color knobs can be represented within that model.
- Given projects may wish to control how roll-up colors are computed and rendered
- When a project-level status config file provides roll-up settings
- Then rqmd supports `rollup_mode` with values like `per_status`, `bucketed`, or `monochrome`, supports `bucket_map` to map statuses into roll-up buckets, and allows per-bucket `color` overrides
- And roll-up output follows these knobs consistently in interactive and non-interactive reports
- And invalid project roll-up settings produce clear validation messages referencing the config file path and offending keys.

### RQMD-ROLLUP-007: Custom roll-up expressions and mappings
- **Status:** 🔧 Implemented
- Given teams may want full control over how individual statuses aggregate into roll-up columns
- When a project-level config defines roll-up mappings
- Then rqmd supports a declarative `rollup_map` (or `rollup_equations`) where each roll-up column may be defined by an expression of statuses, for example:
- `C1 = Implemented + Verified`
- `C2 = Proposed`
- And shorthand using shortcodes is allowed (e.g., `C1 = I + V`), with parsing tolerant to whitespace and case.
- And the config accepts the mapping in YAML or JSON under a top-level key, for example:
- ```yaml
- rollup_map:
-   C1: [implemented, verified]
-   C2: [proposed]
- ```
- or using equation syntax:
- ```yaml
- rollup_equations:
-   - "C1 = I + V"
-   - "C2 = P"
- ```
- And evaluation semantics are simple set-union: a criterion with any of the listed statuses contributes to that roll-up column; a criterion may contribute to multiple roll-up columns if configured to do so.
- And validation ensures referenced status names or shortcodes exist in the configured status catalog and reports precise config errors with file/path context.
- And precedence follows: CLI flags > project config rollup_map > user config > built-in defaults.
- And UI/exports apply the configured roll-up mapping consistently in summary blocks, roll-up tables, and interactive menus.
