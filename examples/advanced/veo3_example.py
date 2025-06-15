#!/usr/bin/env python3
"""
Example of using Google Veo 3 for video generation via fal.ai.

Veo 3 is Google's state-of-the-art video generation model featuring:
- Native sound generation
- Speech capabilities with lip sync
- Improved physics and realism
- Better prompt adherence
"""

import asyncio
import os
from pathlib import Path

from alicemultiverse.providers.fal_provider import FalProvider
from alicemultiverse.providers.types import GenerationRequest, GenerationType


async def generate_veo3_video():
    """Generate a video using Google Veo 3 on fal.ai."""

    # Initialize provider
    provider = FalProvider()

    # Example 1: Basic text-to-video
    print("Generating basic video with Veo 3...")
    request = GenerationRequest(
        prompt="A serene Japanese garden with cherry blossoms gently falling, koi fish swimming in a pond, soft morning light",
        model="veo-3",
        generation_type=GenerationType.VIDEO,
        output_path=Path("output/veo3"),
        parameters={
            "duration": 5,  # 5 seconds
            "aspect_ratio": "16:9",
            "enable_audio": False,  # Set to True for audio (costs more)
        }
    )

    result = await provider.generate(request)

    if result.success:
        print(f"✓ Video generated: {result.file_path}")
        print(f"  Cost: ${result.cost:.2f}")
    else:
        print(f"✗ Generation failed: {result.error}")

    # Example 2: Video with native audio
    print("\nGenerating video with audio...")
    request_audio = GenerationRequest(
        prompt="A bustling city street with cars honking, people talking, and birds chirping in the trees above",
        model="veo-3",
        generation_type=GenerationType.VIDEO,
        output_path=Path("output/veo3"),
        parameters={
            "duration": 5,
            "aspect_ratio": "16:9",
            "enable_audio": True,  # Enable native audio generation
        }
    )

    result_audio = await provider.generate(request_audio)

    if result_audio.success:
        print(f"✓ Video with audio generated: {result_audio.file_path}")
        print(f"  Cost: ${result_audio.cost:.2f} (higher due to audio)")
    else:
        print(f"✗ Generation failed: {result_audio.error}")

    # Example 3: Speech and lip sync
    print("\nGenerating video with speech...")
    request_speech = GenerationRequest(
        prompt='A professional news anchor saying "Welcome to the evening news. Today\'s top story..." with accurate lip sync',
        model="veo-3",
        generation_type=GenerationType.VIDEO,
        output_path=Path("output/veo3"),
        parameters={
            "duration": 5,
            "aspect_ratio": "16:9",
            "enable_audio": True,  # Required for speech
        }
    )

    result_speech = await provider.generate(request_speech)

    if result_speech.success:
        print(f"✓ Video with speech generated: {result_speech.file_path}")
        print(f"  Cost: ${result_speech.cost:.2f}")
    else:
        print(f"✗ Generation failed: {result_speech.error}")

    await provider.cleanup()


async def compare_veo3_styles():
    """Compare different styles with Veo 3."""

    provider = FalProvider()

    styles = [
        "cinematic drone shot",
        "handheld documentary style",
        "smooth steadicam movement",
        "static tripod shot",
    ]

    base_prompt = "A mountain lake at sunset with mist rising from the water"

    for style in styles:
        print(f"\nGenerating {style}...")
        request = GenerationRequest(
            prompt=f"{base_prompt}, {style}",
            model="veo-3",
            generation_type=GenerationType.VIDEO,
            output_path=Path("output/veo3/styles"),
            parameters={
                "duration": 5,
                "aspect_ratio": "16:9",
                "enable_audio": False,
            }
        )

        result = await provider.generate(request)

        if result.success:
            print(f"✓ {style}: {result.file_path}")
        else:
            print(f"✗ {style} failed: {result.error}")

    await provider.cleanup()


async def veo3_physics_demo():
    """Demonstrate Veo 3's improved physics understanding."""

    provider = FalProvider()

    physics_prompts = [
        "Water pouring into a glass, creating ripples and bubbles",
        "A feather floating down in slow motion, twisting in the air",
        "Dominos falling in a perfect cascade, shot from above",
        "Smoke rising from a candle, swirling in the breeze",
    ]

    for prompt in physics_prompts:
        print(f"\nGenerating physics demo: {prompt[:50]}...")
        request = GenerationRequest(
            prompt=prompt,
            model="veo-3",
            generation_type=GenerationType.VIDEO,
            output_path=Path("output/veo3/physics"),
            parameters={
                "duration": 5,
                "aspect_ratio": "16:9",
                "enable_audio": True,  # Include realistic sound effects
            }
        )

        result = await provider.generate(request)

        if result.success:
            print(f"✓ Generated: {result.file_path}")
        else:
            print(f"✗ Failed: {result.error}")

    await provider.cleanup()


if __name__ == "__main__":
    # Check for API key
    if not os.getenv("FAL_KEY"):
        print("Please set FAL_KEY environment variable")
        print("Get your API key from: https://fal.ai/dashboard/keys")
        exit(1)

    print("Google Veo 3 Examples")
    print("=" * 50)
    print("\nVeo 3 Features:")
    print("- Native audio generation (ambient sounds, music)")
    print("- Speech capabilities with accurate lip sync")
    print("- Improved physics and realism")
    print("- Better prompt adherence")
    print("- 5-8 second video generation")
    print("\nPricing:")
    print("- Without audio: $0.50/second ($2.50 for 5s)")
    print("- With audio: $0.75/second ($3.75 for 5s)")
    print("=" * 50)

    # Run examples
    asyncio.run(generate_veo3_video())

    # Uncomment to run additional demos:
    # asyncio.run(compare_veo3_styles())
    # asyncio.run(veo3_physics_demo())
