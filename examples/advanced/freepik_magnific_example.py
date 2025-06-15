#!/usr/bin/env python3
"""Example usage of Freepik provider for Magnific upscaling and Mystic generation."""

import asyncio
import os

from alicemultiverse.providers.base import GenerateRequest, GenerationType
from alicemultiverse.providers.registry import get_provider


async def upscale_with_magnific():
    """Example: Upscale an image using Magnific."""
    print("\n=== Magnific Upscaling Example ===")

    # Get Freepik provider
    provider = get_provider("freepik", api_key=os.getenv("FREEPIK_API_KEY"))

    # Prepare upscaling request
    request = GenerateRequest(
        prompt="",  # Not needed for upscaling
        model="magnific-sparkle",  # Best quality engine
        provider="freepik",
        generation_type=GenerationType.IMAGE,
        reference_assets=["https://example.com/your-image.jpg"],  # Your input image
        parameters={
            "scale": 4,  # 4x upscaling
            "creativity": 0.7,  # Add some creative enhancement (0-10)
            "hdr": 0.8,  # HDR enhancement (0-10)
            "resemblance": 0.6,  # How closely to match original (0-10)
            "fractality": 0.5,  # Fractal detail enhancement (0-10)
            "detail_refinement": 0.8,  # Fine detail enhancement (0-10)
            "style": "cinematic",  # Style preset
        }
    )

    print(f"Upscaling image with {request.model}...")
    print(f"Scale: {request.parameters['scale']}x")
    print(f"Estimated cost: ${provider.estimate_cost(request):.3f}")

    # Generate
    async with provider:
        result = await provider.generate(request)

    print(f"✓ Upscaled image ready: {result.asset_url}")
    print(f"Actual cost: ${result.cost:.3f}")
    print(f"Task ID: {result.metadata['task_id']}")

    return result


async def generate_with_mystic():
    """Example: Generate a photorealistic image with Mystic."""
    print("\n=== Mystic Generation Example ===")

    # Get Freepik provider
    provider = get_provider("freepik", api_key=os.getenv("FREEPIK_API_KEY"))

    # Prepare generation request
    request = GenerateRequest(
        prompt="A professional portrait of a business woman in a modern office, "
               "natural lighting, sharp focus, photorealistic",
        model="mystic-4k",  # 4K resolution
        provider="freepik",
        generation_type=GenerationType.IMAGE,
        parameters={
            "negative_prompt": "blurry, low quality, distorted, artificial",
            "guidance_scale": 7.5,  # How closely to follow prompt (1-10)
            "num_inference_steps": 50,  # Quality vs speed (10-50)
            "style": "professional",  # Style preset
            "detail": 1.5,  # Detail level (0-2)
            "style_strength": 0.7,  # Style influence (0-1)
            "structure": 0.8,  # Structural coherence (0-1)
            "seed": 42,  # For reproducibility
        }
    )

    print(f"Generating with {request.model}...")
    print(f"Prompt: {request.prompt}")
    print(f"Estimated cost: ${provider.estimate_cost(request):.3f}")

    # Generate
    async with provider:
        result = await provider.generate(request)

    print(f"✓ Generated image: {result.asset_url}")
    print(f"Actual cost: ${result.cost:.3f}")
    print(f"Task ID: {result.metadata['task_id']}")

    return result


async def mystic_with_style_reference():
    """Example: Generate with Mystic using a style reference image."""
    print("\n=== Mystic with Style Reference ===")

    provider = get_provider("freepik", api_key=os.getenv("FREEPIK_API_KEY"))

    request = GenerateRequest(
        prompt="A futuristic cityscape at sunset",
        model="mystic",
        provider="freepik",
        generation_type=GenerationType.IMAGE,
        reference_assets=["https://example.com/style-reference.jpg"],  # Style reference
        parameters={
            "negative_prompt": "daytime, old, vintage",
            "guidance_scale": 6.0,
            "style": "cyberpunk",
            "detail": 1.8,
            "style_strength": 0.9,  # Strong style influence
            "lora": "cyberpunk_enhanced",  # Use specific LoRA
            "lora_strength": 0.8,
        }
    )

    print("Generating with style reference...")
    print(f"Style: {request.parameters['style']}")
    print(f"LoRA: {request.parameters['lora']}")

    async with provider:
        result = await provider.generate(request)

    print(f"✓ Generated: {result.asset_url}")

    return result


async def upscale_workflow():
    """Example: Complete workflow - Generate then upscale."""
    print("\n=== Complete Workflow: Generate → Upscale ===")

    provider = get_provider("freepik")

    # Step 1: Generate with Mystic
    print("Step 1: Generating base image...")
    generate_request = GenerateRequest(
        prompt="A majestic mountain landscape with dramatic lighting",
        model="mystic",
        provider="freepik",
        generation_type=GenerationType.IMAGE,
        parameters={
            "guidance_scale": 7.0,
            "style": "landscape",
            "detail": 1.5,
        }
    )

    async with provider:
        generated = await provider.generate(generate_request)
        print(f"✓ Generated: {generated.asset_url}")

        # Step 2: Upscale the result
        print("\nStep 2: Upscaling to 4K...")
        upscale_request = GenerateRequest(
            prompt="",
            model="magnific-illusio",  # Balanced engine
            provider="freepik",
            generation_type=GenerationType.IMAGE,
            reference_assets=[generated.asset_url],
            parameters={
                "scale": 4,
                "creativity": 0.5,
                "hdr": 0.9,  # Enhance landscape HDR
                "style": "landscape",
            }
        )

        upscaled = await provider.generate(upscale_request)
        print(f"✓ Upscaled: {upscaled.asset_url}")

    total_cost = generated.cost + upscaled.cost
    print(f"\nTotal workflow cost: ${total_cost:.3f}")

    return generated, upscaled


async def main():
    """Run all examples."""
    # Check for API key
    if not os.getenv("FREEPIK_API_KEY"):
        print("Please set FREEPIK_API_KEY environment variable")
        print("Get your API key at: https://www.freepik.com/api/")
        return

    try:
        # Run examples
        await upscale_with_magnific()
        await generate_with_mystic()
        await mystic_with_style_reference()
        await upscale_workflow()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
