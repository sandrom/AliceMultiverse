#!/usr/bin/env python3
"""Fix performance_tracker.py by removing TODO comment prefix while preserving indentation."""

from pathlib import Path

def fix_performance_tracker():
    file_path = Path("/Users/sandro/Documents/AI/AliceMultiverse/alicemultiverse/analytics/performance_tracker.py")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for line in lines:
        # Check if this line contains the TODO comment pattern
        if "    # TODO: Review unreachable code - " in line:
            # Replace the exact pattern while preserving everything else
            # The pattern is exactly "    # TODO: Review unreachable code - "
            fixed_line = line.replace("    # TODO: Review unreachable code - ", "    ")
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)
    
    # Write back
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed {file_path}")
    print(f"Processed {len(lines)} lines")
    
    # Count how many TODO comments were removed
    todo_count = sum(1 for line in lines if "    # TODO: Review unreachable code - " in line)
    print(f"Removed {todo_count} TODO comment prefixes")

if __name__ == "__main__":
    fix_performance_tracker()