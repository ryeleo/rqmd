# Undo / History Requirement

Scope: full undo/redo semantics, persistent history across restarts/crashes, branching and "lost changes" recovery, UI affordances, and storage/retention policies.

<!-- acceptance-status-summary:start -->
Summary: 6💡 5🔧 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-UNDO-001: Full undo/redo semantics
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when a user makes sequential edits (status changes, reason edits, file updates)
- I want to request `undo`
- So that the most recent change is reverted and the UI updates to reflect the prior state
- So that `redo` reapplies the reverted change in order when requested
- So that compound user actions (multi-file or multi-field updates performed by one command) are treated atomically for undo/redo.

### RQMD-UNDO-002: Persistent history across restarts and crashes
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when the application exits normally or crashes unexpectedly
- I want to restart rqmd
- So that the full undo/redo history up to the last acknowledged write is available for inspection and replay
- So that no acknowledged write is lost due to process exit or crash (durability is guaranteed for committed operations).

### RQMD-UNDO-003: Branching history and "lost changes" visibility
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when a user performs `undo` multiple times and then issues a new change (creating a divergent history)
- I want the divergence to occur
- So that the system preserves the prior undone sequence as an alternate branch (not permanently discarded)
- So that the UI surfaces the existence of the alternate branch and offers the user options: (a) keep divergent branch as a named branch, (b) replay/apply the branch onto the new HEAD, (c) permanently discard the branch after explicit confirmation
- So that the system supports reapplying or cherry-picking individual changes from alternate branches.

### RQMD-UNDO-004: Interactive reconfirmation when rewriting history
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when the user attempts to perform an action that would lose reachable history (e.g., pruning, garbage-collecting alternate branches, or compacting history beyond retention)
- I want such an action to require explicit confirmation in interactive mode
- So that rqmd prompts the user with a concise summary of what will be lost and requires explicit confirmation before proceeding.

### RQMD-UNDO-005: Storage backend and crash-safety
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when durability and history expressiveness are required
- I want to implement undo stack storage
- So that rqmd uses a single hidden local git repository as the canonical history backend, initialized as `rqmd-history` under `.rqmd/history/`.
- So that this `rqmd-history` repository is wrapped and managed by rqmd itself, and is not intended to be edited manually by users or shared as a remote collaboration repository.
- So that this history backend remains local-only by default (no implicit remotes, push, fetch, or network synchronization).
- So that the backend provides atomic commits, durable fsync semantics for acknowledged writes, and a safe compact/garbage-collection path that preserves user-confirmable alternate branches.

### RQMD-UNDO-006: Metadata, auditability, and provenance
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when teams need traceability for changes
- I want to record history entries
- So that each entry includes timestamp, actor (user or automated), command context, affected file paths, file diffs or delta payloads, and optional human-supplied reason text
- So that each entry includes a stable `rqmd-history` commit identifier (and branch/ref context when applicable) to allow deterministic cross-referencing between undo, history, and audit views.
- So that the UI and `--verify-summaries` mode can render a human-readable history timeline showing provenance and diffs.

### RQMD-UNDO-007: UI affordances and commands
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when working in interactive and non-interactive modes
- I want to expose history controls
- So that rqmd provides:
  - `undo` and `redo` commands / keys
  - `history` listing with paging that shows branches, commits, and diffs
  - `branch` and `checkout` primitives for working with alternate histories
  - `replay` and `cherry-pick` for applying past changes to current head
  - safe `gc`/`prune` commands that require confirmation
- So that interactive prompts clearly explain consequences and offer to save named snapshots before destructive operations.

### RQMD-UNDO-008: Size, retention, and compaction policy
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when history can grow indefinitely
- I want storage to grow beyond configured thresholds
- So that rqmd supports configurable retention policies: retain-last-N, retain-by-age, and retain-by-size
- So that compaction/packing can merge idempotent/delta entries to reduce storage while preserving user-visible undo semantics
- So that defaults are conservative (retain 90 days or last 1000 entries) with project and user overrides.

### RQMD-UNDO-009: Programmatic API and automation
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when CI/automation users may need to inspect or replay history non-interactively
- I want automation to invoke history APIs
- So that a machine-friendly interface is available (JSON output, programmatic commands) to list entries, export patches, and apply or revert specific entries.

### RQMD-UNDO-010: Tests and verification
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when the complexity of persistent undo and branching
- I want to implement the system
- So that an extensive test matrix covers unit tests for journal/git operations, integration tests for crash recovery (simulating abrupt termination), and UX tests for branch/replay flows
- So that test fixtures include representative multi-file edits, branching and replay scenarios, and compaction behavior verification.

### RQMD-UNDO-011: Unified undo and audit capture
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when traceability and recovery guarantees are required
- I want every rqmd write operation to be recorded in the same `rqmd-history` backend used for undo/redo
- So that undo/history and audit logging cannot drift or contradict each other.
- So that all changes made by rqmd are captured with a navigable git-style timeline that rqmd can render in user-facing history and audit views.
