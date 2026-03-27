# Interactive UX Requirement

Scope: interactive menus, keyboard navigation, and in-session requirement status editing.

<!-- acceptance-status-summary:start -->
Summary: 4💡 0🔧 13✅ 0⛔ 4🗑️
<!-- acceptance-status-summary:end -->

### RQMD-INTERACTIVE-001: Interactive mode default
- **Status:** ✅ Verified
- As a rqmd user when the command is run without non-interactive flags
- I want check mode to be disabled
- So that interactive flow opens by default
- So that users can navigate file -> requirement -> status.

### RQMD-INTERACTIVE-002: Single-key menu navigation
- **Status:** ✅ Verified
- As a rqmd user when the interactive menu is visible
- I want to press menu keys
- So that selections and navigation are handled without pressing Enter
- So that key mappings are printed in the menu footer.

### RQMD-INTERACTIVE-003: Paging controls
- **Status:** ✅ Verified
- As a rqmd user when menu options exceed one page
- I want to press next/prev page keys
- So that menu page changes accordingly
- So that selection remains scoped to visible page indices.

### RQMD-INTERACTIVE-004: Requirement next/prev shortcuts
- **Status:** ✅ Verified
- As a rqmd user when the status menu for a requirement is open
- I want to press `n` (next) or `p` (prev)
- So that focus moves across requirements in current ordering
- So that history-aware navigation supports backtracking.

### RQMD-INTERACTIVE-004A: Next/prev stack semantics
- **Status:** ✅ Verified
- As a rqmd user when users navigate requirements using `n` and `p`
- I want to move forward and backward across requirements
- So that rqmd preserves a history stack semantics for backtracking
- So that `p` returns to the previously visited requirement context.

### RQMD-INTERACTIVE-005: Sort toggles
- **Status:** 🗑️ Deprecated
- **Deprecated:** Superseded by RQMD-SORTING-007/008/010, which define sort-column cycling, direction toggling, and standardized legend behavior.
- As a rqmd user when file or requirement list menu is open
- I want to toggle sort
- So that ordering switches between default and priority sorting
- So that the menu reflects the new mode.

### RQMD-INTERACTIVE-006: Status highlight row
- **Status:** ✅ Verified
- As a rqmd user when status options are displayed for a requirement
- I want the menu to render
- So that current status row is highlighted
- So that highlight color aligns with status family.

### RQMD-INTERACTIVE-006A: Color semantics for status families
- **Status:** ✅ Verified
- As a rqmd user when status-driven text appears in menus and tables
- I want status color styles to be applied
- So that Proposed uses the dedicated proposed color treatment
- So that Verified uses green styling
- So that Blocked plus Deprecated use dim styling
- So that non-terminal in-progress statuses retain neutral baseline readability.

### RQMD-INTERACTIVE-006B: Color roll-up and row styling
- **Status:** ✅ Verified
- As a rqmd user when the file selection menu shows aggregate roll-ups
- I want roll-up text to render
- So that blue/proposed, green/completed, normal/in-progress, and dimmed/blocked+deprecated buckets are visually distinct
- So that zebra striping remains visible even when inline ANSI status colors are present

### RQMD-INTERACTIVE-007: Auto-advance after update
- **Status:** ✅ Verified
- As a rqmd user when a requirement status is changed in interactive flow
- I want the update to succeed
- So that the interface advances to the next requirement
- So that summary table refreshes with updated counts.

### RQMD-INTERACTIVE-008: Optional reason prompts
- **Status:** ✅ Verified
- As a rqmd user when user sets status to Blocked or Deprecated
- I want the update to be confirmed
- So that tool prompts for optional reason text
- So that reason line is inserted or updated when provided.

### RQMD-INTERACTIVE-009: Positional requirement lookup mode
- **Status:** ✅ Verified
- As a rqmd user when a requirement ID is passed positionally
- I want the command to execute
- So that matching requirement panel opens directly
- So that users can set status once then exit.

### RQMD-INTERACTIVE-016: Open specific domain file from CLI entry
- **Status:** 💡 Proposed
- As a rqmd user when a user invokes `rqmd` with a path to a domain file (absolute or repo-root-relative)
- I want the provided path to resolve to a valid markdown domain file containing criteria
- So that rqmd opens the interactive session with that file selected and the requirement list for that file presented first
- So that this behavior mirrors positional ID entry: users can immediately set status/priority or navigate requirements within that file
- So that in non-interactive modes the provided file path scopes non-interactive commands (e.g., `--set`, `--check`, `--set-priority`) to that file only
- So that if the file path is invalid the tool prints a helpful error and suggestions (nearest matching domain files, common typos), and offers to search for similar files.

