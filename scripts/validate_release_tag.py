#!/usr/bin/env python3
"""Backward-compatible wrapper for ensure_release_tag.py."""
from ensure_release_tag import main


if __name__ == "__main__":
    raise SystemExit(main())