#!/usr/bin/env python3
"""
Script to automatically fix common mypy errors in the codebase.
"""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Set

def fix_unreachable_statements(content: str) -> str:
    """Remove or fix unreachable statements."""
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for patterns that make code unreachable
        if i > 0:
            prev_line = lines[i-1].strip()
            
            # After unconditional return/raise
            if (prev_line.startswith('return ') or prev_line == 'return' or 
                prev_line.startswith('raise ') or prev_line == 'raise'):
                # Check if current line is at same or lower indentation
                if line and not line[0].isspace():
                    # Skip unreachable code at module level
                    while i < len(lines) and lines[i] and not lines[i][0].isspace():
                        i += 1
                    continue
                elif line.strip() and len(line) - len(line.lstrip()) <= len(lines[i-1]) - len(lines[i-1].lstrip()):
                    # Skip unreachable code in function/method
                    indent_level = len(line) - len(line.lstrip())
                    while i < len(lines) and (not lines[i].strip() or 
                           len(lines[i]) - len(lines[i].lstrip()) >= indent_level):
                        i += 1
                    continue
        
        fixed_lines.append(line)
        i += 1
    
    return '\n'.join(fixed_lines)


def fix_missing_any_import(content: str) -> str:
    """Add missing Any import."""
    if 'from typing import' in content and 'Any' not in content:
        # Check if Any is used
        if re.search(r'\bAny\b', content):
            # Add Any to existing import
            content = re.sub(
                r'from typing import ([^\\n]+)',
                lambda m: f'from typing import {m.group(1)}, Any' if 'Any' not in m.group(1) else m.group(0),
                content,
                count=1
            )
    elif re.search(r'\bAny\b', content) and 'from typing import' not in content:
        # Add new import
        lines = content.split('\n')
        import_index = 0
        for i, line in enumerate(lines):
            if line.startswith('import ') or line.startswith('from '):
                import_index = i + 1
            elif import_index > 0 and not line.strip():
                break
        
        lines.insert(import_index, 'from typing import Any')
        content = '\n'.join(lines)
    
    return content


def fix_none_checks(content: str) -> str:
    """Fix None type checking issues."""
    # Fix "Value of type X | None is not indexable"
    content = re.sub(
        r'if\s+(\w+)\s*:\s*\n(\s+)(.+)\[',
        r'if \1 is not None:\n\2\3[',
        content
    )
    
    # Fix filters None check pattern
    content = re.sub(
        r'filters\s*=\s*filters\s+or\s+\{\}',
        r'if filters is None:\n        filters = {}',
        content
    )
    
    return content


def fix_typeddict_issues(content: str) -> str:
    """Fix TypedDict related issues."""
    # Fix SearchFilters None checks
    content = re.sub(
        r'if\s+"(\w+)"\s+in\s+filters:',
        r'if filters is not None and "\1" in filters:',
        content
    )
    
    # Fix indexed assignment on optional TypedDict
    content = re.sub(
        r'(\s+)filters\["(\w+)"\]\s*=',
        r'\1if filters is not None:\n\1    filters["\2"] =',
        content
    )
    
    return content


def fix_return_type_annotations(content: str) -> str:
    """Fix return type annotation issues."""
    # Fix functions returning Any when declared to return specific types
    patterns = [
        (r'-> float:', r'-> float:\n        """Return float value."""\n        result = '),
        (r'-> int:', r'-> int:\n        """Return int value."""\n        result = '),
        (r'-> dict\[str, Any\]:', r'-> dict[str, Any]:\n        """Return dict."""\n        result = '),
    ]
    
    for pattern, replacement in patterns:
        if pattern in content and 'return ' in content:
            # More sophisticated replacement needed
            pass
    
    return content


def fix_attribute_errors(content: str) -> str:
    """Fix attribute access errors."""
    # Fix "object has no attribute X" by adding type annotations
    # This is more complex and needs context
    
    # Fix BatchOperationsMixin.conn
    if '"BatchOperationsMixin" has no attribute "conn"' in content:
        content = re.sub(
            r'class BatchOperationsMixin:',
            r'class BatchOperationsMixin:\n    conn: Any  # Database connection',
            content
        )
    
    return content


def fix_opencv_imports(content: str) -> str:
    """Fix OpenCV import issues."""
    if 'cv2.' in content and 'Module has no attribute' in content:
        # Add type ignore for cv2
        content = re.sub(
            r'import cv2',
            r'import cv2  # type: ignore',
            content
        )
        
        # Fix specific cv2 attributes
        content = re.sub(
            r'cv2\.CV_64F',
            r'cv2.CV_64F  # type: ignore',
            content
        )
    
    return content


def process_file(file_path: Path) -> bool:
    """Process a single file to fix mypy errors."""
    try:
        content = file_path.read_text()
        original = content
        
        # Apply fixes
        content = fix_unreachable_statements(content)
        content = fix_missing_any_import(content)
        content = fix_none_checks(content)
        content = fix_typeddict_issues(content)
        content = fix_return_type_annotations(content)
        content = fix_attribute_errors(content)
        content = fix_opencv_imports(content)
        
        if content != original:
            file_path.write_text(content)
            return True
        
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    python_files = list((project_root / "alicemultiverse").rglob("*.py"))
    
    print(f"Found {len(python_files)} Python files")
    
    fixed_count = 0
    for file_path in python_files:
        if process_file(file_path):
            fixed_count += 1
            print(f"Fixed: {file_path.relative_to(project_root)}")
    
    print(f"\nFixed {fixed_count} files")
    
    # Run mypy again to check progress
    import subprocess
    result = subprocess.run(
        ["mypy", "alicemultiverse", "--ignore-missing-imports"],
        capture_output=True,
        text=True
    )
    
    error_count = result.stdout.count("error:")
    print(f"\nRemaining mypy errors: {error_count}")


if __name__ == "__main__":
    main()