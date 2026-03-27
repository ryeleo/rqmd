# Development Tools Acceptance Criteria

Scope: editor tooling, debugging utilities, logging infrastructure, and development-only features.

<!-- acceptance-status-summary:start -->
Summary: 8💡 0🔧 0💻 0🎮 4✅ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->

## Editor Tools

### AC-DEVTOOLS-EDITOR-001: Scene creation from menu
- **Status:** ✅ Done
- Given the Unity editor is open
- When Tools > Create Scene: Start Menu is invoked
- Then a fresh start menu scene is generated with correct setup and all dependencies
- And scene is ready for immediate play testing.

### AC-DEVTOOLS-EDITOR-002: Stage editor tooling
- **Status:** 🗑️ Deprecated
**Deprecated:** I haven't used this in forever
- Given a `.stage` file exists
- When Tools > Edit Scene: Test a Stage is invoked
- Then a stage scene is generated from the file definition
- And the StageBuilder can be re-run to iterate on procedural generation without scene save.

### AC-DEVTOOLS-EDITOR-003: Build and deploy scripting
- **Status:** ✅ Done
- Given source code and Unity project are up to date
- When `./scripts/build-and-run.sh` is executed
- Then project is built (if needed), packaged as APK, and deployed to connected Quest device
- And build errors are reported clearly.

## Logging and Debugging

### AC-DEVTOOLS-DEBUG-001: Developer panel accessible from pause menu
- **Status:** 💡 Proposed
- Given the game is paused
- When a developer mode is enabled
- Then a developer panel button appears in the pause menu
- And selecting it opens an overlay panel with organized settings and debugging controls.

### AC-DEVTOOLS-DEBUG-002: Developer panel uses tab-based organization
- **Status:** 💡 Proposed
- Given the developer panel is open
- When tabs are displayed (e.g., "Logging", "Settings", "Replay", "Telemetry")
- Then each tab groups related settings and controls
- And users can switch between tabs without closing the panel
- And tab selection state persists during the session.

### AC-DEVTOOLS-DEBUG-003: Logging tab shows recent debug output
- **Status:** 💡 Proposed
- Given the developer panel Logging tab is active
- When debug logs are generated during gameplay
- Then recent log entries are displayed in a scrollable view
- And log level filtering (Debug, Info, Warning, Error) is available
- And logs can be cleared without interrupting gameplay.

### AC-DEVTOOLS-DEBUG-004: Settings tab allows runtime configuration
- **Status:** 💡 Proposed
- Given the developer panel Settings tab is active
- When development toggles exist (e.g., verbose logging, frame rate cap, replay inspection)
- Then each setting is presented as a toggle or dropdown within the tab
- And changes apply immediately to the running game.

### AC-DEVTOOLS-DEBUG-005: Replay tab provides quick inspection
- **Status:** 💡 Proposed
- Given the developer panel Replay tab is active
- When a replay file has just been recorded
- Then metadata, keyframe count, and basic integrity checks are displayed
- And the developer can choose to export, (re-)upload to telemetry, or delete the replay.

### AC-DEVTOOLS-DEBUG-006: Telemetry tab shows submission status
- **Status:** 💡 Proposed
- Given the developer panel Telemetry tab is active
- When telemetry events are queued or submitted
- Then submission status, queue depth, and endpoint health are visible
- And developers can manually trigger a submission or clear the queue.

## Telemetry Developer Access

### AC-DEVTOOLS-TELEMETRY-001: Local replay inspection
- **Status:** ✅ Done
- Given a replay file exists locally
- When a developer tool is run to inspect it
- Then replay events, waypoints, and metadata are readable in a human-friendly format
- And replay integrity can be verified before submission.
- **Verification:** Ran `python scripts/inspect_replay.py --dir ShooterReplays --latest 1 --show-waypoints 5` and confirmed metadata, waypoints, target hits, and integrity checks are printed.

### AC-DEVTOOLS-TELEMETRY-002: Offline development capability
- **Status:** 💡 Proposed
- Given development is happening locally
- When the telemetry server is unavailable or offline
- Then the game degrades gracefully without crashing
- And events are queued or logged locally for later submission.

## Validation and Linting

### AC-DEVTOOLS-VALIDATE-001: Stage file schema validation
- **Status:** ✅ Done
- Given a `.stage` file is created or modified
- When a validation tool is run
- Then the file is checked against the schema in `docs/stage-format.md`
- And validation errors are reported with line numbers and suggested fixes.

Verification notes:
- Added `scripts/validate_stage_file.py` to validate one file (`--file`) or all files in a directory (`--dir`).
- Verified with `python scripts/validate_stage_file.py --dir Assets/Resources/Stages` and all current stage files pass.

### AC-DEVTOOLS-VALIDATE-002: Code style checking
- **Status:** 💡 Proposed
- Given C# source changes are made
- When a linter is run (or integrated into build)
- Then namespace conventions, naming patterns, and code structure are validated
- And violations are reported without blocking compilation.
