# Requirements

This document is the source-of-truth index for rqmd requirements.

## Project Tooling Metadata

This section records the rqmd tooling versions currently expected by this repository.
Refresh it after upgrading rqmd by running `rqmd --sync-index-metadata --force-yes`.

<!-- rqmd-project-metadata:start -->
- `rqmd_version`: `0.1.0`
- `json_schema_version`: `1.0.0`
<!-- rqmd-project-metadata:end -->

## How To Use

- Keep requirement IDs stable and unique.
- Keep one status line directly below each requirement heading.
- Simple one-line requirements with only a title and status are also valid.
- Prefer pairing a short user story with Given/When/Then when both help clarify intent and behavior.
- Use Given/When/Then when a requirement needs explicit acceptance detail.
- Keep this index at docs/requirements/README.md.
- Keep domain docs under docs/requirements/.

Status workflow:
- 💡 Proposed
- 🔧 Implemented
- ✅ Verified
- ⚠️ Janky
- ⛔ Blocked
- 🗑️ Deprecated

## Requirement Documents

Each requirement document can represent a domain, user story, feature area, or another project-specific grouping. rqmd uses "domain" internally for some parser and API names, but the markdown contract itself is intentionally flexible.

### AC CLI
- [Core Engine](core-engine.md) - parsing, normalization, summaries, requirements extraction
- [Interactive UX](interactive-ux.md) - keyboard-driven status update flows
- [Automation API](automation-api.md) - shared non-interactive set/set-file/filter/json contracts for machine and CI usage
- [AI CLI](ai-cli.md) - `rqmd-ai`-specific prompt export, guarded apply flows, onboarding guidance, and auditability requirements
- [Sorting](sorting.md) - ordering rules, toggles, deterministic ranking behavior
- [Roll-up](roll-up.md) - summary counts, bucket rendering, and visual roll-up output
- [Screen-Write UI](screen-write.md) - full-screen renderer mode, terminal capability fallback, and redraw ergonomics
- [Time Machine](time-machine.md) - branch-aware historical browsing, detached views, and replay from prior states
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
| RQMD-AI-* | AI CLI |
| RQMD-SORTING-* | Sorting |
| RQMD-ROLLUP-* | Roll-up |
| RQMD-UI-* | Screen-Write UI |
| RQMD-TIME-* | Time Machine |
| RQMD-PORTABILITY-* | Portability |
| RQMD-PACKAGING-* | Packaging |

## Tracking Rule

- Run rqmd --verify-summaries to validate summaries.
- Run rqmd to update summaries and optionally edit requirement statuses interactively.
- When turning a brainstorm into implementation work, update the affected requirement docs, this index, and `CHANGELOG.md` before applying code changes so the tracked contract stays ahead of the implementation.
- Use --id-namespace to limit or expand which header prefixes are recognized.