#!/usr/bin/env python3
"""
Direct test of fal.ai provider functionality.
This tests the provider without going through MCP.
"""

import asyncio
import os
from pathlib import Path
import pytest

from alicemultiverse.providers import get_provider_async, GenerationRequest, GenerationType


@pytest.mark.asyncio
async def test_provider_setup():
    """Test that fal.ai provider is properly set up."""
    print("=== Testing fal.ai Provider Setup ===\n")
    
    # Get provider
    provider = await get_provider_async("fal")
    print(f"✅ Provider initialized: {provider.name}")
    
    # Check capabilities
    caps = provider.capabilities
    print(f"\nCapabilities:")
    print(f"  - Generation types: {[t.value for t in caps.generation_types]}")
    print(f"  - Total models: {len(caps.models)}")
    
    # Check new models
    new_models = ["flux-pro", "kling-v1-text", "kling-v2-text", "kling-elements", "kling-lipsync"]
    print(f"\nNew models:")
    for model in new_models:
        if model in caps.models:
            price = caps.pricing.get(model, "Unknown")
            print(f"  ✅ {model}: ${price}")
        else:
            print(f"  ❌ {model}: NOT FOUND")


@pytest.mark.asyncio
async def test_generation_request():
    """Test creating generation requests for new models."""
    print("\n=== Testing Generation Request Creation ===\n")
    
    # Test FLUX Pro request
    flux_request = GenerationRequest(
        prompt="Test prompt for FLUX Pro",
        generation_type=GenerationType.IMAGE,
        model="flux-pro",
        parameters={
            "width": 512,
            "height": 512,
            "num_inference_steps": 50
        }
    )
    print(f"✅ Created FLUX Pro request: {flux_request.model}")
    
    # Test Kling video request
    kling_request = GenerationRequest(
        prompt="Test prompt for Kling video",
        generation_type=GenerationType.VIDEO,
        model="kling-v2-text",
        parameters={
            "duration": "5",
            "aspect_ratio": "16:9"
        }
    )
    print(f"✅ Created Kling v2 request: {kling_request.model}")


@pytest.mark.asyncio
async def test_api_key_availability():
    """Check if API key is available."""
    print("\n=== Testing API Key Availability ===\n")
    
    # Check environment
    has_env_key = bool(os.getenv("FAL_KEY"))
    print(f"FAL_KEY in environment: {'✅ Yes' if has_env_key else '❌ No'}")
    
    # Try to get from keychain
    try:
        from alicemultiverse.core.keys import KeyManager
        key_manager = KeyManager()
        has_keychain_key = bool(key_manager.get_api_key("FAL_KEY"))
        print(f"FAL_KEY in keychain: {'✅ Yes' if has_keychain_key else '❌ No'}")
    except Exception as e:
        print(f"Could not check keychain: {e}")
    
    if not has_env_key:
        print("\n⚠️  No API key found. Generation tests will be skipped.")
        print("Run 'alice keys setup' to configure API keys.")


@pytest.mark.asyncio
async def test_dry_run_generation():
    """Test generation request validation without making API calls."""
    print("\n=== Testing Request Validation (Dry Run) ===\n")
    
    provider = await get_provider_async("fal")
    
    # Test valid request
    valid_request = GenerationRequest(
        prompt="A beautiful sunset",
        generation_type=GenerationType.IMAGE,
        model="flux-schnell"
    )
    
    try:
        # Test cost estimation instead of internal parameter building
        estimate = await provider.estimate_cost(valid_request)
        print(f"✅ Valid request cost estimate: ${estimate.estimated_cost:.4f}")
        print(f"   Model: {valid_request.model}")
        print(f"   Type: {valid_request.generation_type.value}")
    except Exception as e:
        print(f"❌ Failed to estimate cost: {e}")
    
    # Test invalid model
    invalid_request = GenerationRequest(
        prompt="Test",
        generation_type=GenerationType.IMAGE,
        model="nonexistent-model"
    )
    
    # This should fail during generation
    result = await provider.generate(invalid_request)
    if not result.success:
        print(f"\n✅ Invalid model correctly rejected: {result.error[:50]}...")
    else:
        print(f"\n❌ Invalid model should have been rejected")


# This file is now a pytest test file and should be run with pytest