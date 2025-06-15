#!/usr/bin/env python3
"""Example usage of Ideogram provider for text rendering and typography."""

import asyncio
import os

from alicemultiverse.providers import get_provider
from alicemultiverse.providers.ideogram_provider import IdeogramProvider
from alicemultiverse.providers.types import GenerationRequest, GenerationType


async def logo_generation_example():
    """Generate logos with accurate text rendering."""
    print("\n=== Logo Generation Example ===")

    provider = get_provider("ideogram")

    # Professional logo with text
    request = GenerationRequest(
        prompt='Minimalist logo for "CloudSync Pro" tech company, '
               'modern sans-serif typography, cloud icon integrated with text, '
               'blue gradient (#0066CC to #00AAFF), white background',
        generation_type=GenerationType.IMAGE,
        model="ideogram-v3",  # Best quality for logos
        parameters={
            "style": "design",
            "aspect_ratio": "1:1",
            "number_of_images": 3,  # Generate variations
            "negative_prompt": "complex, cluttered, pixelated text",
        }
    )

    print("Generating logo variations...")
    result = await provider.generate(request)

    if result.success:
        print(f"Success! Logo saved to: {result.file_path}")
        print(f"Cost: ${result.cost} for {request.parameters['number_of_images']} variations")
        print(f"Metadata: {result.metadata}")
    else:
        print(f"Error: {result.error}")


async def typography_poster_example():
    """Create typographic posters with custom styling."""
    print("\n=== Typography Poster Example ===")

    provider = get_provider("ideogram")

    # Motivational poster
    request = GenerationRequest(
        prompt='Bold typographic poster with text "CREATE INSPIRE ACHIEVE" '
               'in stacked layout, modern geometric font, vibrant gradient background, '
               'dynamic composition with overlapping letters',
        generation_type=GenerationType.IMAGE,
        model="ideogram-v2",
        parameters={
            "style": "design",
            "aspect_ratio": "9:16",  # Portrait poster
            "color_palette": ["#FF006E", "#8338EC", "#3A86FF"],
            "magic_prompt_option": "AUTO",
        }
    )

    print("Creating typography poster...")
    result = await provider.generate(request)

    if result.success:
        print(f"Poster created: {result.file_path}")


async def turbo_ideation_example():
    """Fast generation for quick concepts and ideation."""
    print("\n=== Turbo Ideation Example ===")

    provider = get_provider("ideogram")

    concepts = [
        'T-shirt design with text "Adventure Awaits" in vintage style',
        'Coffee shop menu board with "Today\'s Specials" header',
        'Wedding invitation with "Save the Date" in elegant script',
    ]

    print("Generating quick concepts with Turbo model...")
    for i, concept in enumerate(concepts, 1):
        request = GenerationRequest(
            prompt=concept,
            generation_type=GenerationType.IMAGE,
            model="turbo",  # Fast generation
            parameters={
                "style": "design",
                "aspect_ratio": "4:3",
            }
        )

        print(f"{i}. Generating: {concept[:50]}...")
        result = await provider.generate(request)

        if result.success:
            print(f"   ✓ Generated in ~{result.generation_time}s (${result.cost})")


async def multilingual_text_example():
    """Generate images with text in multiple languages."""
    print("\n=== Multilingual Text Example ===")

    provider = get_provider("ideogram")

    # Japanese anime poster
    request = GenerationRequest(
        prompt='Anime movie poster with Japanese title "桜の約束" (Promise of Cherry Blossoms) '
               'at the top, English subtitle "A Spring Romance" at bottom, '
               'cherry blossoms, two characters silhouette',
        generation_type=GenerationType.IMAGE,
        model="ideogram-v2",
        parameters={
            "style": "anime",
            "aspect_ratio": "2:3",  # Movie poster ratio
        }
    )

    print("Generating multilingual poster...")
    result = await provider.generate(request)

    if result.success:
        print("✓ Multilingual text rendered successfully")


