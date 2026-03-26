# Core Engine Requirement

Scope: parsing, status normalization, summary generation, and requirement discovery.

<!-- acceptance-status-summary:start -->
Summary: 0💡 10🔧 5✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-CORE-001: Domain file discovery
- **Status:** 🔧 Implemented
- Given repo root and requirements directory are configured
- When the tool scans for domain docs
- Then all markdown files in that directory are discovered in stable sorted order
- And non-markdown files are ignored.

### RQMD-CORE-002: Status line parsing
- **Status:** 🔧 Implemented
- Given a requirement block with a status line
- When the parser reads the document
- Then the status is extracted from `- **Status:** ...`
- And requirement metadata retains status line location for edits.

### RQMD-CORE-003: Canonical status normalization
- **Status:** 🔧 Implemented
- Given variant status spellings or aliases
- When normalization runs
- Then the status is rewritten to canonical labels
- And unsupported values remain unchanged unless explicitly updated by user action.

### RQMD-CORE-004: Summary block insertion
- **Status:** 🔧 Implemented
- Given a domain file without a summary block
- When processing runs
- Then a summary block is inserted near the top of the file
- And the block format uses acceptance-status-summary markers.

### RQMD-CORE-005: Summary block replacement
- **Status:** 🔧 Implemented
- Given a domain file with an existing summary block
- When status counts change
- Then only the existing summary block content is replaced
- And unrelated document content is preserved.

### RQMD-CORE-006: Status count model
- **Status:** ✅ Verified
- Given canonical statuses are present in a file
- When counts are computed
- Then counts include all supported statuses in fixed order
- And summary output uses count+emoji format.

### RQMD-CORE-007: Requirement header matching
- **Status:** 🔧 Implemented
- Given requirement headings follow `### AC-...: ...`
- When parsing runs
- Then each matching requirement is discoverable by ID
- And title text is preserved for menu and reporting output.

### RQMD-CORE-008: Idempotent processing
- **Status:** 🔧 Implemented
- Given no status or summary changes are needed
- When processing runs repeatedly
- Then generated output remains byte-stable for those files
- And no unnecessary rewrites occur.

### RQMD-CORE-009: Missing domain docs handling
- **Status:** 🔧 Implemented
- Given no domain markdown files are found
- When the command is run
- Then the process exits non-zero
- And prints a clear error message.

### RQMD-CORE-010: Blocked/deprecated reason extraction
- **Status:** 🔧 Implemented
- Given a requirement includes blocked or deprecated reason lines
- When parsing runs
- Then those reason lines are captured with line references
- And can be updated or removed consistently by status mutation paths.

### RQMD-CORE-011: Project AC scaffold initialization
- **Status:** ✅ Verified
- Given a project does not yet have AC documentation
- When an initialization command is run
- Then boilerplate docs are created including `docs/requirements/README.md`
- And a starter domain directory `docs/requirements/` is created
- And generated content follows the AC index/domain pattern used by this tool.

### RQMD-CORE-012: Starter dummy requirement generation
- **Status:** ✅ Verified
- Given initialization is generating starter AC content
- When starter domain docs are created
- Then at least one easy-to-delete sample requirement `<PREFIX>-HELLO-001` is included
- And the sample clearly indicates it is a handoff placeholder for teams to replace.

### RQMD-CORE-013: Domain-sync maintenance over time
- **Status:** 🔧 Implemented
- Given users add or evolve domain documentation over time
- When sync/maintenance commands run
- Then index and domain-document references are kept consistent with current domain files
- And stale or missing domain links are flagged with actionable output
- And summary/state regeneration remains accurate after domain additions, removals, or renames.

### RQMD-CORE-014: Automatic ID prefix detection from requirements index
- **Status:** ✅ Verified
- Given users do not pass `--id-prefix`
- When rqmd reads `docs/requirements/README.md` and linked domain docs
- Then requirement ID prefixes are auto-detected from discovered requirement headers
- And filter/lookup/update flows use those detected prefixes without extra CLI flags.

### RQMD-CORE-015: Init key prompt with customizable default
- **Status:** ✅ Verified
- Given users run `rqmd --init`
- When scaffold initialization starts
- Then rqmd prompts for a starter requirement key prefix
- And Enter accepts default `REQ`
- And generated starter requirement IDs use the selected prefix.

### RQMD-CORE-016: Initial scaffolding content/copy
- **Status:** Proposed
- Given users run `rqmd --init`
- When scaffold initialization runs
- Then generated `docs/requirements/README.md` includes a welcome message and instructions for getting started that is copied from:
    - ./init-docs/README.md for the domain index (requirements/README.md)
    - ./init-docs/domain-example.md for the starter domain doc (requirements/domain-example.md)
- And those instructions are included in the python package README somewhere, so they are published on pypi.org as a simple web page.
- And those documents are maintained in the "./init-docs" directory in this repo for easy editing and management.

