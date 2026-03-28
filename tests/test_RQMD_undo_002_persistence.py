"""Tests for RQMD-UNDO-002: Persistent history across restarts and crashes."""

from __future__ import annotations

from pathlib import Path

from rqmd.history import HistoryManager


def _create_history(tmp_path: Path) -> None:
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
    manager.capture(command="baseline", actor="persist")

    req_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    manager.capture(command="update", actor="persist", reason="upgrade")


def test_RQMD_undo_002_history_survives_restart(tmp_path: Path) -> None:
    _create_history(tmp_path)

    manager_after_restart = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    entries = manager_after_restart.list_entries()

    assert len(entries) == 2
    assert entries[0]["command"] == "baseline"
    assert entries[1]["command"] == "update"


def test_RQMD_undo_002_undo_redo_work_after_restart(tmp_path: Path) -> None:
    _create_history(tmp_path)

    manager_after_restart = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    assert manager_after_restart.can_undo() is True
    assert manager_after_restart.can_redo() is False

    undone = manager_after_restart.undo()
    assert undone is not None
    assert manager_after_restart.can_redo() is True

    redone = manager_after_restart.redo()
    assert redone is not None


def test_RQMD_undo_002_state_file_persists_cursor_and_entries(tmp_path: Path) -> None:
    _create_history(tmp_path)

    manager_after_restart = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    timeline = manager_after_restart.get_timeline_graph()

    assert timeline["entries_count"] == 2
    assert timeline["cursor"] == 1
    assert timeline["current_branch"] == "main"


def test_RQMD_undo_002_materialize_after_restart_restores_snapshot(tmp_path: Path) -> None:
    _create_history(tmp_path)

    manager_after_restart = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    first = manager_after_restart.resolve_ref("0")
    assert first is not None

    tempdir = manager_after_restart.materialize_snapshot_tempdir(str(first["commit"]))
    try:
        demo_file = Path(tempdir.name) / "docs" / "requirements" / "demo.md"
        text = demo_file.read_text(encoding="utf-8")
        assert "💡 Proposed" in text
        assert "🔧 Implemented" not in text
    finally:
        tempdir.cleanup()
