#!/usr/bin/env python3
"""
Legacy quality_pipeline.py script wrapper.

This script maintains backward compatibility for users who run:
  python scripts/quality_pipeline.py [args]

It forwards arguments to the main alice CLI with pipeline options.
"""

import sys
import os

# Add parent directory to path so we can import alicemultiverse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alicemultiverse.interface.main_cli import main

if __name__ == "__main__":
    # The quality_pipeline.py script was typically run with pipeline arguments
    # Forward all arguments to the main CLI
    sys.exit(main())