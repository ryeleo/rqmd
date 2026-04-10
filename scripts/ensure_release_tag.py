#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

TAG_PATTERN = re.compile(r"v?\d+\.\d+\.\d+(?:rc\d+)?")
RC_SUFFIX_PATTERN = re.compile(r"rc\d+$")
PROJECT_VERSION_PATTERN = re.compile(
    r'(?ms)(^\[project\]\s*.*?^version\s*=\s*")([^"]+)(")'
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Ensure release tag, pyproject version, and stable changelog are synchronized."
    )
    parser.add_argument(
        "tag",
        nargs="?",
        help="Release tag to ensure. Falls back to RELEASE_TAG when omitted.",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path("pyproject.toml"),
        help="Path to pyproject.toml.",
    )
    parser.add_argument(
        "--changelog",
        type=Path,
        default=Path("CHANGELOG.md"),
        help="Path to CHANGELOG.md to verify stable versioned entry exists.",
    )
    return parser.parse_args()


def resolve_tag(raw_tag: str | None) -> str:
    tag = (raw_tag or os.environ.get("RELEASE_TAG", "")).strip()
    if not tag:
        raise SystemExit("Release tag is required via argument or RELEASE_TAG environment variable")
    return tag


def ensure_pyproject_version(pyproject_path: Path, expected_version: str) -> tuple[str, bool]:
    if not pyproject_path.exists():
        raise SystemExit(f"pyproject file not found: {pyproject_path}")

    text = pyproject_path.read_text(encoding="utf-8")
    match = PROJECT_VERSION_PATTERN.search(text)
    if match is None:
        raise SystemExit(f"Could not find [project].version in {pyproject_path}")

    current_version = match.group(2)
    if current_version == expected_version:
        return current_version, False

    updated = PROJECT_VERSION_PATTERN.sub(rf"\g<1>{expected_version}\g<3>", text, count=1)
    pyproject_path.write_text(updated, encoding="utf-8")
    return current_version, True


def check_changelog_version(changelog_path: Path, version: str) -> None:
    if not changelog_path.exists():
        raise SystemExit(f"Changelog not found: {changelog_path}")
    text = changelog_path.read_text(encoding="utf-8")
    pattern = re.compile(r"^##\s+\[" + re.escape(version) + r"\]", re.MULTILINE)
    if not pattern.search(text):
        raise SystemExit(
            f"{changelog_path} does not contain a versioned entry for {version!r}.\n"
            f"Did you forget to roll [Unreleased] -> [{version}] before tagging?"
        )


def main() -> int:
    args = parse_args()
    tag = resolve_tag(args.tag)

    if not TAG_PATTERN.fullmatch(tag):
        raise SystemExit(
            f"Release tag {tag!r} must be a stable or rc semver tag like v1.2.3, 1.2.3, v1.2.3rc1, or 1.2.3rc1"
        )

    expected_version = tag.removeprefix("v")
    previous_version, updated = ensure_pyproject_version(args.pyproject, expected_version)

    if updated:
        print(
            f"Updated {args.pyproject}: project.version {previous_version!r} -> {expected_version!r}"
        )
    else:
        print(f"No change: {args.pyproject} already has project.version {expected_version!r}")

    # Stable releases must already have a rolled changelog entry.
    if not RC_SUFFIX_PATTERN.search(tag):
        check_changelog_version(args.changelog, expected_version)
        print(f"Verified changelog entry exists for {expected_version!r} in {args.changelog}")

    print(f"OK: ensured release metadata for tag {tag!r}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
