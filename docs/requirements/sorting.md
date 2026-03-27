# Sorting Requirement

Scope: deterministic ordering, sort toggles, and priority-based ranking in interactive views.

<!-- acceptance-status-summary:start -->
Summary: 0💡 0🔧 9✅ 0⛔ 2🗑️
<!-- acceptance-status-summary:end -->

### RQMD-SORTING-001: File ranking by priority buckets
- **Status:** 🗑️ Deprecated
- **Deprecated:** Conflicts with RQMD-SORTING-006 (default name ordering); deprecated in favor of explicit user-selected sort modes.
- As a rqmd user when file rows are shown in interactive selection
- I want to enable sort mode
- So that ordering prioritizes in-progress requirement counts first
- So that tie-breaking remains deterministic.

### RQMD-SORTING-002: Sort toggle key behavior
- **Status:** 🗑️ Deprecated
- **Deprecated:** Replaced by RQMD-SORTING-007 which provides column-cycle sorting via `s` and clearer UX.
- As a rqmd user when users are in file or requirement selection menus
- I want to press the sort toggle key
- So that rqmd switches between default and alternate ordering modes
- So that menu output clearly reflects the current mode.

### RQMD-SORTING-003: Stable deterministic ordering
- **Status:** ✅ Verified
- As a rqmd user when multiple files or requirements share equal priority values
- I want rqmd to render sorted menus
- So that ordering remains stable across repeated renders
- So that avoids jitter between refresh cycles, including going up/down the menu hierarchy.

### RQMD-SORTING-004: Rescan preserves selected sort mode
- **Status:** ✅ Verified
- As a rqmd user when interactive mode rescans files after updates
- I want the active sort mode state to persist
- So that rescan preserves the active mode
- So that ordering is rebuilt using that mode consistently.

### RQMD-SORTING-005: Configurable sort strategy catalog
- **Status:** ✅ Verified
- As a rqmd user when teams may want alternative ranking policies
- I want configurable sort strategies
- So that rqmd allows selecting named sort strategies (for example `standard`, `status-focus`, `alpha-asc`) via CLI
- So that each strategy defines default active sort keys/directions and column cycle order for both file and requirement interactive menus
- So that strategy selection applies consistently across interactive menus.

### RQMD-SORTING-006: Default name ordering
- **Status:** ✅ Verified
- As a rqmd user when no explicit sort preference is set
- I want interactive menus to render file lists
- So that ordering defaults to the `name` sort column rather than a separate filesystem sort mode
- So that the default direction for that active sort is descending
- So that no automatic priority-based reordering is applied unless the user selects a different sort column.

### RQMD-SORTING-007: Column-cycle sorting with `s`
- **Status:** ✅ Verified
- As a rqmd user when a user is viewing a tabular menu or list with multiple sortable columns (e.g., file name, roll-up counts, changed flag)
- I want to press `s`
- So that the active sort column cycles to the next available column from left to right
- So that when the cycle advances past the last sortable column, pressing `s` again returns the view to the default menu sort (for file lists, `name`) so the cycle can continue indefinitely without a separate filesystem-only mode
- So that the UI indicates the active sort column and direction in the menu header/footer.

### RQMD-SORTING-008: Toggle ascending/descending with `d`
- **Status:** ✅ Verified
- As a rqmd user when a sort column is active
- I want to press `d`
- So that the sort direction toggles between ascending and descending
- So that when a new sort column becomes active, its initial direction defaults to descending
- So that the legend shows the current direction as `d=[asc|dsc]` and updates dynamically.

### RQMD-SORTING-009: Refresh/rescan with `r`
- **Status:** ✅ Verified
- As a rqmd user when the user has a current sort column and direction
- I want to press `r`
- So that the UI refreshes all screen content, rescans underlying files, and reapplies the current sort scheme
- So that `r` is a non-destructive operation that does not change the active sort column or direction.

### RQMD-SORTING-010: Standardized interaction legend
- **Status:** ✅ Verified
- As a rqmd user when the interactive UI must remain discoverable and consistent
- I want menus to render
- So that a standardized key legend is shown in the footer in this order and format:
- `keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[asc|dsc] | r=rfrsh | q=quit`
- So that the `d` segment is updated dynamically to reflect the current sort direction.

### RQMD-SORTING-011: Visual indicator for active sort column and direction
- **Status:** ✅ Verified
- As a rqmd user when a column is actively used to sort a view
- I want menus to render
- So that the active column label is rendered in bold and an ASCII arrow indicator is shown to indicate direction (`↑` for ascending, `↓` for descending)
- So that in file-list sort headers, non-`name` column labels are right-aligned for quick scanning while `name` remains left-aligned
- So that the same visual cue is present in file and requirement list headers and any columnized views so users can quickly identify the current sort context.
