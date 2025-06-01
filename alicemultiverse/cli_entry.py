#!/usr/bin/env python
"""Entry point wrapper that ensures proper module loading."""

import sys
import os
from pathlib import Path

def main():
    """Entry point that ensures the package can be imported."""
    # This helps with editable installs where the finder might not be initialized yet
    try:
        from alicemultiverse.interface.main_cli import main as cli_main
    except ImportError:
        # If import fails, try adding the package root to Python path
        package_root = Path(__file__).parent.parent
        if package_root.exists() and (package_root / "alicemultiverse").exists():
            sys.path.insert(0, str(package_root))
            from alicemultiverse.interface.main_cli import main as cli_main
        else:
            raise
    
    return cli_main()

if __name__ == "__main__":
    sys.exit(main())