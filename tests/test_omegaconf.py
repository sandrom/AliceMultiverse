#!/usr/bin/env python3
"""Test script to verify OmegaConf integration"""

import sys
from pathlib import Path
from omegaconf import OmegaConf

# Test loading settings.yaml
settings_path = Path(__file__).parent / "settings.yaml"
if settings_path.exists():
    config = OmegaConf.load(settings_path)
    print("✓ Successfully loaded settings.yaml")
    print(f"  - Inbox path: {config.paths.inbox}")
    print(f"  - Organized path: {config.paths.organized}")
    print(f"  - Quality thresholds loaded: {len(config.quality.thresholds)} star levels")
    print(f"  - 5-star threshold: {config.quality.thresholds['5_star']['min']}-{config.quality.thresholds['5_star']['max']}")
else:
    print("✗ settings.yaml not found")
    sys.exit(1)

# Test command-line override parsing
test_overrides = ["quality.thresholds.5_star.max=30", "paths.inbox=/tmp/test"]
for override in test_overrides:
    key, value = override.split("=")
    OmegaConf.update(config, key, value, merge=True)

print("\n✓ Command-line overrides applied:")
print(f"  - New 5-star max threshold: {config.quality.thresholds['5_star']['max']}")
print(f"  - New inbox path: {config.paths.inbox}")

print("\n✓ OmegaConf integration test passed!")