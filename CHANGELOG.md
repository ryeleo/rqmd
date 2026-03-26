# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Added a project changelog following the Keep a Changelog format.
- Added README-index portability tests for automatic requirements discovery.
- Added deep scratch pagination corpus pages through page 23 for e2e coverage.
- Added first-class `--json` output for non-interactive summary/check/set/filter workflows to support machine-readable automation and AI triage.

### Changed

- Switched requirements index layout from sibling requirements.md files to in-directory README.md files.
- Updated rqmd auto-detection to use docs/requirements/README.md and requirements/README.md.
- Updated scaffold generation to create README.md inside the requirements directory.
- Updated portability, core-engine, and README documentation to match the new requirements index contract.

## [0.1.0] - 2026-03-26

### Added

- Initial rqmd package release with interactive and automation-friendly requirements status workflows.