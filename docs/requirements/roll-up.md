# Roll-up Requirement

Scope: status aggregation, per-file summary generation, and roll-up display output.

<!-- acceptance-status-summary:start -->
Summary: 0💡 0🔧 6✅ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->

### RQMD-ROLLUP-001: Summary count generation per status
- **Status:** ✅ Verified
- As a rqmd user when requirement files contain canonical status lines
- I want rqmd to compute roll-up values
- So that counts are generated for each supported status in canonical order
- So that roll-up values match current file content.

### RQMD-ROLLUP-002: Inline summary block lifecycle
- **Status:** ✅ Verified
- As a rqmd user when files may or may not include a summary block
- I want rqmd to process files
- So that summary blocks are inserted or replaced idempotently
- So that summary markers remain canonical.

### RQMD-ROLLUP-003: Summary table output control
- **Status:** ✅ Verified
- As a rqmd user when automation and humans have different output preferences
- I want to toggle summary table options
- So that roll-up table output is shown or suppressed as requested
- So that command behavior otherwise remains unchanged.

### RQMD-ROLLUP-004: Colored roll-up rendering in interactive menus
- **Status:** ✅ Verified
- As a rqmd user when interactive file selection displays aggregated roll-ups
- I want roll-up text to render
- So that status-family color buckets are visually distinct
- So that zebra/background styling remains legible.

### RQMD-ROLLUP-005: Cross-file/global roll-up report mode
- **Status:** ✅ Verified
- As a rqmd user when teams need quick portfolio-level visibility
- I want a global roll-up mode
- So that rqmd can output aggregate status totals across all domain files
- So that it can optionally export structured machine-readable output.

### RQMD-ROLLUP-006: Project-configurable roll-up color knobs
- **Status:** 🗑️ Deprecated
- **Deprecated:** Superseded by RQMD-ROLLUP-007 which provides a more general `rollup_map`/`rollup_equations` mechanism for defining roll-up columns and mappings; color knobs can be represented within that model.
- As a rqmd user when projects may wish to control how roll-up colors are computed and rendered
- I want a project-level status config file to provide roll-up settings
- So that rqmd supports `rollup_mode` with values like `per_status`, `bucketed`, or `monochrome`, supports `bucket_map` to map statuses into roll-up buckets, and allows per-bucket `color` overrides
- So that roll-up output follows these knobs consistently in interactive and non-interactive reports
- So that invalid project roll-up settings produce clear validation messages referencing the config file path and offending keys.

### RQMD-ROLLUP-007: Custom roll-up expressions and mappings
- **Status:** ✅ Verified
- As a rqmd user when teams may want full control over how individual statuses aggregate into roll-up columns
- I want a project-level config to define roll-up mappings
- So that rqmd supports a declarative `rollup_map` (or `rollup_equations`) where each roll-up column may be defined by an expression of statuses, for example:
- `C1 = Implemented + Verified`
- `C2 = Proposed`
- So that shorthand using shortcodes is allowed (e.g., `C1 = I + V`), with parsing tolerant to whitespace and case.
- So that the config accepts the mapping in YAML or JSON under a top-level key, for example:
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
- So that evaluation semantics are simple set-union: a requirement with any of the listed statuses contributes to that roll-up column; a requirement may contribute to multiple roll-up columns if configured to do so.
- So that validation ensures referenced status names or shortcodes exist in the configured status catalog and reports precise config errors with file/path context.
- So that precedence follows: CLI flags > project config rollup_map > user config > built-in defaults.
- So that UI/exports apply the configured roll-up mapping consistently in summary blocks, roll-up tables, and interactive menus.
