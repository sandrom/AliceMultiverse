#!/usr/bin/env python3
"""
Direct command-line interface for AliceMultiverse.

Run directly with: python alice.py --help
"""

import sys
from pathlib import Path

# Add parent directory to path for direct script execution
sys.path.insert(0, str(Path(__file__).parent.parent))

from alicemultiverse.interface.simple_cli import main

if __name__ == "__main__":
    sys.exit(main())
