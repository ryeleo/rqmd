# Semantic Versioning Policy

rqmd follows Semantic Versioning (`MAJOR.MINOR.PATCH`).

## Version bump rules

- PATCH: backward-compatible bug fixes, docs updates, and internal refactors with no user-facing behavior change.
- MINOR: backward-compatible feature additions, new optional flags, and additive JSON fields.
- MAJOR: breaking changes to CLI flags, defaults, output contracts, or automation behavior.

## CLI compatibility guidance

- Preserve existing command flags and aliases whenever possible.
- If a flag or output behavior must change incompatibly, ship the change in a major release.
- Prefer additive options before removing or repurposing existing behavior.

## Release tagging

- Git tags must use the package version format: `vX.Y.Z` for stable releases or `vX.Y.ZrcN` for release candidates.
- The tagged version must match `project.version` in `pyproject.toml`.

## Prereleases

- Release candidates should use PEP 440 `rc` versions such as `0.1.0rcN`.
- GitHub release tags for release candidates should use the matching form `v0.1.0rcN`.
- Prereleases are appropriate when you want real PyPI installability without promoting a build as the default stable release.
