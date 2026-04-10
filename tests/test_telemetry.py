"""Tests for the rqmd telemetry client module (RQMD-TELEMETRY-002 through 007)."""

from __future__ import annotations

import json
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from threading import Thread
from unittest.mock import patch

import pytest

from rqmd.telemetry import (_CLIENT_ID, _DEFAULT_ENDPOINT, report_error,
                            report_struggle, report_suggestion,
                            resolve_telemetry_api_key,
                            resolve_telemetry_endpoint, submit_event)


class TestResolveTelemetryEndpoint:
    def test_returns_default_when_unconfigured(self, tmp_path: Path):
        """Falls back to built-in production endpoint."""
        with patch.dict("os.environ", {}, clear=True):
            assert resolve_telemetry_endpoint(tmp_path) == _DEFAULT_ENDPOINT

    def test_returns_none_when_disabled(self, tmp_path: Path):
        """RQMD_TELEMETRY_DISABLED=1 opts out entirely."""
        with patch.dict("os.environ", {"RQMD_TELEMETRY_DISABLED": "1"}, clear=True):
            assert resolve_telemetry_endpoint(tmp_path) is None

    def test_env_var_takes_precedence(self, tmp_path: Path):
        """RQMD-TELEMETRY-007: Env var is highest priority."""
        config_file = tmp_path / "rqmd.yml"
        config_file.write_text("telemetry:\n  endpoint: http://from-config:8080\n")
        with patch.dict(
            "os.environ", {"RQMD_TELEMETRY_ENDPOINT": "http://from-env:8080"}
        ):
            assert resolve_telemetry_endpoint(tmp_path) == "http://from-env:8080"

    def test_strips_trailing_slash(self, tmp_path: Path):
        with patch.dict(
            "os.environ", {"RQMD_TELEMETRY_ENDPOINT": "http://localhost:8080/"}
        ):
            assert resolve_telemetry_endpoint(tmp_path) == "http://localhost:8080"

    def test_reads_from_config_file(self, tmp_path: Path):
        config_file = tmp_path / "rqmd.yml"
        config_file.write_text("telemetry:\n  endpoint: http://config-host:18080\n")
        with patch.dict("os.environ", {}, clear=True):
            assert resolve_telemetry_endpoint(tmp_path) == "http://config-host:18080"

    def test_returns_none_when_config_has_no_telemetry(self, tmp_path: Path):
        config_file = tmp_path / "rqmd.yml"
        config_file.write_text("requirements_dir: docs/requirements\n")
        with patch.dict("os.environ", {}, clear=True):
            assert resolve_telemetry_endpoint(tmp_path) == _DEFAULT_ENDPOINT


# ---------------------------------------------------------------------------
# resolve_telemetry_api_key with token exchange
# ---------------------------------------------------------------------------


class TestResolveTelemetryApiKey:
    def test_env_var_takes_precedence(self, tmp_path: Path):
        with patch.dict("os.environ", {"RQMD_TELEMETRY_API_KEY": "my-key"}, clear=True):
            assert resolve_telemetry_api_key(tmp_path) == "my-key"

    def test_returns_none_when_disabled(self, tmp_path: Path):
        with patch.dict("os.environ", {"RQMD_TELEMETRY_DISABLED": "1"}, clear=True):
            assert resolve_telemetry_api_key(tmp_path) is None

    def test_fetches_session_token_from_gateway(
        self, telemetry_server: str, tmp_path: Path
    ):
        """Falls back to token exchange when no static key is configured."""
        with patch.dict(
            "os.environ", {"RQMD_TELEMETRY_ENDPOINT": telemetry_server}, clear=True
        ):
            key = resolve_telemetry_api_key(tmp_path)
        assert key == "stub-session-token"

    def test_caches_session_token(self, telemetry_server: str, tmp_path: Path):
        """Second call returns the cached token without another HTTP request."""
        with patch.dict(
            "os.environ", {"RQMD_TELEMETRY_ENDPOINT": telemetry_server}, clear=True
        ):
            key1 = resolve_telemetry_api_key(tmp_path)
            key2 = resolve_telemetry_api_key(tmp_path)
        assert key1 == key2 == "stub-session-token"


# ---------------------------------------------------------------------------
# File-based token cache (cross-invocation persistence)
# ---------------------------------------------------------------------------


