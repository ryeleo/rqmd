---
name: dev
description: Repository-specific development commands for build, run, smoke-test, and environment setup in this project.
argument-hint: Describe whether you need environment setup, build, run, or smoke-test guidance for this repository.
user-invocable: true
metadata:
  guide:
    summary: Use the repository's canonical development commands instead of guessing build, run, or smoke flows.
    workflow:
      - Start with the generated environment setup and command list.
      - Prefer the canonical build, run, or smoke command over generic guesses.
      - Update this generated skill if the repository's real commands differ from the scaffold.
    examples:
      - Ask for the canonical smoke-test command for this repository.
      - Ask for the canonical build or run command before launching local development.
---

Use this skill when implementation work needs the repository's actual development commands.

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
- Prefer these repository-specific commands over generic guesses.
- Review and edit this generated skill after bootstrap if the detected commands are incomplete or stale.
