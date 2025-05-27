#!/usr/bin/env python3
"""Run the asset processor service."""

import os
import sys

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))

from asset_processor.main import main

if __name__ == "__main__":
    main()
