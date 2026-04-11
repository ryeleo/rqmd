---
name: test
description: Repository-specific automated test, check, and validation commands for this project.
argument-hint: Describe whether you need the primary test command, integration coverage, or lint/check guidance for this repository.
user-invocable: true
metadata:
  guide:
    summary: Use the repository's canonical agent workflow validation interface instead of guessing test workflows.
    workflow:
      - Start with `{{AGENT_WORKFLOW_PATH}} preflight` if repository readiness is uncertain.
      - Prefer `{{AGENT_WORKFLOW_PATH}} validate` and its focused profiles before falling back to raw test commands.
      - Use any dedicated integration or lint/check commands below when customizing or debugging the validation flow.
      - Update this generated skill if the repository's real validation workflow differs from the scaffold.
    examples:
      - Ask which `{{AGENT_WORKFLOW_PATH}} validate --profile ...` mode matches the current batch.
      - Ask for integration or lint commands before finishing a change.
---

Use this skill when work needs the repository's actual automated validation commands.

Canonical validation entry point:
- `{{AGENT_WORKFLOW_PATH}} validate`
- `{{AGENT_WORKFLOW_PATH}} validate --profile test`
- `{{AGENT_WORKFLOW_PATH}} validate --profile integration`
- `{{AGENT_WORKFLOW_PATH}} validate --profile docs`

Detected sources:
{{DETECTED_SOURCES}}

Primary automated test commands:
{{PRIMARY_TEST_COMMANDS}}

Integration or end-to-end test commands:
{{INTEGRATION_TEST_COMMANDS}}

Lint and check commands:
{{LINT_AND_CHECK_COMMANDS}}

Notes:
{{NOTES}}

Constraints:
- Prefer the canonical agent workflow validation interface first; use the raw commands below when debugging or refining that interface.
- Review and edit this generated skill after bootstrap if the detected commands are incomplete or stale.