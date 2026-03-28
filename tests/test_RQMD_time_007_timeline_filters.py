"""Tests for RQMD-TIME-007: Timeline filters and queryable navigation."""

from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner
from rqmd.cli import main as rqmd_main
from rqmd.history import HistoryManager


def _setup_timeline_history(tmp_path: Path) -> HistoryManager:
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
    manager.capture(command="baseline", actor="alpha")

    req_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    manager.capture(command="set-status", actor="beta", reason="Promote alpha")

    req_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )
    manager.capture(command="verify", actor="gamma", reason="Verification pass")

    return manager


def _setup_timeline_with_branch(tmp_path: Path) -> HistoryManager:
    manager = _setup_timeline_history(tmp_path)
    req_file = tmp_path / "docs" / "requirements" / "demo.md"

    manager.undo()
    req_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** ⛔ Blocked
**Blocked:** waiting for review
""",
        encoding="utf-8",
    )
    manager.capture(command="block-alt", actor="delta", reason="Branch alternate")
    return manager


def test_RQMD_time_007_timeline_filter_requires_timeline_flag(tmp_path: Path) -> None:
    _setup_timeline_history(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--timeline-actor",
            "beta",
        ],
    )

    assert result.exit_code != 0
    assert "--timeline-* filters require --timeline" in result.output


def test_RQMD_time_007_timeline_filter_by_actor(tmp_path: Path) -> None:
    _setup_timeline_history(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--timeline",
            "--timeline-actor",
            "beta",
            "--as-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    nodes = payload["timeline"]["nodes"]
    assert nodes
    assert all(str(node.get("actor")) == "beta" for node in nodes.values())


def test_RQMD_time_007_timeline_filter_by_transition_and_requirement_id(tmp_path: Path) -> None:
    _setup_timeline_history(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--timeline",
            "--timeline-transition",
            "Proposed->Implemented",
            "--timeline-requirement-id",
            "RQMD-DEMO-001",
            "--as-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    nodes = payload["timeline"]["nodes"]
    assert len(nodes) == 1
    node = next(iter(nodes.values()))
    assert node["command"] == "set-status"
    assert "RQMD-DEMO-001" in node["changed_requirement_ids"]


def test_RQMD_time_007_timeline_filter_by_date_range(tmp_path: Path) -> None:
    _setup_timeline_history(tmp_path)
    runner = CliRunner()

    all_result = runner.invoke(
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
    assert all_result.exit_code == 0, all_result.output
    all_payload = json.loads(all_result.output)

    ordered_nodes = sorted(
        all_payload["timeline"]["nodes"].values(),
        key=lambda node: int(node.get("entry_index", -1)),
    )
    assert len(ordered_nodes) >= 2
    from_ts = str(ordered_nodes[1]["timestamp"])

    filtered_result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--timeline",
            "--timeline-from",
            from_ts,
            "--as-json",
        ],
    )
    assert filtered_result.exit_code == 0, filtered_result.output
    filtered_payload = json.loads(filtered_result.output)
    filtered_nodes = filtered_payload["timeline"]["nodes"]
    assert filtered_nodes
    filtered_indexes = sorted(int(node["entry_index"]) for node in filtered_nodes.values())
    assert min(filtered_indexes) >= 1


def test_RQMD_time_007_timeline_filter_by_branch(tmp_path: Path) -> None:
    _setup_timeline_with_branch(tmp_path)
    runner = CliRunner()

    result = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(tmp_path),
            "--docs-dir",
            "docs/requirements",
            "--timeline",
            "--timeline-branch",
            "recovery-",
            "--as-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    nodes = payload["timeline"]["nodes"]
    assert nodes
    assert all(str(node.get("branch", "")).startswith("recovery-") for node in nodes.values())
