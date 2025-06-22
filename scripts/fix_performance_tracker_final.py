#!/usr/bin/env python3
"""Final fix for performance_tracker.py indentation."""

from pathlib import Path
import re

def fix_performance_tracker_final():
    file_path = Path("alicemultiverse/analytics/performance_tracker.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # Use regex to fix indentation issues
    # Pattern: lines that start with exactly 4 spaces followed by non-space content
    # that are NOT method definitions, should be indented to 8 spaces
    
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
        
        # Keep method definitions as they are
        if line.strip().startswith('def ') and line.startswith('    def '):
            fixed_lines.append(line)
            continue
        
        # Keep class definitions and module level code as they are
        if not line.startswith('    '):
            fixed_lines.append(line)
            continue
        
        # If the line starts with exactly 4 spaces and has content
        if line.startswith('    ') and len(line) > 4 and line[4] != ' ':
            # This is method content that should be indented to 8 spaces
            fixed_lines.append('    ' + line)
        else:
            # Keep as is
            fixed_lines.append(line)
    
    # Write back
    fixed_content = '\n'.join(fixed_lines)
    with open(file_path, 'w') as f:
        f.write(fixed_content)
    
    print(f"Fixed indentation in {file_path}")
    
    # Test if it compiles
    try:
        import subprocess
        result = subprocess.run(['python', '-m', 'py_compile', str(file_path)], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print("✓ File now compiles successfully!")
            
            # Try ruff format
            format_result = subprocess.run(['python', '-m', 'ruff', 'format', str(file_path)], 
                                         capture_output=True, text=True)
            if format_result.returncode == 0:
                print("✓ Successfully formatted with ruff!")
            else:
                print(f"Ruff format failed: {format_result.stderr}")
        else:
            print(f"✗ Still has syntax error: {result.stderr}")
    except Exception as e:
        print(f"Error checking compilation: {e}")

if __name__ == "__main__":
    fix_performance_tracker_final()