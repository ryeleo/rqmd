# Packaging Acceptance Criteria

Scope: package layout, installability, module entrypoints, and publication readiness.

<!-- acceptance-status-summary:start -->
Summary: 2💡 5🔧 0💻 0🎮 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### AC-ACCLI-PACKAGING-001: src-layout package structure
- **Status:** 🔧 Implemented
- Given the package source tree
- When inspected
- Then Python package code lives under `src/ac_cli`
- And project metadata is defined in `pyproject.toml`.

### AC-ACCLI-PACKAGING-002: Console entrypoint
- **Status:** 🔧 Implemented
- Given package is installed
- When user runs `ac-cli`
- Then command invokes package main CLI handler
- And matches module behavior.

### AC-ACCLI-PACKAGING-003: Module entrypoint
- **Status:** 🔧 Implemented
- Given package source is available
- When user runs `python -m ac_cli`
- Then CLI starts successfully
- And exposes same command options as console script.

### AC-ACCLI-PACKAGING-004: Runtime dependencies declared
- **Status:** 🔧 Implemented
- Given project metadata in pyproject
- When package is installed
- Then required dependencies include click and tabulate
- And missing dependency crashes are avoided at runtime.

### AC-ACCLI-PACKAGING-005: Readme-backed usage docs
- **Status:** 🔧 Implemented
- Given package folder is copied to a new project
- When user reads README
- Then install and command examples are present
- And portability flags are documented.

### AC-ACCLI-PACKAGING-006: PyPI metadata hardening
- **Status:** 💡 Proposed
- Given package is prepared for public release
- When metadata is finalized
- Then author/license/classifiers/urls are complete
- And build+upload instructions remain valid.

### AC-ACCLI-PACKAGING-007: Semantic versioning policy
- **Status:** 💡 Proposed
- Given package evolves across projects
- When versions are tagged
- Then backward-compatible changes use minor/patch bumps
- And breaking CLI changes trigger major version bumps.
