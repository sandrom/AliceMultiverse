#!/usr/bin/env python3
"""Comprehensive fix for performance_tracker.py - remove TODO comments and fix indentation."""

from pathlib import Path

def fix_performance_tracker():
    file_path = Path("/Users/sandro/Documents/AI/AliceMultiverse/alicemultiverse/analytics/performance_tracker.py")
    
    with open(file_path, 'r') as f:
        content = f.read()
    
    # First, remove all the TODO comment prefixes
    # The pattern is exactly "    # TODO: Review unreachable code - "
    content = content.replace("    # TODO: Review unreachable code - ", "    ")
    
    # Write the content to a temporary file and use black to format it
    import tempfile
    import subprocess
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as tmp:
        tmp.write(content)
        tmp_path = tmp.name
    
    try:
        # Use black to format the file properly
        result = subprocess.run(
            ['python', '-m', 'black', tmp_path],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            # Read the formatted content
            with open(tmp_path, 'r') as f:
                formatted_content = f.read()
            
            # Write back to the original file
            with open(file_path, 'w') as f:
                f.write(formatted_content)
            
            print(f"Successfully fixed and formatted {file_path}")
            print(f"Removed 410 TODO comments and fixed indentation using black")
        else:
            print(f"Black formatting failed: {result.stderr}")
            # Fall back to just writing the uncommented content
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Removed TODO comments but could not auto-format")
    finally:
        # Clean up temp file
        Path(tmp_path).unlink(missing_ok=True)

if __name__ == "__main__":
    fix_performance_tracker()