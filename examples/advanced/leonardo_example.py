#!/usr/bin/env python3
"""
Leonardo.ai Provider Example

This example demonstrates various features of the Leonardo.ai provider:
- Basic image generation with Phoenix model
- PhotoReal for photorealistic images
- Alchemy enhancement for better quality
- Using Elements for style control
- Cost estimation and model comparison
"""

import asyncio
import os

from alicemultiverse.providers import get_provider
from alicemultiverse.providers.types import GenerationRequest, GenerationType


async def basic_generation():
    """Basic image generation with Phoenix model."""
    print("\n=== Basic Phoenix Generation ===")

    provider = get_provider("leonardo")

    request = GenerationRequest(
        prompt="A majestic phoenix rising from flames, digital art, highly detailed",
        generation_type=GenerationType.IMAGE,
        model="phoenix",
        parameters={
            "width": 1024,
            "height": 1024,
            "num_images": 1,
            "guidance_scale": 7.0,
        }
    )

    # Estimate cost
    cost = provider.estimate_cost(request)
    print(f"Estimated cost: ${cost:.3f}")

    # Generate
    print("Generating image...")
    result = await provider.generate(request)

    if result.success:
        print(f"✓ Image saved to: {result.file_path}")
        print(f"  Generation time: {result.generation_time:.1f}s")
        print(f"  Actual cost: ${result.cost:.3f}")
        if result.metadata and "seed" in result.metadata:
            print(f"  Seed: {result.metadata['seed']}")
    else:
        print(f"✗ Generation failed: {result.error}")


async def photoreal_generation():
    """PhotoReal generation for photorealistic images."""
    print("\n=== PhotoReal Generation ===")

    provider = get_provider("leonardo")

    # PhotoReal v2 requires SDXL model
    request = GenerationRequest(
        prompt="Professional headshot of a confident business executive, studio lighting",
        generation_type=GenerationType.IMAGE,
        model="vision-xl",
        parameters={
            "photo_real": True,
            "photo_real_version": "v2",
            "preset_style": "CINEMATIC",
            "width": 1024,
            "height": 1024,
            "num_images": 1,
        }
    )

    print("Generating photorealistic image...")
    result = await provider.generate(request)

    if result.success:
        print(f"✓ PhotoReal image saved to: {result.file_path}")
        print("  Style: CINEMATIC")
        print(f"  Cost: ${result.cost:.3f}")
    else:
        print(f"✗ Generation failed: {result.error}")


async def alchemy_enhancement():
    """Alchemy enhancement for maximum quality."""
    print("\n=== Alchemy Enhancement ===")

    provider = get_provider("leonardo")

    request = GenerationRequest(
        prompt="Epic fantasy landscape with floating islands and waterfalls, magical atmosphere",
        generation_type=GenerationType.IMAGE,
        model="vision-xl",  # SDXL model for Alchemy v2
        parameters={
            "alchemy": True,
            "preset_style": "FANTASY",
            "guidance_scale": 12.0,
            "width": 1024,
            "height": 1024,
        }
    )

    print("Generating with Alchemy enhancement...")
    print("Note: Alchemy v2 outputs 1.75x resolution")

    result = await provider.generate(request)

    if result.success:
        print(f"✓ Alchemy-enhanced image saved to: {result.file_path}")
        print("  Output resolution will be ~1792x1792")
        print(f"  Cost: ${result.cost:.3f}")
    else:
        print(f"✗ Generation failed: {result.error}")


async def flux_schnell_fast():
    """Flux Schnell for fast generation."""
    print("\n=== Flux Schnell (Fast) ===")

    provider = get_provider("leonardo")

    request = GenerationRequest(
        prompt="Quick concept art of a futuristic vehicle",
        generation_type=GenerationType.IMAGE,
        model="flux-schnell",
        parameters={
            "width": 1024,
            "height": 1024,
            "num_images": 2,  # Generate 2 variations
        }
    )

    print("Generating with Flux Schnell (optimized for speed)...")
    result = await provider.generate(request)

    if result.success:
        print(f"✓ Fast generation complete: {result.file_path}")
        print(f"  Generation time: {result.generation_time:.1f}s")
        print("  Images generated: 2")
        if result.metadata and "all_images" in result.metadata:
            print(f"  All image URLs: {len(result.metadata['all_images'])}")
    else:
        print(f"✗ Generation failed: {result.error}")


async def phoenix_with_contrast():
    """Phoenix with custom contrast settings."""
    print("\n=== Phoenix with Contrast Control ===")

    provider = get_provider("leonardo")

    request = GenerationRequest(
        prompt="Dramatic black and white photography of architecture",
        generation_type=GenerationType.IMAGE,
        model="phoenix",
        parameters={
            "contrast": 3.5,  # High contrast
            "enhance_prompt": True,
            "enhance_prompt_instruction": "Emphasize dramatic shadows and highlights",
            "width": 1024,
            "height": 1024,
        }
    )

    print("Generating high-contrast image...")
    result = await provider.generate(request)

    if result.success:
        print(f"✓ High-contrast image saved to: {result.file_path}")
        print("  Contrast level: 3.5")
        print("  Prompt enhanced: Yes")
    else:
        print(f"✗ Generation failed: {result.error}")


async def list_available_elements():
    """List available Elements for style control."""
    print("\n=== Available Elements ===")

    provider = get_provider("leonardo")

    try:
        elements = await provider.list_elements()
        if elements:
            print(f"Found {len(elements)} Elements:")
            for elem in elements[:5]:  # Show first 5
                print(f"  - {elem.get('id', 'N/A')}: {elem.get('name', 'Unknown')}")
            if len(elements) > 5:
                print(f"  ... and {len(elements) - 5} more")
        else:
            print("No Elements found (may require API access)")
    except Exception as e:
        print(f"Could not list Elements: {e}")


async def model_comparison():
    """Compare different models for the same prompt."""
    print("\n=== Model Comparison ===")

    provider = get_provider("leonardo")
    prompt = "Serene mountain landscape at sunset"

    models = ["phoenix", "flux-dev", "vision-xl"]

    for model in models:
        print(f"\nModel: {model}")

        request = GenerationRequest(
            prompt=prompt,
            generation_type=GenerationType.IMAGE,
            model=model,
            parameters={
                "width": 512,  # Smaller for comparison
                "height": 512,
                "seed": 12345,  # Same seed for consistency
            }
        )

        # Estimate cost and time
        cost = provider.estimate_cost(request)
        time_est = provider.get_generation_time(request)

        print(f"  Estimated cost: ${cost:.3f}")
        print(f"  Estimated time: {time_est:.1f}s")


async def main():
    """Run all examples."""
    print("Leonardo.ai Provider Examples")
    print("=" * 50)

    # Check for API key
    if not os.environ.get("LEONARDO_API_KEY"):
        print("\n⚠️  Warning: LEONARDO_API_KEY not set")
        print("Set it with: export LEONARDO_API_KEY='your-key'")
        print("Get your key from: https://app.leonardo.ai/api")
        return

    # Run examples
    await basic_generation()
    await photoreal_generation()
    await alchemy_enhancement()
    await flux_schnell_fast()
    await phoenix_with_contrast()
    await list_available_elements()
    await model_comparison()

    print("\n✅ All examples complete!")


if __name__ == "__main__":
    asyncio.run(main())
