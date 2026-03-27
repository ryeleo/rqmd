# Leaderboards Acceptance Criteria

Scope: per-stage leaderboard data model, pause-menu leaderboard panel behavior, and leaderboard-to-scorecard drilldown flow.

<!-- acceptance-status-summary:start -->
Summary: 5💡 4🔧 0💻 0🎮 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

## Stage-Scoped Leaderboard Model

### AC-LEADERBOARD-DATA-001: Leaderboard is stage-scoped
- **Status:** 🔧 Implemented
- Given a leaderboard is shown for gameplay review
- When the player is in a specific stage context
- Then leaderboard rows are scoped to that stage
- And rows from unrelated stages are not mixed into that view.

### AC-LEADERBOARD-DATA-002: Basic per-stage row fields
- **Status:** 💡 Proposed
- Given leaderboard rows are rendered for a stage
- When each row is displayed
- Then each row includes at minimum player label, total time, misses, and make-up shots
- And rows are presented in rank order by best final time.

### AC-LEADERBOARD-DATA-003: Replay-linked row identity
- **Status:** 💡 Proposed
- Given leaderboard rows are persisted or queried
- When row identity is evaluated
- Then each row remains linked to parent replay identity (`replayId`)
- And row-level drilldown can resolve back to replay and scorecard detail.

> **See also:** [String Replays – AC-REPLAY-SCORECARD-003](string-replays.md#ac-replay-scorecard-003-leaderboard-indexing-may-denormalize-but-remains-replay-linked) — leaderboard rows stay replay-linked even when denormalized.

## Pause Menu Panel

### AC-LEADERBOARD-PANEL-001: Leaderboard appears as pause-menu panel
- **Status:** 🔧 Implemented
- Given the player opens pause menu while in a shooter box
- When leaderboard content is available
- Then a leaderboard panel is shown as an extra panel in pause-menu review UI
- And it stays scoped to the active stage.

### AC-LEADERBOARD-PANEL-002: Pause panel supports return to prior panel
- **Status:** 💡 Proposed
- Given the player opens leaderboard panel from pause menu
- When they close leaderboard view
- Then pause menu returns to the prior panel context
- And stage review state is preserved.

## Interaction And Drilldown

### AC-LEADERBOARD-INTERACT-001: Shot-driven row selection
- **Status:** 🔧 Implemented
- Given leaderboard panel rows are visible
- When the player shoots a row once
- Then that row enters selected state
- And when shot again, detailed scorecard view opens for that row.

### AC-LEADERBOARD-INTERACT-002: Detailed scorecard close flow
- **Status:** 🔧 Implemented
- Given a detailed scorecard panel is open from leaderboard drilldown
- When the player shoots the panel once
- Then close is armed
- And when they shoot again, the detailed panel closes.

## Ranking And Stability

### AC-LEADERBOARD-RANK-001: Deterministic ordering for ties
- **Status:** 💡 Proposed
- Given two or more leaderboard rows have equal final time
- When rows are ranked
- Then tie-break ordering is deterministic (for example by misses, then make-up shots, then replay timestamp)
- And repeated loads show stable ordering.

### AC-LEADERBOARD-RANK-002: Local/offline fallback behavior
- **Status:** 💡 Proposed
- Given telemetry/online leaderboard services are unavailable
- When leaderboard panel is opened
- Then a local stage-scoped leaderboard fallback is shown if local data exists
- And the panel communicates that remote sync state is offline.
