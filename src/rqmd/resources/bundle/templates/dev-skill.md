---
name: dev
description: Repository-specific development commands for build, run, smoke-test, and environment setup in this project.
argument-hint: Describe whether you need environment setup, build, run, or smoke-test guidance for this repository.
user-invocable: true
metadata:
  guide:
    summary: Use the repository's canonical agent workflow entry point and development commands instead of guessing build, run, or smoke flows.
    workflow:
      - Start with `{{AGENT_WORKFLOW_PATH}} preflight` to verify repository readiness before implementation.
      - Use the canonical build, run, and smoke commands below for active development work.
      - Prefer `{{AGENT_WORKFLOW_PATH}} validate --profile build` or `{{AGENT_WORKFLOW_PATH}} validate --profile smoke` before handoff when those profiles fit the task.
      - Update this generated skill if the repository's real commands differ from the scaffold.
    examples:
      - Ask which `{{AGENT_WORKFLOW_PATH}}` profile should be used before implementation or handoff.
      - Ask for the canonical build or run command before launching local development.
---

Use this skill when implementation work needs the repository's actual development commands.

Canonical agent workflow entry point:
- `{{AGENT_WORKFLOW_PATH}} preflight`
- `{{AGENT_WORKFLOW_PATH}} validate --profile build`
- `{{AGENT_WORKFLOW_PATH}} validate --profile smoke`

Detected sources:
{{DETECTED_SOURCES}}

Environment setup:
{{ENVIRONMENT_SETUP}}

Build commands:
{{BUILD_COMMANDS}}

Run commands:
{{RUN_COMMANDS}}

Smoke commands:
{{SMOKE_COMMANDS}}

Notes:
{{NOTES}}

Constraints:
- Prefer the canonical agent workflow entry point for readiness and validation checks, and use the commands below for direct development work.
- Review and edit this generated skill after bootstrap if the detected commands are incomplete or stale.