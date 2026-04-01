from __future__ import annotations

import json
import re
import shutil
from pathlib import Path
from types import SimpleNamespace

import click
import pytest
from click.testing import CliRunner

from rqmd import cli, menus
from rqmd.priority_model import configure_priority_catalog


def test_RQMD_interactive_002_single_key_selection(monkeypatch) -> None:
    keys = iter(["1"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu("Pick", ["A", "B"])
    assert result == 0


def test_RQMD_interactive_003_paging_controls(monkeypatch) -> None:
    keys = iter(["j", "1"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    options = [f"opt{i}" for i in range(12)]
    result = cli.select_from_menu("Pick", options)
    assert result == 9


def test_RQMD_interactive_003a_down_arrow_paging_controls(monkeypatch) -> None:
    keys = iter(["\x1b[B", "1"])
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
    assert ":=help" in output
    assert "u=up" in output
    assert "back" not in output.lower()


def test_RQMD_interactive_003d_colon_opens_help_overlay(monkeypatch, capsys) -> None:
    keys = iter([":", "q"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))

    result = cli.select_from_menu("Pick", ["A", "B"])
    output = capsys.readouterr().out

    assert result is None
    assert "Help" in output
    assert "gg=first" in output
    assert "Press : or any invalid key to close help." in output


def test_RQMD_interactive_003e_invalid_key_toggles_help(monkeypatch, capsys) -> None:
    keys = iter(["!", "@", "q"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))

    result = cli.select_from_menu("Pick", ["A", "B"])
    output = capsys.readouterr().out

    assert result is None
    assert output.count("Help") == 1
    assert "Press : or any invalid key to close help." in output


def test_RQMD_interactive_004_nav_shortcuts(monkeypatch) -> None:
    keys = iter(["j"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu(
        "Status",
        ["A", "B"],
        allow_paging_nav=False,
        extra_keys={"j": "nav-next", "k": "nav-prev"},
    )
    assert result == "nav-next"


def test_RQMD_interactive_004b_arrow_nav_shortcuts(monkeypatch) -> None:
    keys = iter(["\x1b[B"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu(
        "Status",
        ["A", "B"],
        allow_paging_nav=False,
        extra_keys={"j": "nav-next", "k": "nav-prev"},
    )
    assert result == "nav-next"


def test_RQMD_interactive_004a_next_prev_stack_semantics(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: One
- **Status:** 💡 Proposed

### AC-DEMO-002: Two
- **Status:** 🔧 Implemented

### AC-DEMO-003: Three
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )

    status_visits: list[str] = []
    status_actions = iter(["nav-next", "nav-next", "nav-prev", "nav-prev", "nav-next", "up"])
    state = {"file_menu_calls": 0, "requirement_menu_calls": 0}

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            state["file_menu_calls"] += 1
            if state["file_menu_calls"] == 1:
                return 0
            return None

        if title.startswith("Select requirement in"):
            state["requirement_menu_calls"] += 1
            if state["requirement_menu_calls"] == 1:
                return 0
            return "up"

        if title.startswith("Choose Status or Priority for "):
            status_visits.append(title.removeprefix("Choose Status or Priority for ").splitlines()[0].removesuffix("."))
            return next(status_actions)

        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert status_visits == [
        "AC-DEMO-003",
        "AC-DEMO-002",
        "AC-DEMO-001",
        "AC-DEMO-002",
        "AC-DEMO-003",
        "AC-DEMO-002",
    ]


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
        footer_legend="keys: 1-9 select | ↓/j=next | ↑/k=prev | gg=first | G=last | ^U/^D=half | /=fwd | ?=rev | n/N=next | u=up | s=sort | S=sort-back | d=[asc] | r=rfrsh | q=quit",
        extra_keys={"s": "cycle-sort", "d": "toggle-direction", "r": "refresh"},
    )
    output = capsys.readouterr().out

    assert result is None
    assert "keys: 1-9 select | ↓/j=next | ↑/k=prev | gg=first | G=last | ^U/^D=half | /=fwd | ?=rev | n/N=next | u=up | s=sort | S=sort-back | d=[asc] | r=rfrsh | q=quit" in output


def test_RQMD_sorting_006_default_file_menu_uses_name_sort_desc(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n- [B](b.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# A Domain Requirement\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )
    (criteria_dir / "b.md").write_text(
        "# B Domain Requirement\n\nScope: b.\n\n### AC-B-001: B\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            captured["title"] = title
            captured["options"] = list(options)
            captured["legend"] = kwargs.get("footer_legend")
            captured["compact_footer"] = kwargs.get("compact_footer")
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "options" in captured
    assert "B Domain" in captured["options"][0]
    assert "A Domain" in captured["options"][1]
    assert "filesystem" not in str(captured["title"])
    assert "\x1b[1mname ↓\x1b[0m" in str(captured["title"])
    title_plain = re.sub(r"\x1b\[[0-9;]*m", "", str(captured["title"]))
    assert re.search(r"priority\s+\|\s+P\s+\|\s+I\s+\|\s+Ver\s+\|\s+Blk/Dep", title_plain)
    assert captured["legend"] == "keys: 1-9 select | ↓/j=next | ↑/k=prev | gg=first | G=last | ^U/^D=half | /=fwd | ?=rev | n/N=next | u=up | s=sort | S=sort-back | d=[dsc] | r=rfrsh | q=quit"
    assert captured["compact_footer"] == "keys: 1-9 select | ↓/j=next | ↑/k=prev | :=help | u=up | q=quit"


def test_RQMD_sorting_006b_emoji_columns_affect_select_file_header(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# A Domain Requirement\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 💡 Proposed\n",
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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--emoji-headers",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    title_plain = re.sub(r"\x1b\[[0-9;]*m", "", str(captured["title"]))
    assert re.search(r"priority\s+\|\s+💡\s+\|\s+🔧\s+\|\s+✅\s+\|\s+⛔/🗑️", title_plain)


def test_RQMD_sorting_007_and_011_file_menu_cycles_columns_and_shows_indicator(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [Z](a.md)\n- [A](z.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# Z Domain Requirement\n\nScope: z.\n\n### AC-Z-001: Z\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )
    (criteria_dir / "z.md").write_text(
        "# A Domain Requirement\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 🔧 Implemented\n",
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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "title" in captured
    assert "\x1b[1mpriority ↓\x1b[0m" in str(captured["title"])
    assert "Z Domain" in captured["options"][0]
    assert "A Domain" in captured["options"][1]
    assert captured["legend"] == "keys: 1-9 select | ↓/j=next | ↑/k=prev | gg=first | G=last | ^U/^D=half | /=fwd | ?=rev | n/N=next | u=up | s=sort | S=sort-back | d=[dsc] | r=rfrsh | q=quit"


def test_RQMD_sorting_shift_s_cycles_file_sort_backward(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# A Domain Requirement\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )

    state = {"call": 0}
    titles: list[str] = []

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            titles.append(title)
            state["call"] += 1
            if state["call"] == 1:
                return "cycle-sort-backward"
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert len(titles) >= 2
    assert "\x1b[1mBlk/Dep ↓\x1b[0m" in titles[1]


def test_RQMD_sorting_011_header_columns_stay_fixed_when_indicator_moves(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n- [B](b.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# A Domain Requirement\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )
    (criteria_dir / "b.md").write_text(
        "# B Domain Requirement\n\nScope: b.\n\n### AC-B-001: B\n- **Status:** 🔧 Implemented\n",
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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
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
        "# A Domain Requirement\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 🔧 Implemented\n",
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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert legends[0] == "keys: 1-9 select | ↓/j=next | ↑/k=prev | gg=first | G=last | ^U/^D=half | /=fwd | ?=rev | n/N=next | u=up | s=sort | S=sort-back | d=[dsc] | r=rfrsh | q=quit"
    assert legends[1] == "keys: 1-9 select | ↓/j=next | ↑/k=prev | gg=first | G=last | ^U/^D=half | /=fwd | ?=rev | n/N=next | u=up | s=sort | S=sort-back | d=[asc] | r=rfrsh | q=quit"


def test_RQMD_sorting_009_refresh_reopens_file_menu(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# A Domain Requirement\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 🔧 Implemented\n",
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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert state["call"] == 2


def test_RQMD_sorting_refresh_preserves_page_selection_context(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)

    links = []
    for index in range(1, 13):
        name = f"page-{index:02d}.md"
        links.append(f"- [Page {index:02d}]({name})")
        (criteria_dir / name).write_text(
            f"""# Page {index:02d}

### AC-PAGE-{index:03d}: Item
- **Status:** 💡 Proposed
""",
            encoding="utf-8",
        )

    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n" + "\n".join(links) + "\n",
        encoding="utf-8",
    )

    state = {"call": 0}
    selected_indices: list[int | None] = []

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            state["call"] += 1
            selected_indices.append(kwargs.get("selected_option_index"))
            if state["call"] == 1:
                return "refresh:1"
            return None
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert selected_indices[0] == 0
    assert selected_indices[1] == 1


def test_RQMD_sorting_003_refresh_keeps_deterministic_file_order(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [A](a.md)\n- [B](b.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# Same Domain Requirement\n\nScope: same.\n\n### AC-A-001: A\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )
    (criteria_dir / "b.md").write_text(
        "# Same Domain Requirement\n\nScope: same.\n\n### AC-B-001: B\n- **Status:** 🔧 Implemented\n",
        encoding="utf-8",
    )

    state = {"call": 0}
    snapshots: list[list[str]] = []

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            snapshots.append(list(options))
            state["call"] += 1
            if state["call"] == 1:
                return "refresh"
            return None
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert len(snapshots) == 2
    assert snapshots[0] == snapshots[1]


def test_RQMD_sorting_004_refresh_preserves_selected_sort_mode(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [One](one.md)\n- [Two](two.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "one.md").write_text(
        "# One Domain Requirement\n\nScope: one.\n\n### AC-ONE-001: One\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )
    (criteria_dir / "two.md").write_text(
        "# Two Domain Requirement\n\nScope: two.\n\n### AC-TWO-001: Two\n- **Status:** 🔧 Implemented\n",
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
            if state["call"] == 2:
                return "refresh"
            return None
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert len(titles) == 3
    assert "\x1b[1mpriority ↓\x1b[0m" in titles[1]
    assert "\x1b[1mpriority ↓\x1b[0m" in titles[2]


def test_RQMD_interactive_refresh_returns_page_metadata(monkeypatch) -> None:
    keys = iter(["j", "r"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    options = [f"opt{i}" for i in range(25)]

    result = cli.select_from_menu(
        "Pick",
        options,
        extra_keys={"r": "refresh"},
    )

    assert result == "refresh:9"


def test_RQMD_interactive_024_gg_jumps_to_first_page(monkeypatch) -> None:
    keys = iter(["j", "g", "g", "1"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    options = [f"opt{i}" for i in range(12)]

    result = cli.select_from_menu("Pick", options)

    assert result == 0


def test_RQMD_interactive_024_G_jumps_to_last_page(monkeypatch) -> None:
    keys = iter(["G", "1"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    options = [f"opt{i}" for i in range(12)]

    result = cli.select_from_menu("Pick", options)

    assert result == 9


def test_RQMD_interactive_024_ctrl_d_half_page_moves_forward(monkeypatch) -> None:
    keys = iter(["\x04", "1"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    options = [f"opt{i}" for i in range(12)]

    result = cli.select_from_menu("Pick", options)

    assert result == 4


def test_RQMD_interactive_025_forward_search_and_repeat(monkeypatch) -> None:
    keys = iter(["/", "n", "N", "1"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    monkeypatch.setattr(cli.click, "prompt", lambda *args, **kwargs: "match")
    options = [f"opt{i}" for i in range(9)] + ["match-alpha", "match-beta", "opt11"]

    result = cli.select_from_menu("Pick", options)

    assert result == 9


def test_RQMD_interactive_025_reverse_search_wraps(monkeypatch) -> None:
    keys = iter(["?", "3"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    monkeypatch.setattr(cli.click, "prompt", lambda *args, **kwargs: "match")
    options = [f"opt{i}" for i in range(9)] + ["opt9", "match-alpha", "match-beta"]

    result = cli.select_from_menu("Pick", options)

    assert result == 11


def test_RQMD_interactive_008_reason_prompt_helpers(monkeypatch) -> None:
    monkeypatch.setattr(cli.click, "prompt", lambda *args, **kwargs: "Some reason")
    assert cli.prompt_for_blocked_reason() == "Some reason"
    assert cli.prompt_for_deprecated_reason() == "Some reason"


def test_RQMD_interactive_009_positional_lookup_mode(monkeypatch, repo_with_domain_docs: Path) -> None:
    called = {"value": False}

    def fake_lookup(repo_root, domain_files, requirement_id, emoji_columns, id_prefixes, include_status_emojis, priority_mode, include_priority_summary):
        called["value"] = True
        assert requirement_id == "AC-HELLO-001"
        assert id_prefixes == ("AC", "R", "RQMD")
        return 0

    monkeypatch.setattr(cli, "lookup_criterion_interactive", fake_lookup)
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "AC-HELLO-001",
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert called["value"] is True


def test_RQMD_interactive_016_positional_file_opens_requirement_list_first(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "one.md").write_text(
        """# One Domain

Scope: one.

### AC-ONE-001: One
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    target = domain / "two.md"
    target.write_text(
        """# Two Domain

Scope: two.

### AC-TWO-001: Two
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    captured: dict[str, object] = {}

    def fake_interactive_loop(repo_root, criteria_dir, domain_files, emoji_columns, sort_files, sort_strategy, id_prefixes, include_status_emojis, priority_mode, include_priority_summary, initial_file_path=None, **kwargs):
        captured["initial_file_path"] = initial_file_path
        captured["domain_files"] = list(domain_files)
        return 0

    monkeypatch.setattr(cli, "interactive_update_loop", fake_interactive_loop)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "docs/requirements/two.md",
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert captured["initial_file_path"] == target
    assert len(captured["domain_files"]) == 2


def test_RQMD_interactive_016_non_interactive_positional_file_scopes_updates(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    one = domain / "one.md"
    two = domain / "two.md"
    one.write_text(
        """# One Domain

Scope: one.

### AC-SHARED-001: Shared
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    two.write_text(
        """# Two Domain

Scope: two.

### AC-SHARED-001: Shared
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "docs/requirements/one.md",
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--update",
            "AC-SHARED-001=verified",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "✅ Verified" in one.read_text(encoding="utf-8")
    assert "✅ Verified" not in two.read_text(encoding="utf-8")


def test_RQMD_interactive_016_prefers_id_lookup_when_id_and_file_are_both_positional(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "one.md").write_text(
        """# One Domain

Scope: one.

### AC-ONE-001: One
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    (domain / "two.md").write_text(
        """# Two Domain

Scope: two.

### AC-TWO-001: Two
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    called = {"lookup": False}

    def fake_lookup(repo_root, domain_files, requirement_id, emoji_columns, id_prefixes, include_status_emojis, priority_mode, include_priority_summary):
        called["lookup"] = True
        assert requirement_id == "AC-TWO-001"
        return 0

    monkeypatch.setattr(cli, "lookup_criterion_interactive", fake_lookup)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "AC-TWO-001",
            "docs/requirements/one.md",
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert called["lookup"] is True


def test_RQMD_interactive_019_multiple_targets_launch_focused_walk(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

## Query API

### AC-DEMO-001: Get item
- **Status:** ✅ Verified

### AC-DEMO-002: Search item
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    called = {"value": False}

    def fake_focused(repo_root, domain_files, selected_items, target_tokens, emoji_columns, id_prefixes, resume_filter, state_dir, include_status_emojis, priority_mode, include_priority_summary):
        called["value"] = True
        assert target_tokens == ["demo", "Query"]
        assert [str(item[1]["id"]) for item in selected_items] == ["AC-DEMO-001", "AC-DEMO-002"]
        return 0

    monkeypatch.setattr(cli, "focused_target_interactive_loop", fake_focused)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "demo",
            "Query",
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
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
        requirement_id="AC-HELLO-001",
        emoji_columns=False,
        id_prefixes=("AC",),
    )

    assert result == 0


def test_RQMD_interactive_017_lookup_toggle_updates_flagged(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain_file = criteria_dir / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: Demo
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    actions = iter(["toggle-field", "toggle-field", 0])
    monkeypatch.setattr(cli, "select_from_menu", lambda *args, **kwargs: next(actions))

    result = cli.lookup_criterion_interactive(
        repo_root=repo,
        domain_files=[domain_file],
        requirement_id="AC-DEMO-001",
        emoji_columns=False,
        id_prefixes=("AC",),
    )

    assert result == 0
    text = domain_file.read_text(encoding="utf-8")
    assert "- **Flagged:** true" in text


def test_RQMD_interactive_031_lookup_opens_linked_requirement_and_returns(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain_file = criteria_dir / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 💡 Proposed
- **Links:**
  - [AC-DEMO-002](demo.md#ac-demo-002)

### AC-DEMO-002: Second
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    visits: list[str] = []
    opened_titles: list[str] = []
    actions = iter(["open-linked", 0, "up", "up"])

    def fake_select(title, options, **kwargs):
        del kwargs
        if title.startswith("Choose Status or Priority for "):
            visits.append(title.removeprefix("Choose Status or Priority for ").splitlines()[0].removesuffix("."))
            return next(actions)
        if title.startswith("Open linked requirement from AC-DEMO-001"):
            opened_titles.extend(options)
            return next(actions)
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    result = cli.lookup_criterion_interactive(
        repo_root=repo,
        domain_files=[domain_file],
        requirement_id="AC-DEMO-001",
        emoji_columns=False,
        id_prefixes=("AC",),
    )

    assert result == 0
    assert opened_titles == ["AC-DEMO-002: Second (docs/requirements/demo.md)"]
    assert visits == ["AC-DEMO-001", "AC-DEMO-002", "AC-DEMO-001"]


def test_RQMD_interactive_031_lookup_reports_no_resolvable_linked_requirements(monkeypatch, tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain_file = criteria_dir / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 💡 Proposed
- **Links:**
  - [External docs](https://example.com)
- See also AC-MISSING-999.
""",
        encoding="utf-8",
    )

    actions = iter(["open-linked", "up"])

    def fake_select(title, options, **kwargs):
        del title, options, kwargs
        return next(actions)

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    result = cli.lookup_criterion_interactive(
        repo_root=repo,
        domain_files=[domain_file],
        requirement_id="AC-DEMO-001",
        emoji_columns=False,
        id_prefixes=("AC",),
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "No linked requirements in the current catalog for AC-DEMO-001." in output


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


def test_RQMD_interactive_021_jump_to_subsection_from_requirement_menu(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

## Query API

### AC-DEMO-001: Query path
- **Status:** 💡 Proposed

## Mutation API

### AC-DEMO-002: Mutation path
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    captured_ids: list[str] = []
    state = {"req_calls": 0}

    def fake_panel(path, requirement, repo_root, id_prefixes):
        del path, repo_root, id_prefixes
        captured_ids.append(str(requirement["id"]))
        return f"PANEL:{requirement['id']}"

    def fake_select(title, options, **kwargs):
        del options
        if title.startswith("Select file"):
            return 0
        if title.startswith("Select requirement in"):
            state["req_calls"] += 1
            if state["req_calls"] == 1:
                return "jump-subsection"
            return None
        if title.startswith("Choose Status or Priority for"):
            assert kwargs.get("prefix_text") == "PANEL:AC-DEMO-002"
            return "up"
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)
    monkeypatch.setattr(cli.workflows_mod, "format_criterion_panel", fake_panel)
    monkeypatch.setattr(cli.click, "prompt", lambda *args, **kwargs: "mutation")

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert captured_ids[0] == "AC-DEMO-002"


def test_RQMD_interactive_021b_requirement_menu_receives_panel_prefix() -> None:
    captured: dict[str, object] = {}

    def fake_select(title, options, **kwargs):
        captured["title"] = title
        captured["prefix_text"] = kwargs.get("prefix_text")
        captured["right_labels"] = list(kwargs.get("option_right_labels") or [])
        captured["right_label_layout"] = kwargs.get("right_label_layout")
        return "up"

    requirement = {
        "id": "RQMD-AUTOMATION-019",
        "title": "Automation body stays visible",
        "status": "💡 Proposed",
    }

    result = cli.workflows_mod._prompt_for_requirement_action(
        requirement,
        "status",
        fake_select,
        panel_text="\nPANEL BODY\n==========",
        title_suffix=" [1/5]",
    )

    assert result == ("up", None)
    plain_title = re.sub(r"\x1b\[[0-9;]*m", "", captured["title"])
    assert plain_title.startswith("Choose Status or Priority for RQMD-AUTOMATION-019 [1/5].\n")
    assert "Status" in plain_title
    assert "Priority" in plain_title
    assert captured["prefix_text"] == "\nPANEL BODY\n=========="
    assert captured["right_label_layout"] == "adjacent"
    assert len(captured["right_labels"]) == 5
    assert captured["right_labels"][0].startswith("  !)")
    assert captured["right_labels"][2].startswith("  #)")


def test_RQMD_interactive_021c_requirement_menu_exposes_history_shortcuts() -> None:
    captured: dict[str, object] = {}

    def fake_select(title, options, **kwargs):
        captured["extra_keys"] = kwargs.get("extra_keys")
        captured["extra_keys_help"] = kwargs.get("extra_keys_help")
        captured["footer_legend"] = kwargs.get("footer_legend")
        captured["compact_footer"] = kwargs.get("compact_footer")
        return "history"

    requirement = {
        "id": "RQMD-UNDO-007",
        "title": "History controls",
        "status": "🔧 Implemented",
    }

    result = cli.workflows_mod._prompt_for_requirement_action(
        requirement,
        "status",
        fake_select,
    )

    assert result == ("history", None)
    assert captured["extra_keys"]["z"] == "undo"
    assert captured["extra_keys"]["y"] == "redo"
    assert captured["extra_keys"]["h"] == "history"
    assert captured["extra_keys"]["v"] == "open-vscode"
    assert captured["extra_keys_help"]["v"] == "code"
    assert "z=undo" in captured["footer_legend"]
    assert "y=redo" in captured["footer_legend"]
    assert "h=history" in captured["footer_legend"]
    assert "v=code" in captured["footer_legend"]
    assert "next-ac" in captured["footer_legend"]
    assert "first-ac" in captured["footer_legend"]
    assert "/=fwd" not in captured["footer_legend"]
    assert captured["compact_footer"] == "keys: 1-9 select | !=p0..$=p3 | ↓/j=next-ac | ↑/k=prev-ac | :=help | v=code | o=refs | u=up | q=quit"


def test_RQMD_interactive_021ca_status_menu_exposes_priority_shortcuts() -> None:
    captured: dict[str, object] = {}

    def fake_select(title, options, **kwargs):
        captured["extra_keys"] = kwargs.get("extra_keys")
        captured["extra_keys_help"] = kwargs.get("extra_keys_help")
        captured["footer_legend"] = kwargs.get("footer_legend")
        captured["compact_footer"] = kwargs.get("compact_footer")
        captured["right_labels"] = list(kwargs.get("option_right_labels") or [])
        return "priority-shortcut:🟠 P1 - High"

    requirement = {
        "id": "RQMD-INTERACTIVE-007",
        "title": "Status menu priority shortcuts",
        "status": "💡 Proposed",
        "priority": "🟡 Medium",
    }

    result = cli.workflows_mod._prompt_for_requirement_action(
        requirement,
        "status",
        fake_select,
    )

    assert result == ("apply-priority", "🟠 P1 - High")
    assert captured["extra_keys"]["!"] == "priority-shortcut:🔴 P0 - Critical"
    assert captured["extra_keys"]["@"] == "priority-shortcut:🟠 P1 - High"
    assert captured["extra_keys"]["#"] == "priority-shortcut:🟡 P2 - Medium"
    assert captured["extra_keys"]["$"] == "priority-shortcut:🟢 P3 - Low"
    assert "priority-shortcut:" not in captured["extra_keys"].get("%", "")
    assert captured["extra_keys_help"]["!"] == "critical"
    assert captured["extra_keys_help"]["@"] == "high"
    assert "1=💡 Proposed" in captured["footer_legend"]
    assert "2=🔧 Implemented" in captured["footer_legend"]
    assert "3=✅ Verified" in captured["footer_legend"]
    assert "4=⛔ Blocked" in captured["footer_legend"]
    assert "5=🗑️ Deprecated" in captured["footer_legend"]
    assert "!=p0" in captured["footer_legend"]
    assert "@=p1" in captured["footer_legend"]
    assert captured["compact_footer"] == "keys: 1-9 select | !=p0..$=p3 | ↓/j=next-ac | ↑/k=prev-ac | :=help | v=code | o=refs | u=up | q=quit"
    right_labels_plain = [re.sub(r"\x1b\[[0-9;]*m", "", item).rstrip() for item in captured["right_labels"]]
    assert right_labels_plain == [
        "  !) 🔴 P0 - Critical",
        "  @) 🟠 P1 - High",
        "→ #) 🟡 P2 - Medium",
        "  $) 🟢 P3 - Low",
        "",
    ]
    widths = [menus.visible_length(item) for item in captured["right_labels"] if item]
    assert len(set(widths)) == 1
    assert "\x1b[48;5;178m" in captured["right_labels"][2]


def test_RQMD_interactive_021cad_status_menu_shows_custom_priorities_beyond_shortcuts() -> None:
    captured: dict[str, object] = {}
    custom_priorities = [
        {"name": "Critical", "shortcode": "p0", "emoji": "🔴"},
        {"name": "High", "shortcode": "p1", "emoji": "🟠"},
        {"name": "Medium", "shortcode": "p2", "emoji": "🟡"},
        {"name": "Low", "shortcode": "p3", "emoji": "🟢"},
        {"name": "Eventually", "shortcode": "p4", "emoji": "🔵"},
        {"name": "Someday", "shortcode": "p5", "emoji": "⚪"},
        {"name": "Deep Backlog", "shortcode": "p6", "emoji": "🟣"},
        {"name": "Icebox", "shortcode": "p7", "emoji": "🟤"},
    ]

    def fake_select(title, options, **kwargs):
        captured["extra_keys"] = kwargs.get("extra_keys")
        captured["footer_legend"] = kwargs.get("footer_legend")
        captured["compact_footer"] = kwargs.get("compact_footer")
        captured["right_labels"] = list(kwargs.get("option_right_labels") or [])
        return "up"

    requirement = {
        "id": "RQMD-INTERACTIVE-007",
        "title": "Status menu custom priority preview",
        "status": "💡 Proposed",
        "priority": "🔵 Eventually",
    }

    configure_priority_catalog(custom_priorities)
    try:
        result = cli.workflows_mod._prompt_for_requirement_action(
            requirement,
            "status",
            fake_select,
        )
    finally:
        configure_priority_catalog(None)

    assert result == ("up", None)
    right_labels_plain = [re.sub(r"\x1b\[[0-9;]*m", "", item).rstrip() for item in captured["right_labels"]]
    assert right_labels_plain == [
        "  !) 🔴 Critical",
        "  @) 🟠 High",
        "  #) 🟡 Medium",
        "  $) 🟢 Low",
        "→ %) 🔵 Eventually",
        "  ^) ⚪ Someday",
        "  &) 🟣 Deep Backlog",
        "  *) 🟤 Icebox",
    ]
    assert captured["extra_keys"]["%"] == "priority-shortcut:🔵 Eventually"
    assert captured["extra_keys"]["^"] == "priority-shortcut:⚪ Someday"
    assert captured["extra_keys"]["&"] == "priority-shortcut:🟣 Deep Backlog"
    assert captured["extra_keys"]["*"] == "priority-shortcut:🟤 Icebox"
    assert "!=p0" in captured["footer_legend"]
    assert "@=p1" in captured["footer_legend"]
    assert "#=p2" in captured["footer_legend"]
    assert "$=p3" in captured["footer_legend"]
    assert "%=p4" in captured["footer_legend"]
    assert "^=p5" in captured["footer_legend"]
    assert "&=p6" in captured["footer_legend"]
    assert "*=p7" in captured["footer_legend"]
    assert captured["compact_footer"] == "keys: 1-9 select | !=p0..*=p7 | ↓/j=next-ac | ↑/k=prev-ac | :=help | v=code | o=refs | u=up | q=quit"


def test_RQMD_interactive_030_lookup_opens_current_requirement_in_vscode(monkeypatch, tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain_file = criteria_dir / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 💡 Proposed

### AC-DEMO-002: Second
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    visits: list[str] = []
    launched: list[list[str]] = []
    actions = iter(["open-vscode", "up"])

    def fake_select(title, options, **kwargs):
        del options, kwargs
        if title.startswith("Choose Status or Priority for "):
            visits.append(title.removeprefix("Choose Status or Priority for ").splitlines()[0].removesuffix("."))
            return next(actions)
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)
    monkeypatch.setattr(cli.workflows_mod.shutil, "which", lambda name: "/usr/local/bin/code" if name == "code" else None)

    def fake_run(cmd, **kwargs):
        del kwargs
        launched.append(list(cmd))
        return SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(cli.workflows_mod.subprocess, "run", fake_run)

    result = cli.lookup_criterion_interactive(
        repo_root=repo,
        domain_files=[domain_file],
        requirement_id="AC-DEMO-001",
        emoji_columns=False,
        id_prefixes=("AC",),
    )

    output = capsys.readouterr().out
    assert result == 0
    assert visits == ["AC-DEMO-001", "AC-DEMO-001"]
    assert launched == [["/usr/local/bin/code", "--goto", f"{domain_file}:5:1"]]
    assert "Opened AC-DEMO-001 in VS Code." in output


def test_RQMD_interactive_030_lookup_reports_missing_vscode_launcher(monkeypatch, tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain_file = criteria_dir / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    actions = iter(["open-vscode", "up"])

    def fake_select(title, options, **kwargs):
        del title, options, kwargs
        return next(actions)

    monkeypatch.setattr(cli, "select_from_menu", fake_select)
    monkeypatch.setattr(cli.workflows_mod.shutil, "which", lambda name: None)

    result = cli.lookup_criterion_interactive(
        repo_root=repo,
        domain_files=[domain_file],
        requirement_id="AC-DEMO-001",
        emoji_columns=False,
        id_prefixes=("AC",),
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "VS Code command-line launcher 'code' is not available." in output


def test_RQMD_interactive_021cc_split_status_and_priority_highlights(monkeypatch, capsys) -> None:
    keys = iter(["q"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    rendered_lines: list[str] = []

    def capture_echo(message="", *args, **kwargs):
        if isinstance(message, str):
            rendered_lines.append(message)

    monkeypatch.setattr(menus.click, "echo", capture_echo)

    result = menus.select_from_menu(
        "Status",
        ["💡 Proposed", "🔧 Implemented"],
        allow_paging_nav=False,
        option_right_labels=[
            "  !) \x1b[31m🔴 P0 - Critical\x1b[0m",
            "→ @) \x1b[43m🟠 P1 - High\x1b[0m",
        ],
        selected_option_index=0,
        selected_option_bg="\x1b[48;5;27m",
        separate_right_label_background=True,
        right_label_layout="adjacent",
    )
    rendered = "\n".join(rendered_lines)

    assert result is None
    assert "\x1b[48;5;27m→ 1) 💡 Proposed\x1b[0m" in rendered
    assert "→ @) \x1b[43m🟠 P1 - High\x1b[0m" in rendered


def test_RQMD_interactive_021cd_adjacent_right_labels_stay_near_left_column(monkeypatch) -> None:
    keys = iter(["q"])
    rendered_lines: list[str] = []

    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    monkeypatch.setattr(menus.click, "echo", lambda message="", *args, **kwargs: rendered_lines.append(message if isinstance(message, str) else str(message)))

    result = menus.select_from_menu(
        "Status",
        ["💡 Proposed", "🔧 Implemented"],
        allow_paging_nav=False,
        option_right_labels=[
            "  !) 🔴 Critical",
            "→ @) 🟠 High",
        ],
        right_label_layout="adjacent",
    )

    assert result is None
    first_option_line = next(line for line in rendered_lines if "1) 💡 Proposed" in line)
    plain_line = re.sub(r"\x1b\[[0-9;]*m", "", first_option_line)
    assert re.search(r"1\) 💡 Proposed\s{2,12}!\) 🔴 Critical", plain_line)


def test_RQMD_interactive_021cb_priority_shortcut_keeps_current_requirement_visible(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    domain_file = criteria_dir / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

### AC-DEMO-001: First
- **Status:** 💡 Proposed
- **Priority:** 🟡 Medium

### AC-DEMO-002: Second
- **Status:** 💡 Proposed
- **Priority:** 🟡 Medium
""",
        encoding="utf-8",
    )

    visits: list[str] = []
    state = {"file_calls": 0, "requirement_calls": 0}

    def fake_select(title, options, **kwargs):
        if title.startswith("Select file"):
            state["file_calls"] += 1
            if state["file_calls"] == 1:
                return 0
            return None
        if title.startswith("Select requirement in"):
            state["requirement_calls"] += 1
            if state["requirement_calls"] == 1:
                return 0
            return "up"
        if title.startswith("Choose Status or Priority for "):
            requirement_id = title.removeprefix("Choose Status or Priority for ").splitlines()[0].removesuffix(".")
            visits.append(requirement_id)
            if len(visits) == 1:
                return "priority-shortcut:🟠 P1 - High"
            return "up"
        return None

    result = cli.workflows_mod.interactive_update_loop(
        repo_root=repo,
        criteria_dir="docs/requirements",
        domain_files=[domain_file],
        emoji_columns=False,
        sort_files=False,
        id_prefixes=("AC",),
        select_from_menu_fn=fake_select,
        include_status_emojis=True,
        priority_mode=False,
        include_priority_summary=False,
    )

    updated_text = domain_file.read_text(encoding="utf-8")

    assert result == 0
    assert visits == ["AC-DEMO-002", "AC-DEMO-002"]
    assert "### AC-DEMO-002: Second\n- **Status:** 💡 Proposed\n- **Priority:** 🟠 P1 - High" in updated_text


def test_RQMD_interactive_021d_history_browser_uses_paged_menu(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    requirements_dir = repo / "docs" / "requirements"
    requirements_dir.mkdir(parents=True)
    domain_file = requirements_dir / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    history_manager = cli.HistoryManager(repo_root=repo, requirements_dir="docs/requirements")
    history_manager.capture(command="baseline", actor="test")
    domain_file.write_text(
        """# Demo Requirements

### RQMD-DEMO-001: Alpha
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    history_manager.capture(command="set-status", actor="test", reason="Implemented")

    captured: dict[str, object] = {}

    def fake_select(title, options, **kwargs):
        captured["title"] = title
        captured["options"] = list(options)
        captured["right_labels"] = list(kwargs.get("option_right_labels") or [])
        captured["selected_option_index"] = kwargs.get("selected_option_index")
        captured["footer_legend"] = kwargs.get("footer_legend")
        captured["compact_footer"] = kwargs.get("compact_footer")
        return "up"

    cli.workflows_mod._show_history_browser(
        repo,
        [domain_file],
        select_from_menu_fn=fake_select,
    )

    assert captured["title"] == "History entries"
    assert len(captured["options"]) == 2
    assert captured["options"][0].startswith("* ")
    assert "(HEAD -> main)" in captured["options"][0]
    assert "set-status: Implemented" in captured["options"][0]
    assert captured["right_labels"][0][:10].count("-") == 2
    assert "+" in captured["right_labels"][0]
    assert captured["selected_option_index"] == 0
    assert "gg=first" in captured["footer_legend"]
    assert "^U/^D=half" in captured["footer_legend"]
    assert "/=fwd" in captured["footer_legend"]
    assert "n/N=next" in captured["footer_legend"]
    assert captured["compact_footer"] == "keys: 1-9 select | ↓/j=next | ↑/k=prev | :=help | u=up | q=quit"


@pytest.mark.timeout(5)
def test_RQMD_interactive_021d2_history_browser_checks_out_selected_branch(monkeypatch) -> None:
    checkout_calls: list[str] = []

    class StubHistoryManager:
        def get_branches(self):
            return {
                "main": {"is_current": True},
                "recovery-branch": {"is_current": False},
            }

        def checkout_branch(self, branch_name: str):
            checkout_calls.append(branch_name)
            return "deadbeefcafebabe"

    monkeypatch.setattr(cli.click, "getchar", lambda: "c")

    action = cli.workflows_mod._prompt_for_history_entry_action(
        {
            "entry_index": 1,
            "command": "implemented",
            "branch": "recovery-branch",
            "commit": "abc12345deadbeef",
            "timestamp": "2026-03-29T00:00:00+00:00",
            "files": ["docs/requirements/demo.md"],
            "delta": {"additions": 1, "deletions": 0, "files_changed": 1},
        },
        StubHistoryManager(),
    )

    assert action == "refresh"
    assert checkout_calls == ["recovery-branch"]


@pytest.mark.timeout(5)
def test_RQMD_interactive_021e_history_browser_cherry_picks_selected_entry(monkeypatch) -> None:
    cherry_pick_calls: list[tuple[str, str | None]] = []

    class StubHistoryManager:
        def get_branches(self):
            return {
                "main": {"is_current": True},
                "recovery-branch": {"is_current": False},
            }

        def cherry_pick(self, commit_hash: str, target_branch: str | None = None):
            cherry_pick_calls.append((commit_hash, target_branch))
            return "deadbeefcafebabe"

    monkeypatch.setattr(cli.click, "getchar", lambda: "p")
    monkeypatch.setattr(cli.click, "confirm", lambda *args, **kwargs: True)

    action = cli.workflows_mod._prompt_for_history_entry_action(
        {
            "entry_index": 1,
            "command": "implemented",
            "branch": "recovery-branch",
            "commit": "abc12345deadbeef",
            "timestamp": "2026-03-29T00:00:00+00:00",
            "files": ["docs/requirements/demo.md"],
            "delta": {"additions": 1, "deletions": 0, "files_changed": 1},
        },
        StubHistoryManager(),
    )

    assert action == "refresh"
    assert len(cherry_pick_calls) == 1
    assert cherry_pick_calls[0][0] == "abc12345deadbeef"
    assert cherry_pick_calls[0][1] == "main"


@pytest.mark.timeout(5)
def test_RQMD_interactive_021f_history_browser_replays_selected_branch(monkeypatch) -> None:
    replay_calls: list[tuple[str, str | None]] = []

    class StubHistoryManager:
        def get_branches(self):
            return {
                "main": {"is_current": True},
                "recovery-branch": {"is_current": False},
            }

        def replay_branch(self, from_branch: str, onto_branch: str | None = None):
            replay_calls.append((from_branch, onto_branch))
            return ["feedfacecafebeef"]

    monkeypatch.setattr(cli.click, "getchar", lambda: "r")
    monkeypatch.setattr(cli.click, "confirm", lambda *args, **kwargs: True)

    action = cli.workflows_mod._prompt_for_history_entry_action(
        {
            "entry_index": 2,
            "command": "verified",
            "branch": "recovery-branch",
            "commit": "feedfacecafebeef",
            "timestamp": "2026-03-29T00:00:00+00:00",
            "files": ["docs/requirements/demo.md"],
            "delta": {"additions": 1, "deletions": 1, "files_changed": 1},
        },
        StubHistoryManager(),
    )

    assert action == "refresh"
    assert len(replay_calls) == 1
    assert replay_calls[0][0] == "recovery-branch"
    assert replay_calls[0][1] == "main"


@pytest.mark.timeout(5)
def test_RQMD_interactive_021g_history_browser_runs_gc(monkeypatch) -> None:
    gc_calls: list[bool] = []
    confirm_answers = iter([False, True])

    class StubHistoryManager:
        def get_branches(self):
            return {
                "main": {"is_current": True},
                "recovery-branch": {"is_current": False},
            }

        def get_storage_stats(self):
            return {"count": 4, "packs": 1}

        def garbage_collect(self, prune_now: bool = False):
            gc_calls.append(prune_now)
            return {
                "prune_now": prune_now,
                "before": {"count": 4, "packs": 1},
                "after": {"count": 1, "packs": 2},
            }

    monkeypatch.setattr(cli.click, "getchar", lambda: "g")
    monkeypatch.setattr(cli.click, "confirm", lambda *args, **kwargs: next(confirm_answers))

    action = cli.workflows_mod._prompt_for_history_entry_action(
        {
            "entry_index": 2,
            "command": "verified",
            "branch": "recovery-branch",
            "commit": "feedfacecafebeef",
            "timestamp": "2026-03-29T00:00:00+00:00",
            "files": ["docs/requirements/demo.md"],
            "delta": {"additions": 1, "deletions": 1, "files_changed": 1},
        },
        StubHistoryManager(),
    )

    assert action == "refresh"
    assert gc_calls == [False]


@pytest.mark.timeout(5)
def test_RQMD_interactive_021g2_history_browser_saves_label_before_gc(monkeypatch) -> None:
    gc_calls: list[bool] = []
    label_calls: list[tuple[str, str]] = []
    confirm_answers = iter([True, True])

    class StubHistoryManager:
        def get_branches(self):
            return {
                "main": {"is_current": True},
                "recovery-branch": {"is_current": False},
            }

        def get_storage_stats(self):
            return {"count": 4, "packs": 1}

        def label_branch(self, branch_name: str, label: str):
            label_calls.append((branch_name, label))
            return True

        def garbage_collect(self, prune_now: bool = False):
            gc_calls.append(prune_now)
            return {
                "prune_now": prune_now,
                "before": {"count": 4, "packs": 1},
                "after": {"count": 1, "packs": 2},
            }

    monkeypatch.setattr(cli.click, "getchar", lambda: "g")
    monkeypatch.setattr(cli.click, "confirm", lambda *args, **kwargs: next(confirm_answers))
    monkeypatch.setattr(cli.click, "prompt", lambda *args, **kwargs: "saved-snapshot")

    action = cli.workflows_mod._prompt_for_history_entry_action(
        {
            "entry_index": 2,
            "command": "verified",
            "branch": "recovery-branch",
            "commit": "feedfacecafebeef",
            "timestamp": "2026-03-29T00:00:00+00:00",
            "files": ["docs/requirements/demo.md"],
            "delta": {"additions": 1, "deletions": 1, "files_changed": 1},
        },
        StubHistoryManager(),
    )

    assert action == "refresh"
    assert label_calls == [("main", "saved-snapshot")]
    assert gc_calls == [False]


@pytest.mark.timeout(5)
def test_RQMD_interactive_021h_history_browser_runs_immediate_prune(monkeypatch) -> None:
    gc_calls: list[bool] = []
    confirm_answers = iter([False, True])

    class StubHistoryManager:
        def get_branches(self):
            return {
                "main": {"is_current": True},
                "recovery-branch": {"is_current": False},
            }

        def get_storage_stats(self):
            return {"count": 7, "packs": 0}

        def garbage_collect(self, prune_now: bool = False):
            gc_calls.append(prune_now)
            return {
                "prune_now": prune_now,
                "before": {"count": 7, "packs": 0},
                "after": {"count": 0, "packs": 1},
            }

    monkeypatch.setattr(cli.click, "getchar", lambda: "G")
    monkeypatch.setattr(cli.click, "confirm", lambda *args, **kwargs: next(confirm_answers))

    action = cli.workflows_mod._prompt_for_history_entry_action(
        {
            "entry_index": 3,
            "command": "verified",
            "branch": "recovery-branch",
            "commit": "feedfacecafebeef",
            "timestamp": "2026-03-29T00:00:00+00:00",
            "files": ["docs/requirements/demo.md"],
            "delta": {"additions": 1, "deletions": 1, "files_changed": 1},
        },
        StubHistoryManager(),
    )

    assert action == "refresh"
    assert gc_calls == [True]


@pytest.mark.timeout(5)
def test_RQMD_interactive_021h2_history_browser_saves_label_before_prune(monkeypatch) -> None:
    gc_calls: list[bool] = []
    label_calls: list[tuple[str, str]] = []
    confirm_answers = iter([True, True])

    class StubHistoryManager:
        def get_branches(self):
            return {
                "main": {"is_current": True},
                "recovery-branch": {"is_current": False},
            }

        def get_storage_stats(self):
            return {"count": 7, "packs": 0}

        def label_branch(self, branch_name: str, label: str):
            label_calls.append((branch_name, label))
            return True

        def garbage_collect(self, prune_now: bool = False):
            gc_calls.append(prune_now)
            return {
                "prune_now": prune_now,
                "before": {"count": 7, "packs": 0},
                "after": {"count": 0, "packs": 1},
            }

    monkeypatch.setattr(cli.click, "getchar", lambda: "G")
    monkeypatch.setattr(cli.click, "confirm", lambda *args, **kwargs: next(confirm_answers))
    monkeypatch.setattr(cli.click, "prompt", lambda *args, **kwargs: "saved-before-prune")

    action = cli.workflows_mod._prompt_for_history_entry_action(
        {
            "entry_index": 3,
            "command": "verified",
            "branch": "recovery-branch",
            "commit": "feedfacecafebeef",
            "timestamp": "2026-03-29T00:00:00+00:00",
            "files": ["docs/requirements/demo.md"],
            "delta": {"additions": 1, "deletions": 1, "files_changed": 1},
        },
        StubHistoryManager(),
    )

    assert action == "refresh"
    assert label_calls == [("main", "saved-before-prune")]
    assert gc_calls == [True]


@pytest.mark.timeout(5)
def test_RQMD_interactive_021i_history_browser_labels_selected_branch(monkeypatch) -> None:
    label_calls: list[tuple[str, str]] = []

    class StubHistoryManager:
        def get_branches(self):
            return {
                "main": {"is_current": True},
                "recovery-branch": {"is_current": False},
            }

        def label_branch(self, branch_name: str, label: str):
            label_calls.append((branch_name, label))
            return True

    monkeypatch.setattr(cli.click, "getchar", lambda: "l")
    monkeypatch.setattr(cli.click, "prompt", lambda *args, **kwargs: "saved-snapshot")

    action = cli.workflows_mod._prompt_for_history_entry_action(
        {
            "entry_index": 4,
            "command": "verified",
            "branch": "recovery-branch",
            "commit": "feedfacecafebeef",
            "timestamp": "2026-03-29T00:00:00+00:00",
            "files": ["docs/requirements/demo.md"],
            "delta": {"additions": 1, "deletions": 1, "files_changed": 1},
        },
        StubHistoryManager(),
    )

    assert action == "refresh"
    assert label_calls == [("recovery-branch", "saved-snapshot")]


@pytest.mark.timeout(5)
def test_RQMD_interactive_021j_history_browser_discards_branch_after_optional_label(monkeypatch) -> None:
    label_calls: list[tuple[str, str]] = []
    discard_calls: list[str] = []
    confirm_answers = iter([True, True])

    class StubHistoryManager:
        def get_branches(self):
            return {
                "main": {"is_current": True},
                "recovery-branch": {"is_current": False},
            }

        def label_branch(self, branch_name: str, label: str):
            label_calls.append((branch_name, label))
            return True

        def discard_branch(self, branch_name: str):
            discard_calls.append(branch_name)
            return True

    monkeypatch.setattr(cli.click, "getchar", lambda: "x")
    monkeypatch.setattr(cli.click, "confirm", lambda *args, **kwargs: next(confirm_answers))
    monkeypatch.setattr(cli.click, "prompt", lambda *args, **kwargs: "keep-for-reference")

    action = cli.workflows_mod._prompt_for_history_entry_action(
        {
            "entry_index": 5,
            "command": "verified",
            "branch": "recovery-branch",
            "commit": "feedfacecafebeef",
            "timestamp": "2026-03-29T00:00:00+00:00",
            "files": ["docs/requirements/demo.md"],
            "delta": {"additions": 1, "deletions": 1, "files_changed": 1},
        },
        StubHistoryManager(),
    )

    assert action == "refresh"
    assert label_calls == [("recovery-branch", "keep-for-reference")]
    assert discard_calls == ["recovery-branch"]


def test_RQMD_interactive_020_shell_completion_suggests_subsection_domain_and_id(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

## Query API

### AC-DEMO-001: First
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    ctx = click.Context(cli.main)
    ctx.params = {
        "repo_root": repo,
        "requirements_dir": "docs/requirements",
        "id_prefixes": (),
    }

    items = cli.shell_complete_target_tokens(ctx, param=None, incomplete="q")
    values = [item.value if hasattr(item, "value") else str(item) for item in items]

    assert "Query API" in values
    assert "AC-DEMO-001" not in values

    items_id = cli.shell_complete_target_tokens(ctx, param=None, incomplete="ac-demo")
    values_id = [item.value if hasattr(item, "value") else str(item) for item in items_id]
    assert "AC-DEMO-001" in values_id


def test_RQMD_interactive_020b_shell_completion_includes_positional_filter_tokens(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "core-engine.md").write_text(
        """# Core Engine Requirements

Scope: core-engine.

### AC-CORE-001: First
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
""",
        encoding="utf-8",
    )

    ctx = click.Context(cli.main)
    ctx.params = {
        "repo_root": repo,
        "requirements_dir": "docs/requirements",
        "id_prefixes": (),
    }

    items = cli.shell_complete_target_tokens(ctx, param=None, incomplete="p")
    values = [item.value if hasattr(item, "value") else str(item) for item in items]

    assert "Proposed" in values
    assert "P1" in values

    items_all = cli.shell_complete_target_tokens(ctx, param=None, incomplete="a")
    values_all = [item.value if hasattr(item, "value") else str(item) for item in items_all]
    assert "all" in values_all


def test_RQMD_interactive_027_positional_status_filter_launches_filtered_walk(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 💡 Proposed

### AC-DEMO-002: Second
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    called: dict[str, object] = {}

    def fake_filtered(repo_root, domain_files, target_status, emoji_columns, id_prefixes, resume_filter, state_dir, include_status_emojis, priority_mode, include_priority_summary):
        called["status"] = target_status
        called["domain_files"] = [path.name for path in domain_files]
        return 0

    monkeypatch.setattr(cli, "filtered_interactive_loop", fake_filtered)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "Prop",
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert called["status"] == "💡 Proposed"
    assert called["domain_files"] == ["demo.md"]


def test_RQMD_interactive_036_positional_all_launches_focused_walk(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    (domain / "demo.md").write_text(
        """# Demo Requirements

Scope: demo.

### REQ-002: Older
- **Status:** 💡 Proposed

### REQ-1000: Newest
- **Status:** 🔧 Implemented

### REQ-010: Middle
- **Status:** ✅ Verified
""",
        encoding="utf-8",
    )

    called: dict[str, object] = {}

    def fake_focused(repo_root, domain_files, selected_items, target_tokens, emoji_columns, id_prefixes, resume_filter, state_dir, include_status_emojis, priority_mode, include_priority_summary):
        called["targets"] = list(target_tokens)
        called["ids"] = [str(requirement["id"]) for _path, requirement in selected_items]
        return 0

    monkeypatch.setattr(cli, "focused_target_interactive_loop", fake_focused)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "all",
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
            "--id-namespace",
            "REQ",
        ],
    )

    assert result.exit_code == 0
    assert called["targets"] == ["all"]
    assert called["ids"] == ["REQ-1000", "REQ-010", "REQ-002"]


def test_RQMD_interactive_filtered_walk_resumes_position_across_runs(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    domain_file = domain / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 🔧 Implemented

### AC-DEMO-002: Second
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    first_actions = iter(["nav-next", None])

    def first_select(title, options, **kwargs):
        if title.startswith("Choose Status or Priority for"):
            return next(first_actions)
        return None

    original_select = cli.select_from_menu
    cli.select_from_menu = first_select

    try:
        first_result = cli.filtered_interactive_loop(
            repo_root=repo,
            domain_files=[domain_file],
            target_status="🔧 Implemented",
            emoji_columns=False,
            id_prefixes=("AC",),
            resume_filter=True,
            state_dir="state-cache",
        )
    finally:
        cli.select_from_menu = original_select

    assert first_result == 0
    resume_files = list((repo / "state-cache").glob("filter-resume-*.json"))
    assert len(resume_files) == 1
    resume_state = json.loads(resume_files[0].read_text(encoding="utf-8"))
    assert resume_state["🔧 Implemented"]["id"] == "AC-DEMO-002"

    seen_titles: list[str] = []

    def second_select(title, options, **kwargs):
        if title.startswith("Choose Status or Priority for"):
            seen_titles.append(title)
            return None
        return None

    original_select = cli.select_from_menu
    cli.select_from_menu = second_select

    try:
        second_result = cli.filtered_interactive_loop(
            repo_root=repo,
            domain_files=[domain_file],
            target_status="🔧 Implemented",
            emoji_columns=False,
            id_prefixes=("AC",),
            resume_filter=True,
            state_dir="state-cache",
        )
    finally:
        cli.select_from_menu = original_select

    assert second_result == 0
    assert seen_titles
    assert "[2/2]" in seen_titles[0]


def test_RQMD_interactive_filtered_walk_shift_n_is_previous_and_g_G_jump(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    domain_file = domain / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 🔧 Implemented

### AC-DEMO-002: Second
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    seen_titles: list[str] = []
    actions = iter(["nav-last", "nav-first", "nav-next", "nav-prev", "up"])

    def fake_select(title, options, **kwargs):
        if title.startswith("Choose Status or Priority for"):
            seen_titles.append(title)
            return next(actions)
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    result = cli.filtered_interactive_loop(
        repo_root=repo,
        domain_files=[domain_file],
        target_status="🔧 Implemented",
        emoji_columns=False,
        id_prefixes=("AC",),
        resume_filter=False,
    )

    assert result == 0
    assert any("[2/2]" in title for title in seen_titles)
    assert any("[1/2]" in title for title in seen_titles)


def test_RQMD_interactive_filtered_walk_end_message_does_not_exit(monkeypatch, tmp_path: Path, capsys) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    domain_file = domain / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 🔧 Implemented

### AC-DEMO-002: Second
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    actions = iter(["nav-last", "nav-next", "up"])

    def fake_select(title, options, **kwargs):
        if title.startswith("Choose Status or Priority for"):
            return next(actions)
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    result = cli.filtered_interactive_loop(
        repo_root=repo,
        domain_files=[domain_file],
        target_status="🔧 Implemented",
        emoji_columns=False,
        id_prefixes=("AC",),
        resume_filter=False,
    )

    output = capsys.readouterr().out
    assert result == 0
    assert "No more 🔧 Implemented requirements in this session list." in output


def test_RQMD_interactive_filtered_priority_walk_keeps_stable_membership_after_priority_change(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    domain_file = domain / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High

### AC-DEMO-002: Second
- **Status:** 💡 Proposed
- **Priority:** 🟠 P1 - High
""",
        encoding="utf-8",
    )

    seen_ids: list[str] = []
    actions = iter(["apply", "nav-next", "up"])

    def fake_select(title, options, **kwargs):
        if title.startswith("Choose Status or Priority for "):
            seen_ids.append(title.removeprefix("Choose Status or Priority for ").splitlines()[0].removesuffix("."))
            action = next(actions)
            if action == "apply":
                return 2
            return action
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    result = cli.filtered_priority_interactive_loop(
        repo_root=repo,
        domain_files=[domain_file],
        target_priority="🟠 P1 - High",
        emoji_columns=False,
        id_prefixes=("AC",),
        resume_filter=False,
        priority_mode=True,
    )

    updated_text = domain_file.read_text(encoding="utf-8")

    assert result == 0
    assert seen_ids == ["AC-DEMO-001 [1/2]", "AC-DEMO-001 [1/2]", "AC-DEMO-002 [2/2]"]
    assert "### AC-DEMO-001: First\n- **Status:** 💡 Proposed\n- **Priority:** 🟡 P2 - Medium" in updated_text


def test_RQMD_interactive_filtered_status_walk_keeps_current_requirement_visible_after_update(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    domain_file = domain / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 🔧 Implemented

### AC-DEMO-002: Second
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    seen_ids: list[str] = []
    actions = iter([2, "nav-next", "up"])

    def fake_select(title, options, **kwargs):
        if title.startswith("Choose Status or Priority for "):
            seen_ids.append(title.removeprefix("Choose Status or Priority for ").splitlines()[0].removesuffix("."))
            return next(actions)
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    result = cli.filtered_interactive_loop(
        repo_root=repo,
        domain_files=[domain_file],
        target_status="🔧 Implemented",
        emoji_columns=False,
        id_prefixes=("AC",),
        resume_filter=False,
    )

    updated_text = domain_file.read_text(encoding="utf-8")

    assert result == 0
    assert seen_ids == ["AC-DEMO-001 [1/2]", "AC-DEMO-001 [1/2]", "AC-DEMO-002 [2/2]"]
    assert "### AC-DEMO-001: First\n- **Status:** ✅ Verified" in updated_text


def test_RQMD_interactive_019_focused_walk_keeps_current_requirement_visible_after_update(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    domain_file = domain / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 💡 Proposed

### AC-DEMO-002: Second
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )

    selected_items = [
        (domain_file, {"id": "AC-DEMO-001", "status": "💡 Proposed", "title": "First"}),
        (domain_file, {"id": "AC-DEMO-002", "status": "💡 Proposed", "title": "Second"}),
    ]
    seen_ids: list[str] = []
    actions = iter([2, "nav-next", "up"])

    def fake_select(title, options, **kwargs):
        if title.startswith("Choose Status or Priority for "):
            seen_ids.append(title.removeprefix("Choose Status or Priority for ").splitlines()[0].removesuffix("."))
            return next(actions)
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)

    result = cli.focused_target_interactive_loop(
        repo_root=repo,
        domain_files=[domain_file],
        selected_items=selected_items,
        target_tokens=["AC-DEMO-001", "AC-DEMO-002"],
        emoji_columns=False,
        id_prefixes=("AC",),
        resume_filter=False,
        include_status_emojis=True,
        priority_mode=False,
        include_priority_summary=False,
    )

    updated_text = domain_file.read_text(encoding="utf-8")

    assert result == 0
    assert seen_ids == ["AC-DEMO-001 [1/2]", "AC-DEMO-001 [1/2]", "AC-DEMO-002 [2/2]"]
    assert "### AC-DEMO-001: First\n- **Status:** ✅ Verified" in updated_text


def test_RQMD_interactive_filtered_walk_project_local_state_dir_writes_under_repo(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    domain = repo / "docs" / "requirements"
    domain.mkdir(parents=True)
    domain_file = domain / "demo.md"
    domain_file.write_text(
        """# Demo Requirements

Scope: demo.

### AC-DEMO-001: First
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    original_select = cli.select_from_menu
    cli.select_from_menu = lambda *args, **kwargs: None
    try:
        result = cli.filtered_interactive_loop(
            repo_root=repo,
            domain_files=[domain_file],
            target_status="🔧 Implemented",
            emoji_columns=False,
            id_prefixes=("AC",),
            resume_filter=True,
            state_dir="project-local",
        )
    finally:
        cli.select_from_menu = original_select

    assert result == 0
    assert list((repo / "tmp" / "rqmd").glob("filter-resume-*.json"))


def test_RQMD_interactive_001_default_invokes_interactive_loop(monkeypatch, repo_with_domain_docs: Path) -> None:
    called = {"value": False}

    def fake_loop(repo_root, criteria_dir, domain_files, emoji_columns, sort_files, sort_strategy, id_prefixes, include_status_emojis, priority_mode, include_priority_summary, **kwargs):
        called["value"] = True
        assert sort_strategy == "standard"
        assert id_prefixes == ("AC", "R", "RQMD")
        return 0

    monkeypatch.setattr(cli, "interactive_update_loop", fake_loop)
    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
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
        "# A Domain Requirement\n\nScope: a.\n\n### AC-A-001: A\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )
    (criteria_dir / "b.md").write_text(
        "# B Domain Requirement\n\nScope: b.\n\n### AC-B-001: B\n- **Status:** 🔧 Implemented\n",
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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--sort-profile",
            "alpha-asc",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "\x1b[1mname ↑\x1b[0m" in str(captured["title"])
    assert "A Domain" in captured["options"][0]
    assert "B Domain" in captured["options"][1]
    assert captured["legend"] == "keys: 1-9 select | ↓/j=next | ↑/k=prev | gg=first | G=last | ^U/^D=half | /=fwd | ?=rev | n/N=next | u=up | s=sort | S=sort-back | d=[asc] | r=rfrsh | q=quit"


def test_RQMD_sorting_005_status_focus_strategy_uses_implemented_default(monkeypatch, tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    criteria_dir = repo / "docs" / "requirements"
    criteria_dir.mkdir(parents=True)
    (criteria_dir / "README.md").write_text(
        "# Requirements\n\n## Domain Documents\n\n- [Low](a.md)\n- [High](b.md)\n",
        encoding="utf-8",
    )
    (criteria_dir / "a.md").write_text(
        "# Low Requirement\n\nScope: low.\n\n### AC-L-001: L1\n- **Status:** 💡 Proposed\n",
        encoding="utf-8",
    )
    (criteria_dir / "b.md").write_text(
        "# High Requirement\n\nScope: high.\n\n### AC-H-001: H1\n- **Status:** 🔧 Implemented\n\n### AC-H-002: H2\n- **Status:** 🔧 Implemented\n",
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
            "--project-root",
            str(repo),
            "--docs-dir",
            "docs/requirements",
            "--sort-profile",
            "status-focus",
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "\x1b[1mI ↓\x1b[0m" in str(captured["title"])
    assert "High" in captured["options"][0]
    assert "Low" in captured["options"][1]
    assert captured["legend"] == "keys: 1-9 select | ↓/j=next | ↑/k=prev | gg=first | G=last | ^U/^D=half | /=fwd | ?=rev | n/N=next | u=up | s=sort | S=sort-back | d=[dsc] | r=rfrsh | q=quit"


def test_RQMD_sorting_unsorted_flag_warns_as_deprecated_alias(monkeypatch, repo_with_domain_docs: Path) -> None:
    monkeypatch.setattr(cli, "select_from_menu", lambda *args, **kwargs: None)

    runner = CliRunner()
    result = runner.invoke(
        cli.main,
        [
            "--project-root",
            str(repo_with_domain_docs),
            "--docs-dir",
            "docs/requirements",
            "--no-table",
            "--filesystem-order",
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
            "--project-root",
            str(repo_with_domain_docs),
            "--no-table",
        ],
    )

    assert result.exit_code == 0
    assert "Auto-selected requirement docs: docs/requirements/README.md" in result.output


@pytest.mark.timeout(10)
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
            f"### AC-F{idx:02d}-001: First requirement\n"
            "- **Status:** 💡 Proposed\n\n"
            f"### AC-F{idx:02d}-002: Second requirement\n"
            "- **Status:** 💡 Proposed\n"
        )
        (criteria_dir / f"domain-{idx:02d}.md").write_text(text, encoding="utf-8")

    # File menu under default descending name sort: j (page2), k (page1), j (page2), 2 (pick file 01)
    # Requirement menu: 1 (pick first requirement)
    # Status menus: 2 (Implemented), j (next requirement), 3 (Verified)
    # Then unwind: u (from wrapped status menu), u (from requirement menu), q (quit file menu)
    keys = iter(["j", "k", "j", "2", "1", "2", "j", "3", "u", "u", "q"])
    monkeypatch.setattr(menus.click, "getchar", lambda: next(keys))

    runner = CliRunner()
    try:
        result = runner.invoke(
            cli.main,
            [
                "--project-root",
                str(repo_root),
                "--docs-dir",
                criteria_rel,
                "--no-table",
            ],
        )

        assert result.exit_code == 0
        # Assert paging reached both pages in file selection flow.
        assert "Page 1/2" in result.output
        assert "Page 2/2" in result.output

        # Assert status updates were persisted in the selected file.
        selected = criteria_dir / "domain-01.md"
        updated = selected.read_text(encoding="utf-8")
        assert "### AC-F01-001: First requirement" in updated
        assert "### AC-F01-002: Second requirement" in updated
        assert "### AC-F01-001: First requirement\n- **Status:** ✅ Verified" in updated
        assert "### AC-F01-002: Second requirement\n- **Status:** 🔧 Implemented" in updated
    finally:
        # Cleanup scratch data so this test leaves the working tree unchanged.
        if scratch_root.exists():
            shutil.rmtree(scratch_root)


# ---------------------------------------------------------------------------
# RQMD-INTERACTIVE-011: Preflight write-permission gate
# ---------------------------------------------------------------------------


def test_RQMD_interactive_011_unwritable_file_blocks_interactive_mode(tmp_path: Path) -> None:
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
                "--project-root", str(repo),
                "--docs-dir", "docs/requirements",
                "--no-table",
                "--walk",
            ],
        )
        assert result.exit_code != 0
        combined = (result.output or "") + (str(result.exception) if result.exception else "")
        assert "writable" in combined.lower() or "write" in combined.lower() or "permission" in combined.lower()
        assert "locked.md" in combined
    finally:
        domain_file.chmod(stat.S_IRUSR | stat.S_IWUSR)