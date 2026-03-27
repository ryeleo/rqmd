# Gong Button Acceptance Criteria

Scope: individual gong-button rendering, interactivity, visual feedback, and audio-visual response behavior.

<!-- acceptance-status-summary:start -->
Summary: 12💡 3🔧 0💻 0🎮 1✅ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->

## Visual Representation

### AC-GONGBUTTON-VIS-001: Gong button visual vs. placeholder
- **Status:** ✅ Done
- Given UI targets are created for menu or interactive contexts
- When those targets are rendered
- Then they are displayed using authentic gong-button visuals
- And not as raw unit-cube placeholders.

### AC-GONGBUTTON-VIS-002: Gong-button size variants
- **Status:** 🗑️ Deprecated
- Given gong buttons are used at various difficulty levels or contexts
- When gong buttons are instantiated
- Then standard sizes (`gong`, `12in`, `10in`) are supported with visually distinct proportions.

### AC-GONGBUTTON-VIS-003: Gong button material and reflection
- **Status:** 💡 Proposed
- Given a gong button is rendered
- When environmental lighting is present
- Then the gong material reflects light realistically (metallic surface)
- And surface wear/patina is visible at typical viewing distances.

## State Feedback

### AC-GONGBUTTON-STATE-001: Selected-state visual feedback
- **Status:** 🔧 Implemented
- Given a menu action requires confirmation
- When a gong button receives the first shot and enters selected state
- Then the button immediately reflects selected state visually (glow, tint, or highlight that persists).

### AC-GONGBUTTON-STATE-002: Reset feedback after confirmation
- **Status:** 💡 Proposed
- Given a gong button action completes (confirmation reached, action executed)
- When the action resolves
- Then the gong button returns to rest state presentation
- And is ready for the next interaction.

### AC-GONGBUTTON-STATE-003: Disabled state appearance
- **Status:** 💡 Proposed
- Given a gong button is temporarily disabled or unavailable
- When the button is shown in disabled state
- Then visual presentation clearly indicates unavailability
- And the button does not register hits or log shots.

## Hit and Interaction

### AC-GONGBUTTON-HIT-001: Gong button hit detection robustness
- **Status:** 💡 Proposed
- Given a gong button is rendered in 3D space
- When a bullet hits the gong surface from any reasonable angle
- Then the hit is reliably detected
- And hit registration does not depend on exact surface-normal alignment.

### AC-GONGBUTTON-HIT-002: Double-tap action completion
- **Status:** 🔧 Implemented
- Given a gong-button action requires confirmation via multi-tap
- When shots are fired at the gong in sequence
- Then the first shot selects the button (visual highlight persists)
- And the second shot immediately executes the action (no additional taps required).
- And double-tap is the maximum interaction required for any menu or gameplay decision.

### AC-GONGBUTTON-HIT-003: Double-tap window and timing
- **Status:** 💡 Proposed
- Given a double-tap action is required (select + confirm)
- When two shots land within a defined time window
- Then both shots complete the action
- And if the time window expires, the button resets to rest state.

## Audio Feedback

### AC-GONGBUTTON-AUDIO-001: Gong strike sound signature
- **Status:** 💡 Proposed
- Given a gong button is struck by a bullet
- When the hit is registered
- Then a distinct metallic gong-strike sound is played
- And sound volume and pitch reflect button size.

### AC-GONGBUTTON-AUDIO-002: Multi-strike audio feedback
- **Status:** 💡 Proposed
- Given multiple gong buttons are struck in sequence
- When hits occur at close time intervals
- Then each gong produces distinct audio feedback
- And audio does not muddy or become incoherent with overlapping strikes.

## Physical Response

### AC-GONGBUTTON-PHYSICS-001: Gong button recoil/knockback on hit
- **Status:** 💡 Proposed
- Given a high-velocity bullet strikes a gong button
- When the hit is resolved
- Then the button displays a brief recoil animation or knockback
- And the physical response completes within a short time (< 0.5 seconds).

### AC-GONGBUTTON-PHYSICS-002: Gong button collision geometry
- **Status:** 💡 Proposed
- Given a gong button is in the scene
- When bullets approach from any direction
- Then collision geometry accurately represents the button's visible surface
- And false-positive hits (behind the gong, off-axis) do not register.

## Durability and Resilience

### AC-GONGBUTTON-DURABILITY-001: Gong button wear and visual degradation
- **Status:** 💡 Proposed
- Given a gong button experiences repeated impacts
- When strike count or cumulative damage increases
- Then visual wear marks, dents, or surface degradation may appear (optional game feature)
- And the button remains functionally interactive.

### AC-GONGBUTTON-DURABILITY-002: Gong button lifetime behavior
- **Status:** 💡 Proposed
- Given a gong button is placed in a stage or menu bay
- When gameplay proceeds for extended duration
- Then the button does not degrade to non-interactive state
- And remains shootable and responsive for the entire session.

## Placement and Depth

### AC-GONGBUTTON-PLACEMENT-001: Menu button depth consistency
- **Status:** 🔧 Implemented
- Given interactive menu gongs are spawned in a bay
- When they are positioned relative to the shooter
- Then all menu gongs are placed at the Ready Spot forward depth
- So all interactions occur at a consistent, ergonomic distance.

### AC-GONGBUTTON-PLACEMENT-002: Button spacing in arrays
- **Status:** 💡 Proposed
- Given multiple gong buttons are arranged in an array
- When button positions are laid out
- Then buttons are spaced sufficiently to allow distinct targeting
- And player cannot accidentally hit multiple buttons with a single shot (unless intentionally overlapped).
