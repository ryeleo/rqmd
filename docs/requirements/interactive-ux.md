# Interactive UX Requirement

Scope: interactive menus, keyboard navigation, and in-session requirement status editing.

<!-- acceptance-status-summary:start -->
Summary: 0💡 4🔧 18✅ 0⛔ 4🗑️
<!-- acceptance-status-summary:end -->

### RQMD-INTERACTIVE-001: Interactive mode default
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when the command is run without non-interactive flags
- I want check mode to be disabled
- So that interactive flow opens by default
- So that users can navigate file -> requirement -> status.
- So that startup and in-session interaction responsiveness follow the app-wide latency budgets defined by RQMD-UI-009 instead of redefining separate thresholds here.

### RQMD-INTERACTIVE-002: Single-key menu navigation
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when the interactive menu is visible
- I want to press menu keys
- So that selections and navigation are handled without pressing Enter
- So that key mappings are printed in the menu footer.

### RQMD-INTERACTIVE-003: Paging controls
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when menu options exceed one page
- I want to press next/prev page keys
- So that menu page changes accordingly
- So that down/up arrow keys are the primary next/prev navigation controls.
- So that legacy `n`/`p` paging shortcuts remain available as compatibility aliases.
- So that selection remains scoped to visible page indices.

### RQMD-INTERACTIVE-004: Requirement next/prev shortcuts
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when the status menu for a requirement is open
- I want to press down arrow (next) or up arrow (prev)
- So that focus moves across requirements in current ordering
- So that history-aware navigation supports backtracking.
- So that legacy `n`/`p` shortcuts remain available as compatibility aliases.
- So that `N` (Shift+N) is treated as reverse navigation for terminals where uppercase shortcuts are easier to reach.

### RQMD-INTERACTIVE-004A: Next/prev stack semantics
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when users navigate requirements using arrow keys or legacy `n`/`p` aliases
- I want to move forward and backward across requirements
- So that rqmd preserves a history stack semantics for backtracking
- So that `p` returns to the previously visited requirement context.
- So that filtered walkthroughs support `g` (beginning) and `G` (end) jump shortcuts.
- So that reaching the end of a filtered walkthrough with next-navigation keeps the session open and displays a clear "no more <target> requirements" message.

### RQMD-INTERACTIVE-005: Sort toggles
- **Status:** 🗑️ Deprecated
- **Priority:** 🟢 P3 - Low
- **Deprecated:** Superseded by RQMD-SORTING-007/008/010, which define sort-column cycling, direction toggling, and standardized legend behavior.
- As a rqmd user when file or requirement list menu is open
- I want to toggle sort
- So that ordering switches between default and priority sorting
- So that the menu reflects the new mode.

### RQMD-INTERACTIVE-006: Status highlight row
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when status options are displayed for a requirement
- I want the menu to render
- So that current status row is highlighted
- So that highlight color aligns with status family.

### RQMD-INTERACTIVE-006A: Color semantics for status families
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when status-driven text appears in menus and tables
- I want status color styles to be applied
- So that Proposed uses the dedicated proposed color treatment
- So that Verified uses green styling
- So that Blocked plus Deprecated use dim styling
- So that non-terminal in-progress statuses retain neutral baseline readability.

### RQMD-INTERACTIVE-006B: Color roll-up and row styling
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when the file selection menu shows aggregate roll-ups
- I want roll-up text to render
- So that blue/proposed, green/completed, normal/in-progress, and dimmed/blocked+deprecated buckets are visually distinct
- So that zebra striping remains visible even when inline ANSI status colors are present

### RQMD-INTERACTIVE-007: Auto-advance after update
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when a requirement status is changed in interactive flow
- I want the update to succeed
- So that the interface advances to the next requirement
- So that summary table refreshes with updated counts.

### RQMD-INTERACTIVE-008: Optional reason prompts
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when user sets status to Blocked or Deprecated
- I want the update to be confirmed
- So that tool prompts for optional reason text
- So that reason line is inserted or updated when provided.

### RQMD-INTERACTIVE-009: Positional requirement lookup mode
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when a requirement ID is passed positionally
- I want the command to execute
- So that matching requirement panel opens directly
- So that users can set status once then exit.

### RQMD-INTERACTIVE-016: Open specific domain file from CLI entry
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when a user invokes `rqmd` with a path to a domain file (absolute or repo-root-relative)
- I want the provided path to resolve to a valid markdown domain file containing requirements
- So that rqmd opens the interactive session with that file selected and the requirement list for that file presented first
- So that this behavior mirrors positional ID entry: users can immediately set status/priority or navigate requirements within that file
- So that in non-interactive modes the provided file path scopes non-interactive commands (e.g., `--update`, `--verify-summaries`, `--update-priority`) to that file only
- So that if the file path is invalid the tool prints a helpful error and suggestions (nearest matching domain files, common typos), and offers to search for similar files.
- If both an ID and a filename are provided as positional arguments, the tool should prioritize the ID for lookup and open the file containing that ID if found; if the ID is not found but the file is valid, it should open the specified file and print a warning about the missing ID.

### RQMD-INTERACTIVE-017: Interactive flagged-state toggling
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when I am reviewing requirements interactively
- I want to toggle a requirement's binary flagged state without changing its status
- So that I can quickly mark or unmark items that need special attention during triage and review.

