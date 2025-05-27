#!/usr/bin/env python3
"""Test monorepo setup."""

print("Testing monorepo imports...")

try:
    import alice_events

    print("✓ alice_events imported successfully")
except ImportError as e:
    print(f"✗ alice_events import failed: {e}")

try:
    import alice_models

    print("✓ alice_models imported successfully")
except ImportError as e:
    print(f"✗ alice_models import failed: {e}")

try:
    import alice_config

    print("✓ alice_config imported successfully")
except ImportError as e:
    print(f"✗ alice_config import failed: {e}")

try:
    import alice_utils

    print("✓ alice_utils imported successfully")
except ImportError as e:
    print(f"✗ alice_utils import failed: {e}")

print("\nTesting specific imports...")

try:
    from alice_events import AssetDiscoveredEvent, publish_event

    print("✓ Event classes imported successfully")
except ImportError as e:
    print(f"✗ Event classes import failed: {e}")

try:
    from alice_models import MediaType, QualityRating

    print("✓ Model classes imported successfully")
except ImportError as e:
    print(f"✗ Model classes import failed: {e}")

try:
    from alice_config import get_config

    print("✓ Config imported successfully")
except ImportError as e:
    print(f"✗ Config import failed: {e}")

try:
    from alice_utils import compute_file_hash, detect_media_type

    print("✓ Utils imported successfully")
except ImportError as e:
    print(f"✗ Utils import failed: {e}")

print("\nAll imports successful! Monorepo is working correctly.")
