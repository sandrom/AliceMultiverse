"""Compatibility wrapper for CLI entry point.

This module exists to support the entry point defined in pyproject.toml.
It simply forwards to the actual CLI implementation.
"""

from alicemultiverse.interface.main_cli import main

if __name__ == "__main__":
    main()
