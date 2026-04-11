---
description: "Send improvement feedback about rqmd to the project's telemetry service. Works iteratively — submits telemetry on start, refines the payload through conversation, and finalizes on close."
name: "feedback"
argument-hint: "Describe the friction, missing feature, or idea you want to report, or leave blank to start interactively."
agent: "rqmd"
---

Start a user-driven improvement feedback session for **rqmd itself**.

> **ℹ️ Info:** This prompt sends feedback about the rqmd CLI and AI workflows to the rqmd developer. To file a bug for **your own project**, use `/bug` instead.

**Before saying anything to the user:**
- Resolve the telemetry endpoint and key using `resolve_telemetry_endpoint()` and `resolve_telemetry_api_key()` from `src/rqmd/telemetry.py`.
- If telemetry is active, immediately submit a `feedback` event with `event_type="feedback"`, `severity="low"`, `summary="Feedback session started"`, and `detail={"phase": "session_start"}`. Generate a session UUID and reuse it for all events in this session.
- If `RQMD_TELEMETRY_DISABLED=1` is set, note this to the user and continue without sending events.

**Working with the user:**
- Ask what friction, idea, or observation they want to report (skip this if the invocation argument already describes it).
- Help shape the feedback into a structured payload. Valid `detail.category` values: `ux_friction`, `missing_feature`, `docs_gap`, `workflow_confusion`, `performance`, `other`.
- After each significant refinement, submit an updated `feedback` event with the current payload so no partial feedback is lost if the session is interrupted.
- Prompt the user to sharpen vague feedback into something actionable — a short description of what happened, what they expected, and what should change.

**Closing the session:**
When the user is satisfied, offer to create a GitHub issue on `ryeleo/rqmd` if the feedback is concrete enough (a specific bug, missing feature, or docs gap with a clear description):
- Check `gh auth status` to verify `gh` CLI is available and authenticated.
- If available and the user confirms, run `gh issue create --repo ryeleo/rqmd --title "..." --body "..."` using the polished feedback as the body.
- Capture the created issue URL and add it to the final feedback payload as `detail.github_issue_url`.
- If `gh` is unavailable or the user declines, note the reason in `detail.issue_skipped_reason`.

Then submit a final `feedback` event with `detail.phase="session_close"` and a polished payload:
- `summary`: a concise one-line description for a developer scanning the dashboard.
- `detail.category`: the agreed category (one of the valid values above).
- `detail.suggested_improvement`: what the user thinks should change, in plain language.
- `severity`: chosen collaboratively — `low` for minor friction, `medium` for noticeable gaps, `high` for significant blockers, `critical` for breaking issues.

For telemetry submission mechanics see the `rqmd-telemetry` skill or `src/rqmd/telemetry.py`.
