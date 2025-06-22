#!/usr/bin/env python3
"""Fix performance_tracker.py by removing TODO comment prefix only."""

from pathlib import Path

def fix_performance_tracker():
    file_path = Path("/Users/sandro/Documents/AI/AliceMultiverse/alicemultiverse/analytics/performance_tracker.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Simply remove the exact string "# TODO: Review unreachable code - " 
    # This preserves all original indentation exactly as it was
    content = content.replace("# TODO: Review unreachable code - ", "")
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")
    print("Removed all TODO comment prefixes while preserving original indentation")

if __name__ == "__main__":
    fix_performance_tracker()