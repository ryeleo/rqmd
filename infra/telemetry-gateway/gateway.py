"""rqmd telemetry gateway.

A lightweight FastAPI service that accepts structured telemetry events
from AI agents and stores them in Postgres, with optional artifact
uploads to MinIO.
"""

from __future__ import annotations

import hashlib
import hmac
import os
import time
import uuid
from collections import defaultdict
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Any, Literal

import asyncpg
from fastapi import (Depends, FastAPI, File, Form, Header, HTTPException,
                     Request, UploadFile)
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Configuration from environment
# ---------------------------------------------------------------------------

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://rqmd:rqmd_dev_pw@localhost:5432/rqmd_telemetry",
)
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://localhost:9000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin_dev_pw")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "rqmd-telemetry")
MINIO_REGION = os.environ.get("MINIO_REGION", "us-east-1")
MINIO_SECURE = os.environ.get("MINIO_SECURE", "false").lower() == "true"
TELEMETRY_API_KEY = os.environ.get("TELEMETRY_API_KEY", "changeme-dev-only")

# Token exchange settings
TOKEN_SECRET = os.environ.get("TELEMETRY_TOKEN_SECRET", "dev-token-secret-change-in-prod")
TOKEN_TTL_SECONDS = int(os.environ.get("TELEMETRY_TOKEN_TTL", "3600"))  # 1 hour

# Accepted client identifiers that may request a session token.
# The client_id shipped in the rqmd package is public and non-secret.
ALLOWED_CLIENT_IDS = set(
    filter(None, os.environ.get("TELEMETRY_ALLOWED_CLIENT_IDS", "rqmd-agent-v1").split(","))
)

# Rate limiting (in-memory sliding window)
RATE_LIMIT_EVENTS_PER_WINDOW = int(os.environ.get("RATE_LIMIT_EVENTS_PER_WINDOW", "60"))
RATE_LIMIT_WINDOW_SECONDS = int(os.environ.get("RATE_LIMIT_WINDOW_SECONDS", "60"))
RATE_LIMIT_TOKEN_REQUESTS_PER_WINDOW = int(os.environ.get("RATE_LIMIT_TOKEN_PER_WINDOW", "10"))
RATE_LIMIT_GLOBAL_PER_WINDOW = int(os.environ.get("RATE_LIMIT_GLOBAL_PER_WINDOW", "600"))


# ---------------------------------------------------------------------------
# In-memory sliding-window rate limiter
# ---------------------------------------------------------------------------

class _RateLimiter:
    """Simple per-key sliding-window counter stored in-memory."""

    def __init__(self) -> None:
        self._hits: dict[str, list[float]] = defaultdict(list)

    def is_allowed(self, key: str, limit: int, window: int) -> tuple[bool, int]:
        """Check whether *key* is under the limit.

        Returns ``(allowed, retry_after_seconds)``.
        """
        now = time.monotonic()
        bucket = self._hits[key]
        # Evict expired entries.
        cutoff = now - window
        bucket[:] = [t for t in bucket if t > cutoff]
        if len(bucket) >= limit:
            retry_after = int(bucket[0] - cutoff) + 1
            return False, max(retry_after, 1)
        bucket.append(now)
        return True, 0


_rate_limiter = _RateLimiter()

