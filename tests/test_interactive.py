from __future__ import annotations

import shutil
from pathlib import Path

from click.testing import CliRunner
from rqmd import cli, menus


def test_RQMD_interactive_002_single_key_selection(monkeypatch) -> None:
    keys = iter(["1"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu("Pick", ["A", "B"])
    assert result == 0


def test_RQMD_interactive_003_paging_controls(monkeypatch) -> None:
    keys = iter(["n", "1"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    options = [f"opt{i}" for i in range(12)]
    result = cli.select_from_menu("Pick", options)
    assert result == 9


def test_RQMD_interactive_003b_up_navigation_key(monkeypatch) -> None:
    keys = iter(["u"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu("Pick", ["A", "B"])
    assert result == "up"


def test_RQMD_interactive_003c_menu_legend_uses_up_not_back(monkeypatch, capsys) -> None:
    keys = iter(["q"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu("Pick", ["A", "B"])
    output = capsys.readouterr().out

    assert result is None
    assert "u=up" in output
    assert "back" not in output.lower()


def test_RQMD_interactive_004_nav_shortcuts(monkeypatch) -> None:
    keys = iter(["n"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu(
        "Status",
        ["A", "B"],
        allow_paging_nav=False,
        extra_keys={"n": "nav-next", "p": "nav-prev"},
    )
    assert result == "nav-next"


def test_RQMD_interactive_005_sort_toggle_key(monkeypatch) -> None:
    keys = iter(["s"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu("Sort", ["A"], extra_key="s", extra_key_return="toggle-sort")
    assert result == "toggle-sort"


def test_RQMD_interactive_008_reason_prompt_helpers(monkeypatch) -> None:
    monkeypatch.setattr(cli.click, "prompt", lambda *args, **kwargs: "Some reason")
    assert cli.prompt_for_blocked_reason() == "Some reason"
    assert cli.prompt_for_deprecated_reason() == "Some reason"


def test_RQMD_interactive_009_positional_lookup_mode(monkeypatch, repo_with_domain_docs: Path) -> None:
    called = {"value": False}

    def fake_lookup(repo_root, domain_files, criterion_id, emoji_columns, id_prefixes):
        called["value"] = True
        assert criterion_id == "AC-HELLO-001"
        assert id_prefixes == ("AC", "R", "RQMD")
        return 0

    monkeypatch.setattr(cli, "lookup_criterion_interactive", fake_lookup)
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "AC-HELLO-001",
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert called["value"] is True


def test_RQMD_interactive_009a_lookup_mode_up_exits(monkeypatch, repo_with_domain_docs: Path) -> None:
    domain_file = repo_with_domain_docs / "docs" / "requirements" / "demo.md"
    monkeypatch.setattr(cli, "select_from_menu", lambda *args, **kwargs: "up")

    result = cli.lookup_criterion_interactive(
        repo_root=repo_with_domain_docs,
        domain_files=[domain_file],
        criterion_id="AC-HELLO-001",
        emoji_columns=False,
        id_prefixes=("AC",),
    )

    assert result == 0


def test_RQMD_interactive_009b_filtered_walk_up_exits(monkeypatch, repo_with_domain_docs: Path) -> None:
    domain_file = repo_with_domain_docs / "docs" / "requirements" / "demo.md"
    monkeypatch.setattr(cli, "select_from_menu", lambda *args, **kwargs: "up")

    result = cli.filtered_interactive_loop(
        repo_root=repo_with_domain_docs,
        domain_files=[domain_file],
        target_status="🔧 Implemented",
        emoji_columns=False,
        id_prefixes=("AC",),
    )

    assert result == 0


def test_RQMD_interactive_001_default_invokes_interactive_loop(monkeypatch, repo_with_domain_docs: Path) -> None:
    called = {"value": False}

    def fake_loop(repo_root, criteria_dir, domain_files, emoji_columns, sort_files, id_prefixes):
        called["value"] = True
        assert id_prefixes == ("AC", "R", "RQMD")
        return 0

    monkeypatch.setattr(cli, "interactive_update_loop", fake_loop)
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert called["value"] is True


def test_RQMD_interactive_001b_default_auto_detect_reaches_interactive(monkeypatch, repo_with_domain_docs: Path) -> None:
    domain_dir = repo_with_domain_docs / "docs" / "requirements"
    (domain_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [Demo](demo.md)\n",
        encoding="utf-8",
    )

    # Simulate immediate quit from the first interactive menu without touching TTY.
    monkeypatch.setattr(cli, "select_from_menu", lambda *args, **kwargs: None)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert "Auto-selected requirement docs: docs/requirements/README.md" in result.output


def test_RQMD_interactive_010_deep_paging_and_status_updates_with_scratch(monkeypatch) -> None:
    repo_root = Path(__file__).resolve().parents[1]
    scratch_root = repo_root / ".scratch" / "test-interactive-deep"
    criteria_dir = scratch_root / "requirements"
    criteria_rel = criteria_dir.relative_to(repo_root).as_posix()

    if scratch_root.exists():
        shutil.rmtree(scratch_root)
    criteria_dir.mkdir(parents=True, exist_ok=True)

    # Build 11 files so file menu has 2 pages with default page-size 9.
    for idx in range(1, 12):
        text = (
            f"# Domain {idx:02d} Requirements\n\n"
            "Scope: interactive deep test.\n\n"
            f"### AC-F{idx:02d}-001: First criterion\n"
            "- **Status:** 💡 Proposed\n\n"
            f"### AC-F{idx:02d}-002: Second criterion\n"
            "- **Status:** 💡 Proposed\n"
        )
        (criteria_dir / f"domain-{idx:02d}.md").write_text(text, encoding="utf-8")

    # File menu: n (page2), p (page1), n (page2), 2 (pick file 11)
    # Criterion menu: 1 (pick first criterion)
    # Status menus: 2 (Implemented), 3 (Verified)
    # Then unwind: u (from wrapped status menu), u (from criterion menu), q (quit file menu)
    keys = iter(["n", "p", "n", "2", "1", "2", "3", "u", "u", "q"])
    monkeypatch.setattr(menus.click, "getchar", lambda: next(keys))

    runner = CliRunner()
    try:
        result = runner.invoke(
            cli.main,
            [
                "--repo-root",
                str(repo_root),
                "--criteria-dir",
                criteria_rel,
                "--no-summary-table",
            ],
        )

        assert result.exit_code == 0
        # Assert paging reached both pages in file selection flow.
        assert "Page 1/2" in result.output
        assert "Page 2/2" in result.output

        # Assert status updates were persisted in the selected file.
        selected = criteria_dir / "domain-11.md"
        updated = selected.read_text(encoding="utf-8")
        assert "### AC-F11-001: First criterion" in updated
        assert "### AC-F11-002: Second criterion" in updated
        assert "### AC-F11-001: First criterion\n- **Status:** 🔧 Implemented" in updated
        assert "### AC-F11-002: Second criterion\n- **Status:** ✅ Verified" in updated
    finally:
        # Cleanup scratch data so this test leaves the working tree unchanged.
        if scratch_root.exists():
            shutil.rmtree(scratch_root)