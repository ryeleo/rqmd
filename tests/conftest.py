from __future__ import annotations

from pathlib import Path

import pytest

SAMPLE_DOMAIN_TEXT = """# Demo Domain Requirement

Scope: demo requirements.

### AC-HELLO-001: Hello requirement
- **Status:** 🔧 Implemented
- Given a demo state
- When the demo runs
- Then behavior is visible.
"""


def pytest_configure(config: pytest.Config) -> None:
    """Require pytest-timeout so interactive regressions cannot hang silently."""
    plugin_manager = config.pluginmanager
    if plugin_manager.hasplugin("timeout") or plugin_manager.hasplugin("pytest_timeout"):
        return
    raise pytest.UsageError(
        "pytest-timeout is required for this test suite. Run 'uv run --extra dev pytest ...' or sync dev extras before executing pytest."
    )


@pytest.fixture
def repo_with_domain_docs(tmp_path: Path) -> Path:
    """Create a test repo with a single domain file.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Path to the test repository root.
    """
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    (domain_dir / "demo.md").write_text(SAMPLE_DOMAIN_TEXT, encoding="utf-8")
    return repo


@pytest.fixture
def two_file_repo(tmp_path: Path) -> Path:
    """Create a test repo with two domain files sharing requirement IDs.

    Args:
        tmp_path: Pytest temporary directory fixture.

    Returns:
        Path to the test repository root.
    """
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)

    first = """# First Requirement

Scope: first.

### AC-OVERLAP-001: Shared ID
- **Status:** 🔧 Implemented
"""
    second = """# Second Requirement

Scope: second.

### AC-OVERLAP-001: Shared ID
- **Status:** 💡 Proposed
"""
    (domain_dir / "first.md").write_text(first, encoding="utf-8")
    (domain_dir / "second.md").write_text(second, encoding="utf-8")
    return repo
