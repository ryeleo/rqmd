"""Tests for RQMD-UNDO-009: Programmatic history API and automation."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from rqmd.cli import main as rqmd_main
from rqmd.history import HistoryManager


def _setup_history(tmp_path: Path) -> None:
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    req_file = req_dir / "demo.md"

    req_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    manager.capture(command="baseline", actor="test")

    req_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    manager.capture(command="update", actor="test", reason="promotion")


def test_RQMD_undo_009_history_json_payload(tmp_path: Path) -> None:
    _setup_history(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history",
            "--as-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-log"
    assert payload["entries_count"] == 2
    assert len(payload["entries"]) == 2
    assert payload["entries"][1]["is_current_head"] is True
    assert str(payload["entries"][0]["stable_id"]).startswith("hid:")


def test_RQMD_undo_009_history_text_output(tmp_path: Path) -> None:
    _setup_history(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history",
        ],
    )

    assert result.exit_code == 0, result.output
    assert "=== History ===" in result.output
    assert "[HEAD]" in result.output


def test_RQMD_undo_009_history_conflicts_with_timeline_mode(tmp_path: Path) -> None:
    _setup_history(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history",
            "--timeline",
        ],
    )

    assert result.exit_code != 0
    assert "Use exactly one non-interactive update mode" in result.output
