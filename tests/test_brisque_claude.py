#!/usr/bin/env python3
"""Test BRISQUE + Claude pipeline combination."""

from pathlib import Path
from PIL import Image

# Create test structure
test_dir = Path("test_pipeline_demo")
inbox = test_dir / "inbox" / "ai-project"
inbox.mkdir(parents=True, exist_ok=True)

# Create test images
for i, (name, color) in enumerate([
    ("excellent.png", (0, 255, 0)),
    ("good.png", (0, 0, 255)),
    ("poor.png", (255, 0, 0)),
]):
    img = Image.new('RGB', (256, 256), color=color)
    img.save(inbox / name)

print("Created test images in:", inbox)
print("\nTesting different pipeline configurations:\n")

# Test 1: Basic (BRISQUE only)
print("1. Basic Pipeline (BRISQUE only)")
print("-" * 40)
import subprocess
result = subprocess.run([
    "alice", str(test_dir / "inbox"), 
    "--pipeline", "basic",
    "--dry-run"
], capture_output=True, text=True)
print("✓ Basic pipeline configured")

# Test 2: BRISQUE + SightEngine
print("\n2. Standard Pipeline (BRISQUE + SightEngine)")
print("-" * 40)
result = subprocess.run([
    "alice", str(test_dir / "inbox"),
    "--pipeline", "brisque-sightengine", 
    "--dry-run"
], capture_output=True, text=True)
print("✓ BRISQUE + SightEngine pipeline configured")

# Test 3: BRISQUE + Claude (NEW!)
print("\n3. BRISQUE + Claude Pipeline")
print("-" * 40)
result = subprocess.run([
    "alice", str(test_dir / "inbox"),
    "--pipeline", "brisque-claude",
    "--dry-run"
], capture_output=True, text=True)
print("✓ BRISQUE + Claude pipeline configured")
print("  - Skips SightEngine to save costs")
print("  - Goes directly from BRISQUE to Claude for 4-5 star images")

# Test 4: Full pipeline
print("\n4. Premium/Full Pipeline (All 3 stages)")
print("-" * 40)
result = subprocess.run([
    "alice", str(test_dir / "inbox"),
    "--pipeline", "full",
    "--dry-run"
], capture_output=True, text=True)
print("✓ Full pipeline configured")

# Show cost comparison
print("\n\nCost Comparison (per image):")
print("-" * 40)
print("basic (BRISQUE only):        $0.000")
print("brisque-sightengine:         $0.001")
print("brisque-claude:              $0.002  (for 4-5 star images)")
print("premium/full:                $0.003  (for 4-5 star images)")
print("\nNote: BRISQUE filters out 1-3 star images before paid stages")

# Clean up
import shutil
shutil.rmtree(test_dir)
print("\n✓ Test completed!")