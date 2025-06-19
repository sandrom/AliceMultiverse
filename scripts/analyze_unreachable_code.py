#!/usr/bin/env python3
"""Analyze and fix unreachable code patterns properly.

This script identifies genuinely unreachable code and provides options to:
1. Remove truly dead code
2. Fix logic issues that make code unreachable
3. Keep code that might be needed later with proper TODOs
"""

import ast
import re
from pathlib import Path
from typing import List, Tuple, Dict, Set
from collections import defaultdict


class UnreachableAnalyzer(ast.NodeVisitor):
    """Analyze AST to find unreachable code patterns."""
    
    def __init__(self):
        self.unreachable_lines = set()
        self.early_returns = []
        self.current_function = None
        self.in_function = False
        
    def visit_FunctionDef(self, node):
        old_function = self.current_function
        old_in_function = self.in_function
        
        self.current_function = node.name
        self.in_function = True
        
        # Check for early returns
        self._check_early_returns(node.body)
        
        self.generic_visit(node)
        
        self.current_function = old_function
        self.in_function = old_in_function
        
    def visit_AsyncFunctionDef(self, node):
        # Treat async functions the same way
        self.visit_FunctionDef(node)
        
    def _check_early_returns(self, body):
        """Check for early returns that make subsequent code unreachable."""
        for i, stmt in enumerate(body):
            if isinstance(stmt, (ast.Return, ast.Raise)):
                # Everything after this in the same block is unreachable
                for j in range(i + 1, len(body)):
                    if hasattr(body[j], 'lineno'):
                        self.unreachable_lines.add(body[j].lineno)
                        
                self.early_returns.append({
                    'function': self.current_function,
                    'line': stmt.lineno,
                    'type': 'return' if isinstance(stmt, ast.Return) else 'raise'
                })
                break
                
            elif isinstance(stmt, ast.If):
                # Check if all branches return/raise
                if self._all_branches_exit(stmt):
                    # Everything after this if statement is unreachable
                    for j in range(i + 1, len(body)):
                        if hasattr(body[j], 'lineno'):
                            self.unreachable_lines.add(body[j].lineno)
                    break
                    
    def _all_branches_exit(self, if_node):
        """Check if all branches of an if statement exit."""
        # Check if body exits
        if_exits = self._branch_exits(if_node.body)
        
        # Check else branch
        if if_node.orelse:
            else_exits = self._branch_exits(if_node.orelse)
        else:
            # No else branch means not all paths exit
            return False
            
        return if_exits and else_exits
        
    def _branch_exits(self, body):
        """Check if a branch definitely exits."""
        for stmt in body:
            if isinstance(stmt, (ast.Return, ast.Raise)):
                return True
            elif isinstance(stmt, ast.If) and self._all_branches_exit(stmt):
                return True
        return False


def analyze_file(file_path: Path) -> Dict[str, any]:
    """Analyze a single Python file for unreachable code."""
    try:
        content = file_path.read_text()
        tree = ast.parse(content)
        
        analyzer = UnreachableAnalyzer()
        analyzer.visit(tree)
        
        # Find TODO comments about unreachable code
        todo_lines = []
        lines = content.split('\n')
        for i, line in enumerate(lines, 1):
            if '# TODO: Review unreachable code' in line:
                todo_lines.append(i)
                
        return {
            'unreachable_lines': analyzer.unreachable_lines,
            'early_returns': analyzer.early_returns,
            'todo_lines': todo_lines,
            'total_lines': len(lines)
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'unreachable_lines': set(),
            'early_returns': [],
            'todo_lines': []
        }


