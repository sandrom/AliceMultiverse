#!/usr/bin/env python3
"""Fix commented functions in cli_parser.py."""

import re
from pathlib import Path

def fix_cli_parser():
    file_path = Path("alicemultiverse/interface/cli_parser.py")
    
    content = file_path.read_text()
    
    # Replace all commented lines, removing the comment prefix
    fixed_content = re.sub(
        r'^# TODO: Review unreachable code - (.*)$',
        r'\1',
        content,
        flags=re.MULTILINE
    )
    
    file_path.write_text(fixed_content)
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    fix_cli_parser()