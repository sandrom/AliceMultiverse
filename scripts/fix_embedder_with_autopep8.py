#!/usr/bin/env python3
"""Use autopep8 with aggressive settings to fix embedder.py."""

import subprocess
import sys
from pathlib import Path

def fix_with_autopep8():
    """Use autopep8 with maximum aggressiveness to fix the file."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    print("Attempting to fix with autopep8...")
    
    # Try different autopep8 options
    commands = [
        # Most aggressive - fix all issues
        ['autopep8', '--in-place', '--aggressive', '--aggressive', '--max-line-length', '120', str(file_path)],
        # With experimental fixes
        ['autopep8', '--in-place', '--experimental', '--aggressive', '--aggressive', str(file_path)],
        # Target specific error codes
        ['autopep8', '--in-place', '--select', 'E1,E2,E3,E4,E5,E7,E9,W1,W2,W3,W6', str(file_path)],
    ]
    
    for i, cmd in enumerate(commands):
        print(f"\nAttempt {i+1}: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode == 0:
                print("✓ autopep8 succeeded")
                
                # Test if it compiles now
                import py_compile
                try:
                    py_compile.compile(str(file_path), doraise=True)
                    print("✓ File now compiles successfully!")
                    return True
                except py_compile.PyCompileError as e:
                    print(f"✗ Still has compilation errors: {e}")
            else:
                print(f"✗ autopep8 failed: {result.stderr}")
        except Exception as e:
            print(f"✗ Error running autopep8: {e}")
    
    return False

def manual_fix_remaining():
    """Manually fix any remaining indentation issues."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    print("\nApplying manual fixes...")
    
    with file_path.open('r') as f:
        content = f.read()
    
    # Fix specific patterns
    lines = content.split('\n')
    fixed_lines = []
    
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # If this is a docstring after a method definition, ensure proper indent
        if i > 0 and lines[i-1].strip().endswith(':') and line.strip().startswith('"""'):
            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
            if not line.startswith(' ' * (prev_indent + 4)):
                line = ' ' * (prev_indent + 4) + line.strip()
        
        # If this is code after a colon, ensure indent
        elif i > 0 and lines[i-1].strip().endswith(':') and line.strip() and not line[0].isspace():
            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
            line = ' ' * (prev_indent + 4) + line.strip()
        
        fixed_lines.append(line)
        i += 1
    
    # Write back
    with file_path.open('w') as f:
        f.write('\n'.join(fixed_lines))
    
    print("✓ Manual fixes applied")

if __name__ == "__main__":
    # First try autopep8
    success = fix_with_autopep8()
    
    if not success:
        # If autopep8 didn't work, try manual fixes
        manual_fix_remaining()
        
        # Test again
        import py_compile
        try:
            py_compile.compile("alicemultiverse/assets/metadata/embedder.py", doraise=True)
            print("\n✅ File now compiles successfully after manual fixes!")
        except py_compile.PyCompileError as e:
            print(f"\n✗ Still has errors: {e}")
            print("\nThe file may need more extensive manual editing.")