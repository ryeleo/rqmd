# Screen-Write UI Requirement

Scope: interactive menus, paginated views, and terminal rendering behavior.

<!-- acceptance-status-summary:start -->
Summary: 2💡 8🔧 0✅ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->

### RQMD-UI-001: Screen-write rendering mode
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
- As a rqmd user when interactive menus are displayed
- I want the UI to use screen-write style full-screen updates instead of line-by-line scrolling
- So that page changes, pagination, and ephemeral menus feel snappy and visually stable
- So that the interactive experience avoids confusing scrollback artifacts and preserves layout across refreshes.

### RQMD-UI-002: Explicit `--screen-write` toggle and config precedence
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
- As a rqmd user when launching the tool
- I want a CLI flag `--screen-write` and a configuration option `screen_write: true|false` in project/user config
- So that users can opt in or out and project settings may assert their preferred rendering mode
- So that precedence follows: CLI > project config > user config > built-in default (default = `true` when TTY supports it).

### RQMD-UI-003: Safe fallback for non-TTY and limited terminals
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
- As a rqmd user when running in a non-interactive environment or a terminal lacking full-capability support
- I want rqmd to automatically fall back to the existing scrolling/append-style output
- So that scripts, CI, and terminals without `clear`/ANSI support remain functional and deterministic.

### RQMD-UI-004: Minimal-diff redraw semantics
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
- As a rqmd developer working on performance
- I want the screen-write implementation to support minimal-diff updates (only redraw changed regions when feasible)
- So that redraws are efficient and avoid excessive flicker on slow terminals
- Implementation note: implement a simple row-diff strategy first, with fallbacks to full `clear` + re-render when diffing is disabled or not supported.

### RQMD-UI-005: Pagination and stable cursor semantics
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
- As a rqmd user navigating pages or lists
- I want the UI to maintain a stable cursor/selection position across page changes and re-renders
- So that pressing `n`, `p`, `s`, or `d` results in predictable focus and selection, and the visible window always centers around the active selection where appropriate.

### RQMD-UI-006: Footer legend and transient notifications area
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
- As a rqmd user in interactive mode
- I want a reserved footer region for the standardized legend and short transient messages (e.g., detection source, errors)
- So that messages do not shift the main content and the legend reliably updates (e.g., `d=[asc|dsc]`).

### RQMD-UI-007: Accessibility & contrast-preserving redraws
- **Status:** 💡 Proposed
- **Priority:** 🟢 P3 - Low
- As an accessibility-minded user
- I want screen-write redrawing to preserve color contrast and zebra/background choices and to re-validate contrast after any automatic adjustments
- So that colors remain legible after mode switches or terminal resize; include a fallback to disable colorized redraw if contrast rules fail.

### RQMD-UI-008: Terminal resize handling
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
- As a rqmd user when the terminal is resized
- I want rqmd to handle SIGWINCH gracefully and reflow the current view into the new dimensions without losing selection state or corrupting the scrollback buffer.

### RQMD-UI-009: Performance targets and heuristics
- **Status:** 💡 Proposed
- **Priority:** 🟢 P3 - Low
- As a rqmd maintainer
- I want the entire rqmd interactive app (startup, first interactive paint, file/requirement/status menus, filtered walks, paging, and redraws) to stay snappy, with a target of <=50ms and an acceptable upper bound of <=60ms on typical modern terminals for menus under 80 rows
- So that interactive latency remains low and perceived snappiness is preserved.
- So that startup regressions are visible early and can block adoption of heavier UI layers unless they stay within the same budget.
- So that this requirement acts as the single latency budget source for interactive mode and other domains reference it rather than redefining thresholds.
- So that renderer-mode switching is protected by anti-thrashing rules (hysteresis plus minimum dwell time) and does not oscillate at threshold boundaries.
- So that the system uses smoothed timing windows (for example rolling median/p95 over recent redraws) rather than one-frame spikes when deciding mode changes.
- So that at most one auto-mode transition can occur within a bounded cooldown window (for example 2-5 seconds) unless explicitly overridden by user input.
- So that when a mode transition occurs, a brief transition notice can be emitted only in verbose mode and never floods the normal interaction surface.
- So that when redraw or startup timing exceeds 60ms consistently, the renderer falls back to coarser updates and emits diagnostics in verbose mode.

### RQMD-UI-010: Testing and CI expectations
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
- As a rqmd QA engineer
- I want unit tests for the rendering diff engine and integration tests that exercise both TTY and non-TTY paths
- So that screen-write behavior is validated across supported terminal types and the fallback mode remains covered in CI.

### RQMD-UI-011: Domain-level body sections for narrative notes
- **Status:** 🗑️ Deprecated
- **Priority:** 🟢 P3 - Low
- **Deprecated:** Superseded by RQMD-CORE-019 so domain-body parsing/preservation remains a single core-engine contract, with UI domains depending on that shared model.
- As a rqmd author maintaining requirement domains
- I want each domain markdown file to support an explicit optional domain-level body section (for notes like design rationale, implementation guidance, and migration details)
- So that long-form notes do not need to be embedded into individual requirement entries where they create noise and drift.
- So that rqmd parsing, normalization, and summary updates preserve domain-body content exactly and never treat it as requirement content.
- So that domain-body content can be optionally included in machine-readable exports behind an explicit flag, and excluded by default for compact automation payloads.

### Implementation notes
- Use ANSI CSI sequences for cursor movement and region clearing (e.g., `ESC[H`, `ESC[J`, `ESC[<n>E/F`), guarded by capability checks.
- Provide a single `Renderer` abstraction with two strategies: `ScreenWriteRenderer` and `AppendRenderer` (existing behavior). Wire selection via config/flag and TTY checks.
- Start with a pragmatic approach: full clear + re-render as the default, then optimize with row-diffing and region updates once stable.
- Hybrid direction: keep Click as the CLI/automation surface and treat any future Textual integration as optional and additive.
- Latency guardrail: keep Textual disabled by default unless measured startup/render latency remains within the screen-write performance targets and no regressions are observed.
- Preserve scrollback by avoiding destructive terminal sequences when running under `tmux` or when the user requests maximum scrollback retention.
- Ensure non-blocking and cancelable redraws so UI keys remain responsive during heavy re-renders.

### Backwards compatibility and migration
- Default to enabling `screen_write` only when stdout is a TTY and common capability checks succeed.
- Document the new flag and config option in the README and `docs/requirements/interactive-ux.md` with guidance on when to disable for CI or remote logging.

### Requirements
- `--screen-write` flag exists and toggles the renderer.
- Interactive flows use full-screen redraws by default on capable TTYs and preserve selection across page changes.
- Startup, first-paint, and redraw timing are measured in tests/benchmarks for representative interactive workflows, with <=50ms as the target and <=60ms as the maximum acceptable bound before fallback/mitigation logic applies.
- If TTY capability checks fail, the tool falls back to previous scrolling output and prints a brief notice when verbose logging is enabled.
- Unit and integration tests cover both renderer implementations and SIGWINCH handling.
- Auto renderer fallback does not oscillate near thresholds: hysteresis, smoothing, and cooldown behaviors are covered by tests.
- Domain-level body content is preserved verbatim across rqmd runs and is never counted as requirement text.
