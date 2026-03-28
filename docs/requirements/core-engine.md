# Core Engine Requirement

Scope: parsing, status normalization, summary generation, and requirement discovery.

<!-- acceptance-status-summary:start -->
Summary: 1💡 7🔧 16✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-CORE-001: Domain file discovery
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when repo root and requirements directory are configured
- I want the tool to scan for domain docs
- So that all markdown files in that directory are discovered in stable sorted order
- So that non-markdown files are ignored.

### RQMD-CORE-002: Status line parsing
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when a requirement block with a status line
- I want the parser to read the document
- So that the status is extracted from `- **Status:** ...`
- So that requirement metadata retains status line location for edits.

### RQMD-CORE-003: Canonical status normalization
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when variant status spellings or aliases
- I want normalization to run
- So that the status is rewritten to canonical labels
- So that unsupported values remain unchanged unless explicitly updated by user action.

### RQMD-CORE-004: Summary block insertion
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when a domain file without a summary block
- I want processing to run
- So that a summary block is inserted near the top of the file
- So that the block format uses acceptance-status-summary markers.

### RQMD-CORE-005: Summary block replacement
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when a domain file with an existing summary block
- I want status counts change
- So that only the existing summary block content is replaced
- So that unrelated document content is preserved.

### RQMD-CORE-006: Status count model
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when canonical statuses are present in a file
- I want counts to be computed
- So that counts include all supported statuses in fixed order
- So that summary output uses count+emoji format.

### RQMD-CORE-007: Requirement header matching
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when requirement headings follow `### <PREFIX>-...: ...`
- I want parsing to run
- So that each matching requirement is discoverable by ID
- So that title text is preserved for menu and reporting output
- So that prefix handling follows configured or auto-detected `--id-namespace` behavior.

### RQMD-CORE-008: Idempotent processing
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when no status or summary changes are needed
- I want processing to run repeatedly
- So that generated output remains byte-stable for those files
- So that no unnecessary rewrites occur.

### RQMD-CORE-009: Missing domain docs handling
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when no domain markdown files are found
- I want to run the command
- So that reqmd prints a clear, actionable error message
- So that it offers to initialize a starter requirements project in the current working directory (the same behavior as `--bootstrap`)
- So that the tool never creates files without explicit user confirmation: the initialization flow must prompt the user to confirm creation and allow a `--force-yes`/`--force-confirm` override for automation
- So that in non-interactive or CI contexts the tool exits non-zero and prints the guidance to run `rqmd --bootstrap` or `rqmd --bootstrap --force-yes` to create starter files.

### RQMD-CORE-010: Blocked/deprecated reason extraction
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when a requirement includes blocked or deprecated reason lines
- I want parsing to run
- So that those reason lines are captured with line references
- So that they can be updated or removed consistently by status mutation paths.

### RQMD-CORE-011: Project scaffold initialization
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when a project does not yet have requirement documentation
- I want to run an initialization command
- So that boilerplate docs are created including `docs/requirements/README.md`
- So that a starter domain directory `docs/requirements/` is created
- So that generated content follows the requirements index/domain pattern used by this tool.

### RQMD-CORE-012: Starter dummy requirement generation
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when initialization is generating starter requirement content
- I want to create starter domain docs
- So that at least one easy-to-delete sample requirement `<PREFIX>-HELLO-001` is included
- So that the sample clearly indicates it is a handoff placeholder for teams to replace.

### RQMD-CORE-013: Domain-sync maintenance over time
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when users add or evolve domain documentation over time
- I want to run sync/maintenance commands
- So that index and domain-document references are kept consistent with current domain files
- So that stale or missing domain links are flagged with actionable output
- So that summary/state regeneration remains accurate after domain additions, removals, or renames.

### RQMD-CORE-014: Automatic ID prefix detection from requirements index
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when users do not pass `--id-namespace`
- I want rqmd to read `docs/requirements/README.md` and linked domain docs
- So that requirement ID prefixes are auto-detected from discovered requirement headers
- So that filter/lookup/update flows use those detected prefixes without extra CLI flags.

### RQMD-CORE-015: Init key prompt with customizable default
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when users run `rqmd --bootstrap`
- I want scaffold initialization to start
- So that rqmd prompts for a starter requirement key prefix
- So that Enter accepts default `REQ`
- So that generated starter requirement IDs use the selected prefix.

### RQMD-CORE-016: Initial scaffolding content/copy
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when users run `rqmd --bootstrap`
- I want scaffold initialization to execute
- So that generated `docs/requirements/README.md` includes a welcome message and instructions for getting started that is copied from:
    - ./init-docs/README.md for the domain index (requirements/README.md)
    - ./init-docs/domain-example.md for the starter domain doc (requirements/domain-example.md)
- So that those instructions are included in the python package README somewhere, so they are published on pypi.org as a simple web page.
- So that those documents are maintained in the "./init-docs" directory in this repo for easy editing and management.

