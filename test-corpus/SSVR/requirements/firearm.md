# Firearm Acceptance Criteria

Scope: firing contract, bullet behavior, visual trace behavior, calibration, and sight trust.

<!-- acceptance-status-summary:start -->
Summary: 2💡 2🔧 0💻 0🎮 7✅ 0⛔ 2🗑️
<!-- acceptance-status-summary:end -->


## Shot And Trigger Contract

### AC-FIREARM-SHOT-001: Trigger reset threshold before next shot
- **Status:** ✅ Done
- Given the player has fired one shot
- When the trigger is not yet released past the reset threshold
- Then another shot cannot fire
- And once the trigger is released past threshold, firing is re-armed.

### AC-FIREARM-SHOT-002: Ready Spot safety during active stage
- **Status:** ✅ Done
- Given a stage is already armed, running, or has partial scorecard progress
- When the player shoots the Ready Spot
- Then the shot is treated as a no-op for stage reset and teleport behavior.

### AC-FIREARM-SHOT-003: Ready Spot shot retries stage after scorecard is complete
- **Status:** 💡 Proposed
- Given the stage scorecard is fully complete (all strings finished)
- **Status:** ✅ Done
- Then the effect is identical to shooting the Retry gong button for the stage
- And a new scorecard is started
- And if the player is already dwelling on the ready spot at the moment of the shot, the shot timer arms and starts immediately on ready-spot departure.

> **See also:** [AC-FIREARM-SHOT-002](#ac-firearm-shot-002-ready-spot-safety-during-active-stage) — no-op behavior while stage is in progress.

## Bullet And Bullet Trace

### AC-FIREARM-BULLET-001: Gameplay shot resolution uses bullet hit logic
- **Status:** ✅ Done
- Given the player fires
- When bullet hit resolution occurs
- Then the gameplay hit result is resolved deterministically for scoring and interactions
- And the visual bullet trace does not alter scoring outcomes.

### AC-FIREARM-BULLET-002: Bullet body debug visibility toggle
- **Status:** 🗑️ Deprecated
**Deprecated:** We don't need this at all anymore.
- Given bullet trace visuals are enabled
- When bullet body debug visibility is toggled on
- Then the bullet body is visible during trace playback for diagnostics
- And when toggled off, only the normal trace presentation is shown.

### AC-FIREARM-BULLET-003: Bullet and bullet trace terminology contract
- **Status:** 🔧 Implemented
- Given gameplay and diagnostics language for shots
- When documenting or exposing runtime labels
- Then the gameplay hit object is referred to as `bullet`
- And the moving visual tracer is referred to as `bullet trace`.

## Ballistic Origin And Sight Trust

### AC-FIREARM-ORIGIN-001: Shared ballistic-origin contract
- **Status:** 🔧 Implemented
- Given supported firearms in the game
- When gameplay bullet origin is configured
- Then bullet emission uses a stable gameplay ballistic-origin contract
- And weapon model muzzle differences do not silently break replay or ghost alignment.

### AC-FIREARM-ORIGIN-002: Red-dot trust requirement
- **Status:** ✅ Done
- Given the red dot appears to be on target
- When a shot is fired under normal gameplay conditions
- Then the bullet result aligns with the red-dot sight picture expectation.

> **See also:** [Aim-Adjust Stage – AC-AIMADJUST-CAL-001](aim-adjust-stage.md#ac-aimadjust-cal-001-firearm-adjustment-during-session) — calibration adjustments that affect red-dot alignment.

### AC-FIREARM-ORIGIN-003: Cosmetic muzzle effects separation
- **Status:** ✅ Done
- Given a firearm has visual muzzle effects
- When muzzle effect transforms differ from gameplay origin
- Then cosmetic visuals may use the weapon-specific muzzle transform
- And gameplay bullet origin remains on the shared ballistic-origin contract unless explicitly redesigned project-wide.

## Reflex Sight

### AC-FIREARM-SIGHT-001: Reflex lens remains transparent
- **Status:** ✅ Done
- Given desktop or VR rendering mode
- When the reflex sight lens is presented
- Then the lens remains fully transparent for aiming visibility.

### AC-FIREARM-SIGHT-002: Lens mesh visibility safety contract
- **Status:** 🗑️ Deprecated
**Deprecated:** Duplicate of AC-FIREARM-SIGHT-001 it seems
- Given runtime reflex lens setup is generated
- When lens rendering is configured
- Then the lens collider remains available for projection behavior
- And opaque lens mesh behavior is not reintroduced.

## Controller Contract

### AC-FIREARM-CTRL-001: Single-controller baseline compatibility
- **Status:** 💡 Proposed
- Given standard gameplay firearm control
- When the player uses either left- or right-hand single-controller setup
- Then core firearm control remains operable without requiring dual-controller dependency.
