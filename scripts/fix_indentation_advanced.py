#!/usr/bin/env python3
"""Advanced indentation fixer for Python files."""

import ast
import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional


class IndentationFixer:
    """Fix various indentation issues in Python code."""
    
    def __init__(self, content: str):
        self.lines = content.split('\n')
        self.fixed_lines = []
        
    def fix(self) -> str:
        """Apply all fixes and return fixed content."""
        self._fix_docstring_indentation()
        self._fix_control_flow_indentation()
        self._fix_try_except_indentation()
        self._fix_duplicate_lines()
        self._fix_hanging_strings()
        return '\n'.join(self.fixed_lines)
    
    def _get_indent_level(self, line: str) -> int:
        """Get indentation level of a line."""
        return len(line) - len(line.lstrip())
    
    def _fix_docstring_indentation(self):
        """Fix docstring indentation after function/class definitions."""
        i = 0
        while i < len(self.lines):
            line = self.lines[i]
            self.fixed_lines.append(line)
            
            # Check for function/class definition
            if re.match(r'^\s*(def |class |async def )', line) and line.rstrip().endswith(':'):
                base_indent = self._get_indent_level(line)
                expected_indent = base_indent + 4
                
                # Look at next line
                if i + 1 < len(self.lines):
                    next_line = self.lines[i + 1]
                    next_indent = self._get_indent_level(next_line)
                    
                    # If it's a docstring at wrong indentation
                    if next_line.strip().startswith(('"""', "'''")) and next_indent <= base_indent:
                        i += 1
                        # Fix the docstring
                        quote_type = '"""' if '"""' in next_line else "'''"
                        
                        # Single line docstring
                        if next_line.count(quote_type) >= 2:
                            self.fixed_lines.append(' ' * expected_indent + next_line.strip())
                        else:
                            # Multi-line docstring
                            self.fixed_lines.append(' ' * expected_indent + next_line.strip())
                            i += 1
                            
                            while i < len(self.lines):
                                doc_line = self.lines[i]
                                self.fixed_lines.append(' ' * expected_indent + doc_line.strip())
                                if quote_type in doc_line:
                                    break
                                i += 1
            i += 1
    
    def _fix_control_flow_indentation(self):
        """Fix indentation after if/for/while/with/try/except/etc."""
        fixed = []
        i = 0
        
        while i < len(self.fixed_lines):
            line = self.fixed_lines[i]
            fixed.append(line)
            
            # Check for control flow statements
            if (line.rstrip().endswith(':') and 
                any(line.lstrip().startswith(kw) for kw in 
                    ['if ', 'elif ', 'else:', 'for ', 'while ', 'with ', 
                     'try:', 'except', 'finally:', 'match ', 'case '])):
                
                base_indent = self._get_indent_level(line)
                expected_indent = base_indent + 4
                
                # Check next line
                if i + 1 < len(self.fixed_lines):
                    next_line = self.fixed_lines[i + 1]
                    next_indent = self._get_indent_level(next_line)
                    
                    # If next line has content but wrong indentation
                    if next_line.strip() and next_indent <= base_indent:
                        i += 1
                        fixed.append(' ' * expected_indent + next_line.lstrip())
                        continue
            
            i += 1
        
        self.fixed_lines = fixed
    
    def _fix_try_except_indentation(self):
        """Fix try/except blocks with missing or incorrect indentation."""
        fixed = []
        i = 0
        
        while i < len(self.fixed_lines):
            line = self.fixed_lines[i]
            
            # Special handling for orphaned try blocks
            if line.strip() == 'try:':
                base_indent = self._get_indent_level(line)
                fixed.append(line)
                
                # Ensure next line is indented
                if i + 1 < len(self.fixed_lines):
                    next_line = self.fixed_lines[i + 1]
                    if next_line.strip() and not next_line.lstrip().startswith(('except', 'finally')):
                        if self._get_indent_level(next_line) <= base_indent:
                            i += 1
                            fixed.append(' ' * (base_indent + 4) + next_line.lstrip())
                            continue
            else:
                fixed.append(line)
            
            i += 1
        
        self.fixed_lines = fixed
    
    def _fix_duplicate_lines(self):
        """Remove duplicate consecutive lines that might have been created."""
        fixed = []
        prev_line = None
        
        for line in self.fixed_lines:
            # Skip duplicate lines unless they're empty
            if line != prev_line or not line.strip():
                fixed.append(line)
            prev_line = line
        
        self.fixed_lines = fixed
    
    def _fix_hanging_strings(self):
        """Fix unterminated strings and add closing quotes if needed."""
        in_string = False
        string_char = None
        fixed = []
        
        for line in self.fixed_lines:
            # Check for unterminated strings
            if not in_string:
                # Check for single quotes
                if line.count("'") % 2 == 1 and '\\' not in line:
                    in_string = True
                    string_char = "'"
                elif line.count('"') % 2 == 1 and '\\' not in line:
                    in_string = True
                    string_char = '"'
            else:
                # Check if string is closed
                if string_char in line:
                    in_string = False
                    string_char = None
            
            fixed.append(line)
        
        # If we ended in a string, close it
        if in_string and string_char:
            fixed.append(string_char)
        
        self.fixed_lines = fixed


