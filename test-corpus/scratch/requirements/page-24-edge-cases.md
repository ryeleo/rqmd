# Pagination Corpus 24 Edge Cases

Scope: frontend interaction edge cases and rendering stress scenarios.

<!-- acceptance-status-summary:start -->
Summary: 2💡 2🔧 2✅ 2⛔ 2🗑️
<!-- acceptance-status-summary:end -->

## Query API
This section intentionally includes long lines, links, and mixed metadata so manual UI QA can exercise truncation, scrolling, and redraw behavior.

### REQ-PAG-231: Very long requirement title to stress horizontal clipping behavior in interactive menus and preserve cursor visibility on redraw cycles
- **Status:** 💡 Proposed
- **Priority:** 🔴 P0 - Critical
- **Flagged:** true
- **Links:**
  - [UI baseline checklist](https://example.invalid/ui-baseline)
- Given a requirement row with long text and metadata
- When the user navigates in interactive mode
- Then the active row remains readable and stable.

### REQ-PAG-232: Link-heavy requirement with plain URL entries for quick link parsing checks
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- **Links:**
  - https://example.invalid/raw-link
  - [labeled link](https://example.invalid/labeled-link)
- Given a requirement containing multiple link formats
- When link-aware filters and renderers run
- Then links remain preserved and visible.

### REQ-PAG-233: Verified requirement with subsection narrative content
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- Given subsection text appears before requirement entries
- When interactive panels show domain context snippets
- Then the section narrative remains stable.

### REQ-PAG-234: Blocked requirement with explicit reason to exercise reason rendering
- **Status:** ⛔ Blocked
**Blocked:** Waiting for dependency REQ-PAG-239 to be implemented.
- **Priority:** 🟠 P1 - High
- Given a blocked criterion with reason text
- When status transitions are reviewed
- Then blocked context is shown without losing formatting.

### REQ-PAG-235: Deprecated requirement with reason text and one-line acceptance body
- **Status:** 🗑️ Deprecated
**Deprecated:** Replaced by REQ-PAG-236 and REQ-PAG-237.
- **Priority:** 🟢 P3 - Low
- Given deprecated criteria include replacement notes
- When scanning interactive lists
- Then deprecation intent remains discoverable.

## Mutation API
This second subsection helps validate subsection filters and sort behavior against mixed statuses.

### REQ-PAG-236: Proposed mutation edge with short body
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- Given a short item
- When sorted by status then priority
- Then ordering remains deterministic.

### REQ-PAG-237: Implemented mutation edge with explicit false flag
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
- **Flagged:** false
- Given flagged metadata is explicitly false
- When filtering with --no-flag
- Then this requirement appears in results.

### REQ-PAG-238: Verified mutation edge with compact description
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- Given compact descriptions and verified status
- When cycling sort columns
- Then row rendering remains aligned.

### REQ-PAG-239: Blocked mutation edge with cross-reference reason
- **Status:** ⛔ Blocked
**Blocked:** Awaiting stabilization of REQ-PAG-231 rendering expectations.
- **Priority:** 🔴 P0 - Critical
- Given cross-linked blocked reasons
- When reviewing timeline diffs
- Then reason payload remains intact.

### REQ-PAG-240: Deprecated mutation edge with links and reason
- **Status:** 🗑️ Deprecated
**Deprecated:** Superseded by alternative interaction model.
- **Priority:** 🟢 P3 - Low
- **Links:**
  - [replacement note](https://example.invalid/replacement)
- Given deprecated entries with links
- When paginating across long lists
- Then footer legends and row content stay stable.
