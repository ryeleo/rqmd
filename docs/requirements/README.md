# Requirements

This document is the source-of-truth index for rqmd requirements.

## How To Use

- Keep requirement IDs stable and unique.
- Keep one status line directly below each requirement heading.
- Simple one-line requirements with only a title and status are also valid.
- Use Given/When/Then when a requirement needs explicit acceptance detail.
- Keep this index at docs/requirements/README.md.
- Keep domain docs under docs/requirements/.

Status workflow:
- 💡 Proposed -> 🔧 Implemented -> ✅ Verified
- Use ⛔ Blocked or 🗑️ Deprecated when needed.

## Domain Documents

### AC CLI
- [Core Engine](core-engine.md) - parsing, normalization, summaries, requirements extraction
- [Interactive UX](interactive-ux.md) - keyboard-driven status update flows
- [Automation API](automation-api.md) - non-interactive set/set-file/filter behavior
- [Sorting](sorting.md) - ordering rules, toggles, deterministic ranking behavior
- [Roll-up](roll-up.md) - summary counts, bucket rendering, and visual roll-up output
- [Portability](portability.md) - repo root, requirements directory, cross-project assumptions
- [Packaging](packaging.md) - package layout, entrypoints, install/run behavior

## Verification

- [Testing](../testing.md) - pytest suite coverage map for implemented requirements

## ID Prefixes

| Prefix | Domain |
|---|---|
| RQMD-CORE-* | Core Engine |
| RQMD-INTERACTIVE-* | Interactive UX |
| RQMD-AUTOMATION-* | Automation API |
| RQMD-SORTING-* | Sorting |
| RQMD-ROLLUP-* | Roll-up |
| RQMD-PORTABILITY-* | Portability |
| RQMD-PACKAGING-* | Packaging |

## Tracking Rule

- Run rqmd --check to validate summaries.
- Run rqmd to update summaries and optionally edit requirement statuses interactively.
- Use --id-prefix to limit or expand which header prefixes are recognized.