async def brand_consistency_example():
    """Maintain brand consistency with color palettes."""
    print("\n=== Brand Consistency Example ===")

    provider = get_provider("ideogram")

    # Brand colors for consistency
    brand_colors = ["#1A1A2E", "#F39C12", "#E74C3C"]

    # Social media post series
    posts = [
        '"New Product Launch" announcement banner',
        '"Limited Time Offer" promotional graphic',
        '"Thank You" customer appreciation post',
    ]

    for post_text in posts:
        request = GenerationRequest(
            prompt=f"Social media post with {post_text}, modern design, "
                   f"bold typography, geometric shapes",
            generation_type=GenerationType.IMAGE,
            model="ideogram-v2",
            parameters={
                "style": "design",
                "aspect_ratio": "1:1",  # Instagram square
                "color_palette": brand_colors,
                "seed": 12345,  # Consistent style
            }
        )

        print(f"Creating branded post: {post_text}")
        result = await provider.generate(request)

        if result.success:
            print("✓ Saved with consistent brand colors")


async def text_effects_showcase():
    """Showcase different text effects and styles."""
    print("\n=== Text Effects Showcase ===")

    provider = get_provider("ideogram")

    effects = [
        ("3D Chrome", "3d", "Metallic chrome 3D text 'PREMIUM' with reflections"),
        ("Neon Glow", "realistic", "Neon sign text 'OPEN 24/7' glowing in the dark"),
        ("Graffiti", "design", "Street art graffiti text 'URBAN' on brick wall"),
        ("Ice", "realistic", "Frozen ice text 'WINTER' with icicles and frost"),
    ]

    for effect_name, style, prompt in effects:
        request = GenerationRequest(
            prompt=prompt,
            generation_type=GenerationType.IMAGE,
            model="ideogram-v2",
            parameters={
                "style": style,
                "aspect_ratio": "16:9",
            }
        )

        print(f"Creating {effect_name} effect...")
        result = await provider.generate(request)

        if result.success:
            print(f"✓ {effect_name} effect completed")


async def upscaling_example():
    """Generate and upscale a design."""
    print("\n=== Upscaling Example ===")

    provider = get_provider("ideogram")

    # First, generate a logo
    request = GenerationRequest(
        prompt='App icon design with text "AI" in futuristic style, gradient background',
        generation_type=GenerationType.IMAGE,
        model="turbo",  # Quick generation first
        parameters={
            "style": "design",
            "aspect_ratio": "1:1",
        }
    )

    print("Generating initial design...")
    result = await provider.generate(request)

    if result.success and isinstance(provider, IdeogramProvider):
        print(f"Initial design saved: {result.file_path}")
        print("Upscaling to high resolution...")

        # Upscale the result
        upscaled = await provider.upscale_image(
            result.file_path,
            resolution="2048x2048"
        )

        if upscaled.success:
            print(f"✓ Upscaled version saved: {upscaled.file_path}")
            print(f"Additional cost: ${upscaled.cost}")


async def cost_estimation_example():
    """Demonstrate cost estimation for different options."""
    print("\n=== Cost Estimation Example ===")

    provider = get_provider("ideogram")

    # Different configurations
    configs = [
        ("V3 Single", "ideogram-v3", 1, False),
        ("V3 Batch (4)", "ideogram-v3", 4, False),
        ("V2 Single", "ideogram-v2", 1, False),
        ("Turbo Single", "turbo", 1, False),
        ("Turbo + Upscale", "turbo", 1, True),
    ]

    total_cost = 0
    for name, model, num_images, upscale in configs:
        request = GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.IMAGE,
            model=model,
            parameters={
                "number_of_images": num_images,
                "upscale": upscale,
            }
        )

        cost = await provider.estimate_cost(request)
        total_cost += cost
        print(f"{name}: ${cost:.2f}")

    print(f"\nTotal estimated cost: ${total_cost:.2f}")


async def main():
    """Run all examples."""
    # Check for API credentials
    if not os.getenv("IDEOGRAM_API_KEY"):
        print("Please set IDEOGRAM_API_KEY environment variable")
        print("Get your API key from: https://ideogram.ai/")
        return

    try:
        # Run examples
        await logo_generation_example()
        await cost_estimation_example()

        # Run these selectively as they consume credits
        # await typography_poster_example()
        # await turbo_ideation_example()
        # await multilingual_text_example()
        # await brand_consistency_example()
        # await text_effects_showcase()
        # await upscaling_example()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
