# Brainstorm

Active ideas and untracked nuggets. Items move out once promoted to `docs/requirements/` or shipped.

---

## Architecture

### Split rqmd-cli requirements into rqmd-vscode?

**Status:** Analyzed, ready to execute.

**What moves:** Only 2 files need splitting (rest is clearly rqmd-cli):
- `ai-cli.md` (63 reqs) — prompt/skill/agent/bundle reqs → rqmd-vscode; CLI query flags stay
- `packaging.md` (19 reqs) — RQMD-PACKAGING-013–019 (extension) → rqmd-vscode; 001–012 (PyPI/CLI) stay
- `telemetry.md` — keep in rqmd-cli (server infra lives here)

**Open decisions:**
- New ID prefix for extension reqs? `RQMD-EXT-*` would be cleaner than `RQMD-AI-*` in a different repo
- Renumber on move or keep original IDs with cross-repo note?

**Steps:** `rqmd init` in rqmd-vscode → copy extension reqs → remove from rqmd-cli → update summaries

---

## New Prompts

### /fix — Quick bug fix without ceremony

Right now: file bug → refine → propose `/go` → spawn implementation agent → fix.

Proposed: `/fix <description>` tries to fix immediately AND files a bug report to `bugs.md` for tracking. Quick path for frustrated devs, still leaves audit trail.

---

## Requirement Format

### Summary field instead of user stories

The verbose "As a... I want... So that..." format is not scannable. Replace with:
- **Summary:** one-line description shown in dashboards and lists
- **Body:** free-form detail + Given/When/Then for implementation

The AI-generated summaries like `"rqmd bug <domain> 'title' — positional domain, tab-completed"` are much better than wall-of-text user stories.

---

## Skills

### Systems Analysis

MTTF equations for estimating system availability from component failure rates. Learned in grad school — immensely powerful. Could be its own skill or tied into diagramming.

### Discovery vs Explore vs Solve modes

- **Explore:** open-ended, breadth-focused, no required outcome
- **Discover:** focused on finding info to drive decisions
- **Solve:** specific problem with a potential solution

Might inform how prompts/skills are categorized.

---

## CLI

### BrokenPipeError handling

AI loves `head`/`tail` but it breaks `--json` output. Add:
```python
except BrokenPipeError:
    pass  # normal when piping to head/tail/less
```

### 🤖 AI Verified status

Distinguish `✅ Verified (human)` from `🤖 Verified (AI)`. Pin model + version + date for audit trail. Lower confidence than human verification but still useful.

---

## Telemetry

### Skill trigger telemetry

Batch skill invocation events instead of per-invocation network calls.

### Local dev admin tools

Docker Compose for Adminer/pgAdmin autoconfigured to reach remote telemetry server via tunnel.

### Feedback loop automation

Weekly GitHub Action that reads telemetry, proposes improvements, opens PR automatically.

### Opt-out by default

Ship telemetry on, easy opt-out via `RQMD_TELEMETRY_DISABLED=1`.

---

## GitHub Integration

### CI/CD examples

Link requirements to GH issues. When issue closes, auto-PR a status update via `rqmd --update`.

---

## Still worth triaging

- Agent-opinionated interview hints (`render_as_checkbox_prompt`, etc.)
- Terminal markdown improvements beyond bold/headings
- Explicit `Ctrl+Z`/`Ctrl+Y` bindings
- README generation as "tool-owned index" policy
- Cross-root config discovery for `--docs-dir`

---

## Reference: Recently Tracked

Items promoted from this file — see `docs/requirements/` for details:

| Area | IDs |
|------|-----|
| @rqmd chat participant | RQMD-EXT-053, 054 |
| VS Code extension | RQMD-EXT-051, 052, 055 |
| Self-healing bootstrap | RQMD-EXT-056–060 |
| Performance | RQMD-CORE-037–040, RQMD-AUTOMATION-038 |
| Bug tracking | RQMD-CORE-041–043, RQMD-AUTOMATION-039, RQMD-AI-059–060 |
| Agent workflow | RQMD-AI-039, 041, 042, 053–058 |
| Feedback/telemetry | RQMD-AI-053–055, RQMD-TELEMETRY-015 |
