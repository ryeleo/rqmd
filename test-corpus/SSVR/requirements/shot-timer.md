# Shot Timer Acceptance Criteria

Scope: string timing contract, timer start/stop triggers, display behavior, per-string precision, and multi-string handling within a stage.

<!-- acceptance-status-summary:start -->
Summary: 10💡 2🔧 0💻 0🎮 2✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->


## Timer Start Contract

### AC-TIMER-START-001: Timer starts on ready-spot departure
- **Status:** 💡 Proposed
- Given the player is at the ready spot and the string is armed
- When the player's firearm movement exceeds the departure threshold (position or rotation)
- Then the string timer starts immediately
- And the start event is captured as a split at `0.0`.

> **See also:** [AC-REPLAY-CAPTURE-006](string-replays.md#ac-replay-capture-006-ready-spot-departure-captures-reaction-onset) — Ready-spot departure keyframe.

### AC-TIMER-START-002: Audible start signal precedes timer window
- **Status:** 💡 Proposed
- Given the player is at the ready spot and the stage is armed
- When the ready-spot beep/signal fires
- Then the departure threshold becomes active at that moment
- And any movement before the signal does not start the timer.

### AC-TIMER-START-003: False-start is detected and reported
- **Status:** 💡 Proposed
- Given the player moves before the audible start signal
- When pre-signal departure is detected
- Then the string is marked as a false-start
- And the event is logged in replay/telemetry.


## Timer Stop Contract

### AC-TIMER-STOP-001: Timer stops on stop-plate hit
- **Status:** 🔧 Implemented
- Given the timer is running during a live string
- When the stop plate is successfully struck
- Then the timer stops immediately at the moment of hit resolution
- And the final string time is recorded to millisecond precision.

> **See also:** [AC-STEELTARGET-TYPE-004](steel-target.md#ac-steeltarget-type-004-stop-plate-designation) — Stop Plate designation.

### AC-TIMER-STOP-002: Timer stop is deterministic and replay-aligned
- **Status:** 💡 Proposed
- Given a string is replayed from recorded data
- When the stop-plate hit keyframe is reached
- Then the reconstructed stop time matches the original stop time to millisecond precision
- And timing does not drift with playback speed or frame rate.

### AC-TIMER-STOP-003: Timer does not stop on penalty or miss
- **Status:** 🔧 Implemented
- Given the player misses a target or accrues a penalty
- When penalty is scored
- Then the timer continues running
- And only the stop-plate hit terminates the string.


## Display Behavior

### AC-TIMER-DISPLAY-001: Timer displays elapsed time in real-time
- **Status:** ✅ Done
- Given a string is in progress
- When each frame renders
- Then the LED timer display shows the current elapsed time in seconds with two decimal places.

### AC-TIMER-DISPLAY-002: Display freezes on string completion
- **Status:** ✅ Done
- Given the string has just ended via stop-plate hit
- When the timer display updates after string completion
- Then the displayed time freezes at the final recorded string time
- And does not continue incrementing after string end.

### AC-TIMER-DISPLAY-003: Display resets between strings
- **Status:** 💡 Proposed
- Given the player completes one string and the stage arms for the next
- When the new string arms
- Then the timer display clears or resets to `0.00`
- And no residual time from the prior string persists on screen.

### AC-TIMER-DISPLAY-004: Slow-motion does not distort displayed timer
- **Status:** 💡 Proposed
- Given slow-motion mode is enabled via the pause menu
- When the timer is running during slow-motion
- Then the displayed time represents actual real-world elapsed time
- And the timer is not affected by slow-motion time scaling.

> **See also:** [AC-PM-SLOWMO-001](pause-menu.md#ac-pm-slowmo-001-slow-motion-toggle-exists) — Slow Motion toggle.


## Precision And Accuracy

### AC-TIMER-PRECISION-001: Timer precision is at minimum milliseconds
- **Status:** 💡 Proposed
- Given string timing is used for scoring and leaderboard comparisons
- When string time is recorded
- Then precision is at least 1 millisecond (0.001s) to resolve close competition results.

### AC-TIMER-PRECISION-002: Timer is independent of frame rate
- **Status:** 💡 Proposed
- Given the game may run at variable frame rates
- When timer values are computed
- Then timing is based on actual elapsed real-world time (unscaled or physics time)
- And dropped frames do not cause timer measurement drift.


## Multi-String Stage Handling

### AC-TIMER-STRING-001: Each string produces an independent time record
- **Status:** 💡 Proposed
- Given a stage allows multiple strings (up to five)
- When each string completes
- Then each string's time is stored as an independent record in the scorecard
- And earlier string times are not overwritten by later strings.

> **See also:** [AC-SCORECARD-VIEW-001](scorecards.md#ac-scorecard-view-001-scorecard-panel-shows-up-to-five-strings) — Scorecard shows up to five strings.

### AC-TIMER-STRING-002: String count is tracked per stage attempt
- **Status:** 💡 Proposed
- Given a player completes strings in sequence for a stage
- When strings are recorded
- Then the stage tracks which string index is active (1–5)
- And string index is preserved in replay and scorecard data.