### RQMD-INTERACTIVE-018: Domain-level notes discoverability in interactive mode
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when I open a domain in interactive mode
- I want optional domain-level notes/body content to be discoverable in-context (for example in a compact notes pane or explicit notes command)
- So that implementation guidance and AI-authored domain rationale are available without cluttering individual requirement bodies.
- So that interactive navigation remains focused on requirement editing while preserving fast access to domain context.
- So that this UX behavior depends on the canonical domain-body model defined by RQMD-CORE-019 rather than a separate interactive-only parsing path.

### RQMD-INTERACTIVE-019: Explicit ReqID-list focused interactive walk
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when I only want to work a specific subset of requirements
- I want to provide an explicit target list at CLI (via positional args or `--targets-file`) and launch a focused interactive walk
- So that the workflow behaves similarly to `--status` navigation but uses user-provided membership instead of status-based filtering.
- So that `n`/`p` traversal, resume behavior, and update flows work consistently within the explicit list scope.
- So that target lists can mix requirement IDs and domain identifiers (filename, stem, or display name), where domain tokens expand deterministically into that domain's requirements.
- So that positional arguments and `--targets-file` use the same token parser, expansion rules, ordering semantics, duplicate handling, and validation behavior.
- So that missing/invalid tokens are reported clearly before entering the walk.

### RQMD-INTERACTIVE-020: Case-insensitive tab completion for positional targets
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user invoking CLI commands from zsh
- I want tab completion for positional target tokens
- So that typing a prefix such as `rqmd Co<TAB>` suggests matching requirement IDs, domain identifiers, and subsection names that start with that prefix.
- So that matching is case-insensitive and deterministic across domain display names, domain file stems/paths, requirement IDs, and H2 subsection names.
- So that completion behavior uses the same token-resolution contract as explicit target-list parsing (`RQMD-INTERACTIVE-019` and `RQMD-AUTOMATION-027/028`).
- So that subsection tokens are expanded when used in target lists or `--targets-file`, expanding to all requirements in that subsection.

### RQMD-INTERACTIVE-021: Subsection navigation and discovery in interactive mode
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As an interactive user when navigating requirements within a domain that has H2 subsections
- I want the menu to expose subsection structure
- So that subsections are visually grouped and labeled in the requirement list view
- So that navigation can jump to subsections (e.g., `g api` to jump to "API" subsection)
- So that when opening a domain, subsections are collapsed/expandable or displayed as distinct menu sections
- So that this behavior depends on the domain-body and subsection parsing model defined by RQMD-CORE-020 rather than a separate interactive-only parsing path.

### RQMD-INTERACTIVE-009A: Up key for hierarchical navigation
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when users are in interactive menus
- I want to press `u` (up)
- So that rqmd moves up exactly one level in the menu hierarchy
- So that rqmd no longer uses `r` as the back/up key.

### RQMD-INTERACTIVE-010: Customizable status catalog and colors
- **Status:** 🗑️ Deprecated
- **Priority:** 🟢 P3 - Low
- **Deprecated:** Superseded by RQMD-PORTABILITY-007/011/012, which own status-catalog schema, configuration loading/precedence, and user/project override behavior.
- As a rqmd user when teams have different status taxonomies
- I want the tool exposes status customization settings
- So that each status can define icon, full_name, and short_code
- So that status color style can be customized per status
- So that roll-up bucket color behavior can be customized independently from per-status styling
- So that interactive and non-interactive outputs both use the same configured status catalog.

### RQMD-INTERACTIVE-011: Preflight write-permission gate before interactive mode
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when interactive mode can modify markdown requirement files
- I want rqmd to validate write permissions before opening interactive menus
- So that rqmd validates write permissions for target requirement files up front
- So that if any file is not writable rqmd exits before opening interactive navigation
- So that rqmd prints a clear per-file permission failure report with remediation guidance.

### RQMD-INTERACTIVE-012: Accessibility-safe zebra and color override rendering
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when terminal themes vary and default zebra/background colors may reduce readability
- I want to configure user or project color overrides
- So that interactive list zebra striping uses configured accessible foreground/background pairs
- So that status text colors remain legible when combined with zebra backgrounds
- So that rqmd falls back to safe defaults when configured colors are invalid or unsupported by the terminal.

### RQMD-INTERACTIVE-013: Terminal light/dark detection for automatic zebra adjustment
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
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
- **Priority:** 🟢 P3 - Low
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
- **Priority:** 🟢 P3 - Low
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

### RQMD-INTERACTIVE-022: Interactive link entry with URL-to-hyperlink auto-formatting
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when I want to add or manage external links on a requirement interactively
- I want a link-editing flow accessible from the requirement detail view
- So that the user can add a new link by entering either a plain URL or a pre-formatted `[label](url)` markdown hyperlink
- So that when the user enters a plain URL without markdown formatting, rqmd prompts "Add a label? (enter to skip)"
- So that if the user provides a label rqmd automatically formats the entry as `[label](url)` before saving
- So that if the user skips the label prompt the plain URL is written to the `**Links:**` field as-is
- So that the user can add multiple links in a single interactive session before returning to the requirement view
- So that existing links are displayed and the user can select one to remove or re-format it
- So that this flow depends on the `**Links:**` field contract defined in RQMD-CORE-021 and does not introduce a separate link storage path.
