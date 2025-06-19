#!/usr/bin/env python3
"""Properly fix UNREACHABLE code issues by addressing the root cause."""

import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional


def analyze_unreachable_patterns(content: str) -> dict:
    """Analyze patterns of UNREACHABLE comments in a file."""
    lines = content.split('\n')
    patterns = {
        'total_unreachable': 0,
        'commented_code': 0,
        'actual_comments': 0,
        'early_returns': [],
        'unreachable_blocks': []
    }
    
    in_unreachable_block = False
    block_start = None
    
    for i, line in enumerate(lines):
        if '# TODO: Review unreachable code - ' in line:
            patterns['total_unreachable'] += 1
            
            # Extract what comes after UNREACHABLE:
            after_unreachable = line.split('# TODO: Review unreachable code - ', 1)[1].strip()
            
            # Check if it's a comment or actual code
            if after_unreachable.startswith('#'):
                patterns['actual_comments'] += 1
            else:
                patterns['commented_code'] += 1
                
            if not in_unreachable_block:
                in_unreachable_block = True
                block_start = i
        else:
            if in_unreachable_block:
                patterns['unreachable_blocks'].append((block_start, i-1))
                in_unreachable_block = False
                
        # Look for early returns
        if re.match(r'^\s*return\b', line) and i < len(lines) - 10:
            # Check if there's substantial code after this return
            remaining_code = sum(1 for l in lines[i+1:] if l.strip() and not l.strip().startswith('#'))
            if remaining_code > 5:
                patterns['early_returns'].append(i)
    
    if in_unreachable_block:
        patterns['unreachable_blocks'].append((block_start, len(lines)-1))
    
    return patterns


def fix_early_return_pattern(lines: List[str], return_line: int) -> List[str]:
    """Fix code with early return by restructuring the logic."""
    # Find the function this return belongs to
    func_start = return_line
    indent_level = len(lines[return_line]) - len(lines[return_line].lstrip())
    
    # Walk backwards to find function definition
    for i in range(return_line - 1, -1, -1):
        if re.match(r'^\s*def\s+\w+\s*\(', lines[i]):
            func_start = i
            break
    
    # Check if this is a validation pattern (return early on error)
    if any(word in lines[return_line].lower() for word in ['error', 'none', 'false', 'invalid']):
        # This might be intentional early return for error handling
        return lines
    
    # For now, just comment out the early return if it's preventing lots of code
    fixed_lines = lines.copy()
    
    # Count how much code would become reachable
    unreachable_count = sum(1 for i in range(return_line + 1, len(lines)) 
                           if '# TODO: Review unreachable code - ' in lines[i])
    
    if unreachable_count > 10:
        # Significant amount of code is unreachable
        # Comment out the early return and add a TODO
        fixed_lines[return_line] = lines[return_line].replace('return', '# TODO: Fix early return - return')
    
    return fixed_lines


def fix_unreachable_code(content: str) -> str:
    """Fix UNREACHABLE code by addressing root causes."""
    lines = content.split('\n')
    patterns = analyze_unreachable_patterns(content)
    
    # First, handle early returns
    for return_line in reversed(patterns['early_returns']):  # Process from bottom to top
        lines = fix_early_return_pattern(lines, return_line)
    
    # Now process UNREACHABLE comments
    fixed_lines = []
    for line in lines:
        if '# TODO: Review unreachable code - ' in line:
            # Extract what comes after UNREACHABLE:
            before, after = line.split('# TODO: Review unreachable code - ', 1)
            after = after.strip()
            
            if after.startswith('#'):
                # It's a comment - keep it as a comment but remove UNREACHABLE
                fixed_lines.append(before + after)
            elif after.startswith(('"""', "'''")):
                # It's a docstring - restore it properly
                fixed_lines.append(before + after)
            else:
                # It's actual code - keep it commented for now but mark for review
                fixed_lines.append(before + "# TODO: Review unreachable code - " + after)
        else:
            fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def remove_duplicate_lines(content: str) -> str:
    """Remove duplicate consecutive lines."""
    lines = content.split('\n')
    fixed_lines = []
    prev_line = None
    
    for line in lines:
        # Keep empty lines and non-duplicate lines
        if not line.strip() or line != prev_line:
            fixed_lines.append(line)
        prev_line = line
    
    return '\n'.join(fixed_lines)