def fix_file_advanced(filepath: Path) -> Tuple[bool, str]:
    """Fix a Python file with advanced indentation fixes.
    
    Returns:
        (success, error_message)
    """
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        fixer = IndentationFixer(content)
        fixed_content = fixer.fix()
        
        # Write back
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(fixed_content)
        
        # Verify it's valid Python
        try:
            ast.parse(fixed_content)
            return True, ""
        except SyntaxError as e:
            return True, f"Fixed but still has syntax error: {e}"
        
    except Exception as e:
        return False, str(e)


def main():
    """Fix remaining files with indentation issues."""
    files_to_fix = [
        "alicemultiverse/assets/hashing.py",
        "alicemultiverse/assets/perceptual_hashing.py",
        "alicemultiverse/assets/video_hashing.py",
        "alicemultiverse/cli/main.py",
        "alicemultiverse/comparison/populate.py",
        "alicemultiverse/comparison/web_server.py",
        "alicemultiverse/core/config_validation.py",
        "alicemultiverse/core/error_recovery.py",
        "alicemultiverse/core/file_operations.py",
        "alicemultiverse/core/first_run.py",
        "alicemultiverse/core/keys/cli.py",
        "alicemultiverse/core/memory_optimization.py",
        "alicemultiverse/core/metrics.py",
        "alicemultiverse/core/startup_validation.py",
        "alicemultiverse/core/structured_logging.py",
        "alicemultiverse/core/validation.py",
        "alicemultiverse/events/workflow_events.py",
        "alicemultiverse/interface/alice_api.py",
        "alicemultiverse/interface/analytics_mcp.py",
        "alicemultiverse/interface/cli_handlers.py",
        "alicemultiverse/interface/creative_models.py",
        "alicemultiverse/interface/main_cli.py",
        "alicemultiverse/interface/multi_version_export_mcp.py",
        "alicemultiverse/interface/simple_cli.py",
        "alicemultiverse/interface/timeline_nlp_mcp.py",
        "alicemultiverse/interface/timeline_preview_mcp.py",
        "alicemultiverse/interface/validation/request_validators.py",
        "alicemultiverse/interface/variation_mcp.py",
        "alicemultiverse/interface/video_providers_mcp.py",
        "alicemultiverse/mcp/base.py",
        "alicemultiverse/mcp/server.py",
        "alicemultiverse/mcp/utils/formatters.py",
        "alicemultiverse/memory/style_memory_mcp.py",
        "alicemultiverse/organizer/organization_helpers.py",
        "alicemultiverse/prompts/hooks.py",
        "alicemultiverse/prompts/project_storage.py",
        "alicemultiverse/selections/models.py",
        "alicemultiverse/understanding/custom_instructions.py",
        "alicemultiverse/understanding/providers.py",
        "alicemultiverse/workflows/base.py",
        "alicemultiverse/workflows/composition/flow_analyzer.py",
        "alicemultiverse/workflows/multi_version_export.py",
        "alicemultiverse/workflows/templates/image_enhancement.py",
        "alicemultiverse/workflows/templates/music_video.py",
        "alicemultiverse/workflows/templates/social_media.py",
        "alicemultiverse/workflows/templates/style_transfer.py",
        "alicemultiverse/workflows/templates/template_mcp.py",
        "alicemultiverse/workflows/templates/video_pipeline.py",
        "alicemultiverse/workflows/transitions/color_flow.py",
        "alicemultiverse/workflows/transitions/match_cuts.py",
        "alicemultiverse/workflows/transitions/morphing.py",
        "alicemultiverse/workflows/variations/variation_tracker.py",
        "alicemultiverse/workflows/video_export.py",
        "tests/integration/test_elevenlabs_integration.py",
        "tests/unit/test_providers.py"
    ]
    
    root_dir = Path(__file__).parent.parent
    
    print(f"Applying advanced fixes to {len(files_to_fix)} files...")
    print()
    
    success_count = 0
    warnings = []
    failed = []
    
    for relative_path in files_to_fix:
        filepath = root_dir / relative_path
        if not filepath.exists():
            print(f"  ❌ {relative_path} - File not found")
            continue
            
        success, message = fix_file_advanced(filepath)
        if success:
            if message:
                print(f"  ⚠️  {relative_path} - {message}")
                warnings.append((relative_path, message))
            else:
                print(f"  ✓ {relative_path}")
            success_count += 1
        else:
            print(f"  ❌ {relative_path} - {message}")
            failed.append((relative_path, message))
    
    print()
    print(f"Fixed: {success_count}/{len(files_to_fix)} files")
    
    if warnings:
        print(f"\nWarnings ({len(warnings)} files):")
        for path, msg in warnings:
            print(f"  {path}: {msg}")
    
    if failed:
        print(f"\nFailed ({len(failed)} files):")
        for path, msg in failed:
            print(f"  {path}: {msg}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())