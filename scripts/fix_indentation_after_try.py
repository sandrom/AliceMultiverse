#!/usr/bin/env python3
"""Fix indentation after commenting out try blocks."""

import re
from pathlib import Path


def fix_indentation_after_try(file_path: Path) -> bool:
    """Fix indentation after commented try blocks."""
    try:
        content = file_path.read_text()
        lines = content.split('\n')
        modified = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for commented try block
            if '# TODO: Review unreachable code - try:' in line:
                indent_match = re.match(r'^(\s*)# TODO: Review unreachable code - try:', line)
                if indent_match:
                    base_indent = indent_match.group(1)
                    
                    # Find the matching except block
                    except_line = -1
                    j = i + 1
                    while j < len(lines):
                        if lines[j].strip().startswith('# TODO: Review unreachable code - except'):
                            except_line = j
                            break
                        j += 1
                    
                    if except_line > 0:
                        # Unindent all lines between try and except
                        for k in range(i + 1, except_line):
                            if lines[k].strip() and not lines[k].strip().startswith('#'):
                                # Remove one level of indentation
                                if lines[k].startswith(base_indent + '    '):
                                    lines[k] = base_indent + lines[k][len(base_indent) + 4:]
                                    modified = True
            
            i += 1
        
        if modified:
            file_path.write_text('\n'.join(lines))
            return True
            
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
    
    return False


def main():
    """Fix indentation in all affected files."""
    files_to_fix = [
        "alicemultiverse/interface/natural/base.py",
        "alicemultiverse/interface/timeline_preview_mcp.py",
        "alicemultiverse/interface/video_creation_mcp.py",
        "alicemultiverse/interface/image_presentation.py",
        "alicemultiverse/interface/structured/base.py",
        "alicemultiverse/interface/broll_suggestions_mcp.py",
        "alicemultiverse/interface/image_presentation_mcp.py",
        "alicemultiverse/core/config_dataclass.py",
        "alicemultiverse/core/metrics.py",
        "alicemultiverse/core/first_run.py",
        "alicemultiverse/core/graceful_degradation.py",
        "alicemultiverse/core/logging_middleware.py",
        "alicemultiverse/core/keys/cli.py",
        "alicemultiverse/core/file_operations.py",
        "alicemultiverse/providers/provider.py",
        "alicemultiverse/organizer/components/process_file.py",
        "alicemultiverse/organizer/resilient_organizer.py",
        "alicemultiverse/workflows/templates/template_mcp.py",
        "alicemultiverse/understanding/simple_analysis.py",
        "alicemultiverse/assets/video_hashing.py",
        "alicemultiverse/assets/hashing.py"
    ]
    
    fixed_count = 0
    for file_str in files_to_fix:
        file_path = Path(file_str)
        if file_path.exists():
            print(f"Processing {file_path}...")
            if fix_indentation_after_try(file_path):
                fixed_count += 1
                print(f"  ✓ Fixed indentation in {file_path}")
    
    print(f"\nFixed indentation in {fixed_count} files")


if __name__ == "__main__":
    main()