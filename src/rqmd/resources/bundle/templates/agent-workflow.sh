#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)"
cd "$SCRIPT_DIR"

if command -v python3 >/dev/null 2>&1; then
  PYTHON_BIN="python3"
elif command -v python >/dev/null 2>&1; then
  PYTHON_BIN="python"
else
  echo "agent-workflow.sh requires python3 or python in PATH" >&2
  exit 127
fi

export RQMD_AGENT_WORKFLOW_ROOT="$SCRIPT_DIR"
export RQMD_AGENT_WORKFLOW_DATA="$(cat <<'JSON'
{{WORKFLOW_PLAN_JSON}}
JSON
)"

exec "$PYTHON_BIN" - "$@" <<'PY'
from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


ROOT = Path(os.environ["RQMD_AGENT_WORKFLOW_ROOT"])
PLAN = json.loads(os.environ["RQMD_AGENT_WORKFLOW_DATA"])
SHELL_EXECUTABLE = os.environ.get("SHELL") or None


def _normalize_command(command: str) -> str:
    text = str(command).strip()
    if len(text) >= 2 and text.startswith("`") and text.endswith("`"):
        return text[1:-1]
    return text


def _tail_text(text: str, max_lines: int = 20) -> str:
    stripped = str(text).rstrip()
    if not stripped:
        return ""
    lines = stripped.splitlines()
    if len(lines) <= max_lines:
        return stripped
    return "\n".join(lines[-max_lines:])


def _command_binary(command: str) -> str:
    normalized = _normalize_command(command)
    if not normalized:
        return ""
    try:
        parts = shlex.split(normalized)
    except ValueError:
        parts = normalized.split()
    return parts[0] if parts else ""


def _command_available(command: str) -> tuple[bool, str]:
    binary = _command_binary(command)
    if not binary:
        return False, "No executable token could be parsed from the command."
    candidate = Path(binary)
    if candidate.is_absolute():
        return candidate.exists(), f"Expected executable path {candidate} to exist."
    if binary.startswith(("./", "../")) or "/" in binary:
        resolved = (ROOT / candidate).resolve()
        return resolved.exists(), f"Expected repository-local command path {resolved} to exist."
    return shutil.which(binary) is not None, f"Expected `{binary}` to be available in PATH."


def _guidance_checks() -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    for relative_path in PLAN.get("guidance_files", []):
        path = ROOT / str(relative_path)
        exists = path.exists()
        results.append(
            {
                "id": f"guidance:{relative_path}",
                "kind": "guidance-file",
                "target": str(relative_path),
                "status": "passed" if exists else "failed",
                "message": "Guidance file is present." if exists else "Guidance file is missing.",
                "fix": "Regenerate or restore the rqmd-managed workflow files for this repository.",
            }
        )
    return results


def _command_checks() -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    seen: set[str] = set()
    for command in PLAN.get("preflight_commands", []):
        normalized = _normalize_command(command)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        available, detail = _command_available(normalized)
        binary = _command_binary(normalized)
        results.append(
            {
                "id": f"command:{binary or normalized}",
                "kind": "command",
                "target": normalized,
                "status": "passed" if available else "failed",
                "message": "Command is available." if available else detail,
                "fix": (
                    f"Install or expose `{binary}` in PATH, or update agent-workflow.sh if `{normalized}` is no longer canonical."
                    if binary
                    else "Update the canonical command definition in agent-workflow.sh."
                ),
            }
        )
    return results


def run_preflight() -> int:
    checks = _guidance_checks() + _command_checks()
    ok = all(check["status"] == "passed" for check in checks)
    payload = {
        "mode": "preflight",
        "ok": ok,
        "root": str(ROOT),
        "detected_sources": list(PLAN.get("detected_sources", [])),
        "checks": checks,
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if ok else 1


def _selected_stage_ids(profile: str) -> list[str]:
    profiles = PLAN.get("profiles", {})
    selected = profiles.get(profile)
    if not isinstance(selected, list):
        raise SystemExit(f"Unknown validation profile: {profile}")
    return [str(item) for item in selected]


def _stage_results_for_profile(profile: str) -> list[dict[str, object]]:
    selected = set(_selected_stage_ids(profile))
    return [stage for stage in PLAN.get("stages", []) if stage.get("id") in selected]


def _run_command(command: str) -> dict[str, object]:
    completed = subprocess.run(
        command,
        cwd=ROOT,
        shell=True,
        executable=SHELL_EXECUTABLE,
        text=True,
        capture_output=True,
        check=False,
    )
    payload: dict[str, object] = {
        "command": command,
        "returncode": completed.returncode,
    }
    stdout_tail = _tail_text(completed.stdout)
    stderr_tail = _tail_text(completed.stderr)
    if stdout_tail:
        payload["stdout_tail"] = stdout_tail
    if stderr_tail:
        payload["stderr_tail"] = stderr_tail
    return payload


def run_validate(profile: str) -> int:
    stages_payload: list[dict[str, object]] = []
    ok = True
    for stage in _stage_results_for_profile(profile):
        commands = [_normalize_command(command) for command in stage.get("commands", []) if _normalize_command(command)]
        if not commands:
            stages_payload.append(
                {
                    "id": stage.get("id"),
                    "label": stage.get("label"),
                    "status": "skipped",
                    "reason": "No commands configured for this stage.",
                    "commands": [],
                }
            )
            continue

        command_results: list[dict[str, object]] = []
        stage_status = "passed"
        for command in commands:
            result = _run_command(command)
            command_results.append(result)
            if int(result["returncode"]) != 0:
                stage_status = "failed"
                ok = False
                break

        stages_payload.append(
            {
                "id": stage.get("id"),
                "label": stage.get("label"),
                "status": stage_status,
                "commands": command_results,
            }
        )

        if stage_status == "failed":
            break

    payload = {
        "mode": "validate",
        "ok": ok,
        "profile": profile,
        "root": str(ROOT),
        "stages": stages_payload,
    }
    json.dump(payload, sys.stdout, indent=2)
    sys.stdout.write("\n")
    return 0 if ok else 1


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Canonical agent workflow entry point for repository readiness and validation."
    )
    subparsers = parser.add_subparsers(dest="command")
    subparsers.add_parser("preflight", help="Verify repository readiness and emit machine-readable JSON.")
    validate = subparsers.add_parser("validate", help="Run canonical validation stages and emit machine-readable JSON.")
    validate.add_argument(
        "--profile",
        default="all",
        choices=sorted(str(key) for key in PLAN.get("profiles", {}).keys()),
        help="Validation profile to run.",
    )
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.command == "preflight":
        return run_preflight()
    if args.command == "validate":
        return run_validate(str(args.profile))
    parser.print_help(sys.stderr)
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
PY