# ---------------------------------------------------------------------------
# Database schema (applied on startup)
# ---------------------------------------------------------------------------

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS telemetry_events (
    event_id        UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id      UUID NOT NULL,
    timestamp       TIMESTAMPTZ NOT NULL DEFAULT now(),
    agent_name      TEXT,
    event_type      TEXT NOT NULL
                    CHECK (event_type IN (
                        'struggle', 'suggestion', 'error', 'success', 'workflow_step',
                        'feedback'
                    )),
    severity        TEXT NOT NULL
                    CHECK (severity IN ('low', 'medium', 'high', 'critical')),
    summary         TEXT NOT NULL,
    detail          JSONB,
    model_id        TEXT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_events_session  ON telemetry_events (session_id);
CREATE INDEX IF NOT EXISTS idx_events_type     ON telemetry_events (event_type);
CREATE INDEX IF NOT EXISTS idx_events_severity ON telemetry_events (severity);
CREATE INDEX IF NOT EXISTS idx_events_ts       ON telemetry_events (timestamp);
CREATE INDEX IF NOT EXISTS idx_events_model    ON telemetry_events (model_id);

-- Migrations for existing databases (idempotent)
ALTER TABLE telemetry_events ADD COLUMN IF NOT EXISTS model_id TEXT;
ALTER TABLE telemetry_events DROP CONSTRAINT IF EXISTS telemetry_events_event_type_check;
ALTER TABLE telemetry_events ADD CONSTRAINT telemetry_events_event_type_check
    CHECK (event_type IN ('struggle', 'suggestion', 'error', 'success', 'workflow_step', 'feedback'));

CREATE TABLE IF NOT EXISTS telemetry_artifacts (
    artifact_id     UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id        UUID NOT NULL REFERENCES telemetry_events(event_id),
    session_id      UUID NOT NULL,
    object_key      TEXT NOT NULL,
    content_type    TEXT,
    size_bytes      BIGINT,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS idx_artifacts_event   ON telemetry_artifacts (event_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_session ON telemetry_artifacts (session_id);

CREATE TABLE IF NOT EXISTS session_tokens (
    token_hash      TEXT PRIMARY KEY,
    client_id       TEXT NOT NULL,
    session_id      UUID NOT NULL,
    issued_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
    expires_at      TIMESTAMPTZ NOT NULL,
    revoked         BOOLEAN NOT NULL DEFAULT FALSE
);

CREATE INDEX IF NOT EXISTS idx_tokens_expires ON session_tokens (expires_at);
"""

# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------


class EventCreate(BaseModel):
    session_id: str = Field(description="UUID or unique session identifier")
    agent_name: str | None = Field(default=None, description="Agent name")
    event_type: Literal["struggle", "suggestion", "error", "success", "workflow_step", "feedback"]
    severity: Literal["low", "medium", "high", "critical"]
    summary: str = Field(max_length=500, description="Concise event summary")
    detail: dict[str, Any] | None = Field(default=None, description="Structured detail")
    timestamp: str | None = Field(default=None, description="ISO-8601 timestamp")
    model_id: str | None = Field(default=None, description="AI model identifier (e.g. gpt-4o, claude-sonnet-4-5)")


class EventResponse(BaseModel):
    event_id: str
    session_id: str
    status: str = "accepted"


class ArtifactResponse(BaseModel):
    artifact_id: str
    event_id: str
    object_key: str
    status: str = "stored"


class HealthResponse(BaseModel):
    status: str = "healthy"
    postgres: bool = False
    minio: bool = False


class TokenRequest(BaseModel):
    client_id: str = Field(description="Public client identifier shipped in the rqmd package")


class TokenResponse(BaseModel):
    token: str = Field(description="Short-lived Bearer token for the session")
    expires_in: int = Field(description="Token lifetime in seconds")
    session_id: str = Field(description="Session UUID bound to this token")


# ---------------------------------------------------------------------------
# Application
# ---------------------------------------------------------------------------

_pool: asyncpg.Pool | None = None
_minio_client: Any = None


def _get_minio_client():
    global _minio_client
    if _minio_client is None:
        from urllib.parse import urlparse

        from minio import Minio

        parsed = urlparse(MINIO_ENDPOINT)
        endpoint = parsed.netloc or parsed.path
        _minio_client = Minio(
            endpoint,
            access_key=MINIO_ACCESS_KEY,
            secret_key=MINIO_SECRET_KEY,
            secure=MINIO_SECURE,
            region=MINIO_REGION,
        )
    return _minio_client


def _extract_bearer_token(authorization: str = Header(None)) -> str:
    """Extract the Bearer token from the Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    parts = authorization.split(" ")
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(status_code=401, detail="Invalid Authorization header format")
    return parts[1]


async def _verify_api_key(request: Request, token: str = Depends(_extract_bearer_token)) -> None:
    """Verify the Bearer token is either the static API key or a valid session token."""
    # Check rate limit (per-IP for event endpoints).
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = _rate_limiter.is_allowed(
        f"events:{client_ip}", RATE_LIMIT_EVENTS_PER_WINDOW, RATE_LIMIT_WINDOW_SECONDS
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )
    # Global rate limit.
    g_allowed, g_retry = _rate_limiter.is_allowed(
        "global:events", RATE_LIMIT_GLOBAL_PER_WINDOW, RATE_LIMIT_WINDOW_SECONDS
    )
    if not g_allowed:
        raise HTTPException(
            status_code=429,
            detail="Global rate limit exceeded",
            headers={"Retry-After": str(g_retry)},
        )

    # Legacy static API key.
    if token == TELEMETRY_API_KEY:
        return

    # Session token — look up by hash.
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    if _pool:
        async with _pool.acquire() as conn:
            row = await conn.fetchrow(
                "SELECT expires_at, revoked FROM session_tokens WHERE token_hash = $1",
                token_hash,
            )
            if row and not row["revoked"] and row["expires_at"] > datetime.now(timezone.utc):
                return

    raise HTTPException(status_code=401, detail="Invalid or expired token")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _pool
    _pool = await asyncpg.create_pool(DATABASE_URL, min_size=2, max_size=10)
    async with _pool.acquire() as conn:
        await conn.execute(_SCHEMA_SQL)
    yield
    if _pool:
        await _pool.close()


app = FastAPI(
    title="rqmd Telemetry Gateway",
    version="0.1.0",
    lifespan=lifespan,
)


# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------


@app.get("/health", response_model=HealthResponse)
async def health():
    pg_ok = False
    minio_ok = False
    if _pool:
        try:
            async with _pool.acquire() as conn:
                await conn.fetchval("SELECT 1")
            pg_ok = True
        except Exception:
            pass
    try:
        mc = _get_minio_client()
        mc.bucket_exists(MINIO_BUCKET)
        minio_ok = True
    except Exception:
        pass
    return HealthResponse(
        status="healthy" if (pg_ok and minio_ok) else "degraded",
        postgres=pg_ok,
        minio=minio_ok,
    )


@app.post("/api/v1/token", response_model=TokenResponse, status_code=201)
async def exchange_token(req: TokenRequest, request: Request):
    """Exchange a public client_id for a short-lived session token."""
    # Rate-limit token requests per IP.
    client_ip = request.client.host if request.client else "unknown"
    allowed, retry_after = _rate_limiter.is_allowed(
        f"token:{client_ip}", RATE_LIMIT_TOKEN_REQUESTS_PER_WINDOW, RATE_LIMIT_WINDOW_SECONDS
    )
    if not allowed:
        raise HTTPException(
            status_code=429,
            detail="Token request rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )

    if req.client_id not in ALLOWED_CLIENT_IDS:
        raise HTTPException(status_code=403, detail="Unknown client_id")

    if not _pool:
        raise HTTPException(status_code=503, detail="Database not available")

    session_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    from datetime import timedelta
    expires_at = now + timedelta(seconds=TOKEN_TTL_SECONDS)

    # Generate an opaque token: HMAC(secret, session_id + timestamp).
    raw = f"{session_id}:{now.isoformat()}:{uuid.uuid4().hex}"
    token = hmac.new(TOKEN_SECRET.encode(), raw.encode(), hashlib.sha256).hexdigest()
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO session_tokens (token_hash, client_id, session_id, issued_at, expires_at)
            VALUES ($1, $2, $3, $4, $5)
            """,
            token_hash,
            req.client_id,
            session_id,
            now,
            expires_at,
        )

    return TokenResponse(
        token=token,
        expires_in=TOKEN_TTL_SECONDS,
        session_id=str(session_id),
    )


@app.post("/api/v1/events", response_model=EventResponse, status_code=201)
async def create_event(event: EventCreate, _: None = Depends(_verify_api_key)):
    if not _pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        session_uuid = uuid.UUID(event.session_id)
    except ValueError:
        raise HTTPException(status_code=422, detail="session_id must be a valid UUID")

    ts = datetime.now(timezone.utc)
    if event.timestamp:
        try:
            ts = datetime.fromisoformat(event.timestamp)
        except ValueError:
            pass

    import json as _json

    detail_json = _json.dumps(event.detail) if event.detail else None

    async with _pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO telemetry_events
                (session_id, timestamp, agent_name, event_type, severity, summary, detail, model_id)
            VALUES ($1, $2, $3, $4, $5, $6, $7::jsonb, $8)
            RETURNING event_id
            """,
            session_uuid,
            ts,
            event.agent_name,
            event.event_type,
            event.severity,
            event.summary[:500],
            detail_json,
            event.model_id,
        )

    return EventResponse(
        event_id=str(row["event_id"]),
        session_id=str(session_uuid),
    )


@app.post("/api/v1/artifacts", response_model=ArtifactResponse, status_code=201)
async def upload_artifact(
    session_id: str = Form(...),
    event_id: str = Form(...),
    file: UploadFile = File(...),
    _: None = Depends(_verify_api_key),
):
    if not _pool:
        raise HTTPException(status_code=503, detail="Database not available")

    try:
        session_uuid = uuid.UUID(session_id)
        event_uuid = uuid.UUID(event_id)
    except ValueError:
        raise HTTPException(
            status_code=422, detail="session_id and event_id must be valid UUIDs"
        )

    # Verify the event exists.
    async with _pool.acquire() as conn:
        exists = await conn.fetchval(
            "SELECT 1 FROM telemetry_events WHERE event_id = $1", event_uuid
        )
        if not exists:
            raise HTTPException(status_code=404, detail="Event not found")

    artifact_id = uuid.uuid4()
    object_key = f"{session_id}/{event_id}/{artifact_id}_{file.filename or 'artifact'}"

    mc = _get_minio_client()
    content = await file.read()
    size = len(content)

    import io

    mc.put_object(
        MINIO_BUCKET,
        object_key,
        io.BytesIO(content),
        length=size,
        content_type=file.content_type or "application/octet-stream",
    )

    async with _pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO telemetry_artifacts
                (artifact_id, event_id, session_id, object_key, content_type, size_bytes)
            VALUES ($1, $2, $3, $4, $5, $6)
            """,
            artifact_id,
            event_uuid,
            session_uuid,
            object_key,
            file.content_type,
            size,
        )

    return ArtifactResponse(
        artifact_id=str(artifact_id),
        event_id=event_id,
        object_key=object_key,
    )


@app.get("/api/v1/events")
async def list_events(
    session_id: str | None = None,
    event_type: str | None = None,
    severity: str | None = None,
    since: str | None = None,
    limit: int = 50,
    offset: int = 0,
    _: None = Depends(_verify_api_key),
):
    """Query stored telemetry events with optional filters.

    ``since`` is an ISO-8601 datetime string (e.g. ``2026-04-23T00:00:00Z``).
    When provided, only events with ``created_at >= since`` are returned.
    """
    if not _pool:
        raise HTTPException(status_code=503, detail="Database not available")

    conditions: list[str] = []
    params: list[Any] = []
    idx = 1

    if since:
        try:
            since_dt = datetime.fromisoformat(since.replace("Z", "+00:00"))
        except ValueError:
            raise HTTPException(
                status_code=422,
                detail="'since' must be a valid ISO-8601 datetime string",
            )
        conditions.append(f"created_at >= ${idx}")
        params.append(since_dt)
        idx += 1
    if session_id:
        conditions.append(f"session_id = ${idx}::uuid")
        params.append(session_id)
        idx += 1
    if event_type:
        conditions.append(f"event_type = ${idx}")
        params.append(event_type)
        idx += 1
    if severity:
        conditions.append(f"severity = ${idx}")
        params.append(severity)
        idx += 1

    where = f"WHERE {' AND '.join(conditions)}" if conditions else ""
    limit = min(limit, 500)

    params.extend([limit, offset])
    query = f"""
        SELECT event_id, session_id, timestamp, agent_name, event_type,
               severity, summary, detail, model_id, created_at
        FROM telemetry_events
        {where}
        ORDER BY timestamp DESC
        LIMIT ${idx} OFFSET ${idx + 1}
    """

    async with _pool.acquire() as conn:
        rows = await conn.fetch(query, *params)

    return [
        {
            "event_id": str(r["event_id"]),
            "session_id": str(r["session_id"]),
            "timestamp": r["timestamp"].isoformat(),
            "agent_name": r["agent_name"],
            "event_type": r["event_type"],
            "severity": r["severity"],
            "summary": r["summary"],
            "detail": r["detail"],
            "model_id": r["model_id"],
            "created_at": r["created_at"].isoformat(),
        }
        for r in rows
    ]
