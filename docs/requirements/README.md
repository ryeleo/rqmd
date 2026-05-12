# Requirements

> **ℹ️ Info:** This index is managed by [rqmd](https://pypi.org/project/rqmd/) — a lightweight requirements tracker for AI-assisted development.

This document is the source-of-truth index for rqmd requirements.




## Project Tooling Metadata

This section records the rqmd tooling versions currently expected by this repository.
Refresh it after upgrading rqmd by running `rqmd --sync-index-metadata --force-yes`.

<!-- rqmd-project-metadata:start -->
- `rqmd_version`: `0.3.0`
- `json_schema_version`: `1.1.0`
<!-- rqmd-project-metadata:end -->




## How To Use

### Requirement Structure

- Keep requirement IDs stable and unique (e.g., `RQMD-CORE-042`, `RQMD-BUG-003`).
- Keep one status line directly below each requirement heading: `- **Status:** <Status>` (e.g., `- **Status:** ✅ Verified`).
- Simple title + status requirements are still valid for lightweight placeholders.
- Prefer pairing a short user story (`As a ...`, `I want ...`, `So that ...`) with Given/When/Then acceptance bullets when both help clarify intent and behavior.
- Optional fields:
  - Priority: `- **Priority:** <Level>` (e.g., `🔴 P0 - Critical`, `🟡 P2 - Medium`)
  - Blocked/Deprecated reasons: `**Blocked:** <reason>` or `**Deprecated:** <reason>` on line(s) following status line
  - Flagged state: `- **Flagged:** true|false` — for marking items needing attention without changing status

### Subsection Organization (Optional)

Requirement docs can use **H2 headers** (`##`) to organize requirements into logical subsections. These docs may represent domains, user stories, feature areas, or any other project-specific grouping. Subsections:
- Are optional — requirements without a containing H2 have no subsection assignment.
- Help organize large requirement sets (e.g., "Query API", "Mutation API", "Authentication").
- Can have optional body content between the H2 header and the first H3 requirement below it.
- Are discoverable via `--sub-domain <NAME>`, tab completion, and JSON metadata.
- Example structure:
  ```markdown
  ## Query API

  Handles read-only data retrieval and projection.
  
  ### AC-001: Simple query retrieval

  - **Status:** ✅ Verified
  ...
  
  ### AC-002: Complex query filtering

  - **Status:** 💡 Proposed
  ...
  
  ## Mutation API

  Handles write operations and side effects.
  
  ### AC-003: Create operation

  - **Status:** ✅ Verified
  ...
  ```

### File Organization

- Keep this index at `docs/requirements/README.md`.
- Keep requirement docs under `docs/requirements/`.
- Each markdown file can represent a domain, user story, feature area, or any other team-defined requirement grouping (e.g., `core-engine.md`, `bugs.md`, `telemetry.md`).
- Requirement ID prefixes are auto-detected from requirement IDs; can override with `--id-namespace`.

### Status Workflow

Canonical status progression:
- `💡 Proposed`
- `🔧 Implemented`
- `✅ Verified`
- `⚠️ Janky`
- `⛔ Blocked`
- `🗑️ Deprecated`

## Schema Reference

This section is intentionally included in the requirements index so both humans and AI tooling have a local contract to reference.

### Requirement Entry Fields

Each requirement parsed by rqmd provides these core fields:

- `id` (string): requirement identifier from the H3 heading (for example `RQMD-CORE-001`)
- `title` (string): heading title text after the ID
- `status` (string): canonical status label (for example `✅ Verified`)
- `sub_domain` (string | null): containing H2 subsection title, or `null` when not in a subsection

Optional metadata fields:

- `priority` (string | null): canonical priority label when present
- `flagged` (bool | null): triage marker when present
- `blocked_reason` (string | null): present when status is blocked and reason exists
- `deprecated_reason` (string | null): present when status is deprecated and reason exists

### Supported Markdown Structure

Expected requirement shape:

```markdown

## Optional Subsection Name

### RQMD-CORE-001: Requirement title

- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- **Flagged:** true
**Blocked:** optional reason
**Deprecated:** optional reason
```

Notes:

- H2 subsections are optional.
- H3 requirement headings and a status line are required for indexing.
- Subsection matching for `--sub-domain` is case-insensitive prefix matching.

### JSON Output Contract (Stable Keys)

Top-level mode keys:

- `summary`: `mode`, `criteria_dir`, `changed_files`, `totals`, `files`, `ok`
- `check`: `mode`, `criteria_dir`, `changed_files`, `totals`, `files`, `ok`
- `set` / `set-priority` / `set-flagged`: `mode`, `criteria_dir`, `changed_files`, `totals`, `files`, `updates`
- `filter-status`: `mode`, `status`, `criteria_dir`, `total`, `files`
- `filter-priority`: `mode`, `priority`, `criteria_dir`, `total`, `files`
- `filter-flagged`: `mode`, `flagged`, `criteria_dir`, `total`, `files`
- `filter-sub-domain`: `mode`, `sub_domain`, `criteria_dir`, `total`, `files`
- `filter-targets`: `mode`, `targets`, `criteria_dir`, `total`, `files`
- `rollup`: `mode`, `criteria_dir`, `file_count`, `totals`, optional `rollup_source`, optional `rollup_columns`

### File-Level JSON Shape

Each file entry in filter/summary outputs includes:

- `path`: repo-relative markdown path
- `requirements`: matched requirement entries
- `sub_sections`: subsection summary entries with `name` and `count`

For detailed parser semantics, see [docs/schema.md](../schema.md).

## Requirement Documents

Each requirement document can represent a domain, user story, feature area, or another project-specific grouping. rqmd uses "domain" internally for some parser and API names, but the markdown contract itself is intentionally flexible.

Bug note: [Bug Tracking](bug-tracking.md) is for meta-requirements about how bug tracking works; [Bugs](bugs.md) is the live backlog of concrete rqmd defects to fix.

### AC CLI

- [Core Engine](core-engine.md) - parsing, normalization, summaries, requirements extraction
- [Interactive UX](interactive-ux.md) - keyboard-driven status update flows
- [Automation API](automation-api.md) - shared non-interactive set/set-file/filter/json contracts for machine and CI usage
- [Sorting](sorting.md) - ordering rules, toggles, deterministic ranking behavior
- [Roll-up](roll-up.md) - summary counts, bucket rendering, and visual roll-up output
- [Screen-Write UI](screen-write.md) - full-screen renderer mode, terminal capability fallback, and redraw ergonomics
- [Portability](portability.md) - repo root, requirements directory, cross-project assumptions
- [Packaging](packaging.md) - package layout, entrypoints, install/run behavior
- [Telemetry](telemetry.md) - agent-facing telemetry for capturing AI workflow friction, improvement suggestions, and session diagnostics
- [Bug Tracking (meta-requirements)](bug-tracking.md) - first-class bug tracking requirements, metadata, templates, and workflow behavior
- [Bugs (rqmd bugs themselves)](bugs.md) - runtime bug backlog and filed bug instances

### Archived

Fully-deprecated domain documents moved to `archived/` — retained for git history, excluded from active processing.

- [Undo / History](archived/undo.md) - 11 RQMD-UNDO-* (undo/redo semantics) — all 🗑️ Deprecated
- [Time Machine](archived/time-machine.md) - 10 RQMD-TIME-* (temporal navigation) — all 🗑️ Deprecated
- [AI CLI](archived/ai-cli.md) - 11 RQMD-AI-001..011 (AI entrypoint, prompt export, guarded apply) — all 🗑️ Deprecated; RQMD-AI-061/063 (`rqmd bug`) relocated to [Bug Tracking](bug-tracking.md)

## Verification

- [Testing](../testing.md) - pytest suite coverage map for implemented requirements

## ID Prefixes

| Prefix | Domain |
|---|---|
| RQMD-CORE-* | Core Engine |
| RQMD-INTERACTIVE-* | Interactive UX |
| RQMD-AUTOMATION-* | Automation API |
| RQMD-AI-* | AI CLI (archived) / Bug Tracking |
| RQMD-SORTING-* | Sorting |
| RQMD-ROLLUP-* | Roll-up |
| RQMD-UI-* | Screen-Write UI |
| RQMD-PORTABILITY-* | Portability |
| RQMD-PACKAGING-* | Packaging |
| RQMD-TELEMETRY-* | Telemetry |
| RQMD-BUG-* | Bug Tracking |

## Tracking Rule

- Run rqmd --verify-summaries to validate summaries.
- Run rqmd to update summaries and optionally edit requirement statuses interactively.
- When turning a brainstorm into implementation work, update the affected requirement docs, this index, and `CHANGELOG.md` before applying code changes so the tracked contract stays ahead of the implementation.
- Use --id-namespace to limit or expand which header prefixes are recognized.
