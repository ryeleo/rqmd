"""Tests for RQMD-TIME-010: Verification coverage for temporal navigation."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from rqmd.ai_cli import main as ai_main
from rqmd.history import HistoryManager


def _setup_temporal_matrix(tmp_path: Path) -> HistoryManager:
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    file_a = req_dir / "a.md"
    file_b = req_dir / "b.md"

    file_a.write_text(
        """# A Requirements

### RQMD-MATRIX-001: Alpha
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    file_b.write_text(
        """# B Requirements

### RQMD-MATRIX-002: Beta
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    manager.capture(command="baseline", actor="matrix")

    file_a.write_text(
        """# A Requirements

### RQMD-MATRIX-001: Alpha
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    file_b.write_text(
        """# B Requirements

### RQMD-MATRIX-002: Beta
- **Status:** 💡 Proposed

### RQMD-MATRIX-003: Gamma
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    manager.capture(command="update", actor="matrix", reason="phase-1")

    file_a.write_text(
        """# A Requirements

### RQMD-MATRIX-001: Alpha
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )
    manager.capture(command="verify", actor="matrix", reason="phase-2")

    # Create divergence for branch-graph validation.
    manager.undo()
    file_a.write_text(
        """# A Requirements

### RQMD-MATRIX-001: Alpha
- **Status:** ⛔ Blocked
**Blocked:** waiting on dependency
""",
        encoding="utf-8",
    )
    manager.capture(command="alt-path", actor="matrix", reason="branch-path")

    return manager


def test_RQMD_time_010_branch_graph_reconstruction(tmp_path: Path) -> None:
    manager = _setup_temporal_matrix(tmp_path)

    timeline = manager.get_timeline_graph()
    branches = manager.get_branches()

    assert timeline["entries_count"] >= 3
    assert "main" in branches
    assert any(name.startswith("recovery-") for name in branches.keys())

    nodes = timeline["nodes"]
    assert nodes
    # At least one node has parent linkage.
    assert any(node.get("parent_commit") for node in nodes.values())


def test_RQMD_time_010_detached_history_reads_and_stable_refs(tmp_path: Path) -> None:
    _setup_temporal_matrix(tmp_path)
    runner = CliRunner()

    first = runner.invoke(
        ai_main,
        [
            "--as-json",
            "--dump-status",
            "proposed",
            "--history-ref",
            "0",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )
    assert first.exit_code == 0, first.output
    payload = json.loads(first.output)
    stable_id = payload["history_source"]["stable_id"]
    assert str(stable_id).startswith("hid:")

    second = runner.invoke(
        ai_main,
        [
            "--as-json",
            "--dump-status",
            "proposed",
            "--history-ref",
            str(stable_id),
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )
    assert second.exit_code == 0, second.output
    second_payload = json.loads(second.output)
    assert second_payload["history_source"]["entry_index"] == 0


def test_RQMD_time_010_point_to_point_diff_multi_file(tmp_path: Path) -> None:
    _setup_temporal_matrix(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        ai_main,
        [
            "--as-json",
            "--compare-refs",
            "0..2",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["summary"]["transitions"] >= 1
    assert payload["summary"]["added"] >= 1


def test_RQMD_time_010_replay_preview_and_steps(tmp_path: Path) -> None:
    _setup_temporal_matrix(tmp_path)
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


def test_RQMD_time_010_history_report_compare_source_metadata(tmp_path: Path) -> None:
    _setup_temporal_matrix(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        ai_main,
        [
            "--as-json",
            "--history-report",
            "--compare-refs",
            "0..2",
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-report"
    assert payload["report_type"] == "compare"
    assert str(payload["source"]["ref_a"]["stable_id"]).startswith("hid:")
    assert str(payload["source"]["ref_b"]["stable_id"]).startswith("hid:")
