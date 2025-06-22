#!/usr/bin/env python3
"""Fix indentation in performance_tracker.py after TODO removal."""

from pathlib import Path

def fix_indentation():
    file_path = Path("/Users/sandro/Documents/AI/AliceMultiverse/alicemultiverse/analytics/performance_tracker.py")
    
    with open(file_path, 'r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    in_class = False
    
    for i, line in enumerate(lines):
        # Check if we're entering the PerformanceTracker class
        if line.strip() == "class PerformanceTracker:":
            in_class = True
            fixed_lines.append(line)
            continue
        
        # If we're in the class and the line starts with exactly 4 spaces
        # followed by content (not more spaces), it needs fixing
        if in_class and line.startswith("    ") and len(line) > 4 and line[4] != ' ':
            # This is content that should be indented by 8 spaces
            # Check if it's a method definition
            if line.strip().startswith("def "):
                # Method definitions stay at 4 spaces
                fixed_lines.append(line)
            else:
                # Method body content needs 8 spaces
                fixed_lines.append("    " + line)  # Add 4 more spaces
        else:
            fixed_lines.append(line)
    
    # Write back
    with open(file_path, 'w') as f:
        f.writelines(fixed_lines)
    
    print(f"Fixed indentation in {file_path}")

if __name__ == "__main__":
    fix_indentation()