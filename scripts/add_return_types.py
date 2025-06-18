#!/usr/bin/env python3
"""Add return type annotations to functions missing them."""

import ast
import re
from pathlib import Path
from typing import Optional, Set, List, Tuple


class ReturnTypeFinder(ast.NodeVisitor):
    """Find functions without return type annotations."""
    
    def __init__(self):
        self.functions_without_returns: List[Tuple[str, int, str]] = []
        self.current_class = None
        
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        old_class = self.current_class
        self.current_class = node.name
        self.generic_visit(node)
        self.current_class = old_class
        
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        # Skip private methods and special methods
        if node.name.startswith('_') and not node.name.startswith('__'):
            return
            
        # Check if return type annotation exists
        if node.returns is None:
            # Try to infer return type from the function
            return_type = self._infer_return_type(node)
            full_name = f"{self.current_class}.{node.name}" if self.current_class else node.name
            self.functions_without_returns.append((full_name, node.lineno, return_type))
            
    def _infer_return_type(self, node: ast.FunctionDef) -> str:
        """Try to infer return type from function body."""
        # Look for return statements
        returns = []
        for n in ast.walk(node):
            if isinstance(n, ast.Return):
                if n.value is None:
                    returns.append("None")
                elif isinstance(n.value, ast.Constant):
                    if isinstance(n.value.value, bool):
                        returns.append("bool")
                    elif isinstance(n.value.value, int):
                        returns.append("int")
                    elif isinstance(n.value.value, str):
                        returns.append("str")
                    elif n.value.value is None:
                        returns.append("None")
                elif isinstance(n.value, ast.Dict):
                    returns.append("dict[str, Any]")
                elif isinstance(n.value, ast.List):
                    returns.append("list[Any]")
                elif isinstance(n.value, ast.Call):
                    if isinstance(n.value.func, ast.Name):
                        if n.value.func.id == "AliceResponse":
                            returns.append("AliceResponse")
                        elif n.value.func.id == "Path":
                            returns.append("Path")
                        else:
                            returns.append("Any")
                    else:
                        returns.append("Any")
                else:
                    returns.append("Any")
        
        if not returns:
            return "None"
        elif all(r == returns[0] for r in returns):
            return returns[0]
        elif "None" in returns and len(set(returns)) == 2:
            other_type = [r for r in returns if r != "None"][0]
            return f"{other_type} | None"
        else:
            return "Any"


def add_return_types_to_file(file_path: Path) -> bool:
    """Add return type annotations to a file."""
    try:
        content = file_path.read_text()
        lines = content.split('\n')
        
        # Parse the file
        tree = ast.parse(content)
        finder = ReturnTypeFinder()
        finder.visit(tree)
        
        if not finder.functions_without_returns:
            return False
        
        # Add return types
        modified = False
        for func_name, lineno, return_type in sorted(finder.functions_without_returns, 
                                                     key=lambda x: x[1], reverse=True):
            # Find the function definition line
            func_line = lines[lineno - 1]
            
            # Skip if already has return type
            if '->' in func_line:
                continue
                
            # Add return type before the colon
            match = re.match(r'(\s*def\s+\w+\s*\([^)]*\))(\s*):', func_line)
            if match:
                new_line = f"{match.group(1)} -> {return_type}{match.group(2)}:"
                lines[lineno - 1] = new_line
                modified = True
        
        if modified:
            # Check if we need to add imports
            new_imports = set()
            content = '\n'.join(lines)
            
            if ' -> Any' in content or 'dict[str, Any]' in content or 'list[Any]' in content:
                new_imports.add('Any')
            if ' -> Path' in content and 'from pathlib import Path' not in content:
                need_path_import = True
            else:
                need_path_import = False
                
            # Add imports if needed
            if new_imports:
                for i, line in enumerate(lines):
                    if line.startswith('from typing import'):
                        # Add to existing typing import
                        for imp in new_imports:
                            if imp not in line:
                                lines[i] = line.rstrip() + f', {imp}'
                        break
                else:
                    # Add new typing import
                    for i, line in enumerate(lines):
                        if line.startswith(('import ', 'from ')) or (i > 0 and not line.strip()):
                            continue
                        else:
                            if i > 0:
                                lines.insert(i, f'from typing import {", ".join(new_imports)}')
                            break
            
            file_path.write_text('\n'.join(lines))
            return True
            
        return False
        
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False


def main():
    """Add return types to functions in the codebase."""
    project_root = Path(__file__).parent.parent
    alicemultiverse_dir = project_root / "alicemultiverse"
    
    # Focus on key modules first
    priority_patterns = [
        "interface/natural/*.py",
        "interface/structured/*.py", 
        "mcp/tools/*.py",
        "core/*.py",
        "interface/*.py",
    ]
    
    fixed_count = 0
    
    for pattern in priority_patterns:
        for py_file in alicemultiverse_dir.glob(pattern):
            if py_file.name == "__init__.py":
                continue
                
            if add_return_types_to_file(py_file):
                print(f"Added return types to: {py_file.relative_to(project_root)}")
                fixed_count += 1
    
    print(f"\nTotal files updated: {fixed_count}")


if __name__ == "__main__":
    main()