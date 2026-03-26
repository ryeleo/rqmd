from __future__ import annotations

from rqmd import cli


def test_RQMD_interactive_006_status_highlight_preserves_background() -> None:
    line = "status \x1b[0m text"
    patched = cli.apply_background_preserving_styles(line, "\x1b[48;5;220m")
    assert patched.startswith("\x1b[48;5;220m")
    assert "\x1b[0m\x1b[48;5;220m" in patched


def test_RQMD_interactive_006a_color_semantics() -> None:
    proposed = cli.style_status_label("💡 Proposed")
    done = cli.style_status_label("✅ Verified")
    blocked = cli.style_status_label("⛔ Blocked")
    implemented = cli.style_status_label("🔧 Implemented")

    assert "\x1b[38;5;135m" in proposed
    assert "\x1b[" in done
    assert "\x1b[" in blocked
    assert implemented == "🔧 Implemented"


def test_RQMD_interactive_006b_color_rollup_contains_bucket_styling() -> None:
    counts = {label: 0 for label, _ in cli.STATUS_ORDER}
    counts["💡 Proposed"] = 1
    counts["🔧 Implemented"] = 2
    counts["✅ Verified"] = 4
    counts["⛔ Blocked"] = 1
    rollup = cli.build_color_rollup_text(counts)

    assert "|" in rollup
    assert "\x1b[" in rollup