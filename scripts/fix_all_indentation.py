#\!/usr/bin/env python3
"""Fix all indentation issues in embedder.py systematically."""

from pathlib import Path

def fix_indentation():
    """Fix all indentation issues by ensuring proper nesting."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    class_level = 0
    method_level = 4
    in_method = False
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Empty lines - keep as is
        if not stripped:
            fixed_lines.append(line)
            continue
        
        # Class definition
        if stripped.startswith('class ') and not line.startswith(' '):
            class_level = 0
            in_method = False
            fixed_lines.append(line)
            continue
        
        # Method definition inside class
        if line.strip().startswith('def ') and '    def ' in line:
            method_level = 4
            in_method = True
            fixed_lines.append(line)
            continue
        
        # If we're inside a method and the line has no indentation
        if in_method and line[0] not in ' \t' and not line.startswith('class'):
            # This line should be indented to method body level (8 spaces)
            fixed_lines.append('        ' + line)
        else:
            fixed_lines.append(line)
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print("Fixed basic indentation")
    
    # Now try black again
    import subprocess
    try:
        result = subprocess.run(['black', str(file_path)], capture_output=True, text=True)
        if result.returncode == 0:
            print("Successfully formatted with black")
        else:
            print(f"Black error: {result.stderr}")
            
            # Manual fixes for common patterns
            with file_path.open('r') as f:
                content = f.read()
            
            # Fix specific patterns
            import re
            
            # Fix lines that should be indented after 'try:'
            content = re.sub(r'(\n    try:\n)    ([^\s])', r'\1        \2', content)
            
            # Fix lines that should be indented after 'if'
            content = re.sub(r'(\n    if [^:]+:\n)    ([^\s])', r'\1        \2', content)
            
            # Fix lines that should be indented after 'for'
            content = re.sub(r'(\n    for [^:]+:\n)    ([^\s])', r'\1        \2', content)
            
            # Write back
            with file_path.open('w') as f:
                f.write(content)
            
            # Try black again
            subprocess.run(['black', str(file_path)], check=True)
            print("Fixed with manual patterns and black")
            
    except subprocess.CalledProcessError as e:
        print(f"Failed to format: {e}")
        return False
    
    # Check for duplicate methods
    with file_path.open('r') as f:
        content = f.read()
    
    duplicates = content.count('def _create_xmp_from_metadata')
    if duplicates > 1:
        print(f"\nFound {duplicates} _create_xmp_from_metadata methods - removing duplicates")
        remove_duplicate_methods(file_path)
    
    return True

def remove_duplicate_methods(file_path):
    """Remove duplicate method definitions."""
    with file_path.open('r') as f:
        lines = f.readlines()
    
    # Find all occurrences
    method_positions = []
    for i, line in enumerate(lines):
        if 'def _create_xmp_from_metadata(self' in line:
            method_positions.append(i)
    
    if len(method_positions) > 1:
        # Keep first, remove others
        for pos in reversed(method_positions[1:]):
            # Find end of method
            end_pos = len(lines)
            method_indent = len(lines[pos]) - len(lines[pos].lstrip())
            
            for j in range(pos + 1, len(lines)):
                line_indent = len(lines[j]) - len(lines[j].lstrip())
                if lines[j].strip() and line_indent <= method_indent:
                    end_pos = j
                    break
            
            # Remove duplicate
            del lines[pos:end_pos]
            print(f"Removed duplicate method from line {pos + 1}")
        
        # Write back
        with file_path.open('w') as f:
            f.writelines(lines)
        
        # Format again
        import subprocess
        subprocess.run(['black', str(file_path)], check=True)

if __name__ == "__main__":
    fix_indentation()
