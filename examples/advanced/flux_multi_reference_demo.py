"""Demonstration of FLUX Kontext multi-reference capabilities."""

import asyncio
from pathlib import Path

from alicemultiverse.providers import GenerationRequest, GenerationType, get_provider


async def multi_reference_example():
    """Example using FLUX Kontext multi-reference models."""

    # Initialize provider
    provider = get_provider("fal")

    print("FLUX Kontext Multi-Reference Demo")
    print("=" * 50)

    # Example 1: Equal weight blending
    print("\n1. Equal Weight Blending")
    print("Combining three art styles with equal influence...")

    request1 = GenerationRequest(
        prompt="Create a majestic dragon combining these artistic styles",
        generation_type=GenerationType.IMAGE,
        model="flux-kontext-pro-multi",
        reference_assets=[
            "https://example.com/traditional_japanese_art.jpg",
            "https://example.com/western_fantasy_art.jpg",
            "https://example.com/modern_digital_art.jpg"
        ],
        # No weights specified = equal influence (1.0 each)
        parameters={
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
        },
        output_path=Path("output/dragon_equal_blend.png")
    )

    try:
        result1 = await provider.generate(request1)
        print(f"✓ Generated: {result1.file_path}")
        print(f"  Cost: ${result1.cost:.3f}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Example 2: Weighted blending
    print("\n2. Weighted Reference Blending")
    print("Creating character with emphasis on first reference...")

    request2 = GenerationRequest(
        prompt="Design a warrior character: armor from first, weapon from second, pose from third",
        generation_type=GenerationType.IMAGE,
        model="flux-kontext-max-multi",  # Using Max for better quality
        reference_assets=[
            "https://example.com/ornate_armor.jpg",      # Main focus
            "https://example.com/legendary_sword.jpg",   # Secondary
            "https://example.com/dynamic_pose.jpg"       # Subtle influence
        ],
        reference_weights=[2.0, 1.5, 0.5],  # Custom weights
        parameters={
            "num_inference_steps": 50,  # Higher for Max model
            "guidance_scale": 4.0,
        },
        output_path=Path("output/warrior_weighted.png")
    )

    try:
        result2 = await provider.generate(request2)
        print(f"✓ Generated: {result2.file_path}")
        print(f"  Cost: ${result2.cost:.3f}")
    except Exception as e:
        print(f"✗ Error: {e}")

    # Example 3: Style progression
    print("\n3. Progressive Style Refinement")
    print("Using output as reference for further refinement...")

    if 'result1' in locals() and result1.file_path:
        request3 = GenerationRequest(
            prompt="Refine the dragon with more detailed textures and lighting",
            generation_type=GenerationType.IMAGE,
            model="flux-kontext-pro-multi",
            reference_assets=[
                str(result1.file_path),  # Previous result
                "https://example.com/detailed_scales.jpg",
                "https://example.com/dramatic_lighting.jpg"
            ],
            reference_weights=[2.0, 1.0, 1.0],  # Keep original dominant
            parameters={
                "num_inference_steps": 35,
                "guidance_scale": 3.0,
            },
            output_path=Path("output/dragon_refined.png")
        )

        try:
            result3 = await provider.generate(request3)
            print(f"✓ Generated: {result3.file_path}")
            print(f"  Cost: ${result3.cost:.3f}")
        except Exception as e:
            print(f"✗ Error: {e}")

    # Example 4: Batch variations
    print("\n4. Generating Variations with Different Weights")
    print("Creating multiple versions with varying influences...")

    weight_variations = [
        ([3.0, 1.0, 0.5], "strong_first"),
        ([1.0, 3.0, 0.5], "strong_second"),
        ([0.5, 1.0, 3.0], "strong_third"),
        ([1.0, 1.0, 1.0], "balanced")
    ]

    base_request = GenerationRequest(
        prompt="Fantasy landscape combining these environmental styles",
        generation_type=GenerationType.IMAGE,
        model="flux-kontext-pro-multi",
        reference_assets=[
            "https://example.com/misty_mountains.jpg",
            "https://example.com/enchanted_forest.jpg",
            "https://example.com/crystal_caves.jpg"
        ],
        parameters={
            "num_inference_steps": 28,
            "guidance_scale": 3.5,
        }
    )

    for weights, variant_name in weight_variations:
        request = GenerationRequest(
            **{**base_request.__dict__,
               "reference_weights": weights,
               "output_path": Path(f"output/landscape_{variant_name}.png")}
        )

        try:
            result = await provider.generate(request)
            print(f"✓ {variant_name}: {result.file_path}")
        except Exception as e:
            print(f"✗ {variant_name}: {e}")

    print("\n" + "=" * 50)
    print("Demo complete!")

    # Summary
    total_cost = sum(
        r.cost for r in [result1, result2]
        if 'r' in locals() and hasattr(r, 'cost') and r.cost
    )
    print(f"\nTotal cost: ${total_cost:.3f}")


async def compare_single_vs_multi():
    """Compare single reference vs multi-reference results."""

    provider = get_provider("fal")

    print("\nComparing Single vs Multi-Reference Models")
    print("=" * 50)

    # Base references
    references = [
        "https://example.com/character1.jpg",
        "https://example.com/character2.jpg",
        "https://example.com/character3.jpg"
    ]

    # Single reference (just first image)
    print("\n1. Single Reference Model (using only first image)")
    single_request = GenerationRequest(
        prompt="Create a hero character based on this reference",
        generation_type=GenerationType.IMAGE,
        model="flux-kontext-pro",  # Single reference model
        reference_assets=[references[0]],  # Only first
        output_path=Path("output/hero_single_ref.png")
    )

    # Multi-reference (all images)
    print("\n2. Multi-Reference Model (blending all images)")
    multi_request = GenerationRequest(
        prompt="Create a hero character combining elements from all references",
        generation_type=GenerationType.IMAGE,
        model="flux-kontext-pro-multi",  # Multi reference model
        reference_assets=references,  # All three
        reference_weights=[1.0, 1.0, 1.0],  # Equal blend
        output_path=Path("output/hero_multi_ref.png")
    )

    # Generate both
    try:
        single_result = await provider.generate(single_request)
        print(f"✓ Single reference: {single_result.file_path}")

        multi_result = await provider.generate(multi_request)
        print(f"✓ Multi reference: {multi_result.file_path}")

        print("\nCost comparison:")
        print(f"  Single: ${single_result.cost:.3f}")
        print(f"  Multi:  ${multi_result.cost:.3f}")

    except Exception as e:
        print(f"✗ Error: {e}")


if __name__ == "__main__":
    # Create output directory
    Path("output").mkdir(exist_ok=True)

    # Run examples
    print("Starting FLUX Kontext Multi-Reference Demo...\n")

    # Run main demo
    asyncio.run(multi_reference_example())

    # Run comparison
    asyncio.run(compare_single_vs_multi())

    print("\nNote: Replace example URLs with actual image URLs for real usage!")
