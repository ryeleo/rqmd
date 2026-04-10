---
name: rqmd-telemetry
description: Report AI workflow friction, improvement suggestions, and session diagnostics to the rqmd telemetry service. Use when an rqmd command fails unexpectedly, when workflow guidance is confusing, or when you notice something that could be improved.
argument-hint: Describe the friction, failure, or improvement idea you want to report.
user-invocable: true
metadata:
  guide:
    summary: Submit structured telemetry events so rqmd developers can see where AI agents struggle and what they think could be better.
    workflow:
      - Check whether telemetry is configured before attempting to send events.
      - Submit struggle reports when rqmd commands fail or produce unexpected output.
      - Submit improvement suggestions when you notice friction that was not a hard failure.
      - Include enough context for a developer to understand the issue without the full chat transcript.
    examples:
      - Report a struggle when rqmd --verify-summaries fails unexpectedly.
      - Suggest an improvement when rqmd-ai JSON output is hard to parse.
      - Report an error when a bundle install command exits non-zero.
---

Use this skill when you encounter friction, errors, or improvement opportunities while using rqmd workflows.

> **⚠️ Note:** This skill is for reporting issues with **rqmd itself** — AI agent friction, CLI failures, or workflow guidance problems in rqmd. To file a bug for **your own project**, use `/bug` instead, which creates a tracked requirement in your `docs/requirements/` folder.

## Telemetry is enabled by default

Telemetry is active out of the box — the rqmd client ships with a built-in production endpoint and uses automatic token exchange so agents can report friction without any setup.

The resolution order for the endpoint is:

1. `RQMD_TELEMETRY_ENDPOINT` environment variable (highest priority).
2. `telemetry.endpoint` in the project `rqmd.yml` / `rqmd.yaml` / `rqmd.json` config file.
3. Built-in production default.

To **opt out**, set `RQMD_TELEMETRY_DISABLED=1` in the environment. When disabled, no events are sent and both `resolve_telemetry_endpoint` and `resolve_telemetry_api_key` return `None`.

## Authentication

All gateway endpoints except `/health` and `/api/v1/token` require a Bearer token. The token is resolved automatically:

1. `RQMD_TELEMETRY_API_KEY` environment variable (highest priority) — use for local dev or overrides.
2. `telemetry.api_key` in the project `rqmd.yml` / `rqmd.yaml` / `rqmd.json` config file.
3. **Automatic token exchange** — the client sends its public client ID to `POST /api/v1/token` on the gateway and receives a short-lived session token (default 1 hour TTL). The token is cached in-process and refreshed transparently.

No plaintext API key is shipped in source. You do not need to configure anything for this to work — the client exchanges a token automatically using the built-in production endpoint.

## When to report

Report a **struggle** event when:
- An rqmd or rqmd-ai command exits non-zero or produces unexpected output.
- You had to retry a command multiple times to get it working.
- Workflow guidance was confusing or led you down a wrong path.
- You could not find the right command, flag, or skill for what you needed.
- JSON output was malformed, missing expected fields, or hard to parse.

Report a **command discovery struggle** (high priority) when:
- You tried to run `rqmd` or `rqmd-ai` and the command was not found.
- You tried multiple invocation variants (`python -m rqmd`, `uv run rqmd`, `rqmd`, etc.) before one worked.
- The CLI exited non-zero due to a missing entrypoint, wrong Python version, or missing extras.
- You gave up on the CLI and fell back to directly reading or editing files in `docs/requirements/`.

This pattern is **always severity "high"** and must include `"category": "command_discovery"` in the detail object, along with the exact commands you attempted and the fallback action you took. Do not silently work around CLI invocation failures — report them so the installation and discoverability can be fixed.

Report a **suggestion** event when:
- You notice friction that was not a hard failure but made the workflow harder than it should be.
- You think a command, flag, or workflow could be designed differently to be more intuitive.
- You see a pattern where rqmd guidance could teach something better or earlier.
- You think a new skill, prompt, or workflow would fill a gap you observed.

Report an **error** event when:
- A Python traceback or unhandled exception occurs during an rqmd command.
- A command hangs or times out unexpectedly.

## How to report

Use `send_event` from `rqmd.telemetry` — it resolves the endpoint and authentication (including automatic token exchange) internally:

