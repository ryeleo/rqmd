# Aim-Adjust Stage Acceptance Criteria

Scope: ephemeral firearm calibration stages, playable/scorable aim-adjust modes, and easter-egg stage behavior.

<!-- acceptance-status-summary:start -->
Summary: 11💡 0🔧 0💻 0🎮 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

## Stage Behavior

### AC-AIMADJUST-STAGE-001: Ephemeral stage generation
- **Status:** 💡 Proposed
- Given a player enters Adjust Aim mode from the pause menu
- When the temporary calibration bay is loaded
- Then the stage is generated as a temporary, in-memory-only instance
- And is discarded when Adjust Aim mode exits (not persisted to disk).

### AC-AIMADJUST-STAGE-002: Playable stage layout
- **Status:** 💡 Proposed
- Given the aim-adjust stage is active
- When the player views the bay
- Then the layout is a functional shooting stage with targets at multiple distances and heights
- And all targets are shootable with standard firearm mechanics (ballistics, zeroing).
- And telemetry and scores are recorded like a normal

### AC-AIMADJUST-STAGE-003: Stage reset on exit
- **Status:** 💡 Proposed
- Given a player is in Adjust Aim mode
- When they exit back to the pause menu
- Then the temporary stage instance is destroyed
- And all state changes (target hits, shots fired) are discarded.

## Scoring and Feedback

### AC-AIMADJUST-SCORE-001: Shot tracking during calibration
- **Status:** 💡 Proposed
- **Priority:** Low
- Given the player fires shots during an Adjust Aim session
- When shots are resolved against targets
- Then each shot is logged for immediate ballistic feedback (hit position, offset from aim point)
- And feedback is displayed live on the stage LED or HUD.

### AC-AIMADJUST-SCORE-002: Provisional scoring (optional)
- **Status:** 💡 Proposed
- Given the Adjust Aim stage is playable with real targets
- When the player completes the session
- Then basic scoring may be calculated for feedback purposes
- And provisional scores are not recorded to permanent leaderboards (easter egg content).

## Calibration Workflow

### AC-AIMADJUST-CAL-001: Firearm adjustment during session
- **Status:** 💡 Proposed
- Given the player is in Adjust Aim mode
- When they perform aim-hold calibration adjustments (pitch, roll, offset tweaks)
- Then adjustments are applied immediately to firearm state
- And subsequent shots reflect the new calibration without requiring mode restart.

### AC-AIMADJUST-CAL-002: Calibration data preservation
- **Status:** 💡 Proposed
- Given calibration adjustments are made during an Adjust Aim session
- When the player exits back to gameplay
- Then calibration state is written back to the firearm controller
- And adjustments persist in subsequent game sessions.

> **See also:** [Firearm – AC-FIREARM-ORIGIN-002](firearm.md#ac-firearm-origin-002-red-dot-trust-requirement) — red-dot trust must hold after calibration changes.  
> **See also:** [Save System – AC-SAVE-WORLD-004](save-system.md#ac-save-world-004-firearm-calibration-persists-across-sessions) — calibration persisted to save slot.

### AC-AIMADJUST-CAL-003: Cancellation option
- **Status:** 💡 Proposed
- Given a player has made adjustments in Adjust Aim mode
- When they press the cancel/return action
- Then adjustments are offered for confirmation before commitment
- And users may revert to pre-session calibration if desired.

## Integration with Pause Menu

### AC-AIMADJUST-INTEGRATE-001: Pause menu entry point
- **Status:** 💡 Proposed
- Given the pause menu is visible during gameplay
- When the player selects Adjust Aim
- Then the pause menu hides
- And the temporary calibration stage appears centered and ready for interaction.

> **See also:** [Pause Menu – AC-PM-AIM-001](pause-menu.md#ac-pm-aim-001-entering-adjust-aim-opens-temporary-calibration-bay) — pause-menu side of the entry contract.

### AC-AIMADJUST-INTEGRATE-002: Return-to-gameplay path
- **Status:** 💡 Proposed
- Given the player is in Adjust Aim mode
- When they activate return-home or confirm adjustments
- Then the temporary stage is closed
- And the player is returned to their latest recorded gameplay location before or during the transition into Adjust Aim
- And that return location should come from the same teleport-history or undo-stack mechanism used for gameplay position restoration when available
- And the restored return point preserves the player's facing, bay context, and immediate gameplay continuity rather than sending them to a fixed home position.

> **See also:** [Teleport Undo/Redo – AC-TELEPORT-HISTORY-001](teleport-undo-redo.md#ac-teleport-history-001-teleport-position-stack-contract) — return-location stack contract.
> **See also:** [Teleport Undo/Redo – AC-TELEPORT-HISTORY-003](teleport-undo-redo.md#ac-teleport-history-003-teleport-position-restoration-precision) — precision requirements for restored position and facing.

### AC-AIMADJUST-INTEGRATE-003: No state pollution
- **Status:** 💡 Proposed
- Given a player is in an active stage with targets and scores
- When they enter Adjust Aim mode
- Then the active stage is paused and hidden (not modified)
- And no shots or adjustments made in Adjust Aim are reflected in the paused stage's score or state.
