---
name: rqmd-feedback
description: Send user-driven improvement feedback about rqmd via the telemetry service. Use to report friction, missing features, docs gaps, or workflow confusion to the rqmd developer with full telemetry context.
argument-hint: Describe the friction, missing feature, or improvement idea to report.
user-invocable: true
metadata:
  guide:
    summary: Guide users through a structured feedback session that submits telemetry events to help the rqmd developer prioritize improvements based on real-world usage.
    workflow:
      - Submit a feedback event immediately on session start to record that feedback is being collected.
      - Work with the user to shape the feedback into a structured payload with category, description, and suggested improvement.
      - Submit updated feedback events as the payload evolves so no partial feedback is lost.
      - Offer to create a GitHub issue on ryeleo/rqmd when the feedback is concrete and actionable.
      - Submit a final polished feedback event on session close.
    examples:
      - Start a feedback session when the user says /feedback.
      - Report ux_friction when a workflow step is confusing or takes more steps than expected.
      - Create a GitHub issue for a concrete bug with a clear reproduction path.
---

Use this skill to run a structured user-driven feedback session for improving rqmd.

> **⚠️ Note:** This skill is for reporting issues with **rqmd itself** — friction, missing features, or bugs in the rqmd CLI and AI workflows. To file a bug for **your own project**, use `/bug` instead, which creates a tracked requirement in your `docs/requirements/` folder.

## When to use this skill

Invoke this skill when the user explicitly asks to give feedback on rqmd — not for autonomous agent friction (use `rqmd-telemetry` for that). This skill is for *human-intentional* improvement feedback submitted through `/feedback`.

## Feedback event type

All feedback submission uses `event_type="feedback"`. This separates user-driven input from autonomous agent reports (`struggle`, `suggestion`, `error`) so the rqmd developer can triage them independently.

## Payload schema

```json
{
  "session_id": "<uuid — reuse across all events in one feedback session>",
  "event_type": "feedback",
  "severity": "low | medium | high | critical",
  "summary": "Concise one-line description for a developer scanning the dashboard",
  "detail": {
    "phase": "session_start | in_progress | session_close",
    "category": "ux_friction | missing_feature | docs_gap | workflow_confusion | performance | other",
    "description": "Plain-language description of the issue or idea",
    "suggested_improvement": "What the user thinks should change",
    "github_issue_url": "<optional: URL if a GitHub issue was created>",
    "issue_skipped_reason": "<optional: why issue creation was skipped>"
  }
}
```

**Valid categories:**

| Category | When to use |
|---|---|
| `ux_friction` | A workflow step is awkward, confusing, or requires more effort than expected |
| `missing_feature` | Something useful is absent — a command, flag, output field, or workflow |
| `docs_gap` | Documentation is missing, misleading, or out of sync with behavior |
| `workflow_confusion` | The rqmd workflow guidance led in a wrong or confusing direction |
| `performance` | A command or workflow is noticeably slow |
| `other` | Anything that does not fit a specific category above |

**Severity guidance:**

| Severity | When to use |
|---|---|
| `low` | Minor friction — annoying but does not block anything |
| `medium` | Noticeable gap that regularly adds friction to real work |
| `high` | Significant blocker that degrades the core workflow |
| `critical` | Breaking issue that makes rqmd unusable for a key workflow |

## Submission workflow

### 1. Session start

Before asking the user anything, submit a `session_start` event:

```python
from rqmd.telemetry import send_event
from uuid import uuid4

session_id = str(uuid4())

send_event(
    event_type="feedback",
    severity="low",
    summary="Feedback session started",
    session_id=session_id,
    detail={"phase": "session_start"},
)
```

Endpoint resolution and authentication (including automatic token exchange) are handled internally by `send_event`. If `RQMD_TELEMETRY_DISABLED=1` is set, `send_event` returns `None` silently — note this to the user and continue without sending events.

### 2. Iterative refinement

As the user describes their feedback, help them shape a structured payload. After each significant refinement, submit an `in_progress` event with the current payload so no partial feedback is lost if the session is interrupted:

```python
send_event(
    event_type="feedback",
    severity="medium",      # update as agreed with user
    summary="Short description of the feedback",
    session_id=session_id,
    detail={
        "phase": "in_progress",
        "category": "ux_friction",
        "description": "The user's description of the issue",
        "suggested_improvement": "What they think should change",
    },
)
```

### 3. GitHub issue creation (when appropriate)

After refining the payload, evaluate whether the feedback is concrete enough to be a GitHub issue — a specific bug, missing feature, or docs gap with a clear description.

If yes, offer to create one:

```bash
# Check gh is available and authenticated
gh auth status

# Create the issue if auth succeeds
gh issue create \
  --repo ryeleo/rqmd \
  --title "<concise title from feedback summary>" \
  --body "<polished body from feedback description + suggested_improvement>"
```

- If `gh` is not installed or not authenticated, set `detail.issue_skipped_reason` and continue.
- If the user declines, also set `detail.issue_skipped_reason = "user_declined"`.
- If the issue is created, capture the URL and include it as `detail.github_issue_url` in the final event.

### 4. Session close

When the user is done, submit a final polished event:

```python
send_event(
    event_type="feedback",
    severity="medium",      # final agreed severity
    summary="Final polished one-line summary",
    session_id=session_id,
    detail={
        "phase": "session_close",
        "category": "ux_friction",
        "description": "Final description",
        "suggested_improvement": "Final improvement text",
        # include github_issue_url or issue_skipped_reason if applicable
    },
)
```

## Telemetry mechanics

See the `rqmd-telemetry` skill for full endpoint resolution, authentication, event field reference, and troubleshooting. The `feedback` event type follows the same HTTP protocol as all other event types.
