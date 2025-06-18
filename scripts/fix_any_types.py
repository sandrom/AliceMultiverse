#!/usr/bin/env python3
"""Fix lowercase 'any' type annotations to proper 'Any' from typing."""

import os
import re
from pathlib import Path

def fix_any_in_file(file_path: Path) -> bool:
    """Fix lowercase 'any' to 'Any' in a single file."""
    try:
        content = file_path.read_text()
        original_content = content
        
        # Pattern to match lowercase 'any' in type annotations
        patterns = [
            (r'\[str, any\]', '[str, Any]'),
            (r'\[any\]', '[Any]'),
            (r': any\b', ': Any'),
            (r'-> any\b', '-> Any'),
            (r'dict\[str, any\]', 'dict[str, Any]'),
            (r'list\[any\]', 'list[Any]'),
            (r'tuple\[any\]', 'tuple[Any]'),
            (r'set\[any\]', 'set[Any]'),
        ]
        
        for pattern, replacement in patterns:
            content = re.sub(pattern, replacement, content)
        
        # Check if we need to add the import
        if content != original_content and 'from typing import' in content:
            # Check if Any is already imported
            if 'Any' not in content.split('from typing import')[1].split('\n')[0]:
                # Add Any to existing import
                content = re.sub(
                    r'(from typing import .*?)(\n)',
                    lambda m: m.group(1) + ', Any' + m.group(2) if ', Any' not in m.group(1) and ' Any' not in m.group(1) else m.group(0),
                    content,
                    count=1
                )
        elif content != original_content and 'from typing import' not in content:
            # Add new import after module docstring and other imports
            lines = content.split('\n')
            insert_pos = 0
            in_docstring = False
            docstring_char = None
            
            for i, line in enumerate(lines):
                # Skip module docstring
                if i == 0 and (line.startswith('"""') or line.startswith("'''")):
                    in_docstring = True
                    docstring_char = '"""' if line.startswith('"""') else "'''"
                    if line.count(docstring_char) >= 2:
                        in_docstring = False
                    continue
                elif in_docstring:
                    if docstring_char in line:
                        in_docstring = False
                    continue
                
                # Find position after imports
                if line.startswith('import ') or line.startswith('from '):
                    insert_pos = i + 1
                elif line and not line.startswith('#') and insert_pos > 0:
                    break
            
            if insert_pos == 0:
                # No imports found, insert after docstring
                for i, line in enumerate(lines):
                    if not line.strip() and i > 0:
                        insert_pos = i
                        break
            
            lines.insert(insert_pos, 'from typing import Any')
            content = '\n'.join(lines)
        
        if content != original_content:
            file_path.write_text(content)
            return True
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Fix all Python files in the project."""
    project_root = Path(__file__).parent.parent
    alicemultiverse_dir = project_root / "alicemultiverse"
    
    fixed_count = 0
    
    for py_file in alicemultiverse_dir.rglob("*.py"):
        if fix_any_in_file(py_file):
            print(f"Fixed: {py_file.relative_to(project_root)}")
            fixed_count += 1
    
    print(f"\nTotal files fixed: {fixed_count}")

if __name__ == "__main__":
    main()