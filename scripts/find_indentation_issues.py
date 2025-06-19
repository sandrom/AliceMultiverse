#!/usr/bin/env python3
"""Find Python files with indentation issues."""

import ast
import sys
from pathlib import Path
from typing import List, Tuple


def check_file_syntax(filepath: Path) -> Tuple[bool, str]:
    """Check if a Python file has valid syntax.
    
    Returns:
        (is_valid, error_message)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Try to parse the file
        ast.parse(content)
        return True, ""
    except IndentationError as e:
        return False, f"IndentationError at line {e.lineno}: {e.msg}"
    except SyntaxError as e:
        return False, f"SyntaxError at line {e.lineno}: {e.msg}"
    except Exception as e:
        return False, f"Error: {str(e)}"


def find_python_files(root_dir: Path) -> List[Path]:
    """Find all Python files in the project."""
    python_files = []
    
    # Directories to skip
    skip_dirs = {'.git', '__pycache__', '.pytest_cache', 'venv', 'env', 
                 '.venv', 'node_modules', '.tox', 'build', 'dist'}
    
    for path in root_dir.rglob('*.py'):
        # Skip if any parent directory is in skip_dirs
        if any(part in skip_dirs for part in path.parts):
            continue
        python_files.append(path)
    
    return sorted(python_files)


def main():
    """Find all Python files with syntax/indentation issues."""
    root_dir = Path(__file__).parent.parent
    python_files = find_python_files(root_dir)
    
    print(f"Checking {len(python_files)} Python files...")
    print()
    
    issues_found = []
    
    for filepath in python_files:
        is_valid, error_msg = check_file_syntax(filepath)
        if not is_valid:
            relative_path = filepath.relative_to(root_dir)
            issues_found.append((relative_path, error_msg))
    
    if issues_found:
        print(f"Found {len(issues_found)} files with issues:\n")
        for filepath, error in issues_found:
            print(f"  {filepath}")
            print(f"    {error}")
            print()
    else:
        print("No syntax or indentation issues found!")
    
    return len(issues_found)


if __name__ == "__main__":
    sys.exit(main())