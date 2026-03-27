from __future__ import annotations

import os
import re
import shutil
import time
from pathlib import Path

import click

from rqmd.markdown_io import iter_domain_files
from rqmd.menus import select_from_menu
from rqmd.req_parser import collect_requirements_by_status
from rqmd.status_model import coerce_status_label


def _ui_009_upper_bound_ms(project_root: Path) -> float:
    """Read the canonical UI-009 upper bound (ms) from requirement docs."""
    text = (project_root / "docs" / "requirements" / "screen-write.md").read_text(
        encoding="utf-8"
    )
    match = re.search(r"upper bound of <=\s*(\d+)ms", text)
    if not match:
        raise AssertionError("Could not find UI-009 upper bound in screen-write.md")
    return float(match.group(1))


def _write_large_corpus(repo: Path, total_requirements: int, files: int = 10) -> None:
    """Create a synthetic requirements corpus spread across domain files."""
    req_dir = repo / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    per_file = max(1, total_requirements // files)

    for file_idx in range(files):
        lines: list[str] = [
            f"# Perf Domain {file_idx}",
            "",
            f"Scope: perf-{file_idx}.",
            "",
        ]
        start = file_idx * per_file
        end = min(total_requirements, start + per_file)
        for i in range(start, end):
            status = ["💡 Proposed", "🔧 Implemented", "✅ Verified"][i % 3]
            lines.extend(
                [
                    f"### AC-PERF-{i:05d}: Fuzzy requirement token-{i % 97}",
                    f"- **Status:** {status}",
                    "- **Priority:** 🟡 P2 - Medium",
                    "- Given a baseline scenario",
                    f"- When operation {i % 11} executes",
                    "- Then observed behavior remains deterministic",
                    "",
                ]
            )

        (req_dir / f"perf-{file_idx:02d}.md").write_text(
            "\n".join(lines), encoding="utf-8"
        )


def _measure_discovery_parse_filter(repo: Path) -> tuple[float, int]:
    """Measure discovery + parse + status filter end-to-end."""
    target_status = coerce_status_label("implemented")
    start = time.perf_counter()
    domain_files = iter_domain_files(repo, "docs/requirements")
    matches = collect_requirements_by_status(repo, domain_files, target_status)
    elapsed_s = time.perf_counter() - start
    total_matches = sum(len(items) for items in matches.values())
    return elapsed_s, total_matches


def test_RQMD_portability_016_large_corpus_scaling_is_near_linear(tmp_path: Path) -> None:
    """Performance scales near-linearly from 100 -> 1000 -> 10000 requirements."""
    sizes = (100, 1000, 10000)
    timings: dict[int, float] = {}

    for size in sizes:
        repo = tmp_path / f"repo-{size}"
        _write_large_corpus(repo, total_requirements=size)
        elapsed_s, total_matches = _measure_discovery_parse_filter(repo)
        timings[size] = elapsed_s
        assert total_matches > 0

    # Guard against super-linear regressions without introducing a second
    # absolute latency budget beyond UI-009.
    ratio_1000_over_100 = timings[1000] / max(timings[100], 1e-9)
    ratio_10000_over_1000 = timings[10000] / max(timings[1000], 1e-9)

    assert ratio_1000_over_100 <= 20.0
    assert ratio_10000_over_1000 <= 20.0


def test_RQMD_portability_016_menu_render_under_80_rows_obeys_ui_009_guardrail(
    monkeypatch,
) -> None:
    """Render-sensitive menu path stays within UI-009 upper bound for <=80 rows."""
    project_root = Path(__file__).resolve().parents[1]
    ui_009_upper_bound_ms = _ui_009_upper_bound_ms(project_root)

    options = [f"Option {i:02d} - latency sample" for i in range(80)]
    right_labels = [f"[{i:02d}]" for i in range(80)]

    # Keep this deterministic and isolated from terminal IO variability.
    monkeypatch.setattr(click, "getchar", lambda: "q")
    monkeypatch.setattr(click, "echo", lambda *args, **kwargs: None)
    monkeypatch.setattr(
        shutil,
        "get_terminal_size",
        lambda fallback=(120, 24): os.terminal_size((120, 24)),
    )

    start = time.perf_counter()
    result = select_from_menu(
        "Perf Menu",
        options,
        option_right_labels=right_labels,
        show_page_indicator=False,
        allow_paging_nav=True,
    )
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert result is None
    assert elapsed_ms <= ui_009_upper_bound_ms
