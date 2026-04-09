# Azure Telemetry v1 (Single VM)

This deployment is intentionally simple and cost-conscious:

- One Linux VM on Azure.
- One Docker Compose stack.
- One systemd unit that keeps the stack running.
- Best-effort availability target (roughly 95 percent).

This keeps operations light while preserving portability. The stack can move across cloud vendors or on-prem with minimal changes.

## Architecture

- Telemetry gateway: FastAPI service from `infra/telemetry-gateway`.
- Database: Postgres container.
- Artifact storage: MinIO container (S3-compatible).
- Optional admin UI: Adminer profile.

## Why this shape works for developer telemetry

- Low cost and simple operations: ~$40–50/month for Standard_B2s + 64 GiB disk in West US 2 (fits comfortably in Azure dev credits).
- No orchestration dependency (no Kubernetes required).
- Data remains on one host with straightforward backups.
- Easy migration path to managed cloud services later.
- Standard_B2s offers 2 vCPU and 4 GiB RAM, sufficient for Postgres + MinIO + gateway with light-to-moderate telemetry load. Override `AZURE_VM_SIZE` in GitHub variables if needed.

## Files added for this blueprint

- `infra/azure/telemetry-vm/`: Terraform for VM provisioning.
- `.github/workflows/deploy-telemetry-vm.yml`: GitHub Actions deployment workflow.
- `docker-compose.telemetry.v1.yml`: production-style compose stack.
- `.env.telemetry.v1.example`: environment template.
- `ops/systemd/rqmd-telemetry.service`: systemd service unit.
- `ops/telemetry/deploy.sh`: install/restart deployment script.
- `ops/telemetry/backup.sh`: backup script.
- `ops/telemetry/restore.sh`: restore script.

## Prerequisites

1. Azure subscription and OIDC GitHub integration.
2. GitHub **environment** secrets (environment: `Azure Telemetry`):
   - `AZURE_CLIENT_ID`
   - `AZURE_TENANT_ID`
   - `AZURE_SUBSCRIPTION_ID`
   - `AZURE_VM_SSH_PUBLIC_KEY`
   - `AZURE_VM_SSH_PRIVATE_KEY`
   - `AZURE_ALLOWED_SSH_CIDR` (for example `203.0.113.10/32`)
3. Optional GitHub repository variables (or environment variables):
   - `AZURE_VM_ADMIN_USERNAME`
   - `AZURE_VM_RESOURCE_GROUP`
   - `AZURE_VM_PREFIX`
   - `AZURE_VM_LOCATION`
   - `AZURE_VM_SIZE`
   - `AZURE_TELEMETRY_PORT`

## First deployment

1. Commit and push these files to `main`, or run the workflow manually.
2. Run workflow: `deploy-telemetry-vm`.
3. SSH to the VM and update `/opt/rqmd/ac-cli/.env.telemetry.v1` with strong secrets:
   - `POSTGRES_PASSWORD`: strong random string
   - `MINIO_ROOT_PASSWORD`: strong random string
   - `TELEMETRY_API_KEY`: shared secret for API authentication (used by agent clients to submit events)
4. Restart service:

```bash
cd /opt/rqmd/ac-cli
sudo systemctl restart rqmd-telemetry
```

5. Verify health:

```bash
curl -sS http://<vm-public-ip>:18080/health
```

## API authentication

All endpoints except `/health` require an API key in the `Authorization` header:

```bash
curl -X POST http://<vm-ip>:18080/api/v1/events \
  -H "Authorization: Bearer <TELEMETRY_API_KEY>" \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "550e8400-e29b-41d4-a716-446655440000",
    "agent_name": "rqmd-dev",
    "event_type": "struggle",
    "severity": "medium",
    "summary": "Command failed unexpectedly"
  }'
```

The `TELEMETRY_API_KEY` from your `.env.telemetry.v1` is the shared secret. Distribute this to your agents/clients; it's embedded in their configurations so they can send events.

## Configuring agents

Agents discover the endpoint and API key through two sources, checked in order:

### Option 1: Environment variables (recommended for CI and local dev)

```bash
export RQMD_TELEMETRY_ENDPOINT="http://<vm-public-ip>:18080"
export RQMD_TELEMETRY_API_KEY="<your-telemetry-api-key>"
```

Set these in your shell profile, CI secrets, or `.env` file (never commit the key).

### Option 2: Project config file

Add a `telemetry` section to your `rqmd.yml` (or `rqmd.yaml` / `rqmd.json`):

```yaml
telemetry:
  endpoint: "http://<vm-public-ip>:18080"
  api_key: "<your-telemetry-api-key>"
```

> **⚠️ Note:** If you commit `rqmd.yml` to version control, use a placeholder for `api_key` and override it via the environment variable at runtime. Never commit real secrets.

### Verify agent configuration

Run the built-in status check to confirm the agent can reach the gateway:

```bash
rqmd telemetry --json
```

This reports whether the endpoint is configured, reachable, and whether an API key is present.

## Backup and restore

Run backup:

```bash
cd /opt/rqmd/ac-cli
./ops/telemetry/backup.sh
```

Restore from snapshot directory:

```bash
cd /opt/rqmd/ac-cli
./ops/telemetry/restore.sh /opt/rqmd/telemetry-backups/<timestamp>
```

## Open-source portability note

This v1 uses Docker + Postgres + S3-compatible object storage primitives. To switch clouds or hosting types later, keep the same gateway contract and only swap infrastructure around it.

## About Garage as an object-store alternative

Garage is a good candidate when you want distributed storage behavior. For this v1 baseline, MinIO keeps setup friction low and is already integrated in the gateway and compose stack. A future step can add a storage backend abstraction in the gateway so MinIO and Garage are interchangeable via config.
