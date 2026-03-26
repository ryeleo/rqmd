# Interactive UX Requirement

Scope: interactive menus, keyboard navigation, and in-session requirement status editing.

<!-- acceptance-status-summary:start -->
Summary: 3💡 14🔧 0✅ 0⛔ 2🗑️
<!-- acceptance-status-summary:end -->

### RQMD-INTERACTIVE-001: Interactive mode default
- **Status:** 🔧 Implemented
- Given the command is run without non-interactive flags
- When check mode is not enabled
- Then interactive flow opens by default
- And user can navigate file -> requirement -> status.

### RQMD-INTERACTIVE-002: Single-key menu navigation
- **Status:** 🔧 Implemented
- Given the interactive menu is visible
- When the user presses menu keys
- Then selections and navigation are handled without pressing Enter
- And key mappings are printed in the menu footer.

### RQMD-INTERACTIVE-003: Paging controls
- **Status:** 🔧 Implemented
- Given menu options exceed one page
- When user presses next/prev page keys
- Then menu page changes accordingly
- And selection remains scoped to visible page indices.

### RQMD-INTERACTIVE-004: Requirement next/prev shortcuts
- **Status:** 🔧 Implemented
- Given the status menu for a requirement is open
- When user presses `n` (next) or `p` (prev)
- Then focus moves across requirements in current ordering
- And history-aware navigation supports backtracking.

### RQMD-INTERACTIVE-004A: Next/prev stack semantics
- **Status:** 🔧 Implemented
- Given users navigate requirements using `n` and `p`
- When users move forward and backward across requirements
- Then rqmd preserves a history stack semantics for backtracking
- And `p` returns to the previously visited requirement context.

### RQMD-INTERACTIVE-005: Sort toggles
- **Status:** 🔧 Implemented
- Given file or requirement list menu is open
- When user toggles sort
- Then ordering switches between default and priority sorting
- And the menu reflects the new mode.

### RQMD-INTERACTIVE-006: Status highlight row
- **Status:** 🔧 Implemented
- Given status options are displayed for a requirement
- When menu renders
- Then current status row is highlighted
- And highlight color aligns with status family.

### RQMD-INTERACTIVE-006A: Color semantics for status families
- **Status:** 🔧 Implemented
- Given status-driven text appears in menus and tables
- When status color styles are applied
- Then Proposed uses the dedicated proposed color treatment
- And Verified uses green styling
- And Blocked plus Deprecated use dim styling
- And non-terminal in-progress statuses retain neutral baseline readability.

### RQMD-INTERACTIVE-006B: Color roll-up and row styling
- **Status:** 🔧 Implemented
- Given the file selection menu shows aggregate roll-ups
- When roll-up text is rendered
- Then blue/proposed, green/completed, normal/in-progress, and dimmed/blocked+deprecated buckets are visually distinct
- And zebra striping remains visible even when inline ANSI status colors are present

### RQMD-INTERACTIVE-007: Auto-advance after update
- **Status:** 🔧 Implemented
- Given a requirement status is changed in interactive flow
- When update succeeds
- Then the interface advances to the next requirement
- And summary table refreshes with updated counts.

### RQMD-INTERACTIVE-008: Optional reason prompts
- **Status:** 🔧 Implemented
- Given user sets status to Blocked or Deprecated
- When update is confirmed
- Then tool prompts for optional reason text
- And reason line is inserted or updated when provided.

### RQMD-INTERACTIVE-009: Positional requirement lookup mode
- **Status:** 🔧 Implemented
- Given a requirement ID is passed positionally
- When command executes
- Then matching requirement panel opens directly
- And user can set status once then exit.

### RQMD-INTERACTIVE-009A: Up key for hierarchical navigation
- **Status:** 🔧 Implemented
- Given users are in interactive menus
- When users press `u` (up)
- Then rqmd moves up exactly one level in the menu hierarchy
- And rqmd no longer uses `r` as the back/up key.

### RQMD-INTERACTIVE-010: Customizable status catalog and colors
- **Status:** 💡 Proposed
- Given teams have different status taxonomies
- When the tool exposes status customization settings
- Then each status can define icon, full_name, and short_code
- And status color style can be customized per status
- And roll-up bucket color behavior can be customized independently from per-status styling
- And interactive and non-interactive outputs both use the same configured status catalog.

