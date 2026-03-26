# Acceptance Criteria

This document is the source-of-truth index for ac-docs-cli acceptance criteria.

## How To Use

- Keep criteria in Given/When/Then format.
- Keep criterion IDs stable and unique.
- Keep one status line directly below each criterion heading.
- Keep domain docs under docs/acceptance-criteria/.

Status workflow:
- 💡 Proposed -> 🔧 Implemented -> 💻 Desktop-Verified -> 🎮 VR-Verified -> ✅ Done
- Use ⛔ Blocked or 🗑️ Deprecated when needed.

## Domain Documents

### AC CLI
- [Core Engine](docs/acceptance-criteria/core-engine.md) - parsing, normalization, summaries, criteria extraction
- [Interactive UX](docs/acceptance-criteria/interactive-ux.md) - keyboard-driven status update flows
- [Automation API](docs/acceptance-criteria/automation-api.md) - non-interactive set/set-file/filter behavior
- [Portability](docs/acceptance-criteria/portability.md) - repo root, criteria directory, cross-project assumptions
- [Packaging](docs/acceptance-criteria/packaging.md) - package layout, entrypoints, install/run behavior

## Verification

- [Testing](docs/testing.md) - pytest suite coverage map for implemented acceptance criteria

## ID Prefixes

| Prefix | Domain |
|---|---|
| AC-ACCLI-CORE-* | Core Engine |
| AC-ACCLI-INTERACTIVE-* | Interactive UX |
| AC-ACCLI-AUTOMATION-* | Automation API |
| AC-ACCLI-PORTABILITY-* | Portability |
| AC-ACCLI-PACKAGING-* | Packaging |

## Tracking Rule

- Run ac-cli --check to validate summaries.
- Run ac-cli to update summaries and optionally edit statuses interactively.
