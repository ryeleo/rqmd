# Priority Acceptance Criteria

Scope: add a first-class `Priority` field to requirement criteria, integrate priority into interactive and non-interactive flows, and allow priority-aware sorting and summaries.

<!-- acceptance-status-summary:start -->
Summary: 6💡 0🔧 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-PRIORITY-001: First-class priority field
- **Status:** 💡 Proposed
- Given a requirement criterion block
- When parsed by rqmd
- Then the parser recognizes an optional `- **Priority:** <label>` line adjacent to the status line
- And the priority is stored as part of the criterion metadata alongside `status`, `id`, and `title`.

### RQMD-PRIORITY-002: Priority normalization and allowed values
- **Status:** 💡 Proposed
- Given different teams may use different priority vocabularies
- When the tool reads or writes priorities
- Then a canonical default set is available (e.g., `P0`,`P1`,`P2`,`P3` or `High`,`Med`,`Low`) and project-level overrides are supported via `.reqmd/status-catalog.yaml` or a new `.reqmd/priority-catalog.yaml`
- And normalization maps common aliases and case variants to canonical labels.

### RQMD-PRIORITY-003: Set status/priority combined UI
- **Status:** 💡 Proposed
- Given interactive status menus exist
- When a user opens the status menu for a criterion
- Then the menu is extended to allow setting both `Status` and `Priority` without leaving the panel
- And a single toggle key (e.g., `t`) switches the panel focus between `Status` and `Priority` entry modes
- And the footer legend reflects the current target (`setting: status` or `setting: priority`).

### RQMD-PRIORITY-004: `--priority-mode` startup flag
- **Status:** 💡 Proposed
- Given users prefer to edit priorities more often than statuses in some workflows
- When `--priority-mode` is supplied at startup
- Then interactive entry panels default to `Priority` focus instead of `Status` focus
- And the CLI supports `--set-priority ID=PRIORITY` analogously to `--set` for statuses.

### RQMD-PRIORITY-005: Persistence and summary integration
- **Status:** 💡 Proposed
- Given files may include the Priority line
- When summary/roll-up blocks are generated
- Then priority-aware aggregates can be optionally included (e.g., counts by priority per file)
- And the inline summary block format supports optional display of priority buckets when `--show-priority-summary` is requested.

### RQMD-PRIORITY-006: Sorting and filters using priority
- **Status:** 💡 Proposed
- Given priority is now a first-class field
- When sorting or filtering in interactive or non-interactive flows
- Then `priority` is available as a sortable/filterable column and integrates with `s` cycling and `d` direction toggles
- And default column-cycle order prefers filesystem/name, then priority, then status, then roll-up counts.

### RQMD-PRIORITY-007: Validation and migration
- **Status:** 💡 Proposed
- Given existing repositories may not include priority lines
- When the new parser encounters missing priorities
- Then it treats them as `unset` and does not break parsing
- And a migration command `rqmd migrate --init-priorities` can populate default priorities (e.g., unset or `P3`) and update files idempotently.

### RQMD-PRIORITY-008: Undo and history semantics
- **Status:** 💡 Proposed
- Given priority edits are recorded
- When changes to priority are made or undone
- Then the undo/history subsystem treats priority changes as first-class operations (atomic with status changes when performed together) and records them in history entries.

### RQMD-PRIORITY-009: Automation and batch updates
- **Status:** 💡 Proposed
- Given automation workflows
- When bulk priority updates are applied (via `--set-priority` or a file)
- Then the tool applies updates deterministically and emits machine-readable summaries showing changed files and counts.

### RQMD-PRIORITY-010: Tests and documentation
- **Status:** 💡 Proposed
- Given the increased surface area
- When implementing priority features
- Then unit tests cover parsing, normalization, UI toggle behavior, sorting integration, and migration; documentation and examples are added to README and examples in `.reqmd/`.
