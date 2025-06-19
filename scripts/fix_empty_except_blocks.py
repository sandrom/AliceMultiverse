#!/usr/bin/env python3
"""Fix empty except blocks by adding pass statements."""

import re
from pathlib import Path


def fix_empty_except_blocks(file_path: Path) -> bool:
    """Fix except blocks that have only commented content."""
    try:
        content = file_path.read_text()
        lines = content.split('\n')
        modified = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for except statement (not commented)
            if re.match(r'^(\s*)except\b', line) and '# TODO: Review unreachable code -' not in line:
                indent_match = re.match(r'^(\s*)except\b', line)
                base_indent = indent_match.group(1) if indent_match else ''
                except_indent = base_indent + '    '
                
                # Check if the next non-empty line is at the same or lower indentation
                # or is a comment
                j = i + 1
                has_body = False
                while j < len(lines):
                    if lines[j].strip():
                        # Check if it's a TODO comment
                        if lines[j].strip().startswith('# TODO: Review unreachable code -'):
                            j += 1
                            continue
                        
                        # Check indentation
                        current_indent = len(lines[j]) - len(lines[j].lstrip())
                        expected_indent = len(except_indent)
                        
                        if current_indent >= expected_indent:
                            # This line is part of the except body
                            has_body = True
                            break
                        else:
                            # This line is at the same or lower level, except body is empty
                            break
                    j += 1
                
                if not has_body:
                    # Add pass statement
                    # Find where to insert it (after all TODO comments)
                    insert_pos = i + 1
                    while insert_pos < len(lines) and lines[insert_pos].strip().startswith('# TODO: Review unreachable code -'):
                        insert_pos += 1
                    
                    lines.insert(insert_pos, except_indent + 'pass')
                    modified = True
                    print(f"  Added pass statement after except at line {i+1}")
                    i = insert_pos  # Skip the inserted line
            
            i += 1
        
        if modified:
            file_path.write_text('\n'.join(lines))
            return True
            
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
    
    return False


def main():
    """Fix all Python files with empty except blocks."""
    # Find all Python files
    python_files = list(Path("alicemultiverse").rglob("*.py"))
    
    fixed_count = 0
    for file_path in python_files:
        if fix_empty_except_blocks(file_path):
            fixed_count += 1
            print(f"Fixed {file_path}")
    
    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()