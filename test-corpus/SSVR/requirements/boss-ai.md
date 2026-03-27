# Boss AI Acceptance Criteria

Scope: boss shooter placement, concurrent duel participation, configurable AI behavior, duel win conditions, feedback displays, and replay-backed boss behavior.

<!-- acceptance-status-summary:start -->
Summary: 17💡 0🔧 0💻 0🎮 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->


## Boss Placement And Presence

### AC-BOSS-SPAWN-001: Boss occupies adjacent shooter box
- **Status:** 💡 Proposed
- Given a duel stage is active
- When the stage is constructed
- Then the boss occupies a shooter box 3 ft to the right of the player's shooter box
- And the boss's box, LED display, and scorecard mirror the player layout.

> **See also:** [AC-ROGUE-DUEL-001](rogue.md#ac-rogue-duel-001-concurrent-player-and-boss-participation) — Duel participation contract.

### AC-BOSS-SPAWN-002: Boss has independent LED display and scorecard
- **Status:** 💡 Proposed
- Given the boss is active in a duel stage
- When the bay is constructed
- Then the boss has its own LED timer display and scorecard visible to the player
- And those elements are positioned symmetrically opposite the player's displays.

### AC-BOSS-SPAWN-003: Center duel display shows per-string outcome
- **Status:** 💡 Proposed
- Given a duel string has just completed
- When string outcomes are evaluated
- Then a third center LED display shows a checkmark when the player wins the string and an X when the boss wins
- And the center display is clearly visible from the player's shooter box.


## Concurrent Duel Behavior

### AC-BOSS-CONCURRENT-001: Player and boss shoot simultaneously
- **Status:** 💡 Proposed
- Given a duel string starts with the audible signal
- When both player and boss respond
- Then both shoot their strings concurrently in real time
- And boss shots are resolved independently of player shots on the shared targets.

### AC-BOSS-CONCURRENT-002: Boss targets the same set of targets as the player
- **Status:** 💡 Proposed
- Given targets are placed in a duel stage
- When the boss engages the stage
- Then boss shots resolve against the same target set as the player
- And the boss can register misses and penalties just like the player.

### AC-BOSS-CONCURRENT-003: Boss stop-plate hit concludes boss string independently
- **Status:** 💡 Proposed
- Given the boss is shooting a duel string
- When the boss hits the stop plate
- Then the boss string time is finalized immediately at that moment
- And the player's timer continues independently until the player hits the stop plate.


## Configurable AI Parameters

### AC-BOSS-AI-PARAM-001: Boss speed to first target is configurable
- **Status:** 💡 Proposed
- Given a boss AI instance is configured
- When the string starts
- Then travel time from start position to first target is driven by the `speedToFirstTarget` parameter.

### AC-BOSS-AI-PARAM-002: Boss between-target movement speed is configurable
- **Status:** 💡 Proposed
- Given a boss AI instance is configured
- When the boss moves between targets
- Then movement speed is driven by the `speedBetweenTargets` parameter
- And jitter magnitude is driven by the `aimJitter` parameter.

### AC-BOSS-AI-PARAM-003: Boss reaction time to missed targets is configurable
- **Status:** 💡 Proposed
- Given the boss misses a target on its firing sequence
- When the miss detection delay elapses
- Then the boss re-engages the missed target according to the `missReactionDelay` parameter
- And it is possible for the boss to hit the stop plate before noticing a miss, creating a penalty.

### AC-BOSS-AI-PARAM-004: Boss target engagement order is configurable
- **Status:** 💡 Proposed
- Given a stage has multiple non-stop targets
- When the boss selects its engagement sequence
- Then sequence is driven by a configurable `engagementOrder` strategy (for example left-to-right, right-to-left, furthest-first, nearest-first, outside-in)
- And the stop plate is never engaged first.

### AC-BOSS-AI-PARAM-005: Boss parameters include RNG fuzz for human-like variation
- **Status:** 💡 Proposed
- Given a boss AI instance runs multiple strings
- When parameters drive movement and aim
- Then configurable random fuzz is applied to speed and jitter values
- And no two consecutive strings are perfectly identical in timing.


## Duel Win Conditions

### AC-BOSS-DUEL-001: String winner is determined by lower string time
- **Status:** 💡 Proposed
- Given both player and boss complete a duel string
- When times are compared
- Then the participant with the lower final time wins that string.

### AC-BOSS-DUEL-002: Match win requires winning three of five strings
- **Status:** 💡 Proposed
- Given a duel match runs up to five strings
- When one participant reaches three string wins
- Then that participant is declared the match winner
- And remaining strings are not played.

### AC-BOSS-DUEL-003: Penalty time is factored into string comparison
- **Status:** 💡 Proposed
- Given either participant accrues penalties during a string
- When string times are compared
- Then penalty time additions are applied before the winner is determined.


## Replay-Backed Boss AI

### AC-BOSS-REPLAY-001: Boss can use a recorded replay as its behavior source
- **Status:** 💡 Proposed
- Given the boss is configured with a pre-recorded gameplay replay
- When the duel string starts
- Then boss movement and shot timing are driven by that replay's keyframes
- And the replay is played back relative to the boss shooter-box origin.

> **See also:** [AC-REPLAY-PLAYBACK-001](string-replays.md#ac-replay-playback-001-playback-fires-only-on-shot-keyframes) — Replay playback fires only on shot keyframes.

### AC-BOSS-REPLAY-002: Replay boss is replay-compatible
- **Status:** 💡 Proposed
- Given a replay is evaluated for boss use
- When required origin-relative metadata is missing
- Then that replay is rejected for boss use rather than producing undefined behavior.

> **See also:** [AC-REPLAY-CAPTURE-002](string-replays.md#ac-replay-capture-002-replay-keyframes-are-origin-relative) — Keyframes must be origin-relative.

### AC-BOSS-REPLAY-003: Boss replay speed is scalable
- **Status:** 💡 Proposed
- Given a replay-backed boss is configured for difficulty scaling
- When difficulty is adjusted via pause menu controls
- Then the replay playback speed is scaled proportionally to adjust boss difficulty
- And the scaled playback results in proportionally scaled shot timing.
