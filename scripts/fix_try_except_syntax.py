#!/usr/bin/env python3
"""Fix try-except syntax errors where except blocks were commented as UNREACHABLE."""

import re
from pathlib import Path

def fix_try_except_syntax(file_path: Path) -> bool:
    """Fix try-except blocks with commented except clauses."""
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        lines = content.split('\n')
        fixed_lines = []
        i = 0
        changes = False
        
        while i < len(lines):
            line = lines[i]
            
            # Look for patterns where we have commented except blocks after try
            # Check if we're at a line that might end a try block
            if i > 0 and lines[i-1].strip() and not line.strip():
                # Check if next line is a commented UNREACHABLE except
                if i + 1 < len(lines) and '# TODO: Review unreachable code - ' in lines[i+1] and 'except' in lines[i+1]:
                    # We found a problematic pattern
                    fixed_lines.append(line)  # Keep the blank line
                    i += 1
                    
                    # Process all the UNREACHABLE except/finally blocks
                    while i < len(lines) and ('# TODO: Review unreachable code - ' in lines[i]):
                        # Remove the UNREACHABLE comment
                        uncommented = lines[i].replace('# TODO: Review unreachable code - ', '')
                        if uncommented.strip():
                            fixed_lines.append(uncommented)
                        else:
                            fixed_lines.append(lines[i])
                        i += 1
                        changes = True
                    continue
                    
            fixed_lines.append(line)
            i += 1
        
        if changes:
            with open(file_path, 'w') as f:
                f.write('\n'.join(fixed_lines))
            return True
            
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
    
    return False

def main():
    """Fix all Python files with try-except syntax errors."""
    project_root = Path(__file__).parent.parent
    
    # Files that are known to have this issue
    problem_files = [
        'alicemultiverse/assets/perceptual_hashing.py',
        'alicemultiverse/assets/video_hashing.py',
        'alicemultiverse/assets/processing/analyzer.py',
        'alicemultiverse/assets/quality/brisque.py',
        'alicemultiverse/cache/cache_adapter.py',
        'alicemultiverse/understanding/enhanced_media_metadata.py',
        'alicemultiverse/organizer/media_organizer.py',
    ]
    
    fixed_count = 0
    for file_path in problem_files:
        full_path = project_root / file_path
        if full_path.exists():
            if fix_try_except_syntax(full_path):
                print(f"Fixed: {file_path}")
                fixed_count += 1
        else:
            print(f"File not found: {file_path}")
    
    print(f"\nFixed {fixed_count} files")

if __name__ == "__main__":
    main()