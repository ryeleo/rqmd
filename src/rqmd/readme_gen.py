"""Generate and maintain README sections from requirement documents.

This module provides functionality for RQMD-CORE-024:
- Read domain files and extract status summary information
- Generate requirement index sections for top-level README
- Keep sections between markers (idempotent)
- Support both manual invocation and automatic updates
"""

from __future__ import annotations

from pathlib import Path
from typing import NamedTuple

from .markdown_io import display_name_from_h1, iter_domain_files
from .summary import count_statuses


class DomainSummary(NamedTuple):
    """Summary of domain file status."""
    path: Path
    display_name: str
    emoji_label: str  
    counts: dict[str, int]


def extract_domain_summaries(repo_root: Path, criteria_dir: str, id_prefixes: tuple[str, ...] = ("AC", "R", "RQMD")) -> list[DomainSummary]:
    """Extract summary information from all domain files.
    
    Args:
        repo_root: Project root path
        criteria_dir: Path to requirements directory
        id_prefixes: Allowed ID prefixes
        
    Returns:
        List of DomainSummary objects in file order
    """
    summaries = []
    
    for path in iter_domain_files(repo_root, criteria_dir):
        content = path.read_text(encoding="utf-8")
        counts = count_statuses(content)
        label = display_name_from_h1(path)
        
        # Build emoji summary: P I Ver Blk Dep
        # Note: count_statuses returns counts with full label as key like "💡 Proposed"
        status_order = [
            ("💡 Proposed", "💡"),
            ("🔧 Implemented", "🔧"),
            ("✅ Verified", "✅"),
            ("⛔ Blocked", "⛔"),
            ("🗑️ Deprecated", "🗑️"),
        ]
        
        emoji_parts = []
        for full_label, emoji in status_order:
            count = counts.get(full_label, 0)
            if count > 0:
                emoji_parts.append(f"{count}{emoji}")
        
        emoji_label = " ".join(emoji_parts) if emoji_parts else "No requirements"
        
        summaries.append(
            DomainSummary(
                path=path,
                display_name=label or path.stem,
                emoji_label=emoji_label,
                counts=counts,
            )
        )
    
    return summaries


def generate_readme_section(summaries: list[DomainSummary]) -> str:
    """Generate README requirement index section.
    
    Args:
        summaries: List of domain summaries
        
    Returns:
        Markdown text for README section
    """
    if not summaries:
        return "No requirement documents found."
    
    lines = ["## Requirement Documents", ""]
    
    for summary in summaries:
        relative_path = summary.path.relative_to(summary.path.parent.parent)
        lines.append(f"- **{summary.display_name}** ({relative_path.name}): {summary.emoji_label}")
    
    lines.append("")
    return "\n".join(lines)


def update_readme_section(readme_path: Path, domain_section: str) -> bool:
    """Update or insert requirement index section in README.
    
    Keeps content between markers:
    <!-- requirement-domains-start -->
    <!-- requirement-domains-end -->
    
    Args:
        readme_path: Path to README.md
        domain_section: Generated section content
        
    Returns:
        True if file was modified, False if no changes needed
    """
    start_marker = "<!-- requirement-domains-start -->"
    end_marker = "<!-- requirement-domains-end -->"
    
    if not readme_path.exists():
        return False
    
    content = readme_path.read_text(encoding="utf-8")
    
    # Build new section with markers
    new_section = f"{start_marker}\n{domain_section}{end_marker}\n"
    
    # Check if markers exist
    if start_marker in content and end_marker in content:
        # Replace existing section
        start_idx = content.index(start_marker)
        end_idx = content.index(end_marker) + len(end_marker)
        new_content = content[:start_idx] + new_section + content[end_idx:]
    else:
        # Append new section before first H2 section, or at end
        lines = content.split("\n")
        insert_idx = len(lines)
        
        for i, line in enumerate(lines):
            if line.startswith("## ") and i > 0:
                insert_idx = i
                break
        
        lines.insert(insert_idx, "")
        lines.insert(insert_idx, new_section)
        new_content = "\n".join(lines)
    
    # Check if content actually changed
    if new_content == content:
        return False
    
    # Write updated content
    readme_path.write_text(new_content, encoding="utf-8")
    return True


def sync_readme_from_domains(repo_root: Path, criteria_dir: str = "docs/requirements") -> tuple[bool, str]:
    """Synchronize README requirement index from domain files.
    
    Args:
        repo_root: Project root path
        criteria_dir: Path to requirements directory
        
    Returns:
        Tuple of (was_modified, message)
    """
    readme_path = repo_root / "README.md"
    
    summaries = extract_domain_summaries(repo_root, criteria_dir)
    
    if not summaries:
        return False, "No requirement documents found"
    
    section = generate_readme_section(summaries)
    modified = update_readme_section(readme_path, section)
    
    message = f"README sync: {len(summaries)} requirement docs, {'updated' if modified else 'no changes'}"
    return modified, message