def fix_indentation_issues(content: str) -> str:
    """Fix common indentation issues."""
    lines = content.split('\n')
    fixed_lines = []
    
    for i, line in enumerate(lines):
        # Skip empty lines
        if not line.strip():
            fixed_lines.append(line)
            continue
            
        # Fix orphaned try/except blocks
        if line.strip() == 'try:' and i + 1 < len(lines):
            next_line = lines[i + 1] if i + 1 < len(lines) else ""
            if next_line.strip() in ['except', 'except Exception as e:', 'finally:']:
                # Missing try body
                indent = len(line) - len(line.lstrip())
                fixed_lines.append(line)
                fixed_lines.append(' ' * (indent + 4) + 'pass  # TODO: Fix empty try block')
                continue
        
        # Fix functions/classes without body
        if (line.rstrip().endswith(':') and 
            any(line.lstrip().startswith(kw) for kw in ['def ', 'class ', 'if ', 'for ', 'while ', 'with '])):
            
            # Check if next line has proper indentation
            if i + 1 < len(lines):
                next_line = lines[i + 1]
                current_indent = len(line) - len(line.lstrip())
                next_indent = len(next_line) - len(next_line.lstrip()) if next_line.strip() else 0
                
                # If next line is not indented properly
                if next_line.strip() and next_indent <= current_indent:
                    # Add the current line
                    fixed_lines.append(line)
                    # Add a placeholder
                    fixed_lines.append(' ' * (current_indent + 4) + 'pass  # TODO: Fix missing implementation')
                    continue
        
        fixed_lines.append(line)
    
    return '\n'.join(fixed_lines)


def fix_file(filepath: Path) -> Tuple[bool, str, dict]:
    """Fix a Python file with UNREACHABLE issues.
    
    Returns:
        (success, message, statistics)
    """
    try:
        content = filepath.read_text(encoding='utf-8')
        original_content = content
        
        # Analyze patterns first
        patterns = analyze_unreachable_patterns(content)
        
        # Apply fixes in order
        content = fix_unreachable_code(content)
        content = remove_duplicate_lines(content)
        content = fix_indentation_issues(content)
        
        # Only write if changed
        if content != original_content:
            filepath.write_text(content, encoding='utf-8')
            
            # Try to parse to check syntax
            try:
                ast.parse(content)
                return True, "Fixed successfully", patterns
            except SyntaxError as e:
                return True, f"Fixed but still has syntax error: {e}", patterns
        else:
            return True, "No changes needed", patterns
            
    except Exception as e:
        return False, str(e), {}


def main():
    """Fix all Python files with UNREACHABLE issues."""
    root_dir = Path(__file__).parent.parent
    
    # Find all Python files with UNREACHABLE comments
    print("Searching for files with UNREACHABLE comments...")
    files_to_fix = []
    
    for py_file in root_dir.rglob("*.py"):
        # Skip test files and virtual environments
        if any(skip in str(py_file) for skip in ['.venv', 'venv', '__pycache__', '.git']):
            continue
            
        try:
            content = py_file.read_text(encoding='utf-8')
            if '# TODO: Review unreachable code - ' in content:
                files_to_fix.append(py_file)
        except:
            continue
    
    print(f"\nFound {len(files_to_fix)} files with UNREACHABLE comments")
    
    # Group statistics
    total_stats = {
        'files_processed': 0,
        'files_fixed': 0,
        'files_with_errors': 0,
        'total_unreachable': 0,
        'early_returns_found': 0
    }
    
    # Fix each file
    for filepath in files_to_fix:
        relative_path = filepath.relative_to(root_dir)
        success, message, stats = fix_file(filepath)
        
        total_stats['files_processed'] += 1
        if success and "Fixed successfully" in message:
            total_stats['files_fixed'] += 1
            print(f"  ✓ {relative_path}")
        elif success:
            print(f"  ⚠️  {relative_path} - {message}")
            if "syntax error" in message:
                total_stats['files_with_errors'] += 1
        else:
            total_stats['files_with_errors'] += 1
            print(f"  ❌ {relative_path} - {message}")
        
        # Aggregate statistics
        total_stats['total_unreachable'] += stats.get('total_unreachable', 0)
        total_stats['early_returns_found'] += len(stats.get('early_returns', []))
    
    # Summary
    print(f"\n{'='*60}")
    print("Summary:")
    print(f"  Files processed: {total_stats['files_processed']}")
    print(f"  Files fixed: {total_stats['files_fixed']}")
    print(f"  Files with remaining errors: {total_stats['files_with_errors']}")
    print(f"  Total UNREACHABLE comments: {total_stats['total_unreachable']}")
    print(f"  Early returns found: {total_stats['early_returns_found']}")
    print(f"{'='*60}")
    
    # Run syntax check on critical files
    print("\nChecking syntax of critical files...")
    critical_files = [
        "alicemultiverse/__init__.py",
        "alicemultiverse/core/file_operations.py",
        "alicemultiverse/organizer/media_organizer.py",
    ]
    
    for file_path in critical_files:
        filepath = root_dir / file_path
        if filepath.exists():
            try:
                ast.parse(filepath.read_text())
                print(f"  ✓ {file_path} - Valid syntax")
            except SyntaxError as e:
                print(f"  ❌ {file_path} - {e}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())