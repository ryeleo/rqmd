# Core Engine Acceptance Criteria

Scope: parsing, status normalization, summary generation, and criterion discovery.

<!-- acceptance-status-summary:start -->
Summary: 1💡 9🔧 5✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### REQMD-CORE-001: Domain file discovery
- **Status:** 🔧 Implemented
- Given repo root and criteria directory are configured
- When the tool scans for domain docs
- Then all markdown files in that directory are discovered in stable sorted order
- And non-markdown files are ignored.

### REQMD-CORE-002: Status line parsing
- **Status:** 🔧 Implemented
- Given a criterion block with a status line
- When the parser reads the document
- Then the status is extracted from `- **Status:** ...`
- And criterion metadata retains status line location for edits.

### REQMD-CORE-003: Canonical status normalization
- **Status:** 🔧 Implemented
- Given variant status spellings or aliases
- When normalization runs
- Then the status is rewritten to canonical labels
- And unsupported values remain unchanged unless explicitly updated by user action.

### REQMD-CORE-004: Summary block insertion
- **Status:** 🔧 Implemented
- Given a domain file without a summary block
- When processing runs
- Then a summary block is inserted near the top of the file
- And the block format uses acceptance-status-summary markers.

### REQMD-CORE-005: Summary block replacement
- **Status:** 🔧 Implemented
- Given a domain file with an existing summary block
- When status counts change
- Then only the existing summary block content is replaced
- And unrelated document content is preserved.

### REQMD-CORE-006: Status count model
- **Status:** ✅ Verified
- Given canonical statuses are present in a file
- When counts are computed
- Then counts include all supported statuses in fixed order
- And summary output uses count+emoji format.

### REQMD-CORE-007: Criterion header matching
- **Status:** 🔧 Implemented
- Given criterion headings follow `### AC-...: ...`
- When parsing runs
- Then each matching criterion is discoverable by ID
- And title text is preserved for menu and reporting output.

### REQMD-CORE-008: Idempotent processing
- **Status:** 🔧 Implemented
- Given no status or summary changes are needed
- When processing runs repeatedly
- Then generated output remains byte-stable for those files
- And no unnecessary rewrites occur.

### REQMD-CORE-009: Missing domain docs handling
- **Status:** 🔧 Implemented
- Given no domain markdown files are found
- When the command is run
- Then the process exits non-zero
- And prints a clear error message.

### REQMD-CORE-010: Blocked/deprecated reason extraction
- **Status:** 🔧 Implemented
- Given a criterion includes blocked or deprecated reason lines
- When parsing runs
- Then those reason lines are captured with line references
- And can be updated or removed consistently by status mutation paths.

### REQMD-CORE-011: Project AC scaffold initialization
- **Status:** ✅ Verified
- Given a project does not yet have AC documentation
- When an initialization command is run
- Then boilerplate docs are created including `docs/requirements.md`
- And a starter domain directory `docs/requirements/` is created
- And generated content follows the AC index/domain pattern used by this tool.

### REQMD-CORE-012: Starter dummy criterion generation
- **Status:** ✅ Verified
- Given initialization is generating starter AC content
- When starter domain docs are created
- Then at least one easy-to-delete sample criterion `<PREFIX>-HELLO-001` is included
- And the sample clearly indicates it is a handoff placeholder for teams to replace.

### REQMD-CORE-013: Domain-sync maintenance over time
- **Status:** 💡 Proposed
- Given users add or evolve domain documentation over time
- When sync/maintenance commands run
- Then index and domain-document references are kept consistent with current domain files
- And stale or missing domain links are flagged with actionable output
- And summary/state regeneration remains accurate after domain additions, removals, or renames.

### REQMD-CORE-014: Automatic ID prefix detection from requirements index
- **Status:** ✅ Verified
- Given users do not pass `--id-prefix`
- When reqmd reads `docs/requirements.md` and linked domain docs
- Then requirement ID prefixes are auto-detected from discovered criterion headers
- And filter/lookup/update flows use those detected prefixes without extra CLI flags.

### REQMD-CORE-015: Init key prompt with customizable default
- **Status:** ✅ Verified
- Given users run `reqmd --init`
- When scaffold initialization starts
- Then reqmd prompts for a starter requirement key prefix
- And Enter accepts default `REQ`
- And generated starter criterion IDs use the selected prefix.
