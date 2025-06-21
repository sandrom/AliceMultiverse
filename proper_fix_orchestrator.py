#!/usr/bin/env python3
"""Properly fix alice_orchestrator.py by restoring and fixing it correctly"""

import subprocess
import re

def fix_orchestrator():
    # First restore from git
    subprocess.run(['git', 'checkout', 'HEAD', '--', 'alicemultiverse/interface/alice_orchestrator.py'])
    
    # Read the file
    with open('alicemultiverse/interface/alice_orchestrator.py', 'r') as f:
        lines = f.readlines()
    
    # Process each line
    fixed_lines = []
    for i, line in enumerate(lines):
        # Check if this is a TODO comment line
        match = re.match(r'^(\s*)# TODO: Review unreachable code - (.*)$', line)
        if match:
            indent = match.group(1)
            code = match.group(2)
            # Replace with the actual code, preserving indentation
            fixed_lines.append(f"{indent}{code}\n")
        else:
            fixed_lines.append(line)
    
    # Write back
    with open('alicemultiverse/interface/alice_orchestrator.py', 'w') as f:
        f.writelines(fixed_lines)
    
    # Now run black to format it properly
    try:
        subprocess.run(['black', 'alicemultiverse/interface/alice_orchestrator.py'], check=True)
        print("Successfully fixed alice_orchestrator.py")
    except subprocess.CalledProcessError:
        print("Black formatting failed, but TODO comments were removed")
        # Try ruff format as backup
        try:
            subprocess.run(['ruff', 'format', 'alicemultiverse/interface/alice_orchestrator.py'], check=True)
            print("Formatted with ruff instead")
        except subprocess.CalledProcessError:
            print("Both formatters failed, manual intervention needed")

if __name__ == "__main__":
    fix_orchestrator()