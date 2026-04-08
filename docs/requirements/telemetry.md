# Telemetry Requirement

Scope: agent-facing telemetry infrastructure for capturing AI workflow friction, improvement suggestions, and session diagnostics — enabling rqmd's own AI agents to report how rqmd can be improved.

<!-- acceptance-status-summary:start -->
Summary: 3💡 11🔧 0✅ 0⚠️ 0⛔ 1🗑️
<!-- acceptance-status-summary:end -->

### RQMD-TELEMETRY-001: Local telemetry development stack
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a developer working on rqmd telemetry features locally
- I want a Docker Compose stack with Postgres, MinIO, a telemetry gateway, and admin tooling
- So that the full telemetry pipeline can run on a single machine without external service dependencies.
- Given a developer runs `docker compose -f docker-compose.telemetry.yml up`
- When all services reach healthy status
- Then a Postgres database is available for structured telemetry events, a MinIO bucket exists for larger artifacts such as session logs and prompt snapshots, and a gateway accepts HTTP posts on a non-standard dev port
- And default credentials are dev-only, clearly marked, and never used for production.

### RQMD-TELEMETRY-002: Telemetry event schema
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a developer querying telemetry data to understand agent behavior
- I want a structured event schema that captures session identity, event type, severity, agent context, and freeform detail
- So that telemetry data is queryable, filterable, and useful for diagnosing patterns across many agent sessions.
- Given an AI agent submits a telemetry event
- When the event is stored
- Then it includes at minimum: event_id, session_id, timestamp, agent_name, event_type (struggle | suggestion | error | success | workflow_step), severity, summary text, and optional structured detail JSON
- And event_type is extensible so new categories can be added without schema migration.

### RQMD-TELEMETRY-003: Telemetry HTTP gateway
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As an AI agent running inside a chat session that encounters friction with rqmd
- I want a simple HTTP endpoint I can POST structured telemetry events to
- So that telemetry capture does not require database drivers, SDK dependencies, or complex client setup inside the agent environment.
- Given an agent has a telemetry endpoint URL configured
- When it POSTs a JSON event body to the gateway
- Then the gateway validates the payload against the event schema, stores the structured event in Postgres, and optionally stores referenced artifacts in MinIO
- And the gateway responds with a confirmation or structured error so the agent knows whether the report succeeded.

### RQMD-TELEMETRY-004: rqmd-telemetry bundle skill
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a maintainer who installs the rqmd AI bundle into a repository
- I want an `/rqmd-telemetry` skill that teaches AI agents how and when to submit telemetry
- So that agents have clear instructions for reporting friction, errors, and improvement ideas without needing ad hoc prompting.
- Given an AI agent encounters a problem while running rqmd workflows
- When the agent has the rqmd-telemetry skill loaded
- Then it knows the telemetry endpoint, the event schema, and the expected submission protocol
- And it can decide autonomously whether to submit a struggle report, an improvement suggestion, or both based on what it observed
- And the skill guidance makes clear that telemetry is opt-in, local-first, and never silently phones home.

### RQMD-TELEMETRY-005: Agent struggle reporting
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a developer reviewing telemetry to understand where rqmd agents fail
- I want agents to report structured "I struggled because..." events when they encounter friction with rqmd workflows
- So that recurring failure patterns surface as queryable data instead of disappearing into chat transcripts.
- Given an AI agent tries to run an rqmd command, parse rqmd output, or follow rqmd workflow guidance and encounters unexpected behavior
- When it recognizes that something went wrong or took significantly more effort than expected
- Then it submits a telemetry event with event_type "struggle", a concise summary of what it was trying to do, what went wrong, any error output or unexpected state it observed, and which rqmd command or skill was involved
- And the event captures enough context for a developer to reproduce or understand the failure without needing the full chat transcript.

### RQMD-TELEMETRY-006: Agent improvement suggestions
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
- As a developer who wants rqmd to get better informed by AI agent experience
- I want agents to proactively submit "rqmd could be improved if..." suggestions based on their direct experience using rqmd
- So that product improvement ideas come from the agents that actually use the tool day to day, not just from manually observed failures.
- Given an AI agent completes or partially completes an rqmd workflow
- When it identifies friction that was not a hard failure but made the workflow harder, slower, or more confusing than it should have been
- Then it submits a telemetry event with event_type "suggestion", a concise description of the observed friction, a proposed improvement or change, and an optional confidence level
- And the suggestion captures enough detail for a developer to evaluate whether the idea is actionable without needing the full session context.

### RQMD-TELEMETRY-007: Telemetry opt-out and privacy controls
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a user who values privacy and does not want telemetry data sent to external services
- I want a clear opt-out mechanism that disables all telemetry transmission
- So that rqmd telemetry cannot become a trust liability.
- Given a repository has the rqmd AI bundle installed with the telemetry skill
- When telemetry is enabled by default with built-in production defaults
- Then agents can submit events without any manual configuration
- And when a user sets `RQMD_TELEMETRY_DISABLED=1` in their environment
- Then both `resolve_telemetry_endpoint` and `resolve_telemetry_api_key` return None and no events are sent
- And the skill guidance makes the opt-out contract visible to both agents and humans reviewing the installed bundle.

