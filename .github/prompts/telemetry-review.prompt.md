---
description: "rqmd-cli: Cluster recent telemetry events into proposed requirements."
name: "telemetry-review"
argument-hint: "Leave blank for the default 14-day window, or specify a number of days (e.g. '30')."
agent: "rqmd"
---

Triage recent telemetry signal into proposed requirements for rqmd-cli.

**Setup:**
- Ensure the SSH tunnel is running: start the `Tunnel to Az TeleVM` VS Code task if not active.
- Default query window: last 14 days. Use the argument to override.

**Query** — run in the terminal to fetch events:

```
python3 scripts/telemetry-review.py [DAYS]
```

Replace `[DAYS]` with the argument if provided (e.g. `python3 scripts/telemetry-review.py 30`); omit for the 14-day default.
Capture stdout as the event JSON array for the clustering step below.

> **⚠️ Note:** Requires the SSH tunnel to be active so `localhost:18080` reaches the gateway.
> If the script exits non-zero, follow the fix hint it prints.

**Cluster** the returned events:
- Group by `(event_type, detail.category, root_cause_from_summary)`.
- Keep only clusters with **≥ 2 events**.
- For each cluster present: severity range, distinct `agent_name` values, representative `detail.command` and `detail.stderr_snippet`, event count, and a suggested requirement title.

**Dedup check** before drafting — scan `docs/requirements/` for open requirements with similar language. Flag matches as `⚠️ Possible duplicate of RQMD-...` and skip drafting for that cluster unless the user confirms it is distinct.

**Draft** (one cluster at a time, with confirmation):
1. Use `rqmd --json --non-interactive` to get the next available ID and identify the best-fit domain file.
2. Write a 💡 Proposed entry in the correct `docs/requirements/` file following the standard format (status, priority, summary, Given/When/Then).
3. Add a back-reference comment immediately after the heading: `<!-- sourced from telemetry cluster, query window: <ISO date range>, event_count: N -->`.
4. After all accepted drafts are written, run `rqmd --verify-summaries --non-interactive`.

**Closeout:** Report total events fetched, clusters surfaced, clusters drafted, clusters flagged as duplicates.
