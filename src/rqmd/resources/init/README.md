# Requirements

This document is the source-of-truth index for rqmd requirements.
Generated from resources/init/README.md.

## How To Use

### Requirement Structure

- Keep requirement IDs stable and unique (e.g., `AC-001`, `R-CORE-042`).
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

- Keep this index at {{INDEX_DISPLAY}}.
- Keep requirement docs under {{CRITERIA_DIR_DISPLAY}}/.
- Each markdown file can represent a domain, user story, feature area, or any other team-defined requirement grouping (e.g., `auth.md`, `payment.md`, `audit.md`).
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

This section is intentionally included in the generated requirements index so both humans and AI tooling have a local contract to reference.

### Requirement Entry Fields

Each requirement parsed by rqmd provides these core fields:

- `id` (string): requirement identifier from the H3 heading (for example `AC-001`)
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

### AC-001: Requirement title
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

For detailed parser semantics, keep an extended `schema.md` in your repository if you need stricter local contracts.

{{INDEX_EXTRA_SECTIONS}}

## Requirement Documents

{{REQUIREMENT_DOCUMENTS_SECTION}}
