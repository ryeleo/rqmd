---
name: rqmd-history
description: Inspect rqmd history, timeline, detached snapshots, comparisons, and replay previews. Use for undo/redo investigation, time-travel debugging, historical diffs, and planning restore or replay actions without mutating the current worktree.
argument-hint: Describe the history question, refs, or time window you want to inspect.
user-invocable: true
metadata:
  guide:
    summary: Inspect detached history and recovery plans without mutating the working catalog.
    workflow:
      - Start with rqmd --history or rqmd --timeline for high-level inspection.
      - Use detached rqmd-ai exports for point-in-time reads, comparisons, and recovery previews.
      - Keep the flow read-only unless a recovery action is explicitly requested.
    examples:
      - rqmd --history --json
      - rqmd-ai --json --history-ref 0 --dump-status proposed
      - rqmd-ai --json --compare-refs 0..1
---

Use this skill when the important question is when a requirement changed, what changed between snapshots, or how to recover prior state.

Workflow:
- Use `rqmd --history` or `rqmd --timeline` for high-level history inspection.
- Use `rqmd-ai --json --history-ref <ref> --dump-status proposed` or another targeted export for detached point-in-time reads.
- Use `rqmd-ai --json --compare-refs A..B` for structured historical diffs.
- Use `rqmd-ai --json --history-report --history-ref <ref>` or `--compare-refs A..B` for report-oriented output.
- Use `rqmd-ai --json --history-action restore:<ref>` or `replay:<A..B>` for read-only recovery planning before any write path.

Constraints:
- Keep historical exploration read-only unless the user explicitly wants a recovery action.
- Prefer stable `hid:<commit>` identifiers when persisting references across conversations.
- Skills improve workflow discovery; shell and tool approvals may still be required.
