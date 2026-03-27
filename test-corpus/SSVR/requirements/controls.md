# Controls Acceptance Criteria

Scope: player control schemes, input mappings, locomotion controls, and platform-specific control behavior for desktop and VR play.

<!-- acceptance-status-summary:start -->
Summary: 8💡 0🔧 0💻 0🎮 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

## Control Scheme Definitions

### AC-CONTROLS-SCHEME-001: Named control schemes are documented and stable
- **Status:** 💡 Proposed
- Given the game supports multiple play contexts
- When controls are presented in docs or UI
- Then each scheme has a stable name (for example `Desktop Debug`, `VR Motion Controller`)
- And mappings do not silently change between releases.

### AC-CONTROLS-SCHEME-002: Control scheme selection follows active runtime context
- **Status:** 💡 Proposed
- Given the player enters gameplay in desktop or VR context
- When input systems initialize
- Then the appropriate control scheme is selected for that context
- And unsupported bindings are ignored without breaking core play.

## Core Gameplay Controls

### AC-CONTROLS-GAMEPLAY-001: Fire action mapping is explicit per scheme
- **Status:** 💡 Proposed
- Given a control scheme is active
- When the player performs fire input
- Then fire input mapping is explicitly defined for that scheme
- And the mapping is reflected in player-facing control references.

### AC-CONTROLS-GAMEPLAY-002: Reload action mapping is explicit per scheme
- **Status:** 💡 Proposed
- Given a control scheme is active
- When the player performs reload input
- Then reload behavior is consistently mapped for that scheme
- And unavailable reload interactions fail gracefully.

## Locomotion And View Controls

### AC-CONTROLS-LOCO-001: Teleport mode entry and cancel mappings are defined
- **Status:** 💡 Proposed
- Given teleport locomotion is enabled for a scheme
- When the player enters or cancels teleport mode
- Then both actions have explicit mappings
- And both mappings are discoverable in controls documentation.

### AC-CONTROLS-LOCO-002: Turn mapping is defined per scheme
- **Status:** 💡 Proposed
- Given turning is available in gameplay
- When the player uses turn input
- Then turn mapping is explicitly defined per scheme
- And the mapping is consistent with active input source expectations.

## UI And Menu Controls

### AC-CONTROLS-UI-001: All interactions are through Gong Buttons
- **Status:** 💡 Proposed
- Given a player wants to move through the game,
- When player input is evaluated for those panels
- Then the interaction controls are clearly specified and consistent per scheme,
- All required locomotion in the game can happen based on are shot-driven teleportation, by shooting gong buttons or stage elements etc that teleport the player 'forward'/'backward' through this world.

## Validation And Regression Safety

### AC-CONTROLS-VALIDATION-001: Control mapping regressions are detectable
- **Status:** 💡 Proposed
- Given control mappings evolve over time
- When a release candidate is validated
- Then there is a repeatable check that verifies core control actions per scheme
- And mapping regressions are surfaced before release.
