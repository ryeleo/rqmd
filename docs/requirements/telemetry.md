# Telemetry Requirement

Scope: agent-facing telemetry infrastructure for capturing AI workflow friction, improvement suggestions, and session diagnostics — enabling rqmd's own AI agents to report how rqmd can be improved.

<!-- acceptance-status-summary:start -->
Summary: 2💡 17🔧 0✅ 0⚠️ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->


### RQMD-TELEMETRY-001: Local telemetry development stack

- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- **Summary:** A Docker Compose stack with Postgres, MinIO, a telemetry gateway, and admin tooling so that the full telemetry pipeline can run on a single machine without external service dependencies.
- Given a developer runs `docker compose -f docker-compose.telemetry.yml up`
- When all services reach healthy status
- Then a Postgres database is available for structured telemetry events, a MinIO bucket exists for larger artifacts such as session logs and prompt snapshots, and a gateway accepts HTTP posts on a non-standard dev port
- And default credentials are dev-only, clearly marked, and never used for production.


### RQMD-TELEMETRY-002: Telemetry event schema

- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- **Summary:** A structured event schema that captures session identity, event type, severity, agent context, and freeform detail so that telemetry data is queryable, filterable, and useful for diagnosing patterns across many agent sessions.
- Given an AI agent submits a telemetry event
- When the event is stored
- Then it includes at minimum: event_id, session_id, timestamp, agent_name, event_type (struggle | suggestion | error | success | workflow_step), severity, summary text, and optional structured detail JSON
- And event_type is extensible so new categories can be added without schema migration.


### RQMD-TELEMETRY-003: Telemetry HTTP gateway

- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- **Summary:** A simple HTTP endpoint I can POST structured telemetry events to so that telemetry capture does not require database drivers, SDK dependencies, or complex client setup inside the agent environment.
- Given an agent has a telemetry endpoint URL configured
- When it POSTs a JSON event body to the gateway
- Then the gateway validates the payload against the event schema, stores the structured event in Postgres, and optionally stores referenced artifacts in MinIO
- And the gateway responds with a confirmation or structured error so the agent knows whether the report succeeded.


### RQMD-TELEMETRY-004: rqmd-telemetry bundle skill

- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- **Summary:** An `/rqmd-telemetry` skill that teaches AI agents how and when to submit telemetry so that agents have clear instructions for reporting friction, errors, and improvement ideas without needing ad hoc prompting.
- Given an AI agent encounters a problem while running rqmd workflows
- When the agent has the rqmd-telemetry skill loaded
- Then it knows the telemetry endpoint, the event schema, and the expected submission protocol
- And it can decide autonomously whether to submit a struggle report, an improvement suggestion, or both based on what it observed
- And the skill guidance makes clear that telemetry is opt-in, local-first, and never silently phones home.


### RQMD-TELEMETRY-005: Agent struggle reporting

- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- **Summary:** Agents to report structured "I struggled because..." events when they encounter friction with rqmd workflows so that recurring failure patterns surface as queryable data instead of disappearing into chat transcripts.
- Given an AI agent tries to run an rqmd command, parse rqmd output, or follow rqmd workflow guidance and encounters unexpected behavior
- When it recognizes that something went wrong or took significantly more effort than expected
- Then it submits a telemetry event with event_type "struggle", a concise summary of what it was trying to do, what went wrong, any error output or unexpected state it observed, and which rqmd command or skill was involved
- And the event captures enough context for a developer to reproduce or understand the failure without needing the full chat transcript.


### RQMD-TELEMETRY-006: Agent improvement suggestions

- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- **Summary:** Agents to proactively submit "rqmd could be improved if..." suggestions based on their direct experience using rqmd so that product improvement ideas come from the agents that actually use the tool day to day, not just from manually observed failures.
- Given an AI agent completes or partially completes an rqmd workflow
- When it identifies friction that was not a hard failure but made the workflow harder, slower, or more confusing than it should have been
- Then it submits a telemetry event with event_type "suggestion", a concise description of the observed friction, a proposed improvement or change, and an optional confidence level
- And the suggestion captures enough detail for a developer to evaluate whether the idea is actionable without needing the full session context.


### RQMD-TELEMETRY-007: Telemetry opt-out and privacy controls

- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- **Summary:** A clear opt-out mechanism that disables all telemetry transmission so that rqmd telemetry cannot become a trust liability.
- Given a repository has the rqmd AI bundle installed with the telemetry skill
- When telemetry is enabled by default with built-in production defaults
- Then agents can submit events without any manual configuration
- And when a user sets `RQMD_TELEMETRY_DISABLED=1` in their environment
- Then both `resolve_telemetry_endpoint` and `resolve_telemetry_api_key` return None and no events are sent
- And the skill guidance makes the opt-out contract visible to both agents and humans reviewing the installed bundle.


