# Priority Requirement

Scope: add a first-class `Priority` field to requirement entries, integrate priority into interactive and non-interactive flows, and allow priority-aware sorting and summaries.

<!-- acceptance-status-summary:start -->
Summary: 1💡 2🔧 9✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-PRIORITY-001: First-class priority field
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when a requirement block is present
- I want rqmd to parse it
- So that the parser recognizes an optional `- **Priority:** <label>` line adjacent to the status line
- So that the priority is stored as part of the requirement metadata alongside `status`, `id`, and `title`.

### RQMD-PRIORITY-002: Priority normalization and allowed values
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when different teams may use different priority vocabularies
- I want the tool to read and write priorities
- So that a canonical default set is available (e.g., `P0`,`P1`,`P2`,`P3` or `High`,`Med`,`Low`) and project-level overrides are supported via `.reqmd/statuses.yml` or a new `.reqmd/priorities.yml`
- So that normalization maps common aliases and case variants to canonical labels.

### RQMD-PRIORITY-003: Set status/priority combined UI
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when interactive status menus exist
- I want to open the status menu for a requirement
- So that the menu is extended to allow setting both `Status` and `Priority` without leaving the panel
- So that a single toggle key (e.g., `t`) switches the panel focus between `Status` and `Priority` entry modes
- So that the footer legend reflects the current target (`setting: status` or `setting: priority`).

### RQMD-PRIORITY-004: `--focus-priority` startup flag
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when users prefer to edit priorities more often than statuses in some workflows
- I want to provide `--focus-priority` at startup
- So that interactive entry panels default to `Priority` focus instead of `Status` focus
- So that the CLI supports `--update-priority ID=PRIORITY` analogously to `--update` for statuses.

### RQMD-PRIORITY-005: Persistence and summary integration
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when files may include the Priority line
- I want to generate summary/roll-up blocks
- So that priority-aware aggregates can be optionally included (e.g., counts by priority per file)
- So that the inline summary block format supports optional display of priority buckets when `--priority-rollup` is requested.

### RQMD-PRIORITY-006: Sorting and filters using priority
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when priority is now a first-class field
- I want sorting or filtering in interactive or non-interactive flows
- So that `priority` is available as a sortable/filterable column and integrates with `s` cycling and `d` direction toggles
- So that default column-cycle order prefers filesystem/name, then priority, then status, then roll-up counts.

### RQMD-PRIORITY-007: Validation and migration
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when existing repositories may not include priority lines
- I want the parser to encounter missing priorities
- So that it treats them as `unset` and does not break parsing
- So that a migration mode (for example `rqmd --seed-priorities`) can populate default priorities (e.g., unset or `P3`) and update files idempotently.

### RQMD-PRIORITY-008: Undo and history semantics
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As a rqmd user when priority edits are recorded
- I want to make or undo priority changes
- So that the undo/history subsystem treats priority changes as first-class operations (atomic with status changes when performed together) and records them in history entries.

### RQMD-PRIORITY-009: Automation and batch updates
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when automation workflows
- I want to apply bulk priority updates (via `--update-priority` or a file)
- So that the tool applies updates deterministically and emits machine-readable summaries showing changed files and counts.

### RQMD-PRIORITY-010: Tests and documentation
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when the increased surface area
- I want to implement priority features
- So that unit tests cover parsing, normalization, UI toggle behavior, sorting integration, and migration; documentation and examples are added to README and examples in `.reqmd/`.

### RQMD-PRIORITY-011: Project-customizable priority catalog schema
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when projects have domain-specific priority terminology
- I want priority definitions to be configurable per project similarly to status definitions
- So that each priority entry supports a custom display name, shortcode, and emoji (for example `{"name": "Critical", "shortcode": "C", "emoji": "🔥"}`)
- So that parsing, normalization, rendering, sorting labels, and JSON outputs all use the configured priority catalog consistently
- So that defaults remain available when no project override is present.

### RQMD-PRIORITY-012: Domain and sub-domain priority metadata
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
- As a rqmd user when planning work at architecture or stream level
- I want optional priority metadata at domain and sub-domain scope
- So that a domain file can declare an overall domain priority and optional per-H2 sub-domain priorities
- So that requirement-level priority remains authoritative for per-item workflows while domain/sub-domain priorities support planning and roll-up views
- So that missing domain/sub-domain priorities are treated as unset and never block existing parsing or mutation behavior
- So that JSON outputs include these fields when present, with stable null/absent behavior when not set.
