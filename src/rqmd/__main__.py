"""Entry point for the rqmd CLI package.

This module serves as the entry point when the rqmd package is invoked as a module
via `python -m rqmd`. It simply delegates to the main CLI function.
"""

from .cli import main

if __name__ == "__main__":
    main()