### RQMD-TELEMETRY-008: Agent telemetry configuration discovery

- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- **Summary:** A single discovery mechanism that resolves both the telemetry endpoint URL and the API key from well-known configuration sources so that I can authenticate with the gateway without ad-hoc credential handling or hard-coded secrets.
- Given an agent invokes the telemetry config discovery
- When the `RQMD_TELEMETRY_ENDPOINT` environment variable is set
- Then the endpoint URL is taken from that variable
- And when the `RQMD_TELEMETRY_API_KEY` environment variable is set
- Then the API key is taken from that variable
- And when the environment variables are not set but a `rqmd.yml` / `rqmd.yaml` / `rqmd.json` config file contains `telemetry.endpoint` and/or `telemetry.api_key`
- Then those config-file values are used as fallbacks
- And when neither source provides an endpoint, telemetry is silently disabled
- And the `submit_event` client includes the resolved API key as a `Bearer` token in the `Authorization` header on every request
- And the `rqmd-ai telemetry` status command reports whether an API key is configured (without revealing the key value).


### RQMD-TELEMETRY-009: Agent struggling to run rqmd reporting

- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- **Summary:** Agents to report a specific telemetry event when they fail to invoke `rqmd` or `rqmd-ai` and fall back to directly reading or writing requirement files so that command-resolution failures are tracked as a distinct, high-signal friction category rather than being lost in generic struggle reports.
- Given an AI agent attempts to run an rqmd or rqmd-ai command
- When the command is not found, exits with a non-zero status due to invocation issues (wrong Python, missing entrypoint, missing extras), or the agent tries multiple invocation variants before succeeding
- Then the agent submits a telemetry event with event_type "struggle", a new detail field `"category": "command_discovery"`, the exact commands attempted, and the fallback action taken
- And the event severity is "high" because CLI unreachability undermines the entire rqmd workflow contract
- And the telemetry skill guidance explicitly teaches agents to recognize and report this pattern rather than silently working around it.


### RQMD-TELEMETRY-010: Telemetry feedback loop — time-window review and proposals

- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- **Summary:** To run a single command that fetches telemetry events from a given time window, clusters them by pattern, and produces actionable improvement proposals so that accumulated agent friction turns into concrete changes instead of sitting unread in a database.
- Given a developer runs a feedback-loop command with a time window (e.g. `rqmd-ai telemetry review --since 7d`)
- When the command queries stored events from the gateway
- Then it groups events by category, command, and recurrence count
- And it produces a ranked list of improvement proposals with suggested patches, skill edits, or requirement updates
- And the developer can accept, reject, or refine each proposal before any changes are applied.


### RQMD-TELEMETRY-011: Automated weekly telemetry triage via GitHub Actions

- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- **Summary:** A scheduled GitHub Actions workflow that runs the telemetry feedback loop weekly and opens a PR when it finds worthwhile improvements so that the project benefits from agent-reported friction even when no human actively checks the telemetry dashboard.
- Given a `telemetry-triage` workflow is scheduled to run weekly
- When the workflow queries the previous week's telemetry events
- Then it runs the feedback-loop review, filters for proposals above a configurable confidence threshold, and applies accepted patches to a new branch
- And it opens a pull request with a summary of the telemetry patterns found, the changes proposed, and links back to the originating events
- And the PR is labeled for human review so no changes merge without approval.


### RQMD-TELEMETRY-012: Short-lived session tokens via gateway exchange

- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- **Summary:** The telemetry client to authenticate via short-lived tokens fetched at runtime from the gateway instead of shipping a long-lived plaintext API key in the source code so that credential exposure in the published package cannot be used to spam or poison the telemetry database indefinitely.
- Given the rqmd client starts a telemetry session
- When it needs to submit its first event
- Then it calls `POST /api/v1/token` on the gateway with a package-embedded client identifier (public, non-secret)
- And the gateway returns a short-lived HMAC token (1-hour TTL) scoped to that session
- And the client caches the token for the session lifetime and includes it as the Bearer token on all subsequent event POSTs
- And when the token expires, the client transparently re-fetches a new one
- And key rotation is a gateway-side config change that does not require a new rqmd package release
- And the `_DEFAULT_API_KEY` plaintext fallback has been removed — the client now uses `_CLIENT_ID` for token exchange.


### RQMD-TELEMETRY-013: Gateway rate limiting

- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- **Summary:** Per-client and global rate limits enforced at the gateway layer so that no single source can flood the database, whether through malice or misconfiguration.
- Given the telemetry gateway is running
- When a client submits events faster than the configured rate limit
- Then the gateway responds with `429 Too Many Requests` and a `Retry-After` header
- And the Python telemetry client respects the 429 and backs off gracefully without crashing or losing the event
- And rate limits are configurable per dimension: per-IP, per-session, per-token, and global
- And the default limits are generous enough for normal agent usage (e.g. 60 events/minute per session, 600 events/minute global) but block obvious abuse patterns
- And the token exchange endpoint (`POST /api/v1/token`) is also rate-limited so bulk token farming is throttled server-side without adding client-side latency
- And rate limit state is stored in-memory or in Postgres (not an external Redis dependency for the v1 single-VM deployment).


### RQMD-TELEMETRY-014: Proof-of-work challenge for token exchange

- **Status:** 🗑️ Deprecated
- **Priority:** 🟢 P3 - Low
- Deprecated: Adds client-side compute latency (~50-200ms) to every token exchange with no way to eliminate it. Rate limiting on the token endpoint (RQMD-TELEMETRY-013) achieves the same anti-abuse goal server-side at zero client cost. Not worth the latency trade-off for a developer telemetry service.


### RQMD-TELEMETRY-015: `feedback` event type for user-driven improvement telemetry

- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- **Summary:** A dedicated `feedback` event type that captures user-driven improvement feedback separately from autonomous agent reports so that feedback submitted through `/feedback` sessions is distinguishable from autonomous struggle and suggestion events, enabling focused triage of human-intentional input.
- Given `EventType` in `src/rqmd/telemetry.py` currently defines `"struggle" | "suggestion" | "error" | "success" | "workflow_step"`
- When the `feedback` event type is added
- Then `EventType` includes `"feedback"` as a valid literal value
- And `submit_event()` accepts `event_type="feedback"` without modification
- And the telemetry skill and `/rqmd-feedback` skill document the `feedback` event type and its expected detail fields
- And feedback events include a `detail.category` field with one of: `ux_friction`, `missing_feature`, `docs_gap`, `workflow_confusion`, `performance`, `other`
- And feedback events optionally include `detail.suggested_improvement` as a freeform text field describing what the user thinks should change
- And the gateway accepts `feedback` events without requiring a schema migration (the event_type column is already extensible per RQMD-TELEMETRY-002).


### RQMD-TELEMETRY-016: Client-side secrets and PII scrubbing before telemetry submission

- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- **Summary:** All telemetry payloads pass through a three-layer scrubbing pipeline before leaving the client process — `detect-secrets` (secret patterns), `gitleaks` subprocess (comprehensive ruleset, best-effort), then `scrubadub` (PII redaction) — so that API keys, tokens, emails, home-directory paths, and other sensitive data in `summary`, `detail`, and `stderr_snippet` fields are never transmitted to the telemetry service.
- Given `src/rqmd/telemetry.py` builds a telemetry event payload
- When `send_event()` is called with any `detail` dict or `summary` string
- Then each freeform string field (`summary`, `detail.stderr_snippet`, `detail.command`, and all other string-valued detail fields) is passed through the following pipeline in order before serialization:
  1. **`detect-secrets` layer** (required pip dep): scan the string using `SecretsCollection`; for each finding, replace the detected span with `{{REDACTED_SECRET}}`. `detect-secrets` is listed in `pyproject.toml` under `[project.dependencies]`.
  2. **`gitleaks` layer** (optional subprocess): if `gitleaks` is found in `PATH`, pipe the string to `gitleaks stdin --report-format json --report-path - --no-banner` and replace each reported `Secret` field value with `{{REDACTED_GITLEAKS}}`. Exit code 0 means no findings; exit code 1 means findings were reported; other exit codes are treated as errors. If `gitleaks` is absent, log a one-time `DEBUG` warning and skip this layer — do not fail.
  3. **`scrubadub` layer** (required pip dep): call `scrubadub.Scrubber().clean(text)` on the output of the previous layers to redact PII (emails, names, addresses, phone numbers). `scrubadub` is listed in `pyproject.toml` under `[project.dependencies]`.
- And if any layer raises an exception, that layer is skipped with a `WARNING` log and the pipeline continues with the previous layer's output — a scrubbing layer failure never propagates to the caller or transmits raw data
- And if the entire pipeline fails, `send_event` logs `ERROR`, drops the affected event, and returns without raising
- And the scrubbing module lives at `src/rqmd/scrubbing.py` and is imported by `telemetry.py`
- And `tests/test_telemetry_scrubbing.py` contains a parametrized test verifying each layer independently and the full pipeline on a synthetic payload containing: a fake AWS key (`AKIA...`), a GitHub token (`ghp_...`), an email address, and a `~/.ssh/` path reference
- And home-directory paths (`~/`, `/home/<user>/`, `/Users/<user>/`) are normalised to `{{REDACTED_PATH}}` as a pre-pass before the pipeline, using `os.path.expanduser` to detect the current user prefix.


