# Packaging Requirements

Scope: package layout, installability, module entrypoints, and publication readiness.

<!-- acceptance-status-summary:start -->
Summary: 3💡 5🔧 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### REQMD-PACKAGING-001: src-layout package structure
- **Status:** 🔧 Implemented
- Given the package source tree
- When inspected
- Then Python package code lives under `src/reqmd`
- And project metadata is defined in `pyproject.toml`.

### REQMD-PACKAGING-002: Console entrypoint
- **Status:** 🔧 Implemented
- Given package is installed
- When user runs `reqmd`
- Then command invokes package main CLI handler
- And matches module behavior.

### REQMD-PACKAGING-003: Module entrypoint
- **Status:** 🔧 Implemented
- Given package source is available
- When user runs `python -m reqmd`
- Then CLI starts successfully
- And exposes same command options as console script.

### REQMD-PACKAGING-004: Runtime dependencies declared
- **Status:** 🔧 Implemented
- Given project metadata in pyproject
- When package is installed
- Then required dependencies include click and tabulate
- And missing dependency crashes are avoided at runtime.

### REQMD-PACKAGING-005: Readme-backed usage docs
- **Status:** 🔧 Implemented
- Given package folder is copied to a new project
- When user reads README
- Then install and command examples are present
- And portability plus ID-prefix flags are documented.

### REQMD-PACKAGING-006: PyPI metadata hardening
- **Status:** 💡 Proposed
- Given package is prepared for public release
- When metadata is finalized
- Then author/license/classifiers/urls are complete
- And build+upload instructions remain valid.

### REQMD-PACKAGING-007: Semantic versioning policy
- **Status:** 💡 Proposed
- Given package evolves across projects
- When versions are tagged
- Then backward-compatible changes use minor/patch bumps
- And breaking CLI changes trigger major version bumps.

### REQMD-PACKAGING-008: Publish to PyPI on GitHub release
- **Status:** 💡 Proposed
- Given a GitHub release is created for this repository
- When the release workflow runs
- Then the tagged package version is published to pypi.org automatically
- And publication uses repository automation rather than a manual local upload.
