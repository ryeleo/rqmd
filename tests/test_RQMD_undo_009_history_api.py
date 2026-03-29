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
    assert "+" in result.output
    assert "promotion" in result.output


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


def test_RQMD_undo_007_history_prune_now_requires_history_gc(tmp_path: Path) -> None:
    _setup_history(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history-prune-now",
        ],
    )

    assert result.exit_code != 0
    assert "--history-prune-now requires --history-gc." in result.output


def test_RQMD_undo_007_history_label_branch_requires_label_value(tmp_path: Path) -> None:
    _setup_history(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history-label-branch",
            "main",
        ],
    )

    assert result.exit_code != 0
    assert "--history-label-branch requires --history-branch-label." in result.output


def test_RQMD_undo_007_history_branch_label_requires_branch_mode(tmp_path: Path) -> None:
    _setup_history(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history-branch-label",
            "named-snapshot",
        ],
    )

    assert result.exit_code != 0
    assert "--history-branch-label requires --history-label-branch." in result.output


def test_RQMD_undo_007_history_label_branch_cli(tmp_path: Path) -> None:
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
    manager.capture(command="implemented", actor="test")

    manager.undo()
    req_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )
    manager.capture(command="verified", actor="test")

    recovery_branch = next(name for name in manager.get_branches() if name.startswith("recovery-"))

    runner = CliRunner()
    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history-label-branch",
            recovery_branch,
            "--history-branch-label",
            "saved-snapshot",
            "--as-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-label-branch"
    assert payload["branch"] == recovery_branch
    assert payload["label"] == "saved-snapshot"
    assert payload["updated"] is True
    assert payload["branches"][recovery_branch]["label"] == "saved-snapshot"


def test_RQMD_undo_007_history_checkout_branch_cli(tmp_path: Path) -> None:
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
    manager.capture(command="implemented", actor="test")

    manager.undo()
    req_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )
    manager.capture(command="verified", actor="test")

    branches = manager.get_branches()
    recovery_branch = next(name for name in branches if name.startswith("recovery-"))

    runner = CliRunner()
    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history-checkout-branch",
            recovery_branch,
            "--as-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-checkout-branch"
    assert payload["branch"] == recovery_branch
    assert payload["changed"] is True
    assert payload["branches"][recovery_branch]["is_current"] is True


def test_RQMD_undo_007_history_cherry_pick_cli(tmp_path: Path) -> None:
    _setup_history(tmp_path)
    manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    entries = manager.list_entries()
    source_commit = str(entries[0]["commit"])

    runner = CliRunner()
    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history-cherry-pick",
            source_commit,
            "--as-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-cherry-pick"
    assert payload["source_commit"] == source_commit
    assert payload["changed"] is True
    assert payload["commit"] is not None


def test_RQMD_undo_007_history_replay_branch_cli(tmp_path: Path) -> None:
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
    manager.capture(command="implemented", actor="test")

    manager.undo()
    req_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )
    manager.capture(command="verified", actor="test")

    branches = manager.get_branches()
    recovery_branch = next(name for name in branches if name.startswith("recovery-"))

    runner = CliRunner()
    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history-replay-branch",
            recovery_branch,
            "--history-target-branch",
            "main",
            "--as-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-replay-branch"
    assert payload["source_branch"] == recovery_branch
    assert payload["target_branch"] == "main"
    assert payload["changed"] is True
    assert payload["replayed_count"] >= 1


def test_RQMD_undo_007_history_target_branch_requires_replay_or_cherry_pick(tmp_path: Path) -> None:
    _setup_history(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history-target-branch",
            "main",
        ],
    )

    assert result.exit_code != 0
    assert "--history-target-branch requires --history-cherry-pick or --history-replay-branch." in result.output
