# Sorting Acceptance Criteria

Scope: deterministic ordering, sort toggles, and priority-based ranking in interactive views.

<!-- acceptance-status-summary:start -->
Summary: 1💡 4🔧 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### REQMD-SORTING-001: File ranking by priority buckets
- **Status:** 🔧 Implemented
- Given file rows are shown in interactive selection
- When sort mode is enabled
- Then ordering prioritizes in-progress requirement counts first
- And tie-breaking remains deterministic.

### REQMD-SORTING-002: Sort toggle key behavior
- **Status:** 🔧 Implemented
- Given users are in file or criterion selection menus
- When users press the sort toggle key
- Then reqmd switches between default and alternate ordering modes
- And menu output clearly reflects the current mode.

### REQMD-SORTING-003: Stable deterministic ordering
- **Status:** 🔧 Implemented
- Given multiple files or criteria share equal priority values
- When reqmd renders sorted menus
- Then ordering remains stable across repeated renders
- And avoids jitter between refresh cycles.

### REQMD-SORTING-004: Rescan preserves selected sort mode
- **Status:** 🔧 Implemented
- Given interactive mode rescans files after updates
- When sort mode is currently enabled or disabled
- Then rescan preserves the active mode
- And ordering is rebuilt using that mode consistently.

### REQMD-SORTING-005: Configurable sort strategy catalog
- **Status:** 💡 Proposed
- Given teams may want alternative ranking policies
- When sort customization is introduced
- Then reqmd allows selecting named sort strategies
- And strategy selection applies consistently across interactive menus.