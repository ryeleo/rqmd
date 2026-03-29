from __future__ import annotations

import json
import re
import shutil
from pathlib import Path

import click
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


def test_RQMD_interactive_004b_arrow_nav_shortcuts(monkeypatch) -> None:
    keys = iter(["\x1b[B"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu(
        "Status",
        ["A", "B"],
        allow_paging_nav=False,
        extra_keys={"n": "nav-next", "p": "nav-prev"},
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

        if title.startswith("Set status for "):
            status_visits.append(title.removeprefix("Set status for ").splitlines()[0])
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
        footer_legend="keys: 1-9 select | ↓/n=next | ↑/p=prev | u=up | s=sort | S=sort-back | d=[asc] | r=rfrsh | q=quit",
        extra_keys={"s": "cycle-sort", "d": "toggle-direction", "r": "refresh"},
    )
    output = capsys.readouterr().out

    assert result is None
    assert "keys: 1-9 select | ↓/n=next | ↑/p=prev | u=up | s=sort | S=sort-back | d=[asc] | r=rfrsh | q=quit" in output


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
    assert captured["legend"] == "keys: 1-9 select | ↓/n=next | ↑/p=prev | u=up | s=sort | S=sort-back | d=[dsc] | r=rfrsh | q=quit"


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
    assert captured["legend"] == "keys: 1-9 select | ↓/n=next | ↑/p=prev | u=up | s=sort | S=sort-back | d=[dsc] | r=rfrsh | q=quit"


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
    assert legends[0] == "keys: 1-9 select | ↓/n=next | ↑/p=prev | u=up | s=sort | S=sort-back | d=[dsc] | r=rfrsh | q=quit"
    assert legends[1] == "keys: 1-9 select | ↓/n=next | ↑/p=prev | u=up | s=sort | S=sort-back | d=[asc] | r=rfrsh | q=quit"


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
    assert selected_indices[1] == 9


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
    keys = iter(["n", "r"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    options = [f"opt{i}" for i in range(25)]

    result = cli.select_from_menu(
        "Pick",
        options,
        extra_keys={"r": "refresh"},
    )

    assert result == "refresh:1"


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

    def fake_select(title, options, **kwargs):
        del options, kwargs
        if title.startswith("Select file"):
            return 0
        if title.startswith("Select requirement in"):
            state["req_calls"] += 1
            if state["req_calls"] == 1:
                return "jump-subsection"
            return None
        if title.startswith("Set status for"):
            return "up"
        return None

    monkeypatch.setattr(cli, "select_from_menu", fake_select)
    monkeypatch.setattr(cli.workflows_mod, "print_criterion_panel", fake_panel)
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
        if title.startswith("Set status for"):
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
        if title.startswith("Set status for"):
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
        if title.startswith("Set status for"):
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
        if title.startswith("Set status for"):
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
    assert "No more 🔧 Implemented requirements." in output


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
    assert captured["legend"] == "keys: 1-9 select | ↓/n=next | ↑/p=prev | u=up | s=sort | S=sort-back | d=[asc] | r=rfrsh | q=quit"


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
    assert captured["legend"] == "keys: 1-9 select | ↓/n=next | ↑/p=prev | u=up | s=sort | S=sort-back | d=[dsc] | r=rfrsh | q=quit"


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

    # File menu under default descending name sort: n (page2), p (page1), n (page2), 2 (pick file 01)
    # Requirement menu: 1 (pick first requirement)
    # Status menus: 2 (Implemented), 3 (Verified)
    # Then unwind: u (from wrapped status menu), u (from requirement menu), q (quit file menu)
    keys = iter(["n", "p", "n", "2", "1", "2", "3", "u", "u", "q"])
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