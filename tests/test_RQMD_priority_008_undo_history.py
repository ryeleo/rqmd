from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner
from rqmd.cli import main as rqmd_main
from rqmd.history import HistoryManager
from rqmd.status_update import apply_status_change_by_id


def _write_domain(path: Path, status: str = "💡 Proposed", priority: str | None = None) -> None:
    lines = [
        "# Demo Requirements",
        "",
        "### AC-001: Demo",
        f"- **Status:** {status}",
    ]
    if priority is not None:
        lines.append(f"- **Priority:** {priority}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def test_RQMD_priority_008_cli_priority_update_records_history_and_undoes(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    req_dir = repo / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    req_file = req_dir / "demo.md"
    _write_domain(req_file)

    runner = CliRunner()
    update = runner.invoke(
        rqmd_main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update-priority",
            "AC-001=high",
            "--no-table",
        ],
    )
    assert update.exit_code == 0, update.output

    manager = HistoryManager(repo_root=repo, requirements_dir="docs/requirements")
    entries = manager.list_entries()
    assert len(entries) == 2
    assert entries[0]["command"] == "baseline"
    assert entries[1]["command"] == "set-priority"

    text_after_update = req_file.read_text(encoding="utf-8")
    assert "- **Priority:** 🟠 P1 - High" in text_after_update

    undone = manager.undo()
    assert undone is not None
    text_after_undo = req_file.read_text(encoding="utf-8")
    assert "- **Priority:**" not in text_after_undo

    redone = manager.redo()
    assert redone is not None
    text_after_redo = req_file.read_text(encoding="utf-8")
    assert "- **Priority:** 🟠 P1 - High" in text_after_redo


def test_RQMD_priority_008_combined_status_priority_is_atomic_history_entry(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    req_dir = repo / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    req_file = req_dir / "demo.md"
    _write_domain(req_file, status="💡 Proposed", priority="🟢 P3 - Low")

    changed = apply_status_change_by_id(
        repo_root=repo,
        domain_files=[req_file],
        requirement_id="AC-001",
        new_status_input="verified",
        new_priority_input="critical",
        new_flagged_value=None,
        file_filter=None,
        emit_output=False,
        dry_run=False,
    )
    assert changed is True

    manager = HistoryManager(repo_root=repo, requirements_dir="docs/requirements")
    entries = manager.list_entries()
    assert len(entries) == 2
    assert entries[1]["command"] == "update-requirement"

    latest_text = req_file.read_text(encoding="utf-8")
    assert "- **Status:** ✅ Verified" in latest_text
    assert "- **Priority:** 🔴 P0 - Critical" in latest_text

    undone = manager.undo()
    assert undone is not None
    reverted_text = req_file.read_text(encoding="utf-8")
    assert "- **Status:** 💡 Proposed" in reverted_text
    assert "- **Priority:** 🟢 P3 - Low" in reverted_text
