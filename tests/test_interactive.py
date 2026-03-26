from __future__ import annotations

import re
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


def test_RQMD_sorting_010_footer_legend_uses_standardized_order(monkeypatch, capsys) -> None:
    keys = iter(["q"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))

    result = cli.select_from_menu(
        "Sort",
        ["A", "B"],
        footer_legend="keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[asc] | r=rfrsh | q=quit",
        extra_keys={"s": "cycle-sort", "d": "toggle-direction", "r": "refresh"},
    )
    output = capsys.readouterr().out

    assert result is None
    assert "keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[asc] | r=rfrsh | q=quit" in output


def test_RQMD_sorting_006_default_file_menu_uses_name_sort_desc(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n- [B](b.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# A Domain Acceptance Criteria\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )
    (criteria_dir / "b.md").write_text(
        "# B Domain Acceptance Criteria\n\nScope: b.\n\n### AC-B-001: B\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            captured["title"] = title
            captured["options"] = list(options)
            captured["legend"] = kwargs.get("footer_legend")
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert "options" in captured
    assert "B Domain" in captured["options"][0]
    assert "A Domain" in captured["options"][1]
    assert "filesystem" not in str(captured["title"])
    assert "\x1b[1mname ↓\x1b[0m" in str(captured["title"])
    title_plain = re.sub(r"\x1b\[[0-9;]*m", "", str(captured["title"]))
    assert re.search(r"P\s+\|\s+I\s+\|\s+Ver\s+\|\s+Blk/Dep", title_plain)
    assert captured["legend"] == "keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[dsc] | r=rfrsh | q=quit"


def test_RQMD_sorting_006b_emoji_columns_affect_select_file_header(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# A Domain Acceptance Criteria\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            captured["title"] = title
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--emoji-columns",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    title_plain = re.sub(r"\x1b\[[0-9;]*m", "", str(captured["title"]))
    assert re.search(r"💡\s+\|\s+🔧\s+\|\s+✅\s+\|\s+⛔/🗑️", title_plain)


def test_RQMD_sorting_007_and_011_file_menu_cycles_columns_and_shows_indicator(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [Z](a.md)\n- [A](z.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# Z Domain Acceptance Criteria\n\nScope: z.\n\n### AC-Z-001: Z\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )
    (criteria_dir / "z.md").write_text(
        "# A Domain Acceptance Criteria\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )

    state = {"call": 0}
    captured: dict[str, object] = {}

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            state["call"] += 1
            if state["call"] == 1:
                return "cycle-sort"
            captured["title"] = title
            captured["options"] = list(options)
            captured["legend"] = kwargs.get("footer_legend")
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert "title" in captured
    assert "\x1b[1mP ↓\x1b[0m" in str(captured["title"])
    assert "Z Domain" in captured["options"][0]
    assert "A Domain" in captured["options"][1]
    assert captured["legend"] == "keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[dsc] | r=rfrsh | q=quit"


def test_RQMD_sorting_011_header_columns_stay_fixed_when_indicator_moves(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n- [B](b.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# A Domain Acceptance Criteria\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )
    (criteria_dir / "b.md").write_text(
        "# B Domain Acceptance Criteria\n\nScope: b.\n\n### AC-B-001: B\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )

    state = {"call": 0}
    titles: list[str] = []

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            titles.append(title)
            state["call"] += 1
            if state["call"] == 1:
                return "cycle-sort"
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert len(titles) >= 2

    def sort_line(menu_title: str) -> str:
        line = menu_title.splitlines()[1]
        return re.sub(r"\x1b\[[0-9;]*m", "", line)

    first = sort_line(titles[0])
    second = sort_line(titles[1])
    assert [i for i, ch in enumerate(first) if ch == "|"] == [i for i, ch in enumerate(second) if ch == "|"]


def test_RQMD_sorting_008_direction_token_updates_in_legend(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# A Domain Acceptance Criteria\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )

    state = {"call": 0}
    legends: list[str] = []

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            legends.append(kwargs.get("footer_legend"))
            state["call"] += 1
            if state["call"] == 1:
                return "toggle-direction"
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert legends[0] == "keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[dsc] | r=rfrsh | q=quit"
    assert legends[1] == "keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[asc] | r=rfrsh | q=quit"


def test_RQMD_sorting_009_refresh_reopens_file_menu(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# A Domain Acceptance Criteria\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )

    state = {"call": 0}

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            state["call"] += 1
            if state["call"] == 1:
                return "refresh"
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert state["call"] == 2


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

    def fake_loop(repo_root, criteria_dir, domain_files, emoji_columns, sort_files, sort_strategy, id_prefixes):
        called["value"] = True
        assert sort_strategy == "standard"
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


def test_RQMD_sorting_005_alpha_asc_strategy_changes_default_direction(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n- [B](b.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# A Domain Acceptance Criteria\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )
    (criteria_dir / "b.md").write_text(
        "# B Domain Acceptance Criteria\n\nScope: b.\n\n### AC-B-001: B\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            captured["title"] = title
            captured["options"] = list(options)
            captured["legend"] = kwargs.get("footer_legend")
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--sort-strategy",
            "alpha-asc",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert "\x1b[1mname ↑\x1b[0m" in str(captured["title"])
    assert "A Domain" in captured["options"][0]
    assert "B Domain" in captured["options"][1]
    assert captured["legend"] == "keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[asc] | r=rfrsh | q=quit"


def test_RQMD_sorting_005_status_focus_strategy_uses_implemented_default(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [Low](a.md)\n- [High](b.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# Low Acceptance Criteria\n\nScope: low.\n\n### AC-L-001: L1\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )
    (criteria_dir / "b.md").write_text(
        "# High Acceptance Criteria\n\nScope: high.\n\n### AC-H-001: H1\n- **Status:** 🔧 Implemented\n\n### AC-H-002: H2\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            captured["title"] = title
            captured["options"] = list(options)
            captured["legend"] = kwargs.get("footer_legend")
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo),
            "--criteria-dir",
            "docs/requirements",
            "--sort-strategy",
            "status-focus",
            "--no-summary-table",
        ],
    )

    assert result.exit_code == 0
    assert "\x1b[1mI ↓\x1b[0m" in str(captured["title"])
    assert "High" in captured["options"][0]
    assert "Low" in captured["options"][1]
    assert captured["legend"] == "keys: 1-9 select | n=next | p=prev | u=up | s=sort | d=[dsc] | r=rfrsh | q=quit"


def test_RQMD_sorting_unsorted_flag_warns_as_deprecated_alias(monkeypatch, repo_with_domain_docs: Path) -> None:
    monkeypatch.setattr(cli, "select_from_menu", lambda *args, **kwargs: None)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--repo-root",
            str(repo_with_domain_docs),
            "--criteria-dir",
            "docs/requirements",
            "--no-summary-table",
            "--unsorted",
        ],
    )

    assert result.exit_code == 0
    assert "deprecated" in result.output.lower()
    assert "compatibility alias" in result.output.lower()


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

    # File menu under default descending name sort: n (page2), p (page1), n (page2), 2 (pick file 01)
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
        selected = criteria_dir / "domain-01.md"
        updated = selected.read_text(encoding="utf-8")
        assert "### AC-F01-001: First criterion" in updated
        assert "### AC-F01-002: Second criterion" in updated
        assert "### AC-F01-001: First criterion\n- **Status:** ✅ Verified" in updated
        assert "### AC-F01-002: Second criterion\n- **Status:** 🔧 Implemented" in updated
    finally:
        # Cleanup scratch data so this test leaves the working tree unchanged.
        if scratch_root.exists():
            shutil.rmtree(scratch_root)


# ---------------------------------------------------------------------------
# RQMD-INTERACTIVE-011: Preflight write-permission gate
# ---------------------------------------------------------------------------


def test_RQMD_interactive_011_unwritable_file_blocks_interactive_mode(tmp_path: Path) -> None:
    import os
    import stat

    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain_file = criteria_dir / "locked.md"
    domain_file.write_text(
        "# Locked\n\n### AC-LOCK-001: Can't touch this\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )
    domain_file.chmod(0o444)  # read-only

    try:
        runner = CliRunner()
        result = runner.invoke(
            cli.main,
            [
                "--repo-root", str(repo),
                "--criteria-dir", "docs/requirements",
                "--no-summary-table",
                "--interactive",
            ],
        )
        assert result.exit_code != 0
        combined = (result.output or "") + (str(result.exception) if result.exception else "")
        assert "writable" in combined.lower() or "write" in combined.lower() or "permission" in combined.lower()
        assert "locked.md" in combined
    finally:
        domain_file.chmod(stat.S_IRUSR | stat.S_IWUSR)