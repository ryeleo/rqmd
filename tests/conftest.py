from __future__ import annotations

from pathlib import Path

import pytest

SAMPLE_DOMAIN_TEXT = """# Demo Domain Acceptance Criteria

Scope: demo criteria.

### AC-HELLO-001: Hello criterion
- **Status:** 🔧 Implemented
- Given a demo state
- When the demo runs
- Then behavior is visible.
"""


@pytest.fixture
def repo_with_domain_docs(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)
    (domain_dir / "demo.md").write_text(SAMPLE_DOMAIN_TEXT, encoding="utf-8")
    return repo


@pytest.fixture
def two_file_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    domain_dir = repo / "docs" / "requirements"
    domain_dir.mkdir(parents=True)

    first = """# First Acceptance Criteria

Scope: first.

### AC-OVERLAP-001: Shared ID
- **Status:** 🔧 Implemented
"""
    second = """# Second Acceptance Criteria

Scope: second.

### AC-OVERLAP-001: Shared ID
- **Status:** 💡 Proposed
"""
    (domain_dir / "first.md").write_text(first, encoding="utf-8")
    (domain_dir / "second.md").write_text(second, encoding="utf-8")
    return repo
