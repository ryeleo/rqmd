# Bay Acceptance Criteria

Scope: bay layout, surface theming, target arrangement, and bay-level procedural variations.

<!-- acceptance-status-summary:start -->
Summary: 9💡 0🔧 0💻 0🎮 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

## Bay Structure

### AC-BAY-STRUCT-001: Bay grid layout
- **Status:** 💡 Proposed
- Given a bay is created at a specific level in a stage
- When procedural layout is generated
- Then bay consists of a rectangular grid area with defined ground and berm boundaries
- And dimensions scale appropriately for the stage difficulty level.

### AC-BAY-STRUCT-002: Target arrangement
- **Status:** 💡 Proposed
- Given a bay is populated with targets
- When target positions are randomized according to stage parameters
- Then no two targets occupy the same location
- And all targets remain within bay boundaries.

## Surface Theming

### AC-BAY-THEME-001: Ground material variation
- **Status:** 💡 Proposed
- Given a bay is created
- When StageBuilder inspector assigns level-based overrides
- Then ground material is selected based on bay level or index range
- And material persists consistently through all bays at that level.

### AC-BAY-THEME-002: Berm and safe-area theming
- **Status:** 💡 Proposed
- Given berms and safe areas are rendered
- When level-based theming is applied
- Then berm color/material and safe-area visual treatment match the level's theme
- And contrast with ground and targets remains sufficient for visual clarity.

### AC-BAY-THEME-003: Lighting and atmosphere
- **Status:** 💡 Proposed
- Given a bay is active
- When ambient lighting is applied
- Then lighting tone matches the stage theme (indoor/outdoor, dawn/dusk, etc.)
- And target visibility and sight-picture clarity are maintained.

## Bay Population

### AC-BAY-POP-001: Target density
- **Status:** 💡 Proposed
- Given a bay is generated at a specific difficulty level
- When targets are placed
- Then target count scales with difficulty (easier levels have fewer targets, harder levels have more)
- And density remains within playable bounds (shootable in reasonable time).

### AC-BAY-POP-002: Obstacle and hazard placement
- **Status:** 💡 Proposed
- Given a bay includes dynamic obstacles or hazards (if any)
- When positions are randomized
- Then obstacles do not spawn on top of targets or within player safe zones
- And hazards are telegraphed visually and audibly.

## Bay Transitions

### AC-BAY-TRANS-001: Bay entry positioning
- **Status:** 💡 Proposed
- Given a player completes a bay and advances to the next
- When the next bay loads
- Then the player is positioned safely outside the bay's shooting zone
- And camera/orientation is set for clear visibility of the bay layout.

### AC-BAY-TRANS-002: Bay reset between runs
- **Status:** 💡 Proposed
- Given a bay is played through again (after restart)
- When the bay resets
- Then all targets, obstacles, and environmental state return to initial state
- And no stale data from the previous run persists.
