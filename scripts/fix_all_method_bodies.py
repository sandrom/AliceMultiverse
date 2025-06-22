#!/usr/bin/env python3
"""Fix all method body indentation issues in embedder.py."""

from pathlib import Path
import re

def fix_all_method_indentation():
    """Fix indentation for all method bodies."""
    file_path = Path("alicemultiverse/assets/metadata/embedder.py")
    
    with file_path.open('r') as f:
        lines = f.readlines()
    
    i = 0
    fixes_made = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check if line ends with colon (method, if, try, etc.)
        if line.strip() and line.strip().endswith(':'):
            # Get the indentation level
            current_indent = len(line) - len(line.lstrip())
            expected_next_indent = current_indent + 4
            
            # Check next non-empty line
            j = i + 1
            while j < len(lines) and not lines[j].strip():
                j += 1
            
            if j < len(lines):
                next_line = lines[j]
                next_indent = len(next_line) - len(next_line.lstrip())
                
                # If next line has no indentation but should have
                if next_line.strip() and next_indent < expected_next_indent:
                    # Fix the indentation
                    lines[j] = ' ' * expected_next_indent + next_line.strip() + '\n'
                    fixes_made += 1
                    print(f"Fixed line {j+1}: {next_line.strip()[:50]}...")
        
        i += 1
    
    # Write the fixed content
    with file_path.open('w') as f:
        f.writelines(lines)
    
    print(f"\nMade {fixes_made} indentation fixes")
    
    # Test compilation
    import py_compile
    error_count = 0
    max_iterations = 5
    
    while error_count < max_iterations:
        try:
            py_compile.compile(str(file_path), doraise=True)
            print("\n✅ Success! File now compiles without errors!")
            
            # Also check for duplicate methods
            check_duplicates(file_path)
            return True
        except py_compile.PyCompileError as e:
            error_count += 1
            print(f"\nIteration {error_count}: {e}")
            
            # Try to fix the specific error
            error_match = re.search(r'line (\d+)', str(e))
            if error_match:
                error_line = int(error_match.group(1))
                
                # Re-read the file
                with file_path.open('r') as f:
                    lines = f.readlines()
                
                # Try to fix the specific line
                if error_line - 1 < len(lines):
                    print(f"Attempting to fix line {error_line}...")
                    
                    # Apply another round of fixes focusing on the error area
                    for idx in range(max(0, error_line - 10), min(len(lines), error_line + 10)):
                        if lines[idx].strip().endswith(':') and idx + 1 < len(lines):
                            current_indent = len(lines[idx]) - len(lines[idx].lstrip())
                            next_line = lines[idx + 1]
                            if next_line.strip() and not next_line[0].isspace():
                                lines[idx + 1] = ' ' * (current_indent + 4) + next_line.strip() + '\n'
                                print(f"  Fixed line {idx + 2}")
                    
                    # Write back
                    with file_path.open('w') as f:
                        f.writelines(lines)
                    continue
            
            # If we can't fix it, break
            break
    
    print("\n❌ Could not fix all compilation errors")
    return False

def check_duplicates(file_path):
    """Check for duplicate method definitions."""
    with file_path.open('r') as f:
        content = f.read()
    
    # Find all method definitions
    methods = re.findall(r'def\s+(\w+)\s*\(', content)
    
    # Count occurrences
    from collections import Counter
    method_counts = Counter(methods)
    
    # Report duplicates
    duplicates = {m: count for m, count in method_counts.items() if count > 1}
    if duplicates:
        print("\n⚠️  Found duplicate method definitions:")
        for method, count in duplicates.items():
            print(f"  - {method}: {count} occurrences")
        print("\nYou should remove the duplicate definitions.")
    else:
        print("\n✓ No duplicate methods found")

if __name__ == "__main__":
    fix_all_method_indentation()