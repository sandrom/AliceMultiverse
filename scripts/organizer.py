#!/usr/bin/env python3
"""
Legacy organizer.py script wrapper.

This script maintains backward compatibility for users who run:
  python scripts/organizer.py [args]

It simply forwards all arguments to the main alice CLI.
"""

import sys
import os

# Add parent directory to path so we can import alicemultiverse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alicemultiverse.interface.main_cli import main

if __name__ == "__main__":
    # Pass all arguments directly to the CLI
    sys.exit(main())