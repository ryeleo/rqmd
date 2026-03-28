"""Tests for RQMD-UNDO-010: Undo/history verification matrix."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from rqmd.ai_cli import main as ai_main
from rqmd.cli import main as rqmd_main
from rqmd.history import HistoryManager


def _setup_matrix_history(tmp_path: Path) -> None:
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    file_a = req_dir / "a.md"
    file_b = req_dir / "b.md"

    file_a.write_text(
        """# A

### RQMD-MAT-001: A1
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    file_b.write_text(
        """# B

### RQMD-MAT-002: B1
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    manager.capture(command="baseline", actor="matrix")

    file_a.write_text(
        """# A

### RQMD-MAT-001: A1
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    manager.capture(command="impl", actor="matrix")

    file_b.write_text(
        """# B

### RQMD-MAT-002: B1
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )
    manager.capture(command="verify", actor="matrix")

    manager.undo()
    file_b.write_text(
        """# B

### RQMD-MAT-002: B1
- **Status:** ⛔ Blocked
**Blocked:** waiting
""",
        encoding="utf-8",
    )
    manager.capture(command="alt", actor="matrix")


def test_RQMD_undo_010_history_log_and_timeline_matrix(tmp_path: Path) -> None:
    _setup_matrix_history(tmp_path)
    runner = CliRunner()

    history_result = runner.invoke(
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
    assert history_result.exit_code == 0, history_result.output
    history_payload = json.loads(history_result.output)
    assert history_payload["entries_count"] >= 3

    timeline_result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--timeline",
            "--as-json",
        ],
    )
    assert timeline_result.exit_code == 0, timeline_result.output
    timeline_payload = json.loads(timeline_result.output)
    assert timeline_payload["timeline"]["entries_count"] >= 3
    assert any(name.startswith("recovery-") for name in timeline_payload["branches"].keys())


def test_RQMD_undo_010_replay_preview_matrix(tmp_path: Path) -> None:
    _setup_matrix_history(tmp_path)
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
    assert payload["preview"]["summary"]["transitions"] >= 1


def test_RQMD_undo_010_restart_then_undo_matrix(tmp_path: Path) -> None:
    _setup_matrix_history(tmp_path)

    manager_after_restart = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    assert manager_after_restart.can_undo() is True
    undone = manager_after_restart.undo()
    assert undone is not None
    assert manager_after_restart.can_redo() is True
