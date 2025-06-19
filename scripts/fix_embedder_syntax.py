#!/usr/bin/env python3
"""Fix syntax error in embedder.py caused by incomplete UNREACHABLE comments."""

from pathlib import Path

def fix_embedder():
    file_path = Path(__file__).parent.parent / "alicemultiverse/assets/metadata/embedder.py"
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # The issue is that multi-line strings starting with UNREACHABLE comment
    # are not properly commented out. Let's fix this by finding and fixing
    # these patterns.
    
    lines = content.split('\n')
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if this is an UNREACHABLE comment with a multi-line string
        if '# TODO: Review unreachable code - ' in line and '"""' in line and not line.strip().endswith('"""'):
            # This starts a multi-line string that needs to be commented
            fixed_lines.append(line)
            i += 1
            
            # Comment out all lines until we find the closing """
            while i < len(lines):
                next_line = lines[i]
                if '"""' in next_line:
                    # Found closing, comment it out
                    fixed_lines.append('    # TODO: Review unreachable code - ' + next_line.lstrip())
                    i += 1
                    break
                else:
                    # Comment out this line
                    fixed_lines.append('    # TODO: Review unreachable code - ' + next_line.lstrip())
                    i += 1
        else:
            fixed_lines.append(line)
            i += 1
    
    # Write back
    with open(file_path, 'w') as f:
        f.write('\n'.join(fixed_lines))
    
    print(f"Fixed {file_path}")

if __name__ == "__main__":
    fix_embedder()