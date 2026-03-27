# Locomotion Acceptance Criteria

Scope: teleport locomotion, snap-turn, locomotion suppression during strings and pause menus, desktop debug camera, and XR rig stability.

<!-- acceptance-status-summary:start -->
Summary: 14💡 0🔧 0💻 0🎮 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->


## Teleport Locomotion

### AC-LOCO-TELEPORT-001: Player teleports to shooter boxes via gong buttons
- **Status:** 💡 Proposed
- Given a stage has one or more shooter boxes
- When the player shoots a shooter-box teleport gong button
- Then the player is teleported to that shooter box
- And the player is oriented toward the stage targets on arrival.

> **See also:** [AC-MM-INTERACT-002](main-menu.md#ac-mm-interact-002-stage-selection-tap-sequence) — Stage select teleport on third tap.

### AC-LOCO-TELEPORT-002: Teleport ray activation requires controller trigger hold
- **Status:** 💡 Proposed
- Given teleport locomotion is enabled
- When the player holds the teleport ray trigger
- Then a teleport arc is displayed from the controller
- And releasing the trigger while a valid landing zone is targeted executes the teleport.

### AC-LOCO-TELEPORT-003: Teleport ray activation is suppressed during active strings
- **Status:** 💡 Proposed
- Given the player is in an active timed string
- When the player attempts to activate the teleport ray
- Then teleport ray activation is suppressed
- And no teleport occurs while timing is live.

> **See also:** [AC-PM-INPUT-001](pause-menu.md#ac-pm-input-001-locomotion-suppression-while-menu-is-open) — Locomotion suppression while pause menu is open.

### AC-LOCO-TELEPORT-004: Valid teleport landing zones are defined per stage context
- **Status:** 💡 Proposed
- Given the player activates the teleport ray
- When the arc points at a surface
- Then only designated valid landing zones accept teleport targets
- And the arc visually distinguishes valid from invalid zones.


## Snap-Turn

### AC-LOCO-TURN-001: Right thumbstick provides snap-turn in VR mode
- **Status:** 💡 Proposed
- Given the player is in VR mode and snap-turn is enabled
- When the player flicks the right thumbstick left or right
- Then the player's view snaps by the configured turn angle increment
- And snap-turn is the only active turn behavior (smooth-turn is not used by default).

> **See also:** [AC-PM-INPUT-001](pause-menu.md#ac-pm-input-001-locomotion-suppression-while-menu-is-open) — Snap-turn is suppressed while pause menu is open.

### AC-LOCO-TURN-002: Snap-turn angle is configurable
- **Status:** 💡 Proposed
- Given snap-turn is enabled
- When the turn angle is adjusted in settings
- Then snap increments scale to the configured value
- And the setting persists across sessions.

### AC-LOCO-TURN-003: Snap-turn is suppressed during active strings
- **Status:** 💡 Proposed
- Given the player is in an active timed string
- When the player attempts snap-turn input
- Then snap-turn does not execute
- And the turn input is ignored until the string ends.


## Locomotion Suppression

### AC-LOCO-SUPPRESS-001: All locomotion suppressed during active string
- **Status:** 💡 Proposed
- Given a timed string is live
- When the player provides teleport or turn input
- Then both teleport and snap-turn are suppressed for the duration of the string.

### AC-LOCO-SUPPRESS-002: All locomotion suppressed while pause menu is open
- **Status:** 💡 Proposed
- Given the pause menu is open
- When the player provides teleport or turn input
- Then both teleport and snap-turn are suppressed until the pause menu closes.

> **See also:** [AC-PM-INPUT-001](pause-menu.md#ac-pm-input-001-locomotion-suppression-while-menu-is-open) — Pause menu locomotion suppression.


## Desktop Debug Camera

### AC-LOCO-DESKTOP-001: Desktop mode uses first-person mouse-look camera
- **Status:** 💡 Proposed
- Given the game is running in desktop/editor mode without a VR headset
- When the player moves the mouse
- Then the camera orientation follows mouse movement as first-person look
- And left-click fires the firearm.

### AC-LOCO-DESKTOP-002: Desktop camera rig does not interfere with XR tracking
- **Status:** 💡 Proposed
- Given both desktop rig and XR rig systems may exist in a scene
- When the game starts in desktop mode
- Then the desktop camera rig is active and XR rig tracking is disabled or disregarded
- And no tracking guard or XR system conflicts arise.


## XR Rig Stability

### AC-LOCO-XR-001: VR camera floors to tracked floor level
- **Status:** 💡 Proposed
- Given the XR rig is active in VR mode
- When floor-level calibration is complete
- Then the player's view origin is aligned to the tracked floor
- And standing gameplay positions the player at a natural real-world height.

### AC-LOCO-XR-002: Camera tracking guard prevents ownership conflicts
- **Status:** 💡 Proposed
- Given multiple XR tracking setups may exist in a scene
- When the scene initializes
- Then the camera tracking guard ensures only one system holds tracking ownership
- And conflicting tracking behaviors are suppressed.

### AC-LOCO-XR-003: XR rig diagnostics are available for troubleshooting
- **Status:** 💡 Proposed
- Given XR rig anomalies occur (tracking loss, orientation jumps, etc.)
- When diagnostics reporting is enabled
- Then XR rig state and anomalies are logged via the diagnostics reporter
- And log entries include context sufficient to identify tracking issues.
