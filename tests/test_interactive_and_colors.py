from __future__ import annotations

from pathlib import Path

from click.testing import CliRunner

from ac_cli import cli


def test_ac_acccli_interactive_002_single_key_selection(monkeypatch) -> None:
    keys = iter(["1"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu("Pick", ["A", "B"])
    assert result == 0


def test_ac_acccli_interactive_003_paging_controls(monkeypatch) -> None:
    keys = iter(["n", "1"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    options = [f"opt{i}" for i in range(12)]
    result = cli.select_from_menu("Pick", options)
    assert result == 9


def test_ac_acccli_interactive_004_nav_shortcuts(monkeypatch) -> None:
    keys = iter(["n"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu(
        "Status",
        ["A", "B"],
        allow_paging_nav=False,
        extra_keys={"n": "nav-next", "p": "nav-prev"},
    )
    assert result == "nav-next"


def test_ac_acccli_interactive_005_sort_toggle_key(monkeypatch) -> None:
    keys = iter(["s"])
    monkeypatch.setattr(cli.click, "getchar", lambda: next(keys))
    result = cli.select_from_menu("Sort", ["A"], extra_key="s", extra_key_return="toggle-sort")
    assert result == "toggle-sort"


def test_ac_acccli_interactive_006_status_highlight_preserves_background() -> None:
    line = "status \x1b[0m text"
    patched = cli.apply_background_preserving_styles(line, "\x1b[48;5;220m")
    assert patched.startswith("\x1b[48;5;220m")
    assert "\x1b[0m\x1b[48;5;220m" in patched


def test_ac_acccli_interactive_006a_color_semantics() -> None:
    proposed = cli.style_status_label("💡 Proposed")
    done = cli.style_status_label("✅ Done")
    blocked = cli.style_status_label("⛔ Blocked")
    implemented = cli.style_status_label("🔧 Implemented")

    assert "\x1b[38;5;135m" in proposed
    assert "\x1b[" in done
    assert "\x1b[" in blocked
    assert implemented == "🔧 Implemented"


def test_ac_acccli_interactive_006b_color_rollup_contains_bucket_styling() -> None:
    counts = {label: 0 for label, _ in cli.STATUS_ORDER}
    counts["💡 Proposed"] = 1
    counts["🔧 Implemented"] = 2
    counts["💻 Desktop-Verified"] = 3
    counts["✅ Done"] = 4
    counts["⛔ Blocked"] = 1
    rollup = cli.build_color_rollup_text(counts)

    assert "|" in rollup
    assert "\x1b[" in rollup


def test_ac_acccli_interactive_008_reason_prompt_helpers(monkeypatch) -> None:
    monkeypatch.setattr(cli.click, "prompt", lambda *args, **kwargs: "Some reason")
    assert cli.prompt_for_blocked_reason() == "Some reason"
    assert cli.prompt_for_deprecated_reason() == "Some reason"


def test_ac_acccli_interactive_009_positional_lookup_mode(monkeypatch, repo_with_domain_docs: Path) -> None:
    called = {"value": False}

    def fake_lookup(repo_root, domain_files, criterion_id, emoji_columns, id_prefixes):
        called["value"] = True
        assert criterion_id == "AC-HELLO-001"
        assert id_prefixes == ("AC", "R")
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


def test_ac_acccli_interactive_001_default_invokes_interactive_loop(monkeypatch, repo_with_domain_docs: Path) -> None:
    called = {"value": False}

    def fake_loop(repo_root, criteria_dir, domain_files, emoji_columns, sort_files, id_prefixes):
        called["value"] = True
        assert id_prefixes == ("AC", "R")
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
