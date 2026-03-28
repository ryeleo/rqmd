"""Tests for RQMD-UNDO-004: Confirmation required for destructive history actions."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from rqmd.cli import main as rqmd_main
from rqmd.history import HistoryManager


def _setup_divergent_history(tmp_path: Path) -> tuple[HistoryManager, str]:
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

    # Create divergence so a recovery branch exists.
    manager.undo()
    req_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )
    manager.capture(command="verified-divergent", actor="test")

    branches = manager.get_branches()
    recovery_branch = next(name for name in branches if name.startswith("recovery-"))
    return manager, recovery_branch


def test_RQMD_undo_004_history_discard_branch_requires_force_yes_non_interactive(tmp_path: Path) -> None:
    manager, recovery_branch = _setup_divergent_history(tmp_path)
    assert recovery_branch in manager.get_branches()

    runner = CliRunner()
    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history-discard-branch",
            recovery_branch,
            "--as-json",
        ],
    )

    assert result.exit_code != 0
    assert "requires confirmation" in result.output

    refreshed = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    assert recovery_branch in refreshed.get_branches()


def test_RQMD_undo_004_history_discard_branch_succeeds_with_force_yes(tmp_path: Path) -> None:
    manager, recovery_branch = _setup_divergent_history(tmp_path)
    assert recovery_branch in manager.get_branches()

    runner = CliRunner()
    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--history-discard-branch",
            recovery_branch,
            "--force-yes",
            "--as-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-discard-branch"
    assert payload["discarded"] is True
    assert payload["cancelled"] is False
    assert recovery_branch not in payload["branches"]