### RQMD-TELEMETRY-008: Agent telemetry configuration discovery
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As an AI agent that needs to submit telemetry events to a remote gateway
- I want a single discovery mechanism that resolves both the telemetry endpoint URL and the API key from well-known configuration sources
- So that I can authenticate with the gateway without ad-hoc credential handling or hard-coded secrets.
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
- As a developer who wants rqmd to be reliably invocable by AI agents
- I want agents to report a specific telemetry event when they fail to invoke `rqmd` or `rqmd-ai` and fall back to directly reading or writing requirement files
- So that command-resolution failures are tracked as a distinct, high-signal friction category rather than being lost in generic struggle reports.
- Given an AI agent attempts to run an rqmd or rqmd-ai command
- When the command is not found, exits with a non-zero status due to invocation issues (wrong Python, missing entrypoint, missing extras), or the agent tries multiple invocation variants before succeeding
- Then the agent submits a telemetry event with event_type "struggle", a new detail field `"category": "command_discovery"`, the exact commands attempted, and the fallback action taken
- And the event severity is "high" because CLI unreachability undermines the entire rqmd workflow contract
- And the telemetry skill guidance explicitly teaches agents to recognize and report this pattern rather than silently working around it.

### RQMD-TELEMETRY-010: Telemetry feedback loop — time-window review and proposals
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
- As a developer returning to the project after time away
- I want to run a single command that fetches telemetry events from a given time window, clusters them by pattern, and produces actionable improvement proposals
- So that accumulated agent friction turns into concrete changes instead of sitting unread in a database.
- Given a developer runs a feedback-loop command with a time window (e.g. `rqmd-ai telemetry review --since 7d`)
- When the command queries stored events from the gateway
- Then it groups events by category, command, and recurrence count
- And it produces a ranked list of improvement proposals with suggested patches, skill edits, or requirement updates
- And the developer can accept, reject, or refine each proposal before any changes are applied.

### RQMD-TELEMETRY-011: Automated weekly telemetry triage via GitHub Actions
- **Status:** 💡 Proposed
- **Priority:** 🟡 P2 - Medium
- As a maintainer who wants telemetry insights to surface automatically
- I want a scheduled GitHub Actions workflow that runs the telemetry feedback loop weekly and opens a PR when it finds worthwhile improvements
- So that the project benefits from agent-reported friction even when no human actively checks the telemetry dashboard.
- Given a `telemetry-triage` workflow is scheduled to run weekly
- When the workflow queries the previous week's telemetry events
- Then it runs the feedback-loop review, filters for proposals above a configurable confidence threshold, and applies accepted patches to a new branch
- And it opens a pull request with a summary of the telemetry patterns found, the changes proposed, and links back to the originating events
- And the PR is labeled for human review so no changes merge without approval.

### RQMD-TELEMETRY-012: Short-lived session tokens via gateway exchange
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer who ships rqmd as a public package
- I want the telemetry client to authenticate via short-lived tokens fetched at runtime from the gateway instead of shipping a long-lived plaintext API key in the source code
- So that credential exposure in the published package cannot be used to spam or poison the telemetry database indefinitely.
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
- As a gateway operator who wants to protect the telemetry database from abuse and misconfigured agents
- I want per-client and global rate limits enforced at the gateway layer
- So that no single source can flood the database, whether through malice or misconfiguration.
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
- **Status:** 💡 Proposed
- **Priority:** 🔴 P0 - Critical
- As a developer reviewing telemetry to prioritize rqmd improvements
- I want a dedicated `feedback` event type that captures user-driven improvement feedback separately from autonomous agent reports
- So that feedback submitted through `/feedback` sessions is distinguishable from autonomous struggle and suggestion events, enabling focused triage of human-intentional input.
- Given `EventType` in `src/rqmd/telemetry.py` currently defines `"struggle" | "suggestion" | "error" | "success" | "workflow_step"`
- When the `feedback` event type is added
- Then `EventType` includes `"feedback"` as a valid literal value
- And `submit_event()` accepts `event_type="feedback"` without modification
- And the telemetry skill and `/rqmd-feedback` skill document the `feedback` event type and its expected detail fields
- And feedback events include a `detail.category` field with one of: `ux_friction`, `missing_feature`, `docs_gap`, `workflow_confusion`, `performance`, `other`
- And feedback events optionally include `detail.suggested_improvement` as a freeform text field describing what the user thinks should change
- And the gateway accepts `feedback` events without requiring a schema migration (the event_type column is already extensible per RQMD-TELEMETRY-002).
