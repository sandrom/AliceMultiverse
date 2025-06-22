#!/usr/bin/env python3
"""Complete fix for all embedder.py indentation issues."""

import re
from pathlib import Path

def fix_embedder_completely():
    """Fix all remaining indentation issues in embedder.py."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    fixed_lines = []
    
    for i, line in enumerate(lines):
        stripped = line.strip()
        
        # Skip empty lines
        if not stripped:
            fixed_lines.append(line)
            continue
        
        # Check if this line needs indentation based on previous line
        if i > 0:
            prev_line = lines[i-1].strip()
            prev_indent = len(lines[i-1]) - len(lines[i-1].lstrip())
            
            # If previous line ends with colon and current line has no indent
            if prev_line.endswith(':') and line and not line[0].isspace():
                # Add proper indentation
                fixed_lines.append(' ' * (prev_indent + 4) + stripped + '\n')
                continue
            
            # Special handling for lines that should maintain same indent as previous control structure
            if stripped.startswith(('elif ', 'else:')) and i > 0:
                # Find the matching if/elif by looking backwards
                for j in range(i-1, -1, -1):
                    check_line = lines[j].strip()
                    if check_line.startswith(('if ', 'elif ')):
                        # Use same indentation as this line
                        match_indent = len(lines[j]) - len(lines[j].lstrip())
                        fixed_lines.append(' ' * match_indent + stripped + '\n')
                        break
                else:
                    # Couldn't find matching if, keep original
                    fixed_lines.append(line)
                continue
            
            # Special handling for except/finally
            if stripped.startswith(('except ', 'finally:')) and i > 0:
                # Find the matching try
                for j in range(i-1, -1, -1):
                    check_line = lines[j].strip()
                    if check_line.startswith('try:'):
                        # Use same indentation as this line
                        match_indent = len(lines[j]) - len(lines[j].lstrip())
                        fixed_lines.append(' ' * match_indent + stripped + '\n')
                        break
                else:
                    # Couldn't find matching try, keep original
                    fixed_lines.append(line)
                continue
        
        # Keep the line as is
        fixed_lines.append(line)
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(fixed_lines)
    
    print("Applied complete indentation fixes")
    
    # Now run a second pass to fix any remaining issues
    with file_path.open('r') as f:
        content = f.read()
    
    # Fix specific patterns that might still be wrong
    # Look for lines after elif/else that aren't indented properly
    pattern = re.compile(r'(elif .+:|else:)\n(\S)', re.MULTILINE)
    def fix_match(match):
        # Get the indentation of the elif/else line
        full_match = match.group(0)
        lines = full_match.split('\n')
        # Add proper indentation to the second line
        return lines[0] + '\n    ' + lines[1]
    
    # Apply fixes
    content = pattern.sub(fix_match, content)
    
    # Write back
    with file_path.open('w') as f:
        f.write(content)
    
    # Test compilation
    import py_compile
    try:
        py_compile.compile(str(file_path), doraise=True)
        print("✓ File now compiles successfully!")
        return True
    except py_compile.PyCompileError as e:
        print(f"✗ Compilation error: {e}")
        # Try to extract and show the error location
        try:
            error_match = re.search(r'line (\d+)', str(e))
            if error_match:
                error_line = int(error_match.group(1))
                lines = content.split('\n')
                print(f"\nError at line {error_line}:")
                for j in range(max(0, error_line - 3), min(len(lines), error_line + 3)):
                    prefix = ">>> " if j == error_line - 1 else "    "
                    print(f"{prefix}{j+1}: {lines[j]}")
        except:
            pass
        return False

if __name__ == "__main__":
    success = fix_embedder_completely()
    
    if success:
        print("\n✅ Successfully fixed all indentation issues!")
        print("The embedder.py file now compiles correctly.")
    else:
        print("\n⚠️  Some issues remain. Manual intervention may be needed.")