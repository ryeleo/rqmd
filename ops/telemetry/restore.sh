#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 /path/to/backup-directory"
  exit 1
fi

BACKUP_DIR="$1"
STACK_ROOT="${STACK_ROOT:-/opt/rqmd/ac-cli}"

cd "${STACK_ROOT}"

set -a
source .env.telemetry.v1
set +a

docker compose --env-file .env.telemetry.v1 -f docker-compose.telemetry.v1.yml up -d postgres minio

for _ in $(seq 1 30); do
  if docker compose --env-file .env.telemetry.v1 -f docker-compose.telemetry.v1.yml exec -T postgres \
    pg_isready -U "${POSTGRES_USER:-rqmd}" -d "${POSTGRES_DB:-rqmd_telemetry}" >/dev/null 2>&1; then
    break
  fi
done

docker compose --env-file .env.telemetry.v1 -f docker-compose.telemetry.v1.yml exec -T postgres \
  psql -U "${POSTGRES_USER:-rqmd}" -d "${POSTGRES_DB:-rqmd_telemetry}" < "${BACKUP_DIR}/postgres.sql"

tar -C /opt/rqmd/telemetry-data -xzf "${BACKUP_DIR}/minio-data.tar.gz"

echo "Restore complete from ${BACKUP_DIR}"
