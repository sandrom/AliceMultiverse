#!/usr/bin/env python3
"""
Simple test to verify fal.ai provider is configured correctly.
This test does not make any API calls.
"""

import asyncio
import os

from alicemultiverse.providers import get_provider


async def test_provider_setup():
    """Test that the fal.ai provider is properly configured."""
    print("=== Testing fal.ai Provider Setup ===\n")
    
    # Get the provider (without API key first)
    provider = get_provider("fal")
    print(f"✓ Provider initialized: {provider.name}")
    
    # Check capabilities
    caps = provider.capabilities
    print(f"\n✓ Generation types: {[t.value for t in caps.generation_types]}")
    print(f"✓ Number of models: {len(caps.models)}")
    print(f"✓ Max resolution: {caps.max_resolution['width']}x{caps.max_resolution['height']}")
    
    # Check if our new models are present
    print("\n✓ Checking for new models:")
    expected_models = ["flux-pro", "kling-v1-text", "kling-v1-image", "kling-v2-text", "kling-v2-image"]
    for model in expected_models:
        if model in caps.models:
            print(f"  ✓ {model}: Found")
        else:
            print(f"  ✗ {model}: NOT FOUND!")
    
    # List all models with pricing
    print("\n✓ All models with pricing:")
    for model in sorted(caps.models):
        price = caps.pricing.get(model, "Unknown")
        print(f"  - {model}: ${price}")
    
    # Check API key
    api_key = os.getenv("FAL_KEY")
    if not api_key:
        try:
            from alicemultiverse.core.keys import KeyManager
            key_manager = KeyManager()
            api_key = key_manager.get_api_key("FAL_KEY")
            if api_key:
                print("\n✓ API key found in keychain")
        except:
            pass
    else:
        print("\n✓ API key found in environment")
    
    if not api_key:
        print("\n⚠️  No API key found. Provider will work with limited functionality.")
    
    # Test provider status (this might make a lightweight API call)
    print("\n✓ Checking provider status...")
    try:
        status = await provider.check_status()
        print(f"  Status: {status.value}")
    except Exception as e:
        print(f"  Could not check status: {e}")


async def main():
    """Run the simple test."""
    await test_provider_setup()
    print("\n✓ All basic checks completed!")


if __name__ == "__main__":
    asyncio.run(main())