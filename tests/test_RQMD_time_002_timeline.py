"""Tests for RQMD-TIME-002: Branch-aware historical timeline."""

from __future__ import annotations

import json
from pathlib import Path

from rqmd.history import HistoryManager


def test_RQMD_time_002_branching_on_divergence(tmp_path: Path) -> None:
    """Test that branches are created when undoing and then making a new change."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    
    req_file = req_dir / "test.md"
    req_file.write_text(
        """# Test Requirements

### TEST-001: First
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    
    # Create initial history
    history_manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    history_manager.capture(command="baseline", actor="test-user")
    history_manager.capture(command="update", actor="test-user", reason="Change 1")
    history_manager.capture(command="update", actor="test-user", reason="Change 2")
    
    # Undo back to first entry
    history_manager.undo()
    history_manager.undo()
    
    # Make a different change (diverge)
    req_file.write_text(
        """# Test Requirements

### TEST-001: First
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    history_manager.capture(command="divergent-update", actor="test-user", reason="Alternate path")
    
    # Check timeline
    timeline = history_manager.get_timeline_graph()
    branches = history_manager.get_branches()
    
    # Should have multiple branches now
    assert len(branches) > 1
    assert "main" in branches
    # Should have a recovery-* branch
    recovery_branches = [b for b in branches.keys() if b.startswith("recovery-")]
    assert len(recovery_branches) > 0


def test_RQMD_time_002_timeline_graph_structure(tmp_path: Path) -> None:
    """Test that timeline graph has proper structure with parent links."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    
    req_file = req_dir / "test.md"
    req_file.write_text(
        """# Test Requirements

### TEST-001: First
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    
    history_manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    commit1 = history_manager.capture(command="baseline", actor="test-user")
    
    req_file.write_text(
        """# Test Requirements

### TEST-001: First
- **Status:** 🔧 Implemented
""",
        encoding="utf-8",
    )
    commit2 = history_manager.capture(command="update", actor="test-user", reason="Change 1")
    
    timeline = history_manager.get_timeline_graph()
    nodes = timeline["nodes"]
    
    # Check that nodes have parent tracking
    assert len(nodes) >= 2
    
    # second commit should have parent_commit field
    if commit2 in nodes:
        node2 = nodes[commit2]
        assert "parent_commit" in node2
        assert "branch" in node2
        assert "entry_index" in node2
        assert "is_current_head" in node2


def test_RQMD_time_002_get_branches_summary(tmp_path: Path) -> None:
    """Test that get_branches() returns proper branch metadata."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    
    req_file = req_dir / "test.md"
    req_file.write_text(
        """# Test Requirements

### TEST-001: First
- **Status:** 💡 Proposed
""",
        encoding="utf-8",
    )
    
    history_manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    history_manager.capture(command="baseline", actor="test-user")
    history_manager.capture(command="update", actor="test-user")
    
    branches = history_manager.get_branches()
    
    assert "main" in branches
    main_branch = branches["main"]
    assert "label" in main_branch
    assert "head" in main_branch
    assert "entry_count" in main_branch
    assert "is_current" in main_branch


def test_RQMD_time_002_timeline_node_details(tmp_path: Path) -> None:
    """Test that timeline nodes contain expected metadata."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    
    req_file = req_dir / "test.md"
    req_file.write_text("# Test\n### TEST-001: First\n- **Status:** 💡 Proposed\n", encoding="utf-8")
    
    history_manager = HistoryManager(repo_root=tmp_path, requirements_dir="docs/requirements")
    commit1 = history_manager.capture(command="baseline", actor="test-user", reason="Initial")
    
    timeline = history_manager.get_timeline_graph()
    assert timeline["entries_count"] == 1
    assert timeline["current_branch"] == "main"
    assert timeline["cursor"] == 0
    
    # Check node details
    if commit1 in timeline["nodes"]:
        node = timeline["nodes"][commit1]
        assert node["command"] == "baseline"
        assert node["actor"] == "test-user"
        assert node["reason"] == "Initial"
        assert node["is_current_head"] == True
        assert node["branch"] == "main"