```python
from rqmd.telemetry import send_event

send_event(
    event_type="struggle",
    severity="high",
    summary="rqmd --verify-summaries exited non-zero unexpectedly",
    agent_name="rqmd",
    detail={
        "command": "rqmd --verify-summaries --non-interactive",
        "expected": "Exit 0 with no output",
        "actual": "Exit 1 with summary mismatch error",
        "stderr_snippet": "...",
    },
)
```

No manual endpoint or API key resolution is needed. If telemetry is disabled (`RQMD_TELEMETRY_DISABLED=1`), `send_event` returns `None` silently.

### HTTP reference

For agents that cannot import the Python client, the raw HTTP protocol is:

```
POST {endpoint}/api/v1/events
Content-Type: application/json
Authorization: Bearer <api-key>

{
  "session_id": "<your-session-id-or-uuid>",
  "agent_name": "<agent-name-if-known>",
  "event_type": "struggle" | "suggestion" | "error" | "success" | "workflow_step",
  "severity": "low" | "medium" | "high" | "critical",
  "summary": "Concise one-line description of what happened",
  "detail": {
    "command": "the rqmd command that was involved, if any",
    "expected": "what you expected to happen",
    "actual": "what actually happened",
    "stderr_snippet": "relevant stderr output, truncated to 2000 chars",
    "suggestion": "what you think should change, for suggestion events",
    "confidence": "low | medium | high, for suggestion events",
    "context": "any other structured context that helps"
  }
}
```

For command-discovery struggles specifically:

```python
send_event(
    event_type="struggle",
    severity="high",
    summary="Could not invoke rqmd-ai; fell back to direct file edits",
    agent_name="rqmd",
    detail={
        "category": "command_discovery",
        "commands_attempted": ["rqmd-ai --json", "python -m rqmd.ai_cli --json", "uv run rqmd-ai --json"],
        "fallback_action": "Edited docs/requirements/telemetry.md directly",
        "stderr_snippet": "zsh: command not found: rqmd-ai",
    },
)
```

Or as raw JSON if using the HTTP API directly:

```json
{
  "session_id": "<your-session-id>",
  "agent_name": "rqmd",
  "event_type": "struggle",
  "severity": "high",
  "summary": "Could not invoke rqmd-ai; fell back to direct file edits",
  "detail": {
    "category": "command_discovery",
    "commands_attempted": ["rqmd-ai --json", "python -m rqmd.ai_cli --json", "uv run rqmd-ai --json"],
    "fallback_action": "Edited docs/requirements/telemetry.md directly",
    "stderr_snippet": "zsh: command not found: rqmd-ai"
  }
}
```

## Event field reference

| Field | Required | Description |
|---|---|---|
| `session_id` | yes | A UUID or unique session identifier. Use one per chat session or agent run. |
| `agent_name` | no | The agent name, e.g. `rqmd`, `rqmd-dev-longrunning`. |
| `event_type` | yes | One of: `struggle`, `suggestion`, `error`, `success`, `workflow_step`. |
| `severity` | yes | One of: `low`, `medium`, `high`, `critical`. |
| `summary` | yes | A concise one-line description. Keep under 200 characters. |
| `detail` | no | Structured JSON object with additional context. Shape varies by event type. |

## Artifact uploads

For larger payloads such as full command output, session logs, or prompt snapshots, POST to the artifact endpoint:

```
POST {endpoint}/api/v1/artifacts
Content-Type: multipart/form-data
Authorization: Bearer <api-key>

Fields:
  - session_id: <session-id>
  - event_id: <event-id-from-event-response>
  - file: <the-artifact-file>
```

The gateway stores artifacts in MinIO and links them to the originating event.

## Quick pipeline test

Before reporting real events, verify the telemetry pipeline is working with:

```bash
rqmd-ai telemetry-test --json
```

This sends a lightweight `success`-type test event and confirms the gateway accepted it. If the response shows `"success": true`, end-to-end telemetry is working. Use this anytime you want to confirm your setup before submitting real struggle or suggestion reports.

## Constraints

- **Never include secrets, tokens, passwords, or file contents that may contain sensitive data in telemetry payloads.**
- Truncate stderr and stdout snippets to 2000 characters maximum.
- Prefer structured `detail` fields over dumping raw text into `summary`.
- One event per observed issue. Do not batch multiple unrelated issues into a single event.
- Skills improve workflow discovery; shell and tool approvals may still be required.
