# Core Engine Requirement

Scope: parsing, status normalization, summary generation, and requirement discovery.

<!-- acceptance-status-summary:start -->
Summary: 2💡 1🔧 16✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-CORE-001: Domain file discovery
- **Status:** ✅ Verified
- As a rqmd user when repo root and requirements directory are configured
- I want the tool to scan for domain docs
- So that all markdown files in that directory are discovered in stable sorted order
- So that non-markdown files are ignored.

### RQMD-CORE-002: Status line parsing
- **Status:** ✅ Verified
- As a rqmd user when a requirement block with a status line
- I want the parser to read the document
- So that the status is extracted from `- **Status:** ...`
- So that requirement metadata retains status line location for edits.

### RQMD-CORE-003: Canonical status normalization
- **Status:** ✅ Verified
- As a rqmd user when variant status spellings or aliases
- I want normalization to run
- So that the status is rewritten to canonical labels
- So that unsupported values remain unchanged unless explicitly updated by user action.

### RQMD-CORE-004: Summary block insertion
- **Status:** ✅ Verified
- As a rqmd user when a domain file without a summary block
- I want processing to run
- So that a summary block is inserted near the top of the file
- So that the block format uses acceptance-status-summary markers.

### RQMD-CORE-005: Summary block replacement
- **Status:** ✅ Verified
- As a rqmd user when a domain file with an existing summary block
- I want status counts change
- So that only the existing summary block content is replaced
- So that unrelated document content is preserved.

### RQMD-CORE-006: Status count model
- **Status:** ✅ Verified
- As a rqmd user when canonical statuses are present in a file
- I want counts to be computed
- So that counts include all supported statuses in fixed order
- So that summary output uses count+emoji format.

### RQMD-CORE-007: Requirement header matching
- **Status:** ✅ Verified
- As a rqmd user when requirement headings follow `### <PREFIX>-...: ...`
- I want parsing to run
- So that each matching requirement is discoverable by ID
- So that title text is preserved for menu and reporting output
- So that prefix handling follows configured or auto-detected `--id-prefix` behavior.

### RQMD-CORE-008: Idempotent processing
- **Status:** ✅ Verified
- As a rqmd user when no status or summary changes are needed
- I want processing to run repeatedly
- So that generated output remains byte-stable for those files
- So that no unnecessary rewrites occur.

### RQMD-CORE-009: Missing domain docs handling
- **Status:** ✅ Verified
- As a rqmd user when no domain markdown files are found
- I want to run the command
- So that reqmd prints a clear, actionable error message
- So that it offers to initialize a starter requirements project in the current working directory (the same behavior as `--init`)
- So that the tool never creates files without explicit user confirmation: the initialization flow must prompt the user to confirm creation and allow a `--yes`/`--confirm` override for automation
- So that in non-interactive or CI contexts the tool exits non-zero and prints the guidance to run `rqmd --init` or `rqmd --init --yes` to create starter files.

### RQMD-CORE-010: Blocked/deprecated reason extraction
- **Status:** ✅ Verified
- As a rqmd user when a requirement includes blocked or deprecated reason lines
- I want parsing to run
- So that those reason lines are captured with line references
- So that they can be updated or removed consistently by status mutation paths.

### RQMD-CORE-011: Project scaffold initialization
- **Status:** ✅ Verified
- As a rqmd user when a project does not yet have requirement documentation
- I want to run an initialization command
- So that boilerplate docs are created including `docs/requirements/README.md`
- So that a starter domain directory `docs/requirements/` is created
- So that generated content follows the requirements index/domain pattern used by this tool.

### RQMD-CORE-012: Starter dummy requirement generation
- **Status:** ✅ Verified
- As a rqmd user when initialization is generating starter requirement content
- I want to create starter domain docs
- So that at least one easy-to-delete sample requirement `<PREFIX>-HELLO-001` is included
- So that the sample clearly indicates it is a handoff placeholder for teams to replace.

### RQMD-CORE-013: Domain-sync maintenance over time
- **Status:** ✅ Verified
- As a rqmd user when users add or evolve domain documentation over time
- I want to run sync/maintenance commands
- So that index and domain-document references are kept consistent with current domain files
- So that stale or missing domain links are flagged with actionable output
- So that summary/state regeneration remains accurate after domain additions, removals, or renames.

### RQMD-CORE-014: Automatic ID prefix detection from requirements index
- **Status:** ✅ Verified
- As a rqmd user when users do not pass `--id-prefix`
- I want rqmd to read `docs/requirements/README.md` and linked domain docs
- So that requirement ID prefixes are auto-detected from discovered requirement headers
- So that filter/lookup/update flows use those detected prefixes without extra CLI flags.

### RQMD-CORE-015: Init key prompt with customizable default
- **Status:** ✅ Verified
- As a rqmd user when users run `rqmd --init`
- I want scaffold initialization to start
- So that rqmd prompts for a starter requirement key prefix
- So that Enter accepts default `REQ`
- So that generated starter requirement IDs use the selected prefix.

### RQMD-CORE-016: Initial scaffolding content/copy
- **Status:** ✅ Verified
- **Priority:** 🟠 P1 - High
- As a rqmd user when users run `rqmd --init`
- I want scaffold initialization to execute
- So that generated `docs/requirements/README.md` includes a welcome message and instructions for getting started that is copied from:
    - ./init-docs/README.md for the domain index (requirements/README.md)
    - ./init-docs/domain-example.md for the starter domain doc (requirements/domain-example.md)
- So that those instructions are included in the python package README somewhere, so they are published on pypi.org as a simple web page.
- So that those documents are maintained in the "./init-docs" directory in this repo for easy editing and management.

### RQMD-CORE-017: Branded init and README messaging
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As a rqmd user when I first encounter rqmd through README or `rqmd --init`
- I want branded, persuasive copy and direct project links
- So that the tool clearly positions itself as human-readable, AI-readable, and ready for Requirements Driven Development (RDD).
- So that generated scaffold copy and README messaging include a concise tagline plus direct links to the project GitHub homepage and/or PyPI page.

### RQMD-CORE-018: First-class binary flagged field
- **Status:** 🔧 Implemented
- As a rqmd user when I want to focus on a subset of requirements without changing project statuses
- I want a simple binary flagged field on requirements
- So that I can mark items for attention without introducing a new `Flagged` status into the status catalog.
- So that flagged state can later participate in interactive focus workflows, filtering, and automation.

### RQMD-CORE-019: Domain-level body parsing and preservation
- **Status:** 💡 Proposed
- As a rqmd maintainer when requirement domains include long-form narrative notes
- I want each domain markdown file to support an explicit optional domain-level body section (separate from per-requirement bodies)
- So that implementation rationale, migration guidance, and AI-generated domain notes can live at domain scope without polluting requirement entries.
- So that parsing and summary regeneration preserve domain-body content verbatim and never treat it as requirement text.
- So that future interactive and automation surfaces can consume this domain-body model through a single canonical core contract.
