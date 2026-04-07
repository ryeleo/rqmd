#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "${SCRIPT_DIR}/../.." && pwd)"

cd "${REPO_ROOT}"

if [[ ! -f .env.telemetry.v1 ]]; then
  cp .env.telemetry.v1.example .env.telemetry.v1
  echo "Created .env.telemetry.v1 from template. Update secrets before exposing telemetry externally."
fi

sudo install -m 0644 ops/systemd/rqmd-telemetry.service /etc/systemd/system/rqmd-telemetry.service
sudo systemctl daemon-reload
sudo systemctl enable rqmd-telemetry
sudo systemctl restart rqmd-telemetry

sudo systemctl --no-pager --full status rqmd-telemetry
