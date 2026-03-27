from __future__ import annotations

from pathlib import Path

import pytest
from rqmd.status_update import update_criterion_status


def test_RQMD_priority_003_update_priority_field(tmp_path: Path) -> None:
    """Test adding/updating priority field to a requirement."""
    path = tmp_path / "demo.md"
    path.write_text(
        """# Demo

### AC-DEMO-001: Feature
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )

    from rqmd.criteria_parser import find_criterion_by_id

    requirement = find_criterion_by_id(path, "AC-DEMO-001")
    assert requirement["priority"] is None

    # Add a priority
    changed = update_criterion_status(
        path,
        requirement,
        "🔧 Implemented",
        new_priority="🔴 P0 - Critical",
    )
    assert changed is True

    updated_text = path.read_text(encoding="utf-8")
    assert "- **Priority:** 🔴 P0 - Critical" in updated_text
    assert updated_text.count("**Status:**") == 1
    assert updated_text.count("**Priority:**") == 1


def test_RQMD_priority_003_update_existing_priority(tmp_path: Path) -> None:
    """Test updating an existing priority field."""
    path = tmp_path / "demo.md"
    path.write_text(
        """# Demo

### AC-DEMO-001: Feature
- **Status:** 🔧 Implemented
- **Priority:** 🟢 P3 - Low
""",
        encoding="utf-8",
    )

    from rqmd.criteria_parser import find_criterion_by_id

    requirement = find_criterion_by_id(path, "AC-DEMO-001")
    assert requirement["priority"] == "🟢 P3 - Low"

    # Change the priority
    changed = update_criterion_status(
        path,
        requirement,
        "🔧 Implemented",
        new_priority="🔴 P0 - Critical",
    )
    assert changed is True

    updated_text = path.read_text(encoding="utf-8")
    assert "- **Priority:** 🔴 P0 - Critical" in updated_text
    assert "🟢 P3 - Low" not in updated_text


def test_RQMD_priority_003_priority_update_idempotent(tmp_path: Path) -> None:
    """Test that updating to the same priority produces no diff."""
    path = tmp_path / "demo.md"
    original_text = """# Demo

### AC-DEMO-001: Feature
- **Status:** 🔧 Implemented
- **Priority:** 🔴 P0 - Critical
"""
    path.write_text(original_text, encoding="utf-8")

    from rqmd.criteria_parser import find_criterion_by_id

    requirement = find_criterion_by_id(path, "AC-DEMO-001")

    # Update to the same priority
    changed = update_criterion_status(
        path,
        requirement,
        "🔧 Implemented",
        new_priority="🔴 P0 - Critical",
    )
    assert changed is False

    # Text should be identical
    updated_text = path.read_text(encoding="utf-8")
    assert updated_text == original_text


def test_RQMD_priority_003_priority_with_blocked_reason(tmp_path: Path) -> None:
    """Test that priority works alongside blocked/deprecated reasons."""
    path = tmp_path / "demo.md"
    path.write_text(
        """# Demo

### AC-DEMO-001: Feature
- **Status:** 🔧 Implemented
- **Priority:** 🟡 P2 - Medium
""",
        encoding="utf-8",
    )

    from rqmd.criteria_parser import find_criterion_by_id

    requirement = find_criterion_by_id(path, "AC-DEMO-001")

    # Add priority and blocked reason when changing status
    changed = update_criterion_status(
        path,
        requirement,
        "⛔ Blocked",
        blocked_reason="Waiting for API",
        new_priority="🔴 P0 - Critical",
    )
    assert changed is True

    updated_text = path.read_text(encoding="utf-8")
    assert "- **Status:** ⛔ Blocked" in updated_text
    assert "**Blocked:** Waiting for API" in updated_text
    assert "- **Priority:** 🔴 P0 - Critical" in updated_text