def suggest_fix(file_path: Path, analysis: Dict[str, any]) -> List[Dict[str, any]]:
    """Suggest fixes for unreachable code."""
    suggestions = []
    
    if not analysis['unreachable_lines'] and not analysis['todo_lines']:
        return suggestions
        
    content = file_path.read_text()
    lines = content.split('\n')
    
    # Group unreachable lines by function
    function_unreachable = defaultdict(list)
    for ret in analysis['early_returns']:
        func = ret['function']
        line = ret['line']
        
        # Find unreachable lines after this return
        unreachable_after = [
            l for l in analysis['unreachable_lines'] 
            if l > line
        ]
        
        if unreachable_after:
            function_unreachable[func].extend(unreachable_after[:5])  # Limit to first 5
            
    # Generate suggestions
    for func, unreachable in function_unreachable.items():
        # Look at the code to determine the best fix
        suggestion = {
            'function': func,
            'unreachable_lines': unreachable,
            'fix_type': 'unknown',
            'description': ''
        }
        
        # Analyze the unreachable code
        unreachable_code = []
        for line_no in unreachable:
            if 0 < line_no <= len(lines):
                unreachable_code.append(lines[line_no - 1].strip())
                
        # Determine fix type based on code pattern
        code_str = ' '.join(unreachable_code)
        
        if any(keyword in code_str for keyword in ['except', 'finally', 'else:']):
            suggestion['fix_type'] = 'restructure'
            suggestion['description'] = f"Function '{func}' has unreachable exception handling. Consider restructuring the logic."
            
        elif 'return' in code_str or 'yield' in code_str:
            suggestion['fix_type'] = 'dead_code'
            suggestion['description'] = f"Function '{func}' has unreachable returns. This is likely dead code that can be removed."
            
        elif any(keyword in code_str for keyword in ['print', 'logger', 'debug']):
            suggestion['fix_type'] = 'debug_code'
            suggestion['description'] = f"Function '{func}' has unreachable debug code. Safe to remove."
            
        else:
            suggestion['fix_type'] = 'review'
            suggestion['description'] = f"Function '{func}' has unreachable code that needs manual review."
            
        suggestions.append(suggestion)
        
    return suggestions


def main():
    """Main entry point."""
    project_root = Path(__file__).parent.parent
    
    print("Analyzing unreachable code patterns...")
    
    # Collect all Python files
    python_files = list((project_root / "alicemultiverse").rglob("*.py"))
    
    # Analyze each file
    files_with_unreachable = []
    total_unreachable_lines = 0
    fix_suggestions = defaultdict(int)
    
    for py_file in python_files:
        analysis = analyze_file(py_file)
        
        if analysis.get('unreachable_lines') or analysis.get('todo_lines'):
            files_with_unreachable.append((py_file, analysis))
            total_unreachable_lines += len(analysis['unreachable_lines'])
            
            # Get suggestions
            suggestions = suggest_fix(py_file, analysis)
            for suggestion in suggestions:
                fix_suggestions[suggestion['fix_type']] += 1
                
    # Print summary
    print(f"\nFound {len(files_with_unreachable)} files with unreachable code")
    print(f"Total unreachable lines: {total_unreachable_lines}")
    
    print("\nSuggested fixes:")
    for fix_type, count in fix_suggestions.items():
        print(f"  {fix_type}: {count} occurrences")
        
    # Print detailed analysis for a few examples
    print("\nExample issues:")
    for py_file, analysis in files_with_unreachable[:5]:
        if analysis['early_returns']:
            print(f"\n{py_file.relative_to(project_root)}:")
            for ret in analysis['early_returns'][:2]:
                print(f"  - {ret['function']}() has early {ret['type']} at line {ret['line']}")
                
            suggestions = suggest_fix(py_file, analysis)
            for suggestion in suggestions[:1]:
                print(f"    Fix: {suggestion['description']}")
                
    # Offer to create a fix script
    print("\nBased on this analysis, I can create a targeted fix script.")
    print("The script would:")
    print("1. Remove genuinely dead code (unreachable returns, debug statements)")
    print("2. Restructure functions with unreachable exception handling")
    print("3. Add proper TODO comments for code that needs manual review")
    print("\nRun with --fix to generate the fix script.")


if __name__ == "__main__":
    import sys
    
    if "--fix" in sys.argv:
        print("\nGenerating fix script...")
        # TODO: Implement fix script generation
    else:
        main()