### RQMD-TELEMETRY-017: AI model identifier in telemetry events

- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- **Summary:** Every telemetry event to carry the identifier of the AI model that produced the session so that recurring friction patterns (e.g. hard-wrapping violations, incorrect command invocations) can be correlated with specific models and prioritised for targeted skill or prompt fixes.
- Given `src/rqmd/telemetry.py` builds a telemetry event
- When `send_event()` is called
- Then the event payload includes a top-level `model_id` field containing the identifier string of the active model (e.g. `"gpt-4o"`, `"claude-sonnet-4-5"`, `"gemini-1.5-pro"`)
- And when no model identifier is available (CLI context, non-agent caller, or the environment does not expose the model name), `model_id` is omitted or `null` — it is never fabricated
- And the `rqmd-telemetry` skill instructs agents to populate `model_id` from the VS Code chat model context (`copilot.model.id` or the value reported by the agent's own system prompt) before calling `send_event()`
- And RQMD-TELEMETRY-002 is amended: `model_id` is added to the minimum required event fields alongside `agent_name`
- And the gateway stores `model_id` in a queryable column so telemetry reviews can group events by model
- And `model_id` is treated as a plain identifier string and passes through the scrubbing pipeline defined in RQMD-TELEMETRY-016 without special handling (no redaction expected for model names).
- **Related:** RQMD-AI-FEEDBACK-007 [spec](../../rqmd-vscode/docs/requirements/feedback.md) — hard-wrap complaint telemetry uses `model_id` to attribute style violations to specific models.


<a id="rqmd-telemetry-018"></a>
### RQMD-TELEMETRY-018: `scripts/telemetry-review.py` — standalone developer script for event triage

<!-- sourced from brainstorm session 2026-05-07; design decision to eliminate direct SQL/HTTP access requirement from AI agents; re-scoped 2026-05-12 from rqmd CLI subcommand to internal dev script -->

- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- **Summary:** A standalone Python script at `scripts/telemetry-review.py` (internal, not distributed with the rqmd package) that fetches events from the gateway HTTP API using the stored session token and outputs structured JSON, so the developer running `/telemetry-review` needs only Python stdlib — no SQL access, no credential env vars, no rqmd package import.
- Given `python3 scripts/telemetry-review.py [DAYS]` is invoked from the rqmd-cli project root
- When the script runs
- Then it reads the session token from `.rqmd-telemetry-token` in the project root (falling back to a fresh token exchange with the gateway)
- And it calls `GET /api/v1/events?since=<ISO cutoff>&limit=500` on the configured gateway URL (default `http://localhost:18080`; overridable via `RQMD_TELEMETRY_URL` or `RQMD_TELEMETRY_ENDPOINT` env vars)
- And it pages through results if the response is at the limit, collecting all events within the window
- And it prints the full event array as pretty-printed JSON to stdout
- And if the token is absent/expired and exchange fails, or the gateway is unreachable, it exits non-zero with a clear human-readable error and a one-line fix hint
- **Not distributed:** this script lives in `scripts/` and is excluded from the published rqmd package.


<a id="rqmd-telemetry-019"></a>
### RQMD-TELEMETRY-019: Gateway date-range filter on `GET /api/v1/events`

<!-- sourced from brainstorm session 2026-05-07; prerequisite for RQMD-TELEMETRY-018 -->

- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- **Summary:** The `GET /api/v1/events` endpoint accepts a `since` query parameter (ISO-8601 datetime) so callers can retrieve only events within a specific time window without fetching and discarding unrelated data.
- Given `GET /api/v1/events?since=2026-04-23T00:00:00Z` is called
- When the gateway processes the request
- Then it returns only events where `created_at >= since`
- And an invalid `since` value returns HTTP 422 with a descriptive message
- And the parameter is optional; omitting it returns all events (existing behaviour unchanged).


<a id="rqmd-telemetry-020"></a>
### RQMD-TELEMETRY-020: SSH tunnel includes gateway HTTP port 18080

<!-- sourced from brainstorm session 2026-05-07; prerequisite for RQMD-TELEMETRY-018 -->

- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- **Summary:** The `telemetry-tunnel.sh` script tunnels port 18080 (gateway HTTP) in addition to the existing Postgres and MinIO ports, so `rqmd telemetry-review` and any other HTTP-based tooling can reach the gateway without a separate tunnel setup.
- Given `./scripts/telemetry-tunnel.sh <vm-ip>` is run
- When the SSH connection is established
- Then `localhost:18080` is forwarded to the VM's `127.0.0.1:18080` (the gateway container's published port)
- And the tunnel banner lists all four forwarded addresses including the gateway.
