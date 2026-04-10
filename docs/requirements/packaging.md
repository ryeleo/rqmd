# Packaging Requirements

Scope: package layout, installability, module entrypoints, and publication readiness.

<!-- acceptance-status-summary:start -->
Summary: 0💡 4🔧 10✅ 0⚠️ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-PACKAGING-001: src-layout package structure
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when the package source tree
- I want to inspect it
- So that Python package code lives under `src/rqmd`
- So that project metadata is defined in `pyproject.toml`.

### RQMD-PACKAGING-002: Console entrypoint
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when package is installed
- I want to run `rqmd`
- So that command invokes package main CLI handler
- So that it matches module behavior.

### RQMD-PACKAGING-003: Module entrypoint
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when package source is available
- I want to run `python -m rqmd`
- So that CLI starts successfully
- So that exposes same command options as console script.

### RQMD-PACKAGING-004: Runtime dependencies declared
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when project metadata in pyproject
- I want to install the package
- So that required dependencies include click and tabulate
- So that missing dependency crashes are avoided at runtime.

### RQMD-PACKAGING-005: Readme-backed usage docs
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when package folder is copied to a new project
- I want to read README
- So that install and command examples are present
- So that portability plus ID-prefix flags are documented.

### RQMD-PACKAGING-006: PyPI metadata hardening
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when package is prepared for public release
- I want to finalize metadata
- So that author/license/classifiers/urls are complete
- So that build+upload instructions remain valid.

### RQMD-PACKAGING-007: Semantic versioning policy
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when package evolves across projects
- I want to tag versions
- So that backward-compatible changes use minor/patch bumps
- So that breaking CLI changes trigger major version bumps.

### RQMD-PACKAGING-008: Publish to PyPI on stable release or rc tag
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when a stable release or internal release candidate is cut for this repository
- I want to run the release workflow
- So that the tagged package version is published to pypi.org automatically
- So that publication uses repository automation rather than a manual local upload.
- So that stable versions publish from a GitHub Release, while PEP 440 `rc` prerelease tags can publish directly from a matching tag push without requiring a full GitHub Release.
- So that publication only proceeds for stable semver release tags or PEP 440 `rc` prerelease tags, and validates that the release tag matches `project.version` before publishing.
- So that publication can use GitHub Actions trusted publishing instead of a long-lived PyPI API token.
- So that release-tag validation logic lives in a repository Python script and can be syntax-checked in CI instead of being embedded inline in workflow YAML.

### RQMD-PACKAGING-009: Keep a Changelog maintained
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- As a rqmd user when contributors ship notable changes
- I want to prepare release and pre-release updates
- So that repository contains a root-level `CHANGELOG.md` following Keep a Changelog structure
- So that updates are recorded under an `Unreleased` section before version cut.

### RQMD-PACKAGING-010: Shell completion distribution and activation guidance
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when installing rqmd on a workstation
- I want shell completion support to be available for zsh (and documented for bash/fish where supported)
- So that users can enable completion using standard shell-init patterns without hand-maintaining completion scripts.
- So that dynamic completion can query rqmd for current domain/requirement tokens at completion time and stay in sync with repository docs.
- So that packaging/README instructions include copy-paste-safe activation commands and troubleshooting notes for completion cache refresh.

### RQMD-PACKAGING-011: Shell completion for positional filter tokens
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a rqmd user when shell completion is enabled and I type positional tokens instead of explicit filter flags
- I want completion candidates for status and priority filter values to appear alongside requirement IDs, domain identifiers, and subsection names
- So that workflows such as `rqmd Pro<TAB>` or `rqmd P1 core<TAB>` remain discoverable and fast without requiring me to remember whether a token is accepted positionally.
- So that completion ordering and display make it clear when a suggestion is a status filter, priority filter, requirement ID, domain token, or subsection token.
- So that the completion engine respects the same precedence and ambiguity rules defined for positional filter-token parsing rather than suggesting tokens that would later resolve differently at execution time.
- So that completion remains deterministic when a token prefix could match both a positional filter value and a domain or subsection name.

### RQMD-PACKAGING-012: Pre-release ReqMD rename and alias plan
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
- As a maintainer when deciding whether the project should be branded as `rqmd` or `reqmd` before broader release
- I want packaging and entrypoint behavior to support an explicit rename/alias plan
- So that the project can adopt `reqmd` branding or a dual-command transition without breaking existing installs, docs, or automation unexpectedly.
- So that any rename decision includes PyPI package-name availability checks, console-script alias behavior, documentation updates, and a compatibility window for existing `rqmd` users.
- So that the package can ship `reqmd` and `reqmd-ai` as pre-release console-script aliases while keeping `rqmd` and `rqmd-ai` as the canonical commands until a future rename decision is finalized.

### RQMD-PACKAGING-014: Fold rqmd-ai query flags into rqmd CLI
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a user or AI agent querying requirements in machine-readable format
- I want the structured JSON export and query flags currently on `rqmd-ai` (e.g., `--json`, `--dump-status`, `--dump-type`, `--dump-id`, `--dump-file`, `--include-requirement-body`, `--include-domain-markdown`, batch mode) folded into the `rqmd` CLI itself
- So that querying requirements in JSON is just a standard `rqmd` feature, not something that requires a separate AI-specific entrypoint.
- So that `rqmd --json` becomes the canonical machine-readable export and agents call `rqmd` directly.
- So that the `--update` and `--write` mutation flags also move to `rqmd` (e.g., `rqmd --update RQMD-CORE-001=implemented --write`).
- Given a user who runs `rqmd --json --dump-status proposed`
- When the command executes
- Then the output is identical to what `rqmd-ai --json --dump-status proposed` produces today.
- And `rqmd --json` includes `next_id` per domain file, the same schema version, and all existing export fields.

### RQMD-PACKAGING-015: Deprecate and remove rqmd-ai CLI entrypoint
- **Status:** ✅ Verified
- **Priority:** 🟡 P2 - Medium
- **Blocked by:** RQMD-EXT-051
- As the rqmd maintainer after the VS Code extension ships and query flags are folded into `rqmd`
- I want to deprecate and eventually remove the `rqmd-ai` console-script entrypoint
- So that there is one CLI command (`rqmd`) and one IDE integration point (the VS Code extension), not a confusing split between `rqmd` and `rqmd-ai`.
- So that `rqmd-ai` emits a deprecation warning pointing users to `rqmd --json` for a transition period before removal.
- Given a user who runs `rqmd-ai --json`
- When the deprecation period is active
- Then the command still works but prints a stderr warning: "rqmd-ai is deprecated. Use `rqmd --json` instead."
- And after the removal version, the `rqmd-ai` entrypoint is no longer registered in the package.


