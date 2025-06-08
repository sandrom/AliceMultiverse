#!/usr/bin/env python3
"""Example of using the new video generation providers."""

import asyncio
from pathlib import Path

from alicemultiverse.providers import get_provider
from alicemultiverse.providers.types import GenerationRequest


async def main():
    """Demonstrate new video provider capabilities."""
    
    # Example 1: Runway Gen-3 Alpha - High quality video
    print("1. Runway Gen-3 Alpha - Professional quality video")
    runway = get_provider("runway")
    
    request = GenerationRequest(
        prompt="A serene Japanese garden with cherry blossoms falling in slow motion, cinematic lighting",
        model="gen3-alpha",
        output_path=Path("outputs/runway_garden.mp4"),
        parameters={
            "duration": 10,  # 10 seconds
            "camera_motion": "slow_zoom_in",
            "style": "cinematic",
        }
    )
    
    result = await runway.generate(request)
    print(f"Generated: {result.output_path} (cost: ${result.cost:.2f})")
    
    # Example 2: Pika Labs - Ingredient control
    print("\n2. Pika Labs - Fine-grained ingredient control")
    pika = get_provider("pika")
    
    request = GenerationRequest(
        prompt="A fantasy scene with magical elements",
        model="pika-2.1-hd",
        output_path=Path("outputs/pika_fantasy.mp4"),
        parameters={
            "aspect_ratio": "16:9",
            "ingredients": [
                {"type": "character", "description": "wise wizard with flowing robes"},
                {"type": "object", "description": "glowing crystal orb"},
                {"type": "environment", "description": "ancient library with floating books"},
                {"type": "style", "description": "ethereal lighting with particle effects"}
            ],
            "motion_strength": 0.7,
        }
    )
    
    result = await pika.generate(request)
    print(f"Generated: {result.output_path} (cost: ${result.cost:.2f})")
    
    # Example 3: Luma Dream Machine - Perfect loops
    print("\n3. Luma Dream Machine - Creating perfect loops")
    luma = get_provider("luma")
    
    request = GenerationRequest(
        prompt="Abstract flowing liquid metal, seamless loop",
        model="luma-loop",
        output_path=Path("outputs/luma_loop.mp4"),
        parameters={
            "loop_frames": 120,  # 5 seconds
            "motion_scale": 0.8,
            "camera_motion": "orbit_left",
        }
    )
    
    result = await luma.generate(request)
    print(f"Generated: {result.output_path} (cost: ${result.cost:.2f})")
    
    # Example 4: Luma Keyframe Control
    print("\n4. Luma Dream Machine - Multi-keyframe animation")
    
    request = GenerationRequest(
        prompt="Transformation sequence",
        model="luma-keyframes",
        output_path=Path("outputs/luma_keyframes.mp4"),
        parameters={
            "keyframes": [
                {"frame": 0, "prompt": "A simple wooden cube on a table"},
                {"frame": 30, "prompt": "The cube begins to glow and levitate"},
                {"frame": 60, "prompt": "The cube transforms into a golden sphere"},
                {"frame": 90, "prompt": "The sphere explodes into butterflies"},
                {"frame": 120, "prompt": "The butterflies form a new shape"}
            ]
        }
    )
    
    result = await luma.generate(request)
    print(f"Generated: {result.output_path} (cost: ${result.cost:.2f})")
    
    # Example 5: MiniMax Hailuo - Music video generation
    print("\n5. MiniMax Hailuo - Music-driven video")
    minimax = get_provider("minimax")
    
    request = GenerationRequest(
        prompt="Dynamic abstract visuals synced to music",
        model="hailuo-music-video",
        output_path=Path("outputs/minimax_music.mp4"),
        parameters={
            "music_url": "https://example.com/music.mp3",  # Replace with actual URL
            "sync_to_beat": True,
            "motion_intensity": 0.9,
        }
    )
    
    # Note: This would fail without a valid music URL
    # result = await minimax.generate(request)
    print("Music video generation requires a valid music URL")
    
    # Example 6: MiniMax Style Transfer
    print("\n6. MiniMax Hailuo - Style transfer video")
    
    request = GenerationRequest(
        prompt="A bustling city street",
        model="hailuo-style-transfer",
        output_path=Path("outputs/minimax_style.mp4"),
        parameters={
            "style_reference": "https://example.com/style.jpg",  # Van Gogh style
            "style_strength": 0.8,
            "language": "en",
        }
    )
    
    # Note: This would fail without a valid style reference
    # result = await minimax.generate(request)
    print("Style transfer requires a valid style reference URL")
    
    # Example 7: Cost comparison across providers
    print("\n\n=== Cost Comparison for 5-second video ===")
    test_request = GenerationRequest(
        prompt="A beautiful sunset over the ocean",
        parameters={"duration": 5}
    )
    
    providers = {
        "Runway Gen-3 Alpha": ("runway", "gen3-alpha"),
        "Runway Gen-3 Turbo": ("runway", "gen3-alpha-turbo"),
        "Pika 2.1 Standard": ("pika", "pika-2.1"),
        "Pika 2.1 HD": ("pika", "pika-2.1-hd"),
        "Luma Dream Machine": ("luma", "dream-machine"),
        "Luma Turbo": ("luma", "dream-machine-turbo"),
        "MiniMax Hailuo": ("minimax", "hailuo-video"),
        "MiniMax Pro": ("minimax", "hailuo-video-pro"),
    }
    
    for name, (provider_name, model) in providers.items():
        provider = get_provider(provider_name)
        test_request.model = model
        cost = provider.estimate_cost(test_request)
        print(f"{name:<25} ${cost:.2f}")
    
    # Example 8: Batch generation for A/B testing
    print("\n\n=== A/B Testing Different Providers ===")
    prompt = "A futuristic cityscape at night with flying cars"
    
    tasks = []
    providers_to_test = [
        ("runway", "gen3-alpha-turbo", "outputs/ab_runway.mp4"),
        ("pika", "pika-2.1", "outputs/ab_pika.mp4"),
        ("luma", "dream-machine-turbo", "outputs/ab_luma.mp4"),
        ("minimax", "hailuo-video", "outputs/ab_minimax.mp4"),
    ]
    
    for provider_name, model, output in providers_to_test:
        provider = get_provider(provider_name)
        request = GenerationRequest(
            prompt=prompt,
            model=model,
            output_path=Path(output),
            parameters={"seed": 42}  # Same seed for consistency
        )
        # tasks.append(provider.generate(request))
    
    # results = await asyncio.gather(*tasks, return_exceptions=True)
    print("A/B testing would generate videos from all providers")


if __name__ == "__main__":
    # Note: This example shows the API but won't run without valid API keys
    print("=== New Video Provider Examples ===")
    print("Note: Set API keys before running:")
    print("  export RUNWAY_API_KEY='your-key'")
    print("  export PIKA_API_KEY='your-key'")
    print("  export LUMA_API_KEY='your-key'")
    print("  export MINIMAX_API_KEY='your-key'")
    print("\nRunning examples (some will be skipped)...\n")
    
    asyncio.run(main())