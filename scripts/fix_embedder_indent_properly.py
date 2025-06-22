#!/usr/bin/env python3
"""Properly fix all indentation issues in embedder.py."""

import re
from pathlib import Path

def fix_all_indentation():
    """Fix all indentation issues in embedder.py comprehensively."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        content = f.read()
    
    # Fix specific known issues first
    fixes = [
        # Fix line 6 indentation
        (r'^- JPEG: EXIF and XMP for metadata storage$', '    - JPEG: EXIF and XMP for metadata storage'),
        # Fix lines after colons that need indentation
        (r'^(\s*)if hasattr\(obj, \'__dict__\'\):.*\n^return obj\.__dict__$', 
         lambda m: m.group(0).replace('\nreturn', '\n            return')),
        (r'^(\s*)return super\(\)\.default\(obj\)$', '            return super().default(obj)'),
    ]
    
    lines = content.split('\n')
    
    # Process line by line for systematic fixes
    fixed_lines = []
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
            
        # Check if previous line ends with colon
        if i > 0 and lines[i-1].strip().endswith(':'):
            # This line should be indented
            if line and not line[0].isspace():
                # Get previous line indentation
                prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                # Add proper indentation
                line = ' ' * (prev_indent + 4) + line.strip()
        
        # Special cases for known problematic lines
        if line.strip() == 'return obj.__dict__' and i > 0:
            # This should be indented under the if statement
            line = '            return obj.__dict__'
        elif line.strip() == 'return super().default(obj)' and i > 0:
            # This should be at the method level
            line = '        return super().default(obj)'
        elif line.strip().startswith('logger.error(') and i > 0:
            # Logger statements after else: need proper indentation
            if lines[i-1].strip() == 'else:':
                prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
                line = ' ' * (prev_indent + 4) + line.strip()
        elif line.strip() == '}' and i > 0:
            # Dictionary closing brace - check context
            # It's part of STANDARD_FIELDS, should be at module level
            if 'sampler' in lines[i-1]:
                line = '}'
                
        fixed_lines.append(line)
    
    # Join and write back
    fixed_content = '\n'.join(fixed_lines)
    
    with file_path.open('w') as f:
        f.write(fixed_content)
    
    print("Applied comprehensive indentation fixes")
    
    # Test compilation
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("✓ File now compiles successfully!")
        return True
    except py_compile.PyCompileError as e:
        print(f"✗ Still has compilation errors: {e}")
        # Extract line number from error
        try:
            error_match = re.search(r'line (\d+)', str(e))
            if error_match:
                error_line = int(error_match.group(1))
                print(f"\nError at line {error_line}:")
                for j in range(max(0, error_line - 3), min(len(fixed_lines), error_line + 3)):
                    prefix = ">>> " if j == error_line - 1 else "    "
                    print(f"{prefix}{j+1}: {fixed_lines[j]}")
        except:
            pass
        return False

if __name__ == "__main__":
    success = fix_all_indentation()
    if not success:
        print("\nTrying black formatter as last resort...")
        import subprocess
        try:
            # Try to format with black, ignoring parse errors if possible
            result = subprocess.run(['black', '--target-version', 'py312', 'alicemultiverse/assets/metadata/embedder.py'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ Black formatting succeeded!")
            else:
                print(f"✗ Black formatting failed: {result.stderr}")
        except Exception as e:
            print(f"✗ Could not run black: {e}")