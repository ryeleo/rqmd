# Time Machine Requirement

Scope: branch-aware temporal navigation, historical inspection, detached point-in-time views, replay from past states, and timeline-oriented UX for requirement catalogs.

<!-- acceptance-status-summary:start -->
Summary: 10💡 0🔧 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-TIME-001: Point-in-time catalog browsing
- **Status:** 💡 Proposed
- As a rqmd user when a requirements catalog with recorded history
- I want to select a prior timestamp, revision, or history entry
- So that rqmd can present the full catalog as it existed at that point in time without mutating the current working state
- So that the user can inspect files, requirement statuses, reasons, and summaries exactly as recorded for that historical point.

### RQMD-TIME-002: Branch-aware historical timeline
- **Status:** 💡 Proposed
- As a rqmd user when history may diverge into multiple branches after undo, replay, or alternate edits
- I want rqmd to render timeline history
- So that the timeline shows branch structure explicitly rather than flattening divergent paths into a single linear list
- So that each node identifies parent lineage, branch name or generated label, timestamp, and affected scope.

### RQMD-TIME-003: Detached historical view mode
- **Status:** 💡 Proposed
- As a rqmd user when a user wants to inspect prior state safely
- I want to enter a historical point from the timeline
- So that rqmd opens a detached read-only view rooted at that historical revision
- So that status changes or edits are blocked until the user returns to a writable head or explicitly starts a replay/apply flow.

### RQMD-TIME-004: Historical context and activity inspection
- **Status:** 💡 Proposed
- As a rqmd user when a user is viewing a prior revision
- I want rqmd to render that historical state
- So that the UI shows what changed at that point including changed files, affected requirement IDs, before/after status values, reason text, and actor/context metadata
- So that the user can move backward or forward through neighboring entries while preserving orientation in the same branch.

### RQMD-TIME-005: Compare historical points and branches
- **Status:** 💡 Proposed
- As a rqmd user when users need to understand how the catalog evolved
- I want to select two points in time, two branches, or a branch point and current head
- So that rqmd can render a diff-oriented comparison of summaries, requirement statuses, reasons, and affected documents
- So that the comparison highlights additions, removals, and status transitions in a machine-readable and human-readable form.

### RQMD-TIME-006: Replay and restore from historical points
- **Status:** 💡 Proposed
- As a rqmd user when a user finds a useful historical point
- I want to choose to restore, replay, or cherry-pick from that point
- So that rqmd offers explicit actions to (a) restore the catalog to that exact state, (b) replay subsequent changes from a chosen branch, or (c) cherry-pick selected historical entries onto current head
- So that each action previews the resulting branch topology and file effects before writes occur.

### RQMD-TIME-007: Timeline filters and queryable navigation
- **Status:** 💡 Proposed
- As a rqmd user when long-lived projects may accumulate dense history
- I want to browse the timeline
- So that rqmd supports filters by branch, requirement ID, file path, actor, status transition, date range, and operation type
- So that filtered navigation still preserves branch lineage so users understand where matching events sit in the larger history graph.

### RQMD-TIME-008: Stable historical identifiers and deep links
- **Status:** 💡 Proposed
- As a rqmd user when users may need to share or automate a historical view
- I want rqmd to expose a timeline node or detached historical view
- So that each point-in-time state has a stable identifier that can be referenced in CLI commands, JSON output, and future UI deep links
- So that identifiers remain valid across process restarts unless history has been explicitly pruned with confirmation.

### RQMD-TIME-009: Exportable temporal reports
- **Status:** 💡 Proposed
- As a rqmd user when teams may need audit or review artifacts from historical states
- I want automation to request a historical export
- So that rqmd can emit JSON and text reports for a selected point-in-time state or comparison range including branch metadata, summary totals, and per-requirement status details
- So that exports clearly indicate the selected historical source and whether the view is detached, restored, or current head.

### RQMD-TIME-010: Verification coverage for temporal navigation
- **Status:** 💡 Proposed
- As a rqmd user when time-travel workflows combine persistence, branching, and presentation logic
- I want to implement the time-machine feature set
- So that tests cover branch graph reconstruction, detached historical reads, point-to-point diffs, replay/restore previews, and stable identifier resolution
- So that fixtures include branching histories where multiple timelines touch the same requirement IDs across multiple files.