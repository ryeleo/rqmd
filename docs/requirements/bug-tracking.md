# Bug Tracking

Scope: first-class bug tracking requirements, templates, and workflow behavior distinct from feature requirements.

Use this file for **meta-requirements about bug tracking itself**.

- Put policy and capability requirements here (metadata fields, workflow rules, templates, filtering behavior).
- Do **not** file day-to-day project defects here.
- File concrete rqmd defects in the [runtime bug backlog](bugs.md).

<!-- acceptance-status-summary:start -->
Summary: 0💡 2🔧 0✅ 0⚠️ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->

### RQMD-BUG-001: Dedicated bug-tracking requirement domain
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer, I want bug-tracking behavior to live in its own requirement domain
- So that bug workflow capability is discoverable without scanning unrelated domains.
- So that bug behavior requirements are separated from runtime bug instances filed during project work.
- So that the requirements index includes an explicit bug-tracking domain entry and ID prefix mapping.

### RQMD-BUG-002: Runtime bug backlog separated from behavior requirements
- **Status:** 🔧 Implemented
- **Priority:** 🟠 P1 - High
- As a maintainer, I want `docs/requirements/bugs.md` to be a runtime bug backlog
- So that filed bug instances have a dedicated place to accumulate without mixing with behavior contracts.
- So that bug-tracking behavior requirements stay stable in `bug-tracking.md` while `bugs.md` remains an operational queue.
- So that the documentation makes this split explicit to users and agents.

## Boundary Rule

- If the item describes how bug tracking should work in rqmd, it belongs in this file.
- If the item describes an actual defect in rqmd behavior, it belongs in the [runtime bug backlog](bugs.md).

## Related Cross-Domain Requirements

These requirements remain in their original domains but define critical bug-tracking behavior:

- `RQMD-CORE-041` (`core-engine.md`): `type` metadata parser support.
- `RQMD-CORE-042` (`core-engine.md`): `affects` cross-reference metadata.
- `RQMD-CORE-043` (`core-engine.md`): bug-report template.
- `RQMD-AUTOMATION-039` (`automation-api.md`): `--dump-type bug` filter.
- `RQMD-AI-059` (`ai-cli.md`): brainstorm/refine bug detection and template routing.
- `RQMD-AI-060` (`ai-cli.md`): `/bug` prompt flow for bug filing.
- `RQMD-INTERACTIVE-034` (`interactive-ux.md`): inline `b` key bug filing in interactive mode.