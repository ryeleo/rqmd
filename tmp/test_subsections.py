#!/usr/bin/env python3
"""Quick test of H2 subsection parsing."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from rqmd.req_parser import parse_requirements

# Test parsing a requirements file
test_file = Path(__file__).parent.parent / "docs" / "requirements" / "core-engine.md"

print(f"Testing subsection parsing on: {test_file}")
print()

if not test_file.exists():
    print(f"❌ File not found: {test_file}")
    sys.exit(1)

requirements = parse_requirements(test_file)
print(f"✅ Parsed {len(requirements)} requirements")
print()

# Check for sub_domain field
print("Checking for sub_domain field in requirements:")
for req in requirements[:5]:  # Show first 5
    sub_domain = req.get("sub_domain")
    status = req.get("status", "NO STATUS")
    print(f"  {req['id']}: sub_domain={repr(sub_domain)} | status={status}")

# Check if any have subsections
has_sub_domain = [r for r in requirements if r.get("sub_domain") is not None]
print()
print(f"Requirements with sub_domain set: {len(has_sub_domain)} / {len(requirements)}")
if has_sub_domain:
    print("Examples:")
    for req in has_sub_domain[:3]:
        print(f"  {req['id']} -> {req['sub_domain']}")

# Verify field exists in all requirements
all_have_field = all("sub_domain" in r for r in requirements)
print(f"All requirements have 'sub_domain' field: {all_have_field}")

print()
print("✅ Test passed!")
