# Releasing rqmd

This repository publishes rqmd to PyPI through GitHub Actions trusted publishing.

## First-time PyPI trusted publisher setup

Do this once before your first release from this repository:

1. Create or sign in to your account on `pypi.org`.
2. Verify your email address and enable two-factor authentication on the PyPI account that will own the project.
3. Reserve the project through a pending publisher instead of creating a long-lived API token.
4. On PyPI, open Account Settings -> Publishing and add a new pending publisher.
5. Choose GitHub Actions and enter:
   - PyPI project name: `rqmd`
   - Owner: your GitHub user or organization
   - Repository name: this repository
   - Workflow name: `publish-pypi.yml`
   - Environment name: `pypi`
6. In GitHub, open repository Settings -> Environments and create an environment named `pypi` if it does not already exist.
7. If you want extra guardrails, add environment protection rules such as restricting deployment to tags or requiring manual approval.
8. Confirm `.github/workflows/publish-pypi.yml` still requests `id-token: write` and uses the same `pypi` environment name.
9. Your first successful GitHub Release publish will create the project on PyPI and bind it to that trusted publisher configuration.

Notes:

- You do not need to store a `PYPI_API_TOKEN` in GitHub secrets for this flow.
- The pending publisher must match the GitHub owner, repository, workflow file, and environment exactly.
- If the `rqmd` name is already taken on PyPI, you will need to use the existing owner account or pick a different package name before releasing.

## Pre-release checklist

Before cutting a stable release or release candidate:

1. Ensure `project.version` in `pyproject.toml` matches the version you intend to ship.
2. Move the relevant items from `CHANGELOG.md` `Unreleased` into a versioned release section if you are cutting a formal release note.
3. Run the repository smoke path and targeted tests:
   - `bash scripts/local-smoke.sh`
   - `uv run --extra dev pytest`
4. Confirm the package metadata still points at the intended public URLs and package name.
5. Confirm the GitHub repository `pypi` environment is configured for PyPI trusted publishing for the `rqmd` project.

## Release steps

1. Choose a tag that matches `project.version`, such as `v0.1.0` for a stable release or `v0.1.0rcN` for a release candidate.
2. Ensure that tag exactly matches `project.version` after removing the optional leading `v`.
3. Push the release commit and create a GitHub Release with that tag.
4. Publish the GitHub Release.
5. Wait for `.github/workflows/publish-pypi.yml` to finish successfully.
6. Verify the new version appears on PyPI and that `pip install rqmd==<version>` succeeds.

## Notes

- The publish workflow accepts stable releases and PEP 440 `rc` prereleases such as `0.1.0rcN`.
- The publish workflow rejects tags that do not match `project.version` in `pyproject.toml`.
- Publication uses GitHub Actions trusted publishing via the `pypi` environment instead of a repository-stored `PYPI_API_TOKEN`.