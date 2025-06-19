#!/usr/bin/env python3
"""Find all Python files with potential syntax errors."""

import subprocess
from pathlib import Path

def find_syntax_errors():
    """Run mypy to find all syntax errors."""
    project_root = Path(__file__).parent.parent
    
    # Keep running mypy until no more syntax errors
    while True:
        result = subprocess.run(
            ["python", "-m", "mypy", "alicemultiverse"],
            capture_output=True,
            text=True,
            cwd=project_root
        )
        
        if "error:" not in result.stderr:
            print("No more syntax errors found!")
            break
            
        # Find the error
        for line in result.stderr.split('\n'):
            if 'error:' in line and 'syntax' in line:
                # Extract file and line number
                parts = line.split(':')
                if len(parts) >= 2:
                    file_path = parts[0]
                    line_num = parts[1]
                    print(f"\nFound syntax error in {file_path} at line {line_num}")
                    
                    # Show context
                    full_path = project_root / file_path
                    if full_path.exists():
                        with open(full_path, 'r') as f:
                            lines = f.readlines()
                            line_idx = int(line_num) - 1
                            
                            # Show 5 lines before and after
                            start = max(0, line_idx - 5)
                            end = min(len(lines), line_idx + 6)
                            
                            print("Context:")
                            for i in range(start, end):
                                marker = ">>>" if i == line_idx else "   "
                                print(f"{marker} {i+1:4d}: {lines[i].rstrip()}")
                    break
        
        # Ask user to fix manually
        input("\nPress Enter after fixing the error to continue...")

if __name__ == "__main__":
    find_syntax_errors()