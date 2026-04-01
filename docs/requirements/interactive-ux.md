# Interactive UX Requirement

Scope: interactive menus, keyboard navigation, and in-session requirement status editing.

<!-- acceptance-status-summary:start -->
Summary: 2💡 9🔧 20✅ 0⛔ 4🗑️
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
- So that Vim-style `j`/`k` paging shortcuts remain available alongside arrow-key navigation.
- So that selection remains scoped to visible page indices.

### RQMD-INTERACTIVE-004: Requirement next/prev shortcuts
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when the status menu for a requirement is open
- I want to press down arrow (next) or up arrow (prev)
- So that focus moves across requirements in current ordering
- So that history-aware navigation supports backtracking.
- So that Vim-style `j`/`k` shortcuts remain available alongside arrow-key navigation.

### RQMD-INTERACTIVE-004A: Next/prev stack semantics
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when users navigate requirements using arrow keys or `j`/`k` aliases
- I want to move forward and backward across requirements
- So that rqmd preserves a history stack semantics for backtracking
- So that `k` returns to the previously visited requirement context.
- So that filtered walkthroughs support `g` (beginning) and `G` (end) jump shortcuts.
- So that reaching the end of a filtered walkthrough with next-navigation keeps the session open and displays a clear "no more <target> requirements" message.
- So that once a filtered walkthrough session starts, its membership remains stable for that session even if an edited requirement no longer matches the original status or priority filter, allowing immediate backtracking to the just-edited requirement.
- So that editing a requirement during a filtered walkthrough does not implicitly advance away from that requirement; advancing remains an explicit next-navigation action.

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
- So that the current selection is explicitly marked with an arrow when the menu opens
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

### RQMD-INTERACTIVE-007: Keep current requirement visible after update
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when a requirement status or priority is changed in interactive flow
- I want the update to succeed
- So that the currently edited requirement remains visible after the change
- So that I can explicitly press down arrow or `j` when I am ready to move to the next requirement
- So that summary table refreshes with updated counts.
- So that status-first entry panels can also assign priority directly with shifted number-row shortcuts such as `!`, `@`, `#`, `$`, `%`, `^`, `&`, and `*` for the first configured priorities without toggling away from the status panel.
- So that the status-first view renders those priority choices as a clearly aligned second column, with the currently assigned priority visibly marked even while status remains the active selection.
- So that the priority preview column stays left-aligned within its own fixed-width block, rather than jittering by priority-label length.
- So that the active status highlight and the current-priority highlight render independently, allowing users to see both selections at once.
- So that those direct priority shortcuts update the current requirement in place without auto-advancing away from it.

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
- So that `j`/`k` traversal, resume behavior, and update flows work consistently within the explicit list scope, including keeping the edited requirement visible until the user explicitly navigates onward.
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

### RQMD-INTERACTIVE-023: Vim-style vertical navigation defaults
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when I navigate interactive menus primarily from the keyboard
- I want `j` and `k` to be the default down/up navigation keys
- So that rqmd aligns with Vim vertical motion expectations while keeping arrow-key support intact.
- So that menu legends, prompts, walkthrough help text, and requirement navigation all show `j`/`k` instead of `n`/`p` as the primary single-key movement contract.
- So that legacy `n`/`p` navigation aliases are removed rather than preserved as hidden compatibility shortcuts.
- So that any old uses of `n`/`p` are either retired or repurposed only where they match familiar Vim semantics such as search result repeat (`n`/`N`).

### RQMD-INTERACTIVE-024: Vim-style list motions and paging
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when interactive lists span many files, requirements, or history entries
- I want rqmd to support common Vim movement primitives beyond one-row navigation
- So that `gg` jumps to the first item and `G` jumps to the last item in the current list context.
- So that `Ctrl-U` and `Ctrl-D` perform deterministic half-page navigation in paged menus and walkthroughs.
- So that page-local selection, visible index rendering, and refresh behavior remain stable after these motions.
- So that these motions work consistently across file menus, requirement menus, filtered walks, and history browsers rather than only in one interactive surface.

### RQMD-INTERACTIVE-025: Vim-style search and repeat navigation
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when interactive menus become long enough that scanning visually is slow
- I want in-session search motions that feel like Vim
- So that `/` opens forward search and `?` opens reverse search for the current interactive list.
- So that `n` repeats the last search in the same direction and `N` repeats it in the opposite direction.
- So that matched items are surfaced predictably without losing the current list context, active filters, or sort order.
- So that history browser, file selection, requirement selection, and focused walkthroughs all share the same search-repeat contract.

