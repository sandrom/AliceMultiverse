#!/usr/bin/env python3
"""Completely fix performance_tracker.py by removing TODO comments properly."""

from pathlib import Path

def fix_performance_tracker():
    file_path = Path("/Users/sandro/Documents/AI/AliceMultiverse/alicemultiverse/analytics/performance_tracker.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Replace the pattern:
    # "    # TODO: Review unreachable code - " with "    "
    # This removes the comment prefix but keeps the indentation
    content = content.replace("    # TODO: Review unreachable code - ", "    ")
    
    # Write back
    with open(file_path, 'w') as f:
        f.write(content)
    
    print(f"Fixed {file_path}")
    
    # Run ruff format to ensure proper formatting
    import subprocess
    try:
        subprocess.run(["python", "-m", "ruff", "format", str(file_path)], check=True)
        print("Formatted with ruff")
    except subprocess.CalledProcessError:
        print("Note: ruff format may have failed, but the TODO comments have been removed")

if __name__ == "__main__":
    fix_performance_tracker()