#!/usr/bin/env bash
set -euo pipefail

STACK_ROOT="${STACK_ROOT:-/opt/rqmd/ac-cli}"
BACKUP_ROOT="${BACKUP_ROOT:-/opt/rqmd/telemetry-backups}"
TS="$(date +%Y%m%d-%H%M%S)"
DEST="${BACKUP_ROOT}/${TS}"

mkdir -p "${DEST}"

cd "${STACK_ROOT}"

set -a
source .env.telemetry.v1
set +a

# Capture Postgres schema/data for telemetry events.
docker compose --env-file .env.telemetry.v1 -f docker-compose.telemetry.v1.yml exec -T postgres \
  pg_dump -U "${POSTGRES_USER:-rqmd}" -d "${POSTGRES_DB:-rqmd_telemetry}" > "${DEST}/postgres.sql"

# Snapshot object storage data volume.
tar -C /opt/rqmd/telemetry-data -czf "${DEST}/minio-data.tar.gz" minio

echo "Backup complete: ${DEST}"
