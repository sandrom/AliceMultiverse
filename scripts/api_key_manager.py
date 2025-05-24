#!/usr/bin/env python3
"""
Legacy api_key_manager.py script wrapper.

This script maintains backward compatibility for users who run:
  python scripts/api_key_manager.py [args]

It forwards to the alice keys command.
"""

import sys
import os

# Add parent directory to path so we can import alicemultiverse
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from alicemultiverse.interface.main_cli import main

if __name__ == "__main__":
    # Convert api_key_manager.py usage to alice keys command
    # If no arguments, show keys help
    if len(sys.argv) == 1:
        sys.argv = ['alice', 'keys', '--help']
    else:
        # Prepend 'keys' to make it a keys subcommand
        sys.argv = ['alice', 'keys'] + sys.argv[1:]
    
    sys.exit(main(sys.argv[1:]))