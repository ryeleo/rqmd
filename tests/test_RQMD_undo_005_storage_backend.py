from __future__ import annotations

import json
from pathlib import Path

from click.testing import CliRunner

from rqmd.cli import main
from rqmd.history import HistoryManager


def _write_demo_domain(path: Path, status: str = "💡 Proposed") -> None:
    path.write_text(
        f"""# Demo Requirements

Scope: demo.

### RQMD-DEMO-001: First
- **Status:** {status}
""",
        encoding="utf-8",
    )


def test_RQMD_undo_005_capture_initializes_git_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    _write_demo_domain(domain_dir / "demo.md")

    manager = HistoryManager(repo_root=repo, requirements_dir="docs/requirements")
    commit_hash = manager.capture("baseline", reason="initial snapshot")

    assert commit_hash
    assert (repo / ".rqmd" / "history" / "rqmd-history" / ".git").exists()
    state = json.loads((repo / ".rqmd" / "history" / "state.json").read_text(encoding="utf-8"))
    assert state["cursor"] == 0
    assert len(state["entries"]) == 1


def test_RQMD_undo_005_undo_and_redo_restore_catalog_contents(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    domain_file = domain_dir / "demo.md"
    _write_demo_domain(domain_file, "💡 Proposed")

    manager = HistoryManager(repo_root=repo, requirements_dir="docs/requirements")
    first_commit = manager.capture("baseline")

    _write_demo_domain(domain_file, "✅ Verified")
    second_commit = manager.capture("set-status")

    assert manager.get_current_head() == second_commit
    assert "✅ Verified" in domain_file.read_text(encoding="utf-8")

    reverted = manager.undo()
    assert reverted == first_commit
    assert "💡 Proposed" in domain_file.read_text(encoding="utf-8")

    restored = manager.redo()
    assert restored == second_commit
    assert "✅ Verified" in domain_file.read_text(encoding="utf-8")


def test_RQMD_undo_005_capture_after_undo_truncates_redo_chain(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    domain_file = domain_dir / "demo.md"
    _write_demo_domain(domain_file, "💡 Proposed")

    manager = HistoryManager(repo_root=repo, requirements_dir="docs/requirements")
    manager.capture("baseline")

    _write_demo_domain(domain_file, "🔧 Implemented")
    manager.capture("implemented")

    _write_demo_domain(domain_file, "✅ Verified")
    manager.capture("verified")

    manager.undo()
    assert manager.can_redo() is True

    _write_demo_domain(domain_file, "⛔ Blocked")
    manager.capture("blocked")

    assert manager.can_redo() is False
    assert len(manager.list_entries()) == 3


def test_RQMD_undo_005_history_persists_across_instances(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    domain_file = domain_dir / "demo.md"
    _write_demo_domain(domain_file)

    manager = HistoryManager(repo_root=repo, requirements_dir="docs/requirements")
    commit_hash = manager.capture("baseline")

    restarted = HistoryManager(repo_root=repo, requirements_dir="docs/requirements")
    assert restarted.get_current_head() == commit_hash
    assert len(restarted.list_entries()) == 1


def test_RQMD_undo_001_cli_update_creates_history_then_undo_redo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    domain_file = domain_dir / "demo.md"
    _write_demo_domain(domain_file)

    runner = CliRunner()

    update_result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update-id",
            "RQMD-DEMO-001",
            "--update-status",
            "verified",
            "--no-walk",
            "--no-table",
        ],
    )
    assert update_result.exit_code == 0
    assert "✅ Verified" in domain_file.read_text(encoding="utf-8")

    undo_result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--undo",
            "--no-walk",
            "--no-table",
        ],
    )
    assert undo_result.exit_code == 0
    assert "💡 Proposed" in domain_file.read_text(encoding="utf-8")

    redo_result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--redo",
            "--no-walk",
            "--no-table",
        ],
    )
    assert redo_result.exit_code == 0
    assert "✅ Verified" in domain_file.read_text(encoding="utf-8")


def test_RQMD_undo_001_cli_undo_json_noop_when_history_missing(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    _write_demo_domain(domain_dir / "demo.md")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--undo",
            "--as-json",
            "--no-walk",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["mode"] == "undo"
    assert payload["changed"] is False
    assert payload["commit"] is None


def test_RQMD_undo_008_history_gc_applies_retain_last_policy(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    domain_file = domain_dir / "demo.md"

    manager = HistoryManager(repo_root=repo, requirements_dir="docs/requirements")
    for status, command in [
        ("💡 Proposed", "baseline"),
        ("🔧 Implemented", "implemented"),
        ("✅ Verified", "verified"),
    ]:
        _write_demo_domain(domain_file, status)
        manager.capture(command)

    result = manager.garbage_collect(
        retention_policy={"retain_last": 2, "retain_days": None, "max_size_kib": None}
    )

    assert result["retention"]["applied"] is True
    assert result["retention"]["entries_count"] == 3
    assert result["retention"]["retained_entries_count"] == 2
    assert result["retention"]["dropped_entries_count"] == 1
    assert len(manager.list_entries()) == 2


def test_RQMD_undo_008_history_output_includes_retention_summary(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    _write_demo_domain(domain_dir / "demo.md")

    (repo / ".rqmd.json").write_text(
        json.dumps(
            {
                "history_retention": {
                    "retain_last": 5,
                    "retain_days": 30,
                    "max_size_kib": 2048,
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    manager = HistoryManager(repo_root=repo, requirements_dir="docs/requirements")
    manager.capture("baseline")

    runner = CliRunner()
    result = runner.invoke(
        main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--history",
            "--as-json",
        ],
    )

    assert result.exit_code == 0, result.output
    payload = json.loads(result.output)
    assert payload["mode"] == "history-log"
    assert payload["retention"]["policy"]["retain_last"] == 5
    assert payload["retention"]["policy"]["retain_days"] == 30
    assert payload["retention"]["policy"]["max_size_kib"] == 2048
