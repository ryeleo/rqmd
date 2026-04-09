#!/usr/bin/env bash
# gh-release-both.sh — create paired GitHub Releases for rqmd-cli and rqmd-vscode
#
# Usage: ./scripts/gh-release-both.sh <version>
# Example: ./scripts/gh-release-both.sh 0.2.1
#
# Requires: gh CLI authenticated (gh auth login)

set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <version>" >&2
  echo "Example: $0 0.2.1" >&2
  exit 1
fi

VERSION="$1"
TAG="v${VERSION}"
ANCHOR="v${VERSION//./-}"

NOTES="Canonical changelog entries:
- rqmd CLI: https://github.com/ryeleo/rqmd/blob/main/CHANGELOG.md#${ANCHOR}
- rqmd VS Code extension: https://github.com/ryeleo/rqmd-vscode/blob/main/CHANGELOG.md#${ANCHOR}

These two products are released together for this version."

echo "Creating GitHub Releases for ${TAG} ..."

gh release create "${TAG}" \
  --repo ryeleo/rqmd \
  --title "${TAG}" \
  --notes "${NOTES}"

gh release create "${TAG}" \
  --repo ryeleo/rqmd-vscode \
  --title "${TAG}" \
  --notes "${NOTES}"

echo "Done. Both releases are live for ${TAG}."
