# Accessibility Acceptance Criteria

Scope: assistive features, input accommodations, sensory options, and inclusive gameplay modes.

<!-- acceptance-status-summary:start -->
Summary: 6💡 0🔧 0💻 0🎮 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

## Input Accessibility

### AC-ACCESSIBILITY-INPUT-001: Adjustable aim hold time
- **Status:** 💡 Proposed
- Given the player is aiming down the ready spot
- When aim-hold calibration is available
- Then hold time can be adjusted to accommodate players with different dwell capabilities
- And the adjustment is persistent across sessions.

### AC-ACCESSIBILITY-INPUT-002: Button hold time customization
- **Status:** 💡 Proposed
- Given the player interacts with UI buttons (pause menu, menu options)
- When a hold-to-confirm action is required
- Then the hold duration can be customized in accessibility settings
- And defaults accommodate both quick and slow-dwell interaction styles.

## Visual Accessibility

### AC-ACCESSIBILITY-VIS-001: High contrast mode
- **Status:** 💡 Proposed
- Given accessibility settings are available
- When high contrast mode is enabled
- Then UI elements, targets, and environmental markers use increased color separation
- And shot sights and reticle visibility remain clear without adding visual clutter.

### AC-ACCESSIBILITY-VIS-002: Text size adjustment
- **Status:** 💡 Proposed
- Given on-screen text is displayed (menu, timers, scores)
- When text size is adjusted in settings
- Then all text scales proportionally without layout breakage
- And minimum readable size is enforced.

## Feedback Options

### AC-ACCESSIBILITY-FEEDBACK-001: Haptic intensity control
- **Status:** 💡 Proposed
- Given haptic feedback is used (reload, trigger, impact)
- When haptic intensity is adjusted
- Then feedback scales from off to maximum without losing responsiveness
- And players can disable specific haptic cues independently.

### AC-ACCESSIBILITY-FEEDBACK-002: Audio cue customization
- **Status:** 💡 Proposed
- Given audio cues are present (ready beep, hit sounds, UI feedback)
- When audio accessibility settings are open
- Then each cue category can be independently enabled, disabled, or adjusted
- And visual alternatives (screen flash, haptic pulse) are available for critical audio cues.
