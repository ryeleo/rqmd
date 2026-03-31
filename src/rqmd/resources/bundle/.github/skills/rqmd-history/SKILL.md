---
name: rqmd-history
description: Inspect rqmd history, timeline, detached snapshots, comparisons, and replay previews. Use for undo/redo investigation, time-travel debugging, historical diffs, and planning restore or replay actions without mutating the current worktree.
argument-hint: Describe the history question, refs, or time window you want to inspect.
user-invocable: true
---

Use this skill when the important question is when a requirement changed, what changed between snapshots, or how to recover prior state.

Workflow:
- Use `uv run rqmd --history` or `uv run rqmd --timeline` for high-level history inspection.
- Use `uv run rqmd-ai --json --history-ref <ref> --dump-status proposed` or another targeted export for detached point-in-time reads.
- Use `uv run rqmd-ai --json --compare-refs A..B` for structured historical diffs.
- Use `uv run rqmd-ai --json --history-report --history-ref <ref>` or `--compare-refs A..B` for report-oriented output.
- Use `uv run rqmd-ai --json --history-action restore:<ref>` or `replay:<A..B>` for read-only recovery planning before any write path.

Constraints:
- Keep historical exploration read-only unless the user explicitly wants a recovery action.
- Prefer stable `hid:<commit>` identifiers when persisting references across conversations.
- Skills improve workflow discovery; shell and tool approvals may still be required.