class TestFileBasedTokenCache:
    def test_writes_token_to_disk(self, telemetry_server: str, tmp_path: Path):
        """Token exchange persists the token to .rqmd-telemetry-token."""
        import rqmd.telemetry as _tmod

        # Create a marker so _token_cache_path finds this as a repo root.
        (tmp_path / "docs" / "requirements").mkdir(parents=True)
        with (
            patch.dict(
                "os.environ", {"RQMD_TELEMETRY_ENDPOINT": telemetry_server}, clear=True
            ),
            patch.object(_tmod, "_token_cache_path", return_value=tmp_path / ".rqmd-telemetry-token"),
        ):
            key = resolve_telemetry_api_key(tmp_path)

        assert key == "stub-session-token"
        cache_file = tmp_path / ".rqmd-telemetry-token"
        assert cache_file.is_file()
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        assert data["token"] == "stub-session-token"
        assert data["expiry"] > 0

    def test_reads_token_from_disk_cache(self, tmp_path: Path):
        """Cached token on disk is reused without hitting the gateway."""
        import time

        import rqmd.telemetry as _tmod

        (tmp_path / "docs" / "requirements").mkdir(parents=True)
        cache_file = tmp_path / ".rqmd-telemetry-token"
        cache_file.write_text(
            json.dumps({"token": "disk-cached-token", "expiry": time.time() + 3600}),
            encoding="utf-8",
        )

        with (
            patch.dict(
                "os.environ",
                {"RQMD_TELEMETRY_ENDPOINT": "http://127.0.0.1:1"},  # unreachable
                clear=True,
            ),
            patch.object(_tmod, "_token_cache_path", return_value=cache_file),
        ):
            key = resolve_telemetry_api_key(tmp_path)

        assert key == "disk-cached-token"

    def test_expired_disk_token_triggers_fresh_exchange(
        self, telemetry_server: str, tmp_path: Path
    ):
        """Expired on-disk token is replaced by a fresh gateway exchange."""
        import rqmd.telemetry as _tmod

        (tmp_path / "docs" / "requirements").mkdir(parents=True)
        cache_file = tmp_path / ".rqmd-telemetry-token"
        cache_file.write_text(
            json.dumps({"token": "expired-token", "expiry": 0.0}),
            encoding="utf-8",
        )

        with (
            patch.dict(
                "os.environ", {"RQMD_TELEMETRY_ENDPOINT": telemetry_server}, clear=True
            ),
            patch.object(_tmod, "_token_cache_path", return_value=cache_file),
        ):
            key = resolve_telemetry_api_key(tmp_path)

        assert key == "stub-session-token"
        data = json.loads(cache_file.read_text(encoding="utf-8"))
        assert data["token"] == "stub-session-token"

    def test_ensures_gitignore_entry(self, telemetry_server: str, tmp_path: Path):
        """Token exchange adds .rqmd-telemetry-token to .gitignore."""
        import rqmd.telemetry as _tmod

        (tmp_path / "docs" / "requirements").mkdir(parents=True)
        (tmp_path / ".gitignore").write_text("node_modules/\n", encoding="utf-8")

        with (
            patch.dict(
                "os.environ", {"RQMD_TELEMETRY_ENDPOINT": telemetry_server}, clear=True
            ),
            patch.object(_tmod, "_token_cache_path", return_value=tmp_path / ".rqmd-telemetry-token"),
        ):
            resolve_telemetry_api_key(tmp_path)

        gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert ".rqmd-telemetry-token" in gitignore

    def test_does_not_duplicate_gitignore_entry(
        self, telemetry_server: str, tmp_path: Path
    ):
        """If .rqmd-telemetry-token is already in .gitignore, don't add it again."""
        import rqmd.telemetry as _tmod

        (tmp_path / "docs" / "requirements").mkdir(parents=True)
        (tmp_path / ".gitignore").write_text(
            "node_modules/\n.rqmd-telemetry-token\n", encoding="utf-8"
        )

        with (
            patch.dict(
                "os.environ", {"RQMD_TELEMETRY_ENDPOINT": telemetry_server}, clear=True
            ),
            patch.object(_tmod, "_token_cache_path", return_value=tmp_path / ".rqmd-telemetry-token"),
        ):
            resolve_telemetry_api_key(tmp_path)

        gitignore = (tmp_path / ".gitignore").read_text(encoding="utf-8")
        assert gitignore.count(".rqmd-telemetry-token") == 1


# ---------------------------------------------------------------------------
# Stub HTTP server for event submission tests
# ---------------------------------------------------------------------------


class _StubHandler(BaseHTTPRequestHandler):
    """Minimal handler that records POSTed JSON bodies and supports token exchange."""

    received: list[dict] = []

    def do_POST(self):
        length = int(self.headers.get("Content-Length", 0))
        raw = self.rfile.read(length)

        if self.path == "/api/v1/token":
            # Token exchange endpoint.
            response = json.dumps(
                {
                    "token": "stub-session-token",
                    "expires_in": 3600,
                    "session_id": "00000000-0000-0000-0000-000000000099",
                }
            )
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response.encode())
            return

        if self.path == "/api/v1/artifacts":
            # Artifact upload endpoint (multipart — not JSON).
            response = json.dumps(
                {
                    "artifact_id": "stub-artifact-id",
                    "status": "accepted",
                }
            )
            self.send_response(201)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(response.encode())
            return

        body = json.loads(raw)
        _StubHandler.received.append(body)
        response = json.dumps(
            {
                "event_id": "test-event-id",
                "session_id": body.get("session_id"),
                "status": "accepted",
            }
        )
        self.send_response(201)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(response.encode())

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(b'{"status":"healthy","postgres":true,"minio":true}')

    def log_message(self, format, *args):
        pass  # Suppress request logging during tests.


