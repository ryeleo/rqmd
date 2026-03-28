"""Tests for RQMD-TIME-006: Replay and restore from historical points."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from rqmd.ai_cli import main as ai_main
from rqmd.history import HistoryManager
DOMAIN_V1 = """\
# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** 💡 Proposed
"""

DOMAIN_V2 = """\
# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** 🔧 Implemented
"""

DOMAIN_V3 = """\
# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** ✅ Verified

### RQMD-DEMO-002: Beta
- **Status:** 💡 Proposed
"""


def _setup_three_snapshots(tmp_path: Path) -> HistoryManager:
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    req_file = req_dir / "demo.md"

    req_file.write_text(DOMAIN_V1, encoding="utf-8")
    manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    manager.capture(command="baseline", actor="test")

    req_file.write_text(DOMAIN_V2, encoding="utf-8")
    manager.capture(command="update", actor="test", reason="V2")

    req_file.write_text(DOMAIN_V3, encoding="utf-8")
    manager.capture(command="update", actor="test", reason="V3")

    return manager


def test_RQMD_time_006_restore_preview_json(tmp_path: Path) -> None:
    _setup_three_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        [
            "--as-json",
            "--history-action",
            "restore:0",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-action-preview"
    assert payload["action"] == "restore"
    assert payload["preview"]["summary"]["transitions"] >= 1


def test_RQMD_time_006_replay_preview_json(tmp_path: Path) -> None:
    _setup_three_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        [
            "--as-json",
            "--history-action",
            "replay:0..2",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["action"] == "replay"
    assert len(payload["steps"]) == 2
    assert payload["preview"]["summary"]["added"] == 1


def test_RQMD_time_006_cherry_pick_preview_json(tmp_path: Path) -> None:
    _setup_three_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        [
            "--as-json",
            "--history-action",
            "cherry-pick:1,2",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["action"] == "cherry-pick"
    assert len(payload["picks"]) == 2
    assert payload["preview_totals"]["transitions"] >= 1


def test_RQMD_time_006_replay_requires_increasing_range(tmp_path: Path) -> None:
    _setup_three_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        [
            "--history-action",
            "replay:2..1",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )

    assert result.exit_code != 0
    assert "requires an increasing range" in result.output


def test_RQMD_time_006_history_action_read_only_guard(tmp_path: Path) -> None:
    _setup_three_snapshots(tmp_path)
    runner = CliRunner()
    result = runner.invoke(
        ai_main,
        [
            "--history-action",
            "restore:0",
            "--write",
            "--update",
            "RQMD-DEMO-001=implemented",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )

    assert result.exit_code != 0
    assert "--history-action is read-only" in result.output
