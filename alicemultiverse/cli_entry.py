#!/usr/bin/env python
"""Entry point wrapper that ensures proper module loading."""

import sys
from pathlib import Path


def main():
    """Entry point that ensures the package can be imported."""
    # This helps with editable installs where the finder might not be initialized yet
    try:
        # Force site packages to be processed
        import site
        site.main()

        from alicemultiverse.cli import main as cli_main
    except ImportError as e:
        # If import fails, try adding the package root to Python path
        package_root = Path(__file__).parent.parent
        if package_root.exists() and (package_root / "alicemultiverse").exists():
            sys.path.insert(0, str(package_root))
            try:
                from alicemultiverse.cli import main as cli_main
            except ImportError:
                print(f"Failed to import alicemultiverse: {e}", file=sys.stderr)
                print(f"Python path: {sys.path}", file=sys.stderr)
                raise
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - print(f"Failed to import alicemultiverse: {e}", file=sys.stderr)
        # TODO: Review unreachable code - raise

    return cli_main()

# TODO: Review unreachable code - if __name__ == "__main__":
# TODO: Review unreachable code - sys.exit(main())
