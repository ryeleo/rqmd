# Undo / History Requirement

Scope: full undo/redo semantics, persistent history across restarts/crashes, branching and "lost changes" recovery, UI affordances, and storage/retention policies.

<!-- acceptance-status-summary:start -->
Summary: 10💡 0🔧 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-UNDO-001: Full undo/redo semantics
- **Status:** 💡 Proposed
- Given a user makes sequential edits (status changes, reason edits, file updates)
- When the user requests `undo`
- Then the most recent change is reverted and the UI updates to reflect the prior state
- And `redo` reapplies the reverted change in order when requested
- And compound user actions (multi-file or multi-field updates performed by one command) are treated atomically for undo/redo.

### RQMD-UNDO-002: Persistent history across restarts and crashes
- **Status:** 💡 Proposed
- Given the application exits normally or crashes unexpectedly
- When the user restarts rqmd
- Then the full undo/redo history up to the last acknowledged write is available for inspection and replay
- And no acknowledged write is lost due to process exit or crash (durability is guaranteed for committed operations).

### RQMD-UNDO-003: Branching history and "lost changes" visibility
- **Status:** 💡 Proposed
- Given a user performs `undo` multiple times and then issues a new change (creating a divergent history)
- When the divergence occurs
- Then the system preserves the prior undone sequence as an alternate branch (not permanently discarded)
- And the UI surfaces the existence of the alternate branch and offers the user options: (a) keep divergent branch as a named branch, (b) replay/apply the branch onto the new HEAD, (c) permanently discard the branch after explicit confirmation
- And the system supports reapplying or cherry-picking individual changes from alternate branches.

### RQMD-UNDO-004: Interactive reconfirmation when rewriting history
- **Status:** 💡 Proposed
- Given the user attempts to perform an action that would lose reachable history (e.g., pruning, garbage-collecting alternate branches, or compacting history beyond retention)
- When such an action is requested in interactive mode
- Then rqmd prompts the user with a concise summary of what will be lost and requires explicit confirmation before proceeding.

### RQMD-UNDO-005: Storage backend and crash-safety
- **Status:** 💡 Proposed
- Given the need for durability and history expressiveness
- When implementing the undo stack storage
- Then implementations may choose from two recommended models:
  - Append-only journal (JSONL or WAL) persisted to disk with atomic rename/fsync semantics and an optional compact/pack step
  - Lightweight embedded git repository (recommended for maximum robustness and transparency) initialized in `.rqmd/history/` to leverage commit/branch semantics and existing tools
- And whichever backend is chosen, the system must provide atomic commits, durable fsync semantics for acknowledged writes, and a safe compact/garbage-collection path that preserves user-confirmable alternate branches.

### RQMD-UNDO-006: Metadata, auditability, and provenance
- **Status:** 💡 Proposed
- Given teams need traceability for changes
- When recording history entries
- Then each entry includes timestamp, actor (user or automated), command context, affected file paths, file diffs or delta payloads, and optional human-supplied reason text
- And the UI and `--check` mode can render a human-readable history timeline showing provenance and diffs.

### RQMD-UNDO-007: UI affordances and commands
- **Status:** 💡 Proposed
- Given interactive and non-interactive usage modes
- When exposing history controls
- Then rqmd provides:
  - `undo` and `redo` commands / keys
  - `history` listing with paging that shows branches, commits, and diffs
  - `branch` and `checkout` primitives for working with alternate histories
  - `replay` and `cherry-pick` for applying past changes to current head
  - safe `gc`/`prune` commands that require confirmation
- And interactive prompts clearly explain consequences and offer to save named snapshots before destructive operations.

### RQMD-UNDO-008: Size, retention, and compaction policy
- **Status:** 💡 Proposed
- Given history can grow indefinitely
- When storage grows beyond configured thresholds
- Then rqmd supports configurable retention policies: retain-last-N, retain-by-age, and retain-by-size
- And compaction/packing can merge idempotent/delta entries to reduce storage while preserving user-visible undo semantics
- And defaults are conservative (retain 90 days or last 1000 entries) with project and user overrides.

### RQMD-UNDO-009: Programmatic API and automation
- **Status:** 💡 Proposed
- Given CI/automation users may need to inspect or replay history non-interactively
- When automation invokes history APIs
- Then a machine-friendly interface is available (JSON output, programmatic commands) to list entries, export patches, and apply or revert specific entries.

### RQMD-UNDO-010: Tests and verification
- **Status:** 💡 Proposed
- Given the complexity of persistent undo and branching
- When implementing the system
- Then an extensive test matrix covers unit tests for journal/git operations, integration tests for crash recovery (simulating abrupt termination), and UX tests for branch/replay flows
- And test fixtures include representative multi-file edits, branching and replay scenarios, and compaction behavior verification.