### RQMD-INTERACTIVE-026: Compact footer with full help menu
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when interactive menus accumulate many shortcuts and modes
- I want the default interface to stay visually uncluttered while still exposing a complete help menu
- So that the main footer can emphasize only the highest-frequency keys instead of listing every command at once.
- So that a dedicated help surface can show all available bindings, meanings, and context-specific actions without truncation or visual overload.
- So that the app can present a classic Vim-style `:` affordance when the interactive session first opens, hinting that deeper command/help discovery is available without forcing a long default legend.
- So that discoverability remains high for advanced features such as sort cycling, refresh, history, paging, and search even when they are not all shown in the default footer.
- So that pressing an otherwise invalid or unmapped key can toggle the help surface open as a playful discovery shortcut, and pressing another invalid/unmapped key while help is open can close it again.
- So that this invalid-key help toggle remains deterministic, does not trigger destructive actions, and does not silently consume valid command keys that belong to the current menu context.
- So that opening and closing help does not discard the current menu context, selection, sort state, or active search position.
- So that shared menus and workflow-specific prompts converge on a consistent compact-footer-plus-help pattern instead of each surface inventing its own long legend.

### RQMD-INTERACTIVE-027: Positional status and priority filter walk
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when I run rqmd with positional status and/or priority tokens instead of explicit filter flags
- I want rqmd to open the same focused interactive walk that explicit `--status` and `--priority` filters would produce
- So that commands such as `rqmd P1 Proposed` or `rqmd Prop P1` immediately start a walk over the matching requirements instead of opening the generic file menu.
- So that when both positional status and priority filter tokens are present, the resulting walk narrows to requirements that satisfy each filter family rather than broadening across them.
- So that the resulting interactive session preserves the same navigation, resume, summary-refresh, and filtered-context behavior already defined for explicit status/priority walks.
- So that the UI clearly surfaces which positional filters were resolved before the user begins editing requirements.

### RQMD-INTERACTIVE-028: Dedicated interactive rank mode
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As a rqmd user when I want to groom backlog order instead of editing statuses
- I want a dedicated `rqmd rank` interactive mode
- So that rqmd opens directly into a ranking-focused workflow rather than the standard status-editing flow.
- So that requirements are displayed in rank-aware order using a compact one-line presentation optimized for fast reordering.
- So that this mode focuses on moving items up or down in backlog order while preserving access to the existing detailed requirement view when needed.

### RQMD-INTERACTIVE-029: Rank-editing shortcuts and placement suggestions
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As a rqmd user when I am reviewing requirements in either the standard interactive flow or the dedicated rank mode
- I want rank to be editable with direct keyboard shortcuts plus guided placement suggestions
- So that I can move the selected requirement to the top, to the bottom, up one slot, down one slot, up one page, or down one page without manually calculating rank values.
- So that rqmd can suggest concrete resulting rank values for those actions before applying them.
- So that I can also choose to place a requirement above another requirement by searching for that target by ID or title text.
- So that after using a rank shortcut I can optionally open the normal detailed requirement view, inspect more context, make other edits, and then return to the ranking flow without losing my place.

### RQMD-INTERACTIVE-030: Open current requirement in VS Code
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when I am focused on a requirement in the interactive UI
- I want a direct keyboard action that opens the current requirement in VS Code at its source location
- So that I can jump from the interactive review flow to the exact markdown block without manually searching for the file and requirement ID.
- So that the action targets the current requirement heading line, or the closest stable source location for that requirement, in the active workspace.
- So that the UI surfaces the shortcut clearly and reports a graceful fallback when VS Code integration is unavailable.
- So that after opening the editor location I can return to rqmd without losing my interactive context.

### RQMD-INTERACTIVE-031: Open linked requirement references from interactive detail view
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when I am reading a requirement in the interactive detail view and it references another local requirement ID
- I want to click or otherwise activate that referenced requirement link and have rqmd offer to open the referenced requirement immediately
- So that I can jump quickly to related requirements such as `See also` links, blocking links, or other cross-references without manually searching by ID.
- So that rqmd recognizes repo-local markdown links and inline requirement-ID references that resolve to another requirement in the current catalog.
- So that opening the linked requirement keeps me inside the interactive workflow and preserves enough history that I can return to the originating requirement after making related updates.
- So that unresolved or external links fail gracefully with clear feedback instead of interrupting the current review flow.