### RQMD-INTERACTIVE-017: Interactive flagged-state toggling
- **Status:** 💡 Proposed
- As a rqmd user when I am reviewing requirements interactively
- I want to toggle a requirement's binary flagged state without changing its status
- So that I can quickly mark or unmark items that need special attention during triage and review.

### RQMD-INTERACTIVE-009A: Up key for hierarchical navigation
- **Status:** ✅ Verified
- As a rqmd user when users are in interactive menus
- I want to press `u` (up)
- So that rqmd moves up exactly one level in the menu hierarchy
- So that rqmd no longer uses `r` as the back/up key.

### RQMD-INTERACTIVE-010: Customizable status catalog and colors
- **Status:** 🗑️ Deprecated
- **Deprecated:** Superseded by RQMD-PORTABILITY-007/011/012, which own status-catalog schema, configuration loading/precedence, and user/project override behavior.
- As a rqmd user when teams have different status taxonomies
- I want the tool exposes status customization settings
- So that each status can define icon, full_name, and short_code
- So that status color style can be customized per status
- So that roll-up bucket color behavior can be customized independently from per-status styling
- So that interactive and non-interactive outputs both use the same configured status catalog.

### RQMD-INTERACTIVE-011: Preflight write-permission gate before interactive mode
- **Status:** ✅ Verified
- As a rqmd user when interactive mode can modify markdown requirement files
- I want rqmd to validate write permissions before opening interactive menus
- So that rqmd validates write permissions for target requirement files up front
- So that if any file is not writable rqmd exits before opening interactive navigation
- So that rqmd prints a clear per-file permission failure report with remediation guidance.

### RQMD-INTERACTIVE-012: Accessibility-safe zebra and color override rendering
- **Status:** 💡 Proposed
- As a rqmd user when terminal themes vary and default zebra/background colors may reduce readability
- I want to configure user or project color overrides
- So that interactive list zebra striping uses configured accessible foreground/background pairs
- So that status text colors remain legible when combined with zebra backgrounds
- So that rqmd falls back to safe defaults when configured colors are invalid or unsupported by the terminal.

### RQMD-INTERACTIVE-013: Terminal light/dark detection for automatic zebra adjustment
- **Status:** 💡 Proposed
- As a rqmd user when users benefit from automatic contrast-appropriate styling
- I want rqmd to start an interactive session
- So that reqmd attempts to infer a light or dark display context using a best-effort detection strategy (in priority order):
	- explicit CLI flag `--theme light|dark`
	- project config / user config override
	- macOS system appearance (`defaults read -g AppleInterfaceStyle`) when available
	- common desktop environment settings (e.g., GNOME via `gsettings get org.gnome.desktop.interface color-scheme`) when available
	- environment hints such as `TERM_PROGRAM` or terminal-specific profile hints (best-effort only)
- So that when detection yields `dark` or `light`, reqmd automatically selects zebra foreground/background pairs and contrast-safe status colors appropriate for the detected mode
- So that when detection is inconclusive, reqmd falls back to user/project config or accessibility-safe defaults and documents the chosen source used for the decision.

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
- As a rqmd user when interactive menus must show keyboard affordances consistently
- I want to open any interactive menu
- So that the footer displays a standardized legend in this exact order and compact format:
- `keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[asc|dsc] | r=rfrsh | q=quit`
- So that the `d` token updates in-place to reflect the current sort direction (either `asc` or `dsc`)
- So that pressing `s` cycles the active sort column while `d` toggles direction and `r` triggers a full refresh/rescan using the current sort scheme.
	- When the cycle advances past the last sortable column, pressing `s` again returns the view to the default filesystem ordering.

### RQMD-INTERACTIVE-015: Bold active sort column and arrow direction indicator
- **Status:** 🗑️ Deprecated
- **Deprecated:** Superseded by RQMD-SORTING-011, which owns active sort-column emphasis and direction indicators across interactive views.
- As a rqmd user when a sortable tabular or list view is displayed interactively
- I want a column to be the active sort key
- So that the column label is rendered in bold and an ASCII arrow (`↑` or `↓`) is shown adjacent to the label to indicate ascending or descending order
- So that the same visual indicator appears in the menu footer or header where space-constrained views cannot bold column headers directly
- So that these visual cues are applied consistently across file lists, requirement lists, and summary tables so users can always identify the active sort and its direction.
 

# optional status color overrides (names or hex)
colors:
	proposed: cyan
	in_progress: yellow
	done: green
	blocked: red
	deprecated: grey
```