### RQMD-INTERACTIVE-011: Preflight write-permission gate before interactive mode
- **Status:** 🔧 Implemented
- Given interactive mode can modify markdown requirement files
- When rqmd is about to open interactive menus
- Then rqmd validates write permissions for target requirement files up front
- And if any file is not writable rqmd exits before opening interactive navigation
- And rqmd prints a clear per-file permission failure report with remediation guidance.

### RQMD-INTERACTIVE-012: Accessibility-safe zebra and color override rendering
- **Status:** 💡 Proposed
- Given terminal themes vary and default zebra/background colors may reduce readability
- When user or project color overrides are configured
- Then interactive list zebra striping uses configured accessible foreground/background pairs
- And status text colors remain legible when combined with zebra backgrounds
- And rqmd falls back to safe defaults when configured colors are invalid or unsupported by the terminal.

### RQMD-INTERACTIVE-013: Terminal light/dark detection for automatic zebra adjustment
- **Status:** 💡 Proposed
- Given users benefit from automatic contrast-appropriate styling
- When reqmd starts an interactive session
- Then reqmd attempts to infer a light or dark display context using a best-effort detection strategy (in priority order):
	- explicit CLI flag `--theme light|dark`
	- project config / user config override
	- macOS system appearance (`defaults read -g AppleInterfaceStyle`) when available
	- common desktop environment settings (e.g., GNOME via `gsettings get org.gnome.desktop.interface color-scheme`) when available
	- environment hints such as `TERM_PROGRAM` or terminal-specific profile hints (best-effort only)
- And when detection yields `dark` or `light`, reqmd automatically selects zebra foreground/background pairs and contrast-safe status colors appropriate for the detected mode
- And when detection is inconclusive, reqmd falls back to user/project config or accessibility-safe defaults and documents the chosen source used for the decision.

- Implementation notes:
	- Use platform probes cautiously and only as best-effort heuristics; preferred ordered probes: explicit CLI, project/user config, platform API, terminal hints.
	- macOS probe example: `defaults read -g AppleInterfaceStyle` (returns `Dark` when dark mode enabled) — guard with platform checks and timeouts.
	- Linux desktops: try `gsettings` for GNOME when available; otherwise treat as inconclusive.
	- Windows detection requires registry/Win32 API access; implement as an optional probe behind a safe fallback.
	- Always validate chosen colors with a contrast check (WCAG-like thresholds) and auto-adjust zebra pairs if contrast is insufficient.
	- Do not block startup on probes; treat failures as "inconclusive" and continue with fallbacks.
	- Log or surface the detection source (CLI, project, user, system probe, heuristic) in verbose output or UI footer for transparency.
	- Add unit/integration tests that simulate each detection path and verify contrast-based fallbacks and final chosen colors.

### RQMD-INTERACTIVE-014: Standardized footer legend and dynamic sort indicator
- **Status:** 🗑️ Deprecated
- **Deprecated:** Superseded by RQMD-SORTING-010, which owns the standardized interaction legend and dynamic sort-direction footer behavior.
- Given interactive menus must show keyboard affordances consistently
- When any interactive menu is shown
- Then the footer displays a standardized legend in this exact order and compact format:
- `keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[asc|dsc] | r=rfrsh | q=quit`
- And the `d` token updates in-place to reflect the current sort direction (either `asc` or `dsc`)
- And pressing `s` cycles the active sort column while `d` toggles direction and `r` triggers a full refresh/rescan using the current sort scheme.
	- When the cycle advances past the last sortable column, pressing `s` again returns the view to the default filesystem ordering.

### RQMD-INTERACTIVE-015: Bold active sort column and arrow direction indicator
- **Status:** 🗑️ Deprecated
- **Deprecated:** Superseded by RQMD-SORTING-011, which owns active sort-column emphasis and direction indicators across interactive views.
- Given a sortable tabular or list view is displayed interactively
- When a column is the current sort key
- Then the column label is rendered in bold and an ASCII arrow (`↑` or `↓`) is shown adjacent to the label to indicate ascending or descending order
- And the same visual indicator appears in the menu footer or header where space-constrained views cannot bold column headers directly
- And these visual cues are applied consistently across file lists, requirement lists, and summary tables so users can always identify the active sort and its direction.
 

# optional status color overrides (names or hex)
colors:
	proposed: cyan
	in_progress: yellow
	done: green
	blocked: red
	deprecated: grey
```
