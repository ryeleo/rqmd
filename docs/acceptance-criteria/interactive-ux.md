# Interactive UX Acceptance Criteria

Scope: interactive menus, keyboard navigation, and in-session criterion status editing.

<!-- acceptance-status-summary:start -->
Summary: 1💡 11🔧 0💻 0🎮 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### AC-ACCLI-INTERACTIVE-001: Interactive mode default
- **Status:** 🔧 Implemented
- Given the command is run without non-interactive flags
- When check mode is not enabled
- Then interactive flow opens by default
- And user can navigate file -> criterion -> status.

### AC-ACCLI-INTERACTIVE-002: Single-key menu navigation
- **Status:** 🔧 Implemented
- Given the interactive menu is visible
- When the user presses menu keys
- Then selections and navigation are handled without pressing Enter
- And key mappings are printed in the menu footer.

### AC-ACCLI-INTERACTIVE-003: Paging controls
- **Status:** 🔧 Implemented
- Given menu options exceed one page
- When user presses next/prev page keys
- Then menu page changes accordingly
- And selection remains scoped to visible page indices.

### AC-ACCLI-INTERACTIVE-004: Criterion next/prev shortcuts
- **Status:** 🔧 Implemented
- Given the status menu for a criterion is open
- When user presses criterion next/prev keys
- Then focus moves across criteria in current ordering
- And history-aware navigation supports backtracking.

### AC-ACCLI-INTERACTIVE-005: Sort toggles
- **Status:** 🔧 Implemented
- Given file or criterion list menu is open
- When user toggles sort
- Then ordering switches between default and priority sorting
- And the menu reflects the new mode.

### AC-ACCLI-INTERACTIVE-006: Status highlight row
- **Status:** 🔧 Implemented
- Given status options are displayed for a criterion
- When menu renders
- Then current status row is highlighted
- And highlight color aligns with status family.

### AC-ACCLI-INTERACTIVE-006A: Color semantics for status families
- **Status:** 🔧 Implemented
- Given status-driven text appears in menus and tables
- When status color styles are applied
- Then Proposed uses the dedicated proposed color treatment
- And Done plus VR-Verified use green styling
- And Blocked plus Deprecated use dim styling
- And non-terminal in-progress statuses retain neutral baseline readability.

### AC-ACCLI-INTERACTIVE-006B: Color roll-up and row styling
- **Status:** 🔧 Implemented
- Given the file selection menu shows aggregate roll-ups
- When roll-up text is rendered
- Then blue/proposed, green/completed, normal/in-progress, and dimmed/blocked+deprecated buckets are visually distinct
- And zebra striping remains visible even when inline ANSI status colors are present
- And waiting-for-VR roll-up value uses a distinct cyan treatment in summary tables.

### AC-ACCLI-INTERACTIVE-007: Auto-advance after update
- **Status:** 🔧 Implemented
- Given a criterion status is changed in interactive flow
- When update succeeds
- Then the interface advances to the next criterion
- And summary table refreshes with updated counts.

### AC-ACCLI-INTERACTIVE-008: Optional reason prompts
- **Status:** 🔧 Implemented
- Given user sets status to Blocked or Deprecated
- When update is confirmed
- Then tool prompts for optional reason text
- And reason line is inserted or updated when provided.

### AC-ACCLI-INTERACTIVE-009: Positional criterion lookup mode
- **Status:** 🔧 Implemented
- Given a criterion ID is passed positionally
- When command executes
- Then matching criterion panel opens directly
- And user can set status once then exit.

### AC-ACCLI-INTERACTIVE-010: Customizable status catalog and colors
- **Status:** 💡 Proposed
- Given teams have different status taxonomies
- When the tool exposes status customization settings
- Then each status can define icon, full_name, and short_code
- And status color style can be customized per status
- And roll-up bucket color behavior can be customized independently from per-status styling
- And interactive and non-interactive outputs both use the same configured status catalog.
