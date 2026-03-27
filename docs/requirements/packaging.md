# Packaging Requirements

Scope: package layout, installability, module entrypoints, and publication readiness.

<!-- acceptance-status-summary:start -->
Summary: 0💡 0🔧 9✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-PACKAGING-001: src-layout package structure
- **Status:** ✅ Verified
- As a rqmd user when the package source tree
- I want to inspect it
- So that Python package code lives under `src/rqmd`
- So that project metadata is defined in `pyproject.toml`.

### RQMD-PACKAGING-002: Console entrypoint
- **Status:** ✅ Verified
- As a rqmd user when package is installed
- I want to run `rqmd`
- So that command invokes package main CLI handler
- So that it matches module behavior.

### RQMD-PACKAGING-003: Module entrypoint
- **Status:** ✅ Verified
- As a rqmd user when package source is available
- I want to run `python -m rqmd`
- So that CLI starts successfully
- So that exposes same command options as console script.

### RQMD-PACKAGING-004: Runtime dependencies declared
- **Status:** ✅ Verified
- As a rqmd user when project metadata in pyproject
- I want to install the package
- So that required dependencies include click and tabulate
- So that missing dependency crashes are avoided at runtime.

### RQMD-PACKAGING-005: Readme-backed usage docs
- **Status:** ✅ Verified
- As a rqmd user when package folder is copied to a new project
- I want to read README
- So that install and command examples are present
- So that portability plus ID-prefix flags are documented.

### RQMD-PACKAGING-006: PyPI metadata hardening
- **Status:** ✅ Verified
- As a rqmd user when package is prepared for public release
- I want to finalize metadata
- So that author/license/classifiers/urls are complete
- So that build+upload instructions remain valid.

### RQMD-PACKAGING-007: Semantic versioning policy
- **Status:** ✅ Verified
- As a rqmd user when package evolves across projects
- I want to tag versions
- So that backward-compatible changes use minor/patch bumps
- So that breaking CLI changes trigger major version bumps.

### RQMD-PACKAGING-008: Publish to PyPI on GitHub release
- **Status:** ✅ Verified
- As a rqmd user when a GitHub release is created for this repository
- I want to run the release workflow
- So that the tagged package version is published to pypi.org automatically
- So that publication uses repository automation rather than a manual local upload.

### RQMD-PACKAGING-009: Keep a Changelog maintained
- **Status:** ✅ Verified
- As a rqmd user when contributors ship notable changes
- I want to prepare release and pre-release updates
- So that repository contains a root-level `CHANGELOG.md` following Keep a Changelog structure
- So that updates are recorded under an `Unreleased` section before version cut.
