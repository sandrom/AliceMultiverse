#!/usr/bin/env python3
"""Test script to verify pipeline_stages dict structure prevents duplicates."""

import json
from pathlib import Path

# Simulate processing the same file multiple times
metadata = {
    'file_name': 'test.png',
    'quality_stars': 4
}

# Old list-based approach (would create duplicates)
print("=== OLD LIST-BASED APPROACH ===")
old_metadata = metadata.copy()
old_metadata['pipeline_stages'] = []

# Process 3 times (simulating multiple runs)
for i in range(3):
    old_metadata['pipeline_stages'].append({
        'name': 'brisque',
        'score': 35.0,
        'stars': 4,
        'passed': True
    })

print(f"Number of BRISQUE entries: {len([s for s in old_metadata['pipeline_stages'] if s['name'] == 'brisque'])}")
print(json.dumps(old_metadata['pipeline_stages'], indent=2))

# New dict-based approach (prevents duplicates)
print("\n=== NEW DICT-BASED APPROACH ===")
new_metadata = metadata.copy()
new_metadata['pipeline_stages'] = {}

# Process 3 times (simulating multiple runs)
import time
for i in range(3):
    new_metadata['pipeline_stages']['brisque'] = {
        'score': 35.0,
        'stars': 4,
        'passed': True,
        'timestamp': time.time()
    }
    time.sleep(0.1)  # Small delay to show timestamp updates

print(f"Number of BRISQUE entries: {len([k for k in new_metadata['pipeline_stages'] if k == 'brisque'])}")
print(json.dumps(new_metadata['pipeline_stages'], indent=2))

# Show how to check if a stage was processed
print("\n=== CHECKING STAGE RESULTS ===")
if 'brisque' in new_metadata['pipeline_stages']:
    brisque_result = new_metadata['pipeline_stages']['brisque']
    print(f"BRISQUE processed: score={brisque_result['score']}, passed={brisque_result['passed']}")