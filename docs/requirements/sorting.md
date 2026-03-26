# Sorting Requirement

Scope: deterministic ordering, sort toggles, and priority-based ranking in interactive views.

<!-- acceptance-status-summary:start -->
Summary: 0💡 8🔧 1✅ 0⛔ 2🗑️
<!-- acceptance-status-summary:end -->

### RQMD-SORTING-001: File ranking by priority buckets
- **Status:** 🗑️ Deprecated
- **Deprecated:** Conflicts with RQMD-SORTING-006 (default name ordering); deprecated in favor of explicit user-selected sort modes.
- Given file rows are shown in interactive selection
- When sort mode is enabled
- Then ordering prioritizes in-progress requirement counts first
- And tie-breaking remains deterministic.

### RQMD-SORTING-002: Sort toggle key behavior
- **Status:** 🗑️ Deprecated
- **Deprecated:** Replaced by RQMD-SORTING-007 which provides column-cycle sorting via `s` and clearer UX.
- Given users are in file or requirement selection menus
- When users press the sort toggle key
- Then rqmd switches between default and alternate ordering modes
- And menu output clearly reflects the current mode.

### RQMD-SORTING-003: Stable deterministic ordering
- **Status:** ✅ Verified
- Given multiple files or requirements share equal priority values
- When rqmd renders sorted menus
- Then ordering remains stable across repeated renders
- And avoids jitter between refresh cycles, including going up/down the menu hierarchy.

### RQMD-SORTING-004: Rescan preserves selected sort mode
- **Status:** 🔧 Implemented
- Given interactive mode rescans files after updates
- When sort mode is currently enabled or disabled
- Then rescan preserves the active mode
- And ordering is rebuilt using that mode consistently.

### RQMD-SORTING-005: Configurable sort strategy catalog
- **Status:** 🔧 Implemented
- Given teams may want alternative ranking policies
- When sort customization is introduced
- Then rqmd allows selecting named sort strategies (for example `standard`, `status-focus`, `alpha-asc`) via CLI
- And each strategy defines default active sort keys/directions and column cycle order for both file and requirement interactive menus
- And strategy selection applies consistently across interactive menus.

### RQMD-SORTING-006: Default name ordering
- **Status:** 🔧 Implemented
- Given no explicit sort preference is set
- When interactive menus render file lists
- Then ordering defaults to the `name` sort column rather than a separate filesystem sort mode
- And the default direction for that active sort is descending
- And no automatic priority-based reordering is applied unless the user selects a different sort column.

### RQMD-SORTING-007: Column-cycle sorting with `s`
- **Status:** 🔧 Implemented
- Given a user is viewing a tabular menu or list with multiple sortable columns (e.g., file name, roll-up counts, changed flag)
- When the user presses `s`
- Then the active sort column cycles to the next available column from left to right
- And when the cycle advances past the last sortable column, pressing `s` again returns the view to the default menu sort (for file lists, `name`) so the cycle can continue indefinitely without a separate filesystem-only mode
- And the UI indicates the active sort column and direction in the menu header/footer.

### RQMD-SORTING-008: Toggle ascending/descending with `d`
- **Status:** 🔧 Implemented
- Given a sort column is active
- When the user presses `d`
- Then the sort direction toggles between ascending and descending
- And when a new sort column becomes active, its initial direction defaults to descending
- And the legend shows the current direction as `d=[asc|dsc]` and updates dynamically.

### RQMD-SORTING-009: Refresh/rescan with `r`
- **Status:** 🔧 Implemented
- Given the user has a current sort column and direction
- When the user presses `r`
- Then the UI refreshes all screen content, rescans underlying files, and reapplies the current sort scheme
- And `r` is a non-destructive operation that does not change the active sort column or direction.

### RQMD-SORTING-010: Standardized interaction legend
- **Status:** 🔧 Implemented
- Given the interactive UI must remain discoverable and consistent
- When menus render
- Then a standardized key legend is shown in the footer in this order and format:
- `keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[asc|dsc] | r=rfrsh | q=quit`
- And the `d` segment is updated dynamically to reflect the current sort direction.

### RQMD-SORTING-011: Visual indicator for active sort column and direction
- **Status:** 🔧 Implemented
- Given a column is actively used to sort a view
- When menus render
- Then the active column label is rendered in bold and an ASCII arrow indicator is shown to indicate direction (`↑` for ascending, `↓` for descending)
- And in file-list sort headers, non-`name` column labels are right-aligned for quick scanning while `name` remains left-aligned
- And the same visual cue is present in file and requirement list headers and any columnized views so users can quickly identify the current sort context.
