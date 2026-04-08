---
name: dev
description: Repository-specific development commands for build, run, smoke-test, and environment setup in this project.
argument-hint: Describe whether you need environment setup, build, run, or smoke-test guidance for this repository.
user-invocable: true
metadata:
  guide:
    summary: Use the repository's canonical agent workflow entry point and development commands instead of guessing build, run, or smoke flows.
    workflow:
      - Start with `bash ./agent-workflow.sh preflight` to verify repository readiness before implementation.
      - Use the canonical build, run, and smoke commands below for active development work.
      - Prefer `bash ./agent-workflow.sh validate --profile build` or `bash ./agent-workflow.sh validate --profile smoke` before handoff when those profiles fit the task.
      - Update this generated skill if the repository's real commands differ from the scaffold.
    examples:
      - Ask which `bash ./agent-workflow.sh` profile should be used before implementation or handoff.
      - Ask for the canonical build or run command before launching local development.
---

Use this skill when implementation work needs the repository's actual development commands.

Canonical agent workflow entry point:
- `bash ./agent-workflow.sh preflight`
- `bash ./agent-workflow.sh validate --profile build`
- `bash ./agent-workflow.sh validate --profile smoke`

Detected sources:
- pyproject.toml
- scripts/local-smoke.sh

Environment setup:
- `uv sync --extra dev`

Build commands:
- No canonical build command was detected yet. Replace this with the repository's real build step.

Run commands:
- No canonical run or dev-server command was detected yet. Replace this with the repository's real run step.

Smoke commands:
- `./scripts/local-smoke.sh`

Notes:
- Smoke coverage was detected under the development skill; keep `/test` focused on repeatable automated checks.
- Review the generated commands and tighten them to the repository's canonical workflows before relying on them in automation.

Constraints:
- Prefer the canonical agent workflow entry point for readiness and validation checks, and use the commands below for direct development work.
- Review and edit this generated skill after bootstrap if the detected commands are incomplete or stale.
