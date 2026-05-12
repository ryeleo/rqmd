#!/usr/bin/env bash
# Open SSH tunnels to the remote telemetry VM so local admin tools
# (Adminer, VS Code extensions, MinIO console) can reach the backends.
#
# Usage:
#   ./scripts/telemetry-tunnel.sh <vm-ip> [ssh-user] [ssh-key]
#
# Tunnels opened:
#   localhost:55432 → VM Postgres (55432)
#   localhost:19001 → VM MinIO console (19001)
#   localhost:19000 → VM MinIO API (19000)
#
# Press Ctrl+C to close all tunnels.

set -euo pipefail

VM_IP="${1:?Usage: $0 <vm-ip> [ssh-user] [ssh-key]}"
SSH_USER="${2:-azureuser}"
SSH_KEY="${3:-}"

SSH_OPTS=(-N -o ServerAliveInterval=30 -o ServerAliveCountMax=3)
if [[ -n "$SSH_KEY" ]]; then
  SSH_OPTS+=(-i "$SSH_KEY")
fi

echo "Opening SSH tunnels to $VM_IP..."
echo ""
echo "  localhost:18080 → Telemetry gateway HTTP"
echo "  localhost:55432 → Postgres"
echo "  localhost:19000 → MinIO API"
echo "  localhost:19001 → MinIO Console"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "  MinIO Console:  http://localhost:19001"
echo "    → Log in with your production MINIO_ROOT_USER / MINIO_ROOT_PASSWORD"
echo ""
echo "  Adminer (DB):   http://localhost:8081"
echo "    → Start it:  docker compose -f docker-compose.telemetry-admin.yml up -d"
echo "    → System:    PostgreSQL"
echo "    → Server:    host.docker.internal:55432  (NOT localhost!)"
echo "    → Username:  your production POSTGRES_USER"
echo "    → Password:  your production POSTGRES_PASSWORD"
echo "    → Database:  rqmd_telemetry"
echo ""
echo "  VS Code DB:     Connect any Postgres extension to localhost:55432"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "Press Ctrl+C to close all tunnels."

ssh "${SSH_OPTS[@]}" \
  -L 18080:127.0.0.1:18080 \
  -L 55432:127.0.0.1:55432 \
  -L 19000:127.0.0.1:19000 \
  -L 19001:127.0.0.1:19001 \
  "${SSH_USER}@${VM_IP}"
