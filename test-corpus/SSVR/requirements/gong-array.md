# Gong Button Array Acceptance Criteria

Scope: multi-button grid/array layout, dynamic population, refresh behavior, and array-level performance.

<!-- acceptance-status-summary:start -->
Summary: 5💡 10🔧 0💻 0🎮 0✅ 0⛔ 4🗑️
<!-- acceptance-status-summary:end -->

## Array Layout and Organization

### AC-GONGARRAY-LAYOUT-001: Grid-based array positioning
- **Status:** 🔧 Implemented
- Given a gong button array is created for menu selection (stages, offers, etc.)
- When buttons are positioned
- Then they are arranged in a logical grid pattern (rows × columns) on an arc curving around the shooter.
- And spacing is uniform and ergonomic for VR aiming
- And the arc is centered on a provided transform (shooter-box, panel, etc.), or auto-resolves to nearby shooter-box/player-camera
- And each button's rotation is adjusted so it faces toward the center point
- And button spacing respects the configured gridding (columns, rows, button-spacing distance)
- Arc positioning can be toggled on/off via `useArcLayout` boolean (default: enabled)
- Arc positioning is configured via:
  - `arcRadiusMeters`: distance from arc center to buttons (default 2m)
  - `arcAngularSpanDegrees`: total angle span left-to-right (default 110°)
  - `arcHeightOffsetMeters`: vertical offset of arc from center (default 0.35m)
  - `arcCenterTransform`: explicit reference to the arc center point; if null, auto-resolves
- Flat grid layout can be enabled by setting `useArcLayout = false`
- Arc layout works for arrays positioned around shooter boxes, panels, or any other central point



### AC-GONGARRAY-LAYOUT-002: Array positioning
- **Status:** 💡 Proposed
- Given multiple gong button arrays may be visible in the same bay
- When arrays are presented
- Then visual grouping or framing makes array boundaries clear to the player
- And arrays do not visually merge into a single undifferentiated mass.

### AC-GONGARRAY-LAYOUT-003: Center or focal-point anchoring
- **Status:** 🗑️ Deprecated
- **Deprecation:** This is more complicated than it needs to be. Placement should be anchored based on shooter box or shooters current position.
- Given a gong button array is placed in a bay
- When the array is positioned relative to the shooter's Ready Spot
- Then the array is anchored to a clear focal point (center, top-left, etc.)
- And all buttons remain visible within the player's comfortable aiming range.

### AC-GONGARRAY-LAYOUT-004: Incomplete-row centering
- **Status:** 🔧 Implemented
- Given a gong button array uses a configured fixed column count
- When the final row has fewer items than that column count
- Then that incomplete row is horizontally centered within the array
- And partial menu rows do not appear visually drifted left or right.

### AC-GONGARRAY-LAYOUT-005: Stage-selection array bay-midline centering
- **Status:** 🔧 Implemented
- Given a stage-selection gong array is shown in the main-menu bay
- When the array root is positioned
- Then its local X offset is reset to the bay midline
- And the array does not sit arbitrarily off to the left or right of the bay.

## Dynamic Population

### AC-GONGARRAY-POPULATE-001: Stage list array population
- **Status:** 🗑️ Deprecated
**Deprecated:** There are actually multiple arrays planned now rather than one large array.
- Given the player enters stage selection from the main menu
- When the stage list is populated
- Then available stages are rendered as gong buttons in an array
- And the array includes only stages that are valid for the current context (new stages, existing stages, etc.).

### AC-GONGARRAY-POPULATE-002: Array refresh after stage creation
- **Status:** 🔧 Implemented
- Given the player creates a new stage
- When stage creation and registration completes
- Then the "existing stages" gong button array at the main menu bay is automatically refreshed
- And the newly created stage is immediately selectable without scene reload.

### AC-GONGARRAY-POPULATE-003: Conditional array visibility
- **Status:** 🔧 Implemented
- Given multiple gong arrays may exist in the same bay (e.g., Practice mode: new stages vs. existing stages)
- When visibility conditions change (e.g., no new stages available)
- Then arrays are shown or hidden based on context rules
- And hidden arrays do not consume interaction bandwidth or create visual clutter.

## Selection and Navigation

### AC-GONGARRAY-SELECT-001: Single-element selection within array
- **Status:** 🔧 Implemented
- Given a player shoots a gong button within an array
- When the first shot lands
- Then that specific button is selected and highlighted
- And only that button is marked as selected (no multi-select).

### AC-GONGARRAY-SELECT-002: Array action confirmation
- **Status:** 🔧 Implemented
- Given a gong button is selected within an array
- When a confirmation shot is fired at that button
- Then the array-level action (e.g., "load this stage") executes
- And the player transitions to the appropriate next state or scene.

### AC-GONGARRAY-NAV-001: No wrapping within array
- **Status:** 🗑️ Deprecated
- **Deprecation:** This doesn't make sense to me...
- Given gong arrays are interacted with via direct shot selection
- When reviewing historical navigation requirements
- Then index-based previous/next traversal is not part of the current gong-array interaction model
- And wraparound semantics are intentionally out of scope for this domain.

## Scaling and Performance

### AC-GONGARRAY-PERF-001: Array rendering pagination
- **Status:** 💡 Proposed
- Given a gong button array conta-100 buttons
- When the array is rendered
- Then gong bottons will be rendered in paginated subsets (e.g., 20 buttons per page by default)
- And frame rate is not materially impacted by gong array rendering.


### AC-GONGARRAY-PERF-002: Large array memory footprint
- **Status:** 💡 Proposed
- Given an array may grow to contain many stage options (10+ stages)
- When memory and render cost are evaluated
- Then the array implementation scales gracefully
- And memory usage remains proportional to button count (no exponential overhead).

## Persistence and State

### AC-GONGARRAY-STATE-001: Array state persistence across menu transitions
- **Status:** 🗑️ Deprecated
**Deprecated:** We do not want this behavior!
- Given a player navigates away from a gong button array and returns
- When they come back to that array in the same session
- Then the array retains its previous state (selections, scroll position if applicable)
- And the transition is seamless.

### AC-GONGARRAY-STATE-002: Array reset on mode change
- **Status:** 💡 Proposed
- Given a player is exploring an array in Practice mode
- When they switch between Practice and Rogue modes
- Then the Practice array state is not carried over
- And the new array starts in a clean, context-appropriate state.

## Contextual Variants

### AC-GONGARRAY-CONTEXT-STAGES-001: Stage selection array behavior
- **Status:** 🔧 Implemented
- Given a stage-selection gong array is visible
- When a stage button is shot once
- Then that stage is selected and highlighted
- And when shot again, the stage is loaded/generated
- And when shot a third time, the player is teleported to that stage.

### AC-GONGARRAY-CONTEXT-OFFERS-001: Offer selection array behavior
- **Status:** 🔧 Implemented
- Given an "offers" gong array presents difficulty/skill adjustments
- When the player shoots an offer button once
- Then that offer is selected
- And when shot again, the offer is confirmed and applied.

### AC-GONGARRAY-CONTEXT-PRACTICE-001: Existing-stages array behavior
- **Status:** 🔧 Implemented
- Given the "existing stages" gong array is shown after Continue in Practice
- When a player shoots an existing stage button
- Then that stage loads directly (no new generation, no generator UI)
- And the player is teleported into the already-existing stage.

## Accessibility

### AC-GONGARRAY-A11Y-001: Array navigation via verbal callouts
- **Status:** 💡 Proposed
- Given a gong button array is displayed
- When accessibility audio is enabled
- Then each button or group can be announced with descriptive labels
- And auditory feedback helps players navigate without perfect aiming.
