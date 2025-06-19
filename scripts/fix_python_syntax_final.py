#!/usr/bin/env python3
"""Final comprehensive fix for Python syntax issues."""

import re
import sys
from pathlib import Path
from typing import List, Tuple, Optional


class PythonSyntaxFixer:
    """Comprehensive Python syntax fixer."""
    
    def __init__(self, filepath: Path):
        self.filepath = filepath
        self.content = filepath.read_text(encoding='utf-8')
        self.lines = self.content.split('\n')
        
    def fix(self) -> bool:
        """Apply all fixes and save the file."""
        try:
            # Apply fixes in order
            self._remove_duplicate_code_lines()
            self._fix_try_except_blocks()
            self._fix_missing_indentation()
            self._fix_unterminated_strings()
            self._fix_invalid_syntax()
            
            # Save the fixed content
            self.filepath.write_text('\n'.join(self.lines), encoding='utf-8')
            return True
        except Exception as e:
            print(f"Error fixing {self.filepath}: {e}")
            return False
    
    def _remove_duplicate_code_lines(self):
        """Remove consecutive duplicate code lines (but keep empty lines)."""
        fixed = []
        prev_line = None
        
        for line in self.lines:
            # Keep empty lines or non-duplicate lines
            if not line.strip() or line != prev_line:
                fixed.append(line)
            # Skip duplicate lines unless they're control flow
            elif not any(line.lstrip().startswith(kw) for kw in 
                        ['if ', 'elif ', 'else:', 'for ', 'while ', 'except', 'finally:']):
                continue
            else:
                fixed.append(line)
            
            prev_line = line
        
        self.lines = fixed
    
    def _fix_try_except_blocks(self):
        """Fix orphaned try blocks without except/finally."""
        fixed = []
        i = 0
        
        while i < len(self.lines):
            line = self.lines[i]
            fixed.append(line)
            
            # Found a try block
            if line.strip() == 'try:' or (line.lstrip().startswith('try:') and line.rstrip().endswith(':')):
                indent = len(line) - len(line.lstrip())
                
                # Look for the body and check if except/finally exists
                j = i + 1
                has_except_finally = False
                while j < len(self.lines):
                    next_line = self.lines[j]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    # Found except or finally at correct indentation
                    if (next_line.strip() and next_indent == indent and 
                        any(next_line.lstrip().startswith(kw) for kw in ['except', 'finally'])):
                        has_except_finally = True
                        break
                    
                    # If we've exited the try block without finding except/finally
                    if next_line.strip() and next_indent <= indent:
                        break
                    
                    j += 1
                
                # If no except/finally found, add a generic except
                if not has_except_finally:
                    # Add all lines up to where except should be
                    while i + 1 < j:
                        i += 1
                        fixed.append(self.lines[i])
                    
                    # Add generic except block
                    fixed.append(' ' * indent + 'except Exception as e:')
                    fixed.append(' ' * (indent + 4) + 'logger.error(f"Error: {e}")')
                    fixed.append(' ' * (indent + 4) + 'raise')
            
            i += 1
        
        self.lines = fixed
    
    def _fix_missing_indentation(self):
        """Fix missing indentation after colons."""
        fixed = []
        i = 0
        
        while i < len(self.lines):
            line = self.lines[i]
            fixed.append(line)
            
            # Check if line ends with colon
            if line.rstrip().endswith(':') and line.strip():
                indent = len(line) - len(line.lstrip())
                expected_indent = indent + 4
                
                # Check next line
                if i + 1 < len(self.lines):
                    next_line = self.lines[i + 1]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    # If next line has content but wrong indentation
                    if next_line.strip() and next_indent <= indent:
                        # Don't indent if it's except/finally/elif/else
                        if not any(next_line.lstrip().startswith(kw) for kw in 
                                  ['except', 'finally:', 'elif ', 'else:']):
                            i += 1
                            fixed.append(' ' * expected_indent + next_line.lstrip())
                            continue
            
            i += 1
        
        self.lines = fixed
    
    def _fix_unterminated_strings(self):
        """Fix unterminated string literals."""
        fixed = []
        in_string = False
        string_char = None
        triple_quote = False
        
        for line in self.lines:
            # Handle triple quotes
            if '"""' in line or "'''" in line:
                # Count occurrences
                double_count = line.count('"""')
                single_count = line.count("'''")
                
                if double_count % 2 == 1:
                    if not in_string:
                        in_string = True
                        string_char = '"""'
                        triple_quote = True
                    else:
                        in_string = False
                        string_char = None
                        triple_quote = False
                
                if single_count % 2 == 1:
                    if not in_string:
                        in_string = True
                        string_char = "'''"
                        triple_quote = True
                    else:
                        in_string = False
                        string_char = None
                        triple_quote = False
            
            # Handle single/double quotes (if not in triple quote)
            elif not triple_quote:
                # Simple check for unterminated strings
                if line.strip() and not in_string:
                    # Check for unterminated single quote
                    if line.count("'") % 2 == 1 and "\\\\" not in line and "\\'" not in line:
                        line += "'"
                    # Check for unterminated double quote
                    elif line.count('"') % 2 == 1 and "\\\\" not in line and '\\"' not in line:
                        line += '"'
            
            fixed.append(line)
        
        # Close any unclosed triple quotes
        if in_string and triple_quote:
            fixed.append(string_char)
        
        self.lines = fixed
    
    def _fix_invalid_syntax(self):
        """Fix other invalid syntax patterns."""
        fixed = []
        
        for line in self.lines:
            # Fix invalid decimal literals (e.g., 0.5.0 -> 0.5)
            line = re.sub(r'(\d+\.\d+)\.\d+', r'\1', line)
            
            # Fix mismatched brackets
            # This is complex, so just ensure counts match
            if line.count('[') != line.count(']'):
                # Try to fix by adding missing bracket at end
                if line.count('[') > line.count(']'):
                    line += ']' * (line.count('[') - line.count(']'))
                else:
                    line = '[' * (line.count(']') - line.count('[')) + line
            
            fixed.append(line)
        
        self.lines = fixed


def main():
    """Fix all Python files with syntax issues."""
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
    
    print(f"Applying comprehensive fixes to {len(files_to_fix)} files...")
    print()
    
    success_count = 0
    
    for relative_path in files_to_fix:
        filepath = root_dir / relative_path
        if not filepath.exists():
            print(f"  ❌ {relative_path} - File not found")
            continue
        
        fixer = PythonSyntaxFixer(filepath)
        if fixer.fix():
            print(f"  ✓ {relative_path}")
            success_count += 1
        else:
            print(f"  ❌ {relative_path} - Failed to fix")
    
    print()
    print(f"Successfully fixed: {success_count}/{len(files_to_fix)} files")
    
    # Now run syntax check
    print("\nRunning syntax check...")
    from find_indentation_issues import check_file_syntax
    
    issues = 0
    for relative_path in files_to_fix:
        filepath = root_dir / relative_path
        if filepath.exists():
            is_valid, error = check_file_syntax(filepath)
            if not is_valid:
                print(f"  {relative_path}: {error}")
                issues += 1
    
    if issues == 0:
        print("All files have valid syntax!")
    else:
        print(f"\nStill {issues} files with syntax errors.")
    
    return 0 if issues == 0 else 1


if __name__ == "__main__":
    sys.exit(main())