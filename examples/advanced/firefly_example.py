#!/usr/bin/env python3
"""Example usage of Adobe Firefly provider for various image generation tasks."""

import asyncio
import io
import os
from pathlib import Path

from PIL import Image

from alicemultiverse.providers import get_provider
from alicemultiverse.providers.base import GenerationRequest


async def text_to_image_example():
    """Generate images from text prompts."""
    print("\n=== Text to Image Example ===")

    provider = get_provider("firefly")

    # Basic generation
    request = GenerationRequest(
        prompt="A serene Japanese garden with cherry blossoms and a koi pond",
        model="firefly-v3",
        width=1024,
        height=1024,
        num_images=1,
        extra_params={
            "style_preset": "watercolor",
            "content_class": "art",
        }
    )

    print(f"Generating: {request.prompt}")
    result = await provider.generate(request)

    # Save the image
    if result.images:
        image = Image.open(io.BytesIO(result.images[0]))
        image.save("firefly_garden.png")
        print("Saved: firefly_garden.png")
        print(f"Cost: ${result.cost:.4f}")
        print(f"Metadata: {result.metadata}")


async def style_transfer_example():
    """Apply artistic styles from reference images."""
    print("\n=== Style Transfer Example ===")

    provider = get_provider("firefly")

    # Load a style reference image
    style_path = Path("style_reference.jpg")
    if not style_path.exists():
        print("Please provide a style_reference.jpg file")
        return

    with open(style_path, "rb") as f:
        style_data = f.read()

    request = GenerationRequest(
        prompt="A bustling city street at night",
        model="firefly-v3",
        width=1024,
        height=1024,
        extra_params={
            "style_reference": style_data,
            "style_strength": 80,  # Strong style influence
        }
    )

    print("Generating with style transfer...")
    result = await provider.generate(request)

    if result.images:
        image = Image.open(io.BytesIO(result.images[0]))
        image.save("firefly_styled_city.png")
        print("Saved: firefly_styled_city.png")


async def generative_fill_example():
    """Use generative fill to modify parts of an image."""
    print("\n=== Generative Fill Example ===")

    provider = get_provider("firefly")

    # Load input image and mask
    input_path = Path("input_image.jpg")
    mask_path = Path("mask.png")

    if not input_path.exists() or not mask_path.exists():
        print("Please provide input_image.jpg and mask.png files")
        return

    with open(input_path, "rb") as f:
        image_data = f.read()
    with open(mask_path, "rb") as f:
        mask_data = f.read()

    request = GenerationRequest(
        prompt="A vintage red convertible car",
        model="firefly-fill",
        width=1024,
        height=1024,
        image=image_data,
        mask=mask_data,
    )

    print("Performing generative fill...")
    result = await provider.generate(request)

    if result.images:
        image = Image.open(io.BytesIO(result.images[0]))
        image.save("firefly_filled.png")
        print("Saved: firefly_filled.png")


async def expand_image_example():
    """Expand an image beyond its original boundaries."""
    print("\n=== Generative Expand Example ===")

    provider = get_provider("firefly")

    # Load input image
    input_path = Path("input_image.jpg")
    if not input_path.exists():
        print("Please provide an input_image.jpg file")
        return

    with open(input_path, "rb") as f:
        image_data = f.read()

    # Load and check original dimensions
    original = Image.open(input_path)
    print(f"Original size: {original.size}")

    request = GenerationRequest(
        model="firefly-expand",
        width=original.width + 512,   # Add 512px width
        height=original.height + 256, # Add 256px height
        image=image_data,
        extra_params={
            "placement": {
                "inset": {
                    "left": 256,   # Expand 256px left
                    "right": 256,  # Expand 256px right
                    "top": 128,    # Expand 128px up
                    "bottom": 128  # Expand 128px down
                }
            }
        }
    )

    print("Expanding image...")
    result = await provider.generate(request)

    if result.images:
        image = Image.open(io.BytesIO(result.images[0]))
        image.save("firefly_expanded.png")
        print(f"Saved: firefly_expanded.png (new size: {image.size})")


async def batch_generation_example():
    """Generate multiple variations with different styles."""
    print("\n=== Batch Generation Example ===")

    provider = get_provider("firefly")

    styles = ["cyberpunk", "watercolor", "oil_paint", "anime"]
    prompt = "A majestic mountain landscape at sunrise"

    for style in styles:
        request = GenerationRequest(
            prompt=prompt,
            model="firefly-v3",
            width=1024,
            height=768,
            num_images=1,
            extra_params={
                "style_preset": style,
                "content_class": "art",
            }
        )

        print(f"Generating {style} style...")
        result = await provider.generate(request)

        if result.images:
            image = Image.open(io.BytesIO(result.images[0]))
            image.save(f"firefly_{style}_landscape.png")
            print(f"Saved: firefly_{style}_landscape.png")

    print("Batch generation complete!")


async def cost_estimation_example():
    """Demonstrate cost estimation before generation."""
    print("\n=== Cost Estimation Example ===")

    provider = get_provider("firefly")

    # Different request configurations
    requests = [
        GenerationRequest(
            prompt="Simple test",
            model="firefly-v3",
            width=512,
            height=512,
            num_images=1,
        ),
        GenerationRequest(
            prompt="High resolution test",
            model="firefly-v3",
            width=2048,
            height=2048,
            num_images=1,
        ),
        GenerationRequest(
            prompt="Multiple images",
            model="firefly-v3",
            width=1024,
            height=1024,
            num_images=4,
        ),
        GenerationRequest(
            prompt="With image input",
            model="firefly-fill",
            width=1024,
            height=1024,
            num_images=1,
            image=b"dummy_data",  # Just for estimation
        ),
    ]

    total_cost = 0
    for i, request in enumerate(requests, 1):
        cost = provider.estimate_cost(request)
        total_cost += cost
        print(f"Request {i}: ${cost:.4f} - {request.prompt}")

    print(f"\nTotal estimated cost: ${total_cost:.4f}")


async def main():
    """Run all examples."""
    # Check for API credentials
    if not os.getenv("ADOBE_CLIENT_ID") or not os.getenv("ADOBE_CLIENT_SECRET"):
        print("Please set ADOBE_CLIENT_ID and ADOBE_CLIENT_SECRET environment variables")
        print("Or provide them as 'client_id:client_secret' when getting the provider")
        return

    try:
        # Run examples
        await text_to_image_example()
        await cost_estimation_example()

        # These require additional files
        # await style_transfer_example()
        # await generative_fill_example()
        # await expand_image_example()
        # await batch_generation_example()

    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