@pytest.fixture
def telemetry_server():
    """Start a local stub telemetry server and yield its base URL."""
    import rqmd.telemetry as _tmod

    _StubHandler.received = []
    # Reset the cached session token between tests.
    _tmod._cached_token = None
    _tmod._cached_token_expiry = 0.0
    server = HTTPServer(("127.0.0.1", 0), _StubHandler)
    port = server.server_address[1]
    thread = Thread(target=server.serve_forever, daemon=True)
    thread.start()
    yield f"http://127.0.0.1:{port}"
    server.shutdown()
    _tmod._cached_token = None
    _tmod._cached_token_expiry = 0.0


# ---------------------------------------------------------------------------
# submit_event
# ---------------------------------------------------------------------------


class TestSubmitEvent:
    def test_returns_none_when_no_endpoint(self):
        """RQMD-TELEMETRY-007: submit_event is a no-op with empty endpoint."""
        result = submit_event("", event_type="error", severity="high", summary="test")
        assert result is None

    def test_posts_event_to_endpoint(self, telemetry_server: str):
        """RQMD-TELEMETRY-002/003: event reaches the gateway with correct schema."""
        result = submit_event(
            telemetry_server,
            event_type="struggle",
            severity="medium",
            summary="Could not parse JSON output",
            agent_name="rqmd-dev",
            session_id="00000000-0000-0000-0000-000000000001",
            detail={"command": "rqmd-ai --json"},
        )
        assert result is not None
        assert result["status"] == "accepted"
        assert len(_StubHandler.received) == 1
        body = _StubHandler.received[0]
        assert body["event_type"] == "struggle"
        assert body["severity"] == "medium"
        assert body["agent_name"] == "rqmd-dev"
        assert body["detail"]["command"] == "rqmd-ai --json"

    def test_truncates_long_summary(self, telemetry_server: str):
        """RQMD-TELEMETRY-002: summary is capped at 200 chars."""
        long_summary = "x" * 500
        submit_event(
            telemetry_server,
            event_type="error",
            severity="high",
            summary=long_summary,
        )
        body = _StubHandler.received[0]
        assert len(body["summary"]) <= 200

    def test_truncates_detail_snippets(self, telemetry_server: str):
        """RQMD-TELEMETRY-005: large stderr snippets are truncated."""
        submit_event(
            telemetry_server,
            event_type="error",
            severity="high",
            summary="test",
            detail={"stderr_snippet": "e" * 5000},
        )
        body = _StubHandler.received[0]
        assert len(body["detail"]["stderr_snippet"]) <= 2003  # 2000 + "..."

    def test_handles_unreachable_endpoint_gracefully(self):
        """RQMD-TELEMETRY-003: unreachable endpoint returns None instead of raising."""
        result = submit_event(
            "http://127.0.0.1:1",  # almost certainly not listening
            event_type="error",
            severity="high",
            summary="should not crash",
        )
        assert result is None


# ---------------------------------------------------------------------------
# Convenience wrappers
# ---------------------------------------------------------------------------


class TestReportStruggle:
    def test_posts_struggle_event(self, telemetry_server: str):
        """RQMD-TELEMETRY-005: struggle events include expected detail fields."""
        result = report_struggle(
            telemetry_server,
            summary="rqmd --verify-summaries exited 1",
            command="rqmd --verify-summaries",
            expected="exit 0",
            actual="exit 1 with summary mismatch",
            stderr_snippet="Error: summary mismatch in core-engine.md",
        )
        assert result is not None
        body = _StubHandler.received[0]
        assert body["event_type"] == "struggle"
        assert body["detail"]["command"] == "rqmd --verify-summaries"
        assert body["detail"]["expected"] == "exit 0"


class TestReportSuggestion:
    def test_posts_suggestion_event(self, telemetry_server: str):
        """RQMD-TELEMETRY-006: suggestion events include suggestion text and confidence."""
        result = report_suggestion(
            telemetry_server,
            summary="rqmd-ai JSON output should include domain file path in each requirement",
            suggestion="Add a 'domain_file' field to each requirement in --dump-status output",
            confidence="high",
            command="rqmd-ai --json --dump-status proposed",
        )
        assert result is not None
        body = _StubHandler.received[0]
        assert body["event_type"] == "suggestion"
        assert body["detail"]["suggestion"].startswith("Add a")
        assert body["detail"]["confidence"] == "high"


class TestReportError:
    def test_posts_error_event(self, telemetry_server: str):
        """RQMD-TELEMETRY-005: error events include stderr output."""
        result = report_error(
            telemetry_server,
            summary="rqmd crashed with traceback",
            command="rqmd --verify-summaries",
            stderr_snippet="Traceback (most recent call last): ...",
        )
        assert result is not None
        body = _StubHandler.received[0]
        assert body["event_type"] == "error"
        assert body["severity"] == "high"


