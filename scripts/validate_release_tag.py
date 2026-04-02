#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import re
from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:
    tomllib = None


TAG_PATTERN = re.compile(r"v?\d+\.\d+\.\d+(?:rc\d+)?")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate that a release tag matches project.version in pyproject.toml."
    )
    parser.add_argument(
        "tag",
        nargs="?",
        help="Release tag to validate. Falls back to RELEASE_TAG when omitted.",
    )
    parser.add_argument(
        "--pyproject",
        type=Path,
        default=Path("pyproject.toml"),
        help="Path to pyproject.toml.",
    )
    return parser.parse_args()


def resolve_tag(raw_tag: str | None) -> str:
    tag = (raw_tag or os.environ.get("RELEASE_TAG", "")).strip()
    if not tag:
        raise SystemExit("Release tag is required via argument or RELEASE_TAG environment variable")
    return tag


def load_project_version(pyproject_path: Path) -> str:
    pyproject_text = pyproject_path.read_text(encoding="utf-8")

    if tomllib is not None:
        return tomllib.loads(pyproject_text)["project"]["version"]

    project_table_match = re.search(r"(?ms)^\[project\]\s*(.*?)(^\[|\Z)", pyproject_text)
    if project_table_match is None:
        raise SystemExit(f"Could not find [project] table in {pyproject_path}")

    version_match = re.search(r'^version\s*=\s*"([^"]+)"', project_table_match.group(1), re.MULTILINE)
    if version_match is None:
        raise SystemExit(f"Could not find project.version in {pyproject_path}")

    return version_match.group(1)


def main() -> int:
    args = parse_args()
    tag = resolve_tag(args.tag)

    if not TAG_PATTERN.fullmatch(tag):
        raise SystemExit(
            f"Release tag {tag!r} must be a stable or rc semver tag like v1.2.3, 1.2.3, v1.2.3rc1, or 1.2.3rc1"
        )

    version = load_project_version(args.pyproject)
    if tag.removeprefix("v") != version:
        raise SystemExit(
            f"Release tag {tag!r} does not match project.version {version!r} in {args.pyproject}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())