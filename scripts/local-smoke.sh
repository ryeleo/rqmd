#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
UV_BIN="${UV_BIN:-uv}"
SKIP_INSTALL="false"

for arg in "$@"; do
  case "$arg" in
    --skip-install)
      SKIP_INSTALL="true"
      ;;
    *)
      echo "Unknown argument: $arg" >&2
      echo "Usage: bash scripts/local-smoke.sh [--skip-install]" >&2
      exit 2
      ;;
  esac
done

cd "$ROOT_DIR"

if ! command -v "$UV_BIN" >/dev/null 2>&1; then
  echo "[rqmd] uv is required for this developer workflow" >&2
  exit 1
fi

echo "[rqmd] uv: $UV_BIN"
"$UV_BIN" --version

if [[ "$SKIP_INSTALL" != "true" ]]; then
  echo "[rqmd] Syncing project + dev dependencies"
  "$UV_BIN" sync --extra dev
fi

echo "[rqmd] Running pytest"
"$UV_BIN" run --extra dev pytest -q

echo "[rqmd] Running acceptance summary check"
"$UV_BIN" run rqmd --project-root . --docs-dir docs/requirements --verify-summaries --no-walk --no-table

echo "[rqmd] Smoke checks passed"