### RQMD-CORE-017: Branded init and README messaging
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when I first encounter rqmd through README or `rqmd --bootstrap`
- I want branded, persuasive copy and direct project links
- So that the tool clearly positions itself as human-readable, AI-readable, and ready for Requirements Driven Development (RDD).
- So that generated scaffold copy and README messaging include a concise tagline plus direct links to the project GitHub homepage and/or PyPI page.

### RQMD-CORE-018: First-class binary flagged field
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when I want to focus on a subset of requirements without changing project statuses
- I want a simple binary flagged field on requirements
- So that I can mark items for attention without introducing a new `Flagged` status into the status catalog.
- So that flagged state can later participate in interactive focus workflows, filtering, and automation.

### RQMD-CORE-019: Domain-level body parsing and preservation
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a rqmd maintainer when requirement domains include long-form narrative notes
- I want each domain markdown file to support an explicit optional domain-level body section (separate from per-requirement bodies)
- So that implementation rationale, migration guidance, and AI-generated domain notes can live at domain scope without polluting requirement entries.

### RQMD-CORE-020: H2 subsection parsing and metadata capture
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a rqmd maintainer when a domain markdown file includes H2 section headings
- I want rqmd to recognize H2 headers as subsection boundaries
- So that each requirement captures a `sub_domain` metadata field indicating which H2 section contains it
- So that optional narrative body content between an H2 header and the first H3 requirement below it is captured as subsection-level body content
- So that H2 sections are optional; requirements without a containing H2 have empty/null `sub_domain`
- So that subsection names are normalized deterministically (trimmed, lowercased internally for matching; original case preserved for display)
- So that RQMD-AUTOMATION-029/030 and RQMD-INTERACTIVE-020/021 can expose subsection metadata for filtering, JSON export, and completion behavior.
- So that parsing and summary regeneration preserve domain-body content verbatim and never treat it as requirement text.
- So that future interactive and automation surfaces can consume this domain-body model through a single canonical core contract.

### RQMD-CORE-021: Per-requirement external links field
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when I want to link a requirement to external systems (GitHub issues, Jira, TDX, etc.)
- I want each requirement to support an optional top-level `**Links:**` field
- So that the field appears directly below Status/Priority and contains one or more link entries as list items
- So that each entry may be a plain URL or a markdown hyperlink in `[label](url)` format
- So that the parser recognizes the `**Links:**` field as a first-class top-level metadata field alongside Status and Priority
- So that requirements without a Links field parse and serialize without any change in behavior
- So that the links list is included in JSON export as a `links` array where each entry carries `url` and optional `label` fields
- So that plain URLs without markdown formatting are stored with a null/empty label and round-trip back as plain URLs
- So that write-back preserves the original link formatting verbatim unless the user explicitly edits or reformats it
- So that summary block generation and status counting are not affected by the presence or absence of links.

### RQMD-CORE-022: Enhanced blocking with linked requirements
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when marking a requirement as blocked
- I want to optionally link it to another requirement that is blocking it
- So that the block reason field supports both free-form text and markdown hyperlinks to other requirement IDs
- So that users can quickly navigate between blocking and blocked requirements
- So that interactive mode offers a search/select UI for finding and linking blocking requirements by ID or title prefix
- So that round-trip editing preserves manually entered hyperlinks verbatim
- So that JSON export includes an optional `blocking_id` field capturing the linked requirement ID when present.

### RQMD-CORE-023: Global requirement ID prefix renaming tool
- **Status:** 💡 Proposed
- **Priority:** 🟢 P3 - Low
- As a rqmd user when a project outgrows its initial ID prefix (e.g., REQ- becomes too generic)
- I want a one-time bulk rename command
- So that all requirement headers, links, and citations are updated consistently across all domain files
- So that the tool validates that the new prefix is unique and does not conflict with existing IDs in other domains
- So that the operation is reversible via undo (once RQMD-UNDO is implemented)
- So that a summary report shows all changed files and rename counts.

### RQMD-CORE-024: Generated top-level README from requirement domains
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when project README guidance drifts from requirement docs
- I want rqmd to generate the project-level README requirement index sections from domain files automatically and on demand
- So that top-level README sections describing requirement domains and status rollups are regenerated deterministically from `docs/requirements/*.md`
- So that generated sections are clearly bounded by markers and preserve hand-authored content outside those markers
- So that repeated generation is idempotent and produces no diff when inputs are unchanged
- So that teams can treat README generation as a routine maintenance step in local workflows and CI.
- So that during normal usage, the README is automatically kept up to date 
- So that every time the summary renders or anything changes, make sure the README is up to date (if that isn't too slow..? -- test performance when we add this)
- So that when app opens, when app closes, when user makes any change in any requirement file, the top level README is kept up to date.
- So that README can be regenerated with separate CLI flag.
