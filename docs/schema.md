# RQMD Data Schema & Contract

This document comprehensively specifies the data structures, parsing rules, and metadata contracts used by rqmd.

## Table of Contents
1. [Requirement (Criterion) Object](#requirement-criterion-object)
2. [Subsection (H2) Structure](#subsection-h2-structure)
3. [Markdown Syntax](#markdown-syntax)
4. [Status & Priority Models](#status--focus-priorityls)
5. [JSON Export Contracts](#json-export-contracts)
6. [Parsing Rules](#parsing-rules)

---

## Requirement (Criterion) Object

Each parsed requirement is represented as a dictionary with the following fields:

### Core Fields

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `id` | string | ✅ Yes | Requirement identifier (e.g., `AC-001`, `R-CORE-042`). Format: `PREFIX-ID` where prefix is configurable. |
| `title` | string | ✅ Yes | Requirement title extracted from H3 header. |
| `header_line` | int | ✅ Yes | Zero-based line number of the H3 requirement header in source file. |
| `status` | string \| null | ⚠️ Conditional | Current status as canonical label (e.g., `✅ Verified`). Must be present for requirement to be indexed. |
| `status_line` | int \| null | ✅ Yes | Zero-based line number of status line (`- **Status:** ...`). Null if no status line found. |

### Optional Metadata Fields

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `priority` | string \| null | `null` | Optional priority level (e.g., `🔴 P0 - Critical`). Parsed from `- **Priority:** ...` |
| `priority_line` | int \| null | `null` | Line number of priority line. |
| `blocked_reason` | string \| null | `null` | Free-text reason if status is Blocked. Parsed from `**Blocked:** <reason>`. |
| `blocked_reason_line` | int \| null | `null` | Line number of blocked reason. |
| `deprecated_reason` | string \| null | `null` | Free-text reason if status is Deprecated. Parsed from `**Deprecated:** <reason>`. |
| `deprecated_reason_line` | int \| null | `null` | Line number of deprecated reason. |
| `flagged` | bool \| null | `null` | Binary marker for triage/attention (true/false). Parsed from `- **Flagged:** true\|false`. |
| `flagged_line` | int \| null | `null` | Line number of flagged line. |

### Subsection Field (Wave 1)

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `sub_domain` | string \| null | `null` | Name of containing H2 subsection header (e.g., "Query API"). Null if requirement is not within an H2 section. Subsection names are trimmed whitespace but preserve original casing for display. |

---

## Subsection (H2) Structure

**RQMD-CORE-020** introduces optional H2 headers for organizing requirements within a domain file.

### Syntax

```markdown
## Subsection Name Here

Optional body text describing the subsection scope, design rationale, or implementation notes.

### AC-001: First requirement in subsection
- **Status:** ✅ Verified
...

### AC-002: Second requirement in subsection
- **Status:** 💡 Proposed
...

## Another Subsection

### AC-003: Requirement in different subsection
- **Status:** ✅ Verified
...
```

### Parsing Rules

- H2 header **must** be detected before H3 requirement headers to assign subsection membership.
- Pattern: `^##\s+(?P<section_title>.+?)\s*$` (matches `## Subsection Name`)
- Subsection name is **extracted as verbatim text** (preserve casing, internal whitespace).
- When parsing encounters an H2, it becomes the `current_subsection` for all subsequent H3 requirements until another H2 is found.
- Resetting subsection: parsing next H2 overwrites `current_subsection`; there is **no** explicit "end of subsection" marker.
- Body content between H2 and first H3 is **not currently captured** by core parser (RQMD-CORE-020 for future enhancement).

### Example with Parser State

```
Line 5:  ## Query API                     ← current_subsection = "Query API"
Line 7:  ### AC-001: Get user           ← parsed with sub_domain = "Query API"
Line 12: ### AC-002: Search items       ← parsed with sub_domain = "Query API"
Line 18: ## Mutation API                ← current_subsection = "Mutation API"
Line 20: ### AC-003: Create entity      ← parsed with sub_domain = "Mutation API"
```

---

## Markdown Syntax

### Full Requirement Example (All Optional Fields)

```markdown
## Query API

Details about this subsection go here (optional).

### AC-001: Retrieve user by ID
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- **Flagged:** false
- Given a valid user ID
- When the API endpoint is called
- Then the user object is returned with all fields
- And response time is < 100ms.

**Blocked:** This is blocked reason text.

## Mutation API

### AC-002: Update user profile
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- Given a user with edit permissions
- When updating a field
- Then the field is persisted
- And an audit log entry is created.
```

### Parsing Precedence

**Status line search** happens **once per requirement** (uses first match):
```python
if status_match and current and current["status"] is None:
    # Parse and normalize
    current["status"] = coerce_status_label(status_match.group("status"))
    current["status_line"] = index
    continue  # Subsequent matches ignored
```

**Reason lines** can appear on consecutive lines:
```python
blocked_match = BLOCKED_REASON_PATTERN.match(line)
if blocked_match and current and current["status_line"] is not None:
    current["blocked_reason"] = blocked_match.group(1).strip()
    current["blocked_reason_line"] = index
    # Does NOT continue; allows multiple reason lines
```

---

## Status & Priority Models

### Canonical Status Order

| Label | Emoji | Shortcode | Internal | Aliases |
|-------|-------|-----------|----------|---------|
| Proposed | 💡 | P | proposed | proposal, propose |
| Implemented | 🔧 | I | implemented | — |
| Verified | ✅ | V | verified | done |
| Blocked | ⛔ | B | blocked | — |
| Deprecated | 🗑️ | D | deprecated | — |

### Canonical Priority Order

| Label | Emoji | Shortcode | Internal | Aliases |
|-------|-------|-----------|----------|---------|
| P0 - Critical | 🔴 | C | p0 | critical |
| P1 - High | 🟠 | H | p1 | high |
| P2 - Medium | 🟡 | M | p2 | medium |
| P3 - Low | 🟢 | L | p3 | low |

### Coercion Rules

**Status:**
- Input examples: `✅ Verified`, `verified`, `Verified`, `V`, `Done`, `✅ Done`
- Output: Always canonical form with emoji prefix (e.g., `✅ Verified`)
- Unrecognized values raise `ValueError` and are **not** coerced
- Exception: Input `✅ Done` maps to `✅ Verified` (legacy alias)

**Priority:**
- Input examples: `P1 - High`, `p1`, `high`, `🟠 P1 - High`
- Output: Always canonical form with emoji prefix
- Unrecognized values raise `ValueError`

---

## JSON Export Contracts

### Stable Top-Level Keys By Mode

When `--as-json` is used, top-level keys are stable by mode:

- `summary`: `mode`, `criteria_dir`, `changed_files`, `totals`, `files`, `ok`
- `check`: `mode`, `criteria_dir`, `changed_files`, `totals`, `files`, `ok`
- `set` / `set-priority` / `set-flagged`: `mode`, `criteria_dir`, `changed_files`, `totals`, `files`, `updates`
- `filter-status`: `mode`, `status`, `criteria_dir`, `total`, `files`
- `filter-priority`: `mode`, `priority`, `criteria_dir`, `total`, `files`
- `filter-flagged`: `mode`, `flagged`, `criteria_dir`, `total`, `files`
- `filter-sub-domain`: `mode`, `sub_domain`, `criteria_dir`, `total`, `files`
- `filter-targets`: `mode`, `targets`, `criteria_dir`, `total`, `files`
- `rollup`: `mode`, `criteria_dir`, `file_count`, `totals`, optional `rollup_source`, optional `rollup_columns`
- `init`: `mode`, `criteria_dir`, `starter_prefix`, `created_files`, `created_count`
- `init-priorities`: `mode`, `criteria_dir`, `default_priority`, `changed_files`, `changed_count`

### Filter Payload Example (Current)

```json
{
  "mode": "filter-sub-domain",
  "sub_domain": "query",
  "requirements_dir": "docs/requirements",
  "total": 2,
  "files": [
    {
      "path": "docs/requirements/demo.md",
      "requirements": [
        {
          "id": "AC-DEMO-001",
          "title": "Get record",
          "sub_domain": "Query API",
          "flagged": false,
          "body": {
            "markdown": "### AC-DEMO-001: Get record\\n- **Status:** ✅ Verified",
            "lines": {
              "header": 9,
              "status": 10,
              "body_start": 9,
              "body_end": 10
            }
          }
        }
      ],
      "sub_sections": [
        {
          "name": "Query API",
          "count": 2
        },
        {
          "name": "Mutation API",
          "count": 1
        }
      ]
    }
  ]
}
```

### Contract Notes

- `criteria_dir` is repo-relative and machine-stable for the current workspace.
- Filter payloads use `total` for match counts.
- `files` entries are deterministic by path order.
- `requirements` entries are deterministic by requirement ID order in JSON filter modes.
- `sub_domain` is present on every requirement entry in filter-targeted payloads and is `null` when no subsection applies.
- `sub_sections` is present on file entries for summary/filter payloads and includes subsection `name` plus aggregated `count`.
- `--no-requirement-body` omits `body` from filter payload requirements.
- Text modes `--as-tree` and `--as-list` are display-only and intentionally not part of JSON contracts.

---

## Parsing Rules

### File Discovery

- **Pattern**: `*.md` files in `--docs-dir` (default: `docs/requirements/`).
- **Order**: Sorted lexicographically by filename.
- **Exclusions**: Files starting with `.`, directories, non-markdown files.

### Requirement Indexing

A requirement is **indexed** (included in result sets) if and only if:
1. **Header matches** `###\s+(?P<id>PREFIX-ID):\s*(?P<title>.+?)` pattern, AND
2. **Status line exists** (`- **Status:** ...`) somewhere in requirement block

If header matches but no status line found, requirement is **not indexed** but does not raise error.

### ID Prefix Detection

rqmd auto-detects valid ID prefixes by:
1. Scanning `docs/requirements/README.md` for requirement headers
2. Following markdown links in the index to discover domain files
3. Collecting all observed ID prefixes (e.g., `AC`, `R`, `RQMD`)
4. Fallback: If no detection possible, use `DEFAULT_ID_PREFIXES = ("AC", "R", "RQMD")`

Override with `--id-namespace AC,R` (comma-separated list).

### Deterministic Ordering

- **Files**: Sorted by filename (ASCII/lexicographic)
- **Requirements within file**:
  - Parser indexing: `header_line` (appearance order)
  - JSON filter payloads: sorted by requirement ID
  - Explicit target payloads: preserve resolved target order with de-duplication
- **Deterministic tie-breaking**: no unstable ordering is expected for equal keys

---

## Configuration & Customization

### Project Config Files

rqmd supports optional `.rqmd.yml` or `.rqmd.json` for custom status/priority catalogs:

```yaml
# .rqmd.yml
statuses:
  - name: Proposed
    shortcode: P
    emoji: "💡"
  - name: Implemented
    shortcode: I
    emoji: "🔧"
  - name: Verified
    shortcode: V
    emoji: "✅"
```

Custom statuses **override** canonical order and aliases. Schema must include `name`, `shortcode`, and `emoji` fields.

---

## Future Enhancements

- **RQMD-CORE-020+**: Subsection-level body content capture (narrative + optional metadata per subsection)
- **RQMD-AUTOMATION-032+**: Domain-level body parsing (domain-scope narrative separate from requirements)
- **Schema versioning**: JSON responses will include `schema_version` field when versioning policy is established
