#!/usr/bin/env python3
"""Comprehensive fix for try-except syntax errors."""

import re
from pathlib import Path


def fix_try_except_blocks(file_path: Path) -> bool:
    """Fix try-except blocks in a file."""
    try:
        content = file_path.read_text()
        lines = content.split('\n')
        modified = False
        
        i = 0
        while i < len(lines):
            line = lines[i]
            
            # Check for uncommented try: at any indentation level
            if re.match(r'^(\s*)try:\s*$', line):
                indent_match = re.match(r'^(\s*)try:\s*$', line)
                indent = indent_match.group(1) if indent_match else ''
                
                # Look for the matching except block
                found_except = False
                j = i + 1
                while j < len(lines):
                    except_match = re.match(rf'^{re.escape(indent)}except\b', lines[j])
                    if except_match:
                        # Check if except is commented
                        if '# TODO: Review unreachable code -' in lines[j]:
                            # Comment out the try block
                            lines[i] = f'{indent}# TODO: Review unreachable code - try:'
                            modified = True
                            print(f"  Fixed try block at line {i+1}")
                        found_except = True
                        break
                    # Check if we've gone too far (found something at same or lower indent)
                    elif lines[j].strip() and not lines[j].strip().startswith('#'):
                        current_indent = len(lines[j]) - len(lines[j].lstrip())
                        if current_indent <= len(indent):
                            break
                    j += 1
                
                if not found_except:
                    # No except found, comment out the try
                    lines[i] = f'{indent}# TODO: Review unreachable code - try:'
                    modified = True
                    print(f"  Fixed orphan try block at line {i+1}")
            
            # Check for uncommented except with commented try
            elif re.match(r'^(\s*)except\b', line) and '# TODO: Review unreachable code -' not in line:
                indent_match = re.match(r'^(\s*)except\b', line)
                indent = indent_match.group(1) if indent_match else ''
                
                # Look back for the matching try
                found_try = False
                j = i - 1
                while j >= 0:
                    if re.match(rf'^{re.escape(indent)}try:\s*$', lines[j]):
                        if '# TODO: Review unreachable code -' in lines[j]:
                            # Comment out the except block and its contents
                            lines[i] = f'{indent}# TODO: Review unreachable code - {line.strip()}'
                            modified = True
                            print(f"  Fixed except block at line {i+1}")
                            
                            # Comment out the body of except block
                            k = i + 1
                            while k < len(lines):
                                if lines[k].strip() and not lines[k].strip().startswith('#'):
                                    current_indent = len(lines[k]) - len(lines[k].lstrip())
                                    if current_indent > len(indent):
                                        lines[k] = f'{indent}# TODO: Review unreachable code - {lines[k][len(indent):]}'
                                        modified = True
                                    else:
                                        break
                                k += 1
                        found_try = True
                        break
                    j -= 1
            
            i += 1
        
        if modified:
            file_path.write_text('\n'.join(lines))
            return True
            
    except Exception as e:
        print(f"  Error processing {file_path}: {e}")
    
    return False


def main():
    """Fix all Python files with try-except issues."""
    files_with_errors = [
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
        "alicemultiverse/core/ai_errors.py",
        "alicemultiverse/core/utils.py",
        "alicemultiverse/core/keys/cli.py",
        "alicemultiverse/core/file_operations.py",
        "alicemultiverse/selections/service.py",
        "alicemultiverse/providers/provider.py",
        "alicemultiverse/organizer/components/process_file.py",
        "alicemultiverse/organizer/organizer_runner.py",
        "alicemultiverse/organizer/resilient_organizer.py",
        "alicemultiverse/workflows/templates/template_mcp.py",
        "alicemultiverse/understanding/simple_analysis.py",
        "alicemultiverse/assets/video_hashing.py",
        "alicemultiverse/assets/hashing.py"
    ]
    
    fixed_count = 0
    for file_str in files_with_errors:
        file_path = Path(file_str)
        if file_path.exists():
            print(f"Processing {file_path}...")
            if fix_try_except_blocks(file_path):
                fixed_count += 1
                print(f"  ✓ Fixed {file_path}")
    
    print(f"\nFixed {fixed_count} files")


if __name__ == "__main__":
    main()