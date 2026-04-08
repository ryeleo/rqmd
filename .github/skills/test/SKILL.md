---
name: test
description: Repository-specific automated test, check, and validation commands for this project.
argument-hint: Describe whether you need the primary test command, integration coverage, or lint/check guidance for this repository.
user-invocable: true
metadata:
  guide:
    summary: Use the repository's canonical agent workflow validation interface instead of guessing test workflows.
    workflow:
      - Start with `bash ./agent-workflow.sh preflight` if repository readiness is uncertain.
      - Prefer `bash ./agent-workflow.sh validate` and its focused profiles before falling back to raw test commands.
      - Use any dedicated integration or lint/check commands below when customizing or debugging the validation flow.
      - Update this generated skill if the repository's real validation workflow differs from the scaffold.
    examples:
      - Ask which `bash ./agent-workflow.sh validate --profile ...` mode matches the current batch.
      - Ask for integration or lint commands before finishing a change.
---

Use this skill when work needs the repository's actual automated validation commands.

Canonical validation entry point:
- `bash ./agent-workflow.sh validate`
- `bash ./agent-workflow.sh validate --profile test`
- `bash ./agent-workflow.sh validate --profile integration`
- `bash ./agent-workflow.sh validate --profile docs`

Detected sources:
- pyproject.toml
- scripts/local-smoke.sh

Primary automated test commands:
- `uv run --extra dev pytest -q`

Integration or end-to-end test commands:
- No dedicated integration or end-to-end test command was detected yet. Add one here if the repository has it.

Lint and check commands:
- No lint or check command was detected yet. Add one here if the repository uses it.

Notes:
- Smoke coverage was detected under the development skill; keep `/test` focused on repeatable automated checks.
- Review the generated commands and tighten them to the repository's canonical workflows before relying on them in automation.

Constraints:
- Prefer the canonical agent workflow validation interface first; use the raw commands below when debugging or refining that interface.
- Review and edit this generated skill after bootstrap if the detected commands are incomplete or stale.
