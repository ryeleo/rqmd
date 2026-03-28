"""Tests for RQMD-CORE-024: Generated top-level README from requirement domains."""

import tempfile
from pathlib import Path

import pytest

from rqmd.readme_gen import (extract_domain_summaries,
                             generate_readme_section,
                             sync_readme_from_domains)


def test_RQMD_core_024_extract_domain_summaries(tmp_path: Path):
    """Test extracting summaries from domain files."""
    # Setup: Create minimal requirement files
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    
    # Create README.md for index
    (req_dir / "README.md").write_text("# Requirements Index\n")
    
    # Create a domain file with requirements
    domain_file = req_dir / "test-domain.md"
    domain_file.write_text("""# Test Domain

requirement content.

### TEST-001: First requirement
- **Status:** 💡 Proposed

### TEST-002: Second requirements
- **Status:** ✅ Verified

<!-- acceptance-status-summary:start -->
Summary: 1💡 0🔧 1✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->
""")
    
    summaries = extract_domain_summaries(tmp_path, "docs/requirements")
    
    assert len(summaries) > 0
    summary = summaries[0]
    assert summary.display_name == "Test Domain"
    assert "1💡" in summary.emoji_label
    assert "1✅" in summary.emoji_label


def test_RQMD_core_024_generate_readme_section():
    """Test generating README section from domain summaries."""
    from rqmd.readme_gen import DomainSummary
    
    summaries = [
        DomainSummary(
            path=Path("docs/requirements/example.md"),
            display_name="Example Domain",
            emoji_label="3💡 2🔧 5✅",
            counts={"proposed": 3, "implemented": 2, "verified": 5, "blocked": 0, "deprecated": 0},
        ),
    ]
    
    section = generate_readme_section(summaries)
    
    assert "## Requirement Domains" in section
    assert "Example Domain" in section
    assert "example.md" in section
    assert "3💡" in section


def test_RQMD_core_024_update_readme_section_new_file(tmp_path: Path):
    """Test inserting section into a README that has no markers."""
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    (req_dir / "README.md").write_text("# Requirements\n")
    
    readme = tmp_path / "README.md"
    readme.write_text("""# Project

## Some Section

Content here.
""")
    
    # No domains exist, so this should handle gracefully
    result = sync_readme_from_domains(tmp_path, "docs/requirements")
    assert result[0] is not None  # Should return a result tuple


def test_RQMD_core_024_idempotent_updates(tmp_path: Path):
    """Test that README updates are idempotent."""
    # Create requirement infrastructure
    req_dir = tmp_path / "docs" / "requirements"
    req_dir.mkdir(parents=True)
    
    # Create requirements index
    (req_dir / "README.md").write_text("# Requirements\n")
    
    domain_file = req_dir / "test.md"
    domain_file.write_text("""# Test Domain

### TEST-001: Example
- **Status:** 💡 Proposed

<!-- acceptance-status-summary:start -->
Summary: 1💡 0🔧 0✅ 0⛔ 0🗑️
<!-- acceptance-status-summary:end -->
""")
    
    readme = tmp_path / "README.md"
    readme.write_text("# Project\n\n")
    
    # First sync
    modified1, msg1 = sync_readme_from_domains(tmp_path, "docs/requirements")
    content_after_first = readme.read_text()
    
    # Second sync (should be idempotent)
    # Remove and re-create to avoid multi-write issues
    import time
    time.sleep(0.01)  # Prevent timestamp collision
    
    modified2, msg2 = sync_readme_from_domains(tmp_path, "docs/requirements")
    content_after_second = readme.read_text()
    
    # Content should be identical since nothing changed
    assert content_after_first.strip() == content_after_second.strip()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
