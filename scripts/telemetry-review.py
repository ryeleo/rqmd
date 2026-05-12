#!/usr/bin/env python3
"""Fetch recent telemetry events from the gateway and print them as JSON.

Internal developer script — not part of the distributed rqmd package.

Usage:
    python3 scripts/telemetry-review.py [DAYS]

    DAYS  Number of days to look back (default: 14).

Requires:
  - The SSH tunnel to be active (localhost:18080 → gateway).
    Start the "Tunnel to Az TeleVM" VS Code task if not running.
  - A valid .rqmd-telemetry-token in the project root, or the gateway
    must be reachable for a fresh token exchange.

Gateway URL resolution order:
  1. RQMD_TELEMETRY_URL env var
  2. RQMD_TELEMETRY_ENDPOINT env var
  3. Default: http://localhost:18080 (tunnel address)
"""

from __future__ import annotations

import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

_DEFAULT_GATEWAY = "http://localhost:18080"
_TOKEN_FILENAME = ".rqmd-telemetry-token"
_CLIENT_ID = "rqmd-agent-v1"
_PAGE_LIMIT = 500


def _gateway_url() -> str:
    return (
        os.environ.get("RQMD_TELEMETRY_URL")
        or os.environ.get("RQMD_TELEMETRY_ENDPOINT")
        or _DEFAULT_GATEWAY
    ).rstrip("/")


def _project_root() -> Path:
    """Walk up from cwd to find the rqmd project root."""
    cur = Path.cwd()
    for parent in [cur, *cur.parents]:
        if (parent / "docs" / "requirements").is_dir() or (parent / ".git").exists():
            return parent
    return cur


def _read_token() -> tuple[str | None, float]:
    """Read the cached session token from .rqmd-telemetry-token."""
    token_path = _project_root() / _TOKEN_FILENAME
    if not token_path.is_file():
        return None, 0.0
    try:
        data = json.loads(token_path.read_text(encoding="utf-8"))
        token = data.get("token")
        expiry = float(data.get("expiry", 0.0))
        if token and isinstance(token, str):
            return token, expiry
    except (json.JSONDecodeError, OSError, ValueError, TypeError):
        pass
    return None, 0.0


def _write_token(token: str, expiry: float) -> None:
    token_path = _project_root() / _TOKEN_FILENAME
    try:
        token_path.write_text(
            json.dumps({"token": token, "expiry": expiry}),
            encoding="utf-8",
        )
        token_path.chmod(0o600)
    except OSError:
        pass


def _exchange_token(gateway: str) -> str | None:
    """Fetch a short-lived session token from the gateway."""
    import time as _time

    url = f"{gateway}/api/v1/token"
    body = json.dumps({"client_id": _CLIENT_ID}).encode("utf-8")
    try:
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            token = data.get("token")
            expires_in = data.get("expires_in", 3600)
            if token:
                _write_token(token, _time.time() + expires_in)
                return token
    except Exception as exc:
        print(f"token exchange failed: {exc}", file=sys.stderr)
    return None


def _ensure_token(gateway: str) -> str | None:
    import time as _time

    token, expiry = _read_token()
    if token and _time.time() < (expiry - 60):
        return token
    return _exchange_token(gateway)


def fetch_events(gateway: str, token: str, days: int) -> list[dict]:
    since = (datetime.now(timezone.utc) - timedelta(days=days)).isoformat()
    offset = 0
    all_events: list[dict] = []

    while True:
        url = f"{gateway}/api/v1/events?since={since}&limit={_PAGE_LIMIT}&offset={offset}"
        req = urllib.request.Request(
            url,
            headers={"Authorization": f"Bearer {token}"},
            method="GET",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            batch = json.loads(resp.read())

        if not isinstance(batch, list):
            raise ValueError(f"Unexpected gateway response shape: {type(batch).__name__}")

        all_events.extend(batch)
        if len(batch) < _PAGE_LIMIT:
            break
        offset += _PAGE_LIMIT

    return all_events


def main() -> None:
    days = 14
    if len(sys.argv) >= 2:
        try:
            days = int(sys.argv[1])
            if days < 1:
                raise ValueError("must be a positive integer")
        except ValueError as exc:
            print(f"Error: invalid DAYS argument {sys.argv[1]!r}: {exc}", file=sys.stderr)
            sys.exit(1)

    gateway = _gateway_url()
    token = _ensure_token(gateway)
    if not token:
        print(
            "Error: no valid telemetry token and token exchange failed.\n"
            f"Fix: ensure the tunnel is running (start 'Tunnel to Az TeleVM' in VS Code tasks)\n"
            f"     and the gateway is reachable at {gateway}.",
            file=sys.stderr,
        )
        sys.exit(1)

    try:
        events = fetch_events(gateway, token, days)
    except Exception as exc:
        print(
            f"Error: gateway request failed: {exc}\n"
            "Fix: start the 'Tunnel to Az TeleVM' VS Code task and ensure the gateway is running.",
            file=sys.stderr,
        )
        sys.exit(1)

    print(json.dumps(events, indent=2, default=str))


if __name__ == "__main__":
    main()
