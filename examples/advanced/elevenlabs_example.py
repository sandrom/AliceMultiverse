"""Example usage of ElevenLabs provider for AI sound effects generation.

This example demonstrates:
1. Basic sound effect generation
2. Duration and influence control
3. Different output formats
4. Batch generation for multiple sounds
5. Error handling
"""

import asyncio
import os
from pathlib import Path

from alicemultiverse.providers import get_provider, GenerationRequest, GenerationType


async def basic_sound_generation():
    """Generate a simple sound effect."""
    print("\n=== Basic Sound Generation ===")
    
    # Get provider
    provider = get_provider("elevenlabs")
    
    # Create request
    request = GenerationRequest(
        prompt="dog barking happily",
        generation_type=GenerationType.AUDIO,
        output_path=Path("output/elevenlabs/dog_bark.mp3")
    )
    
    # Generate
    print(f"Generating: {request.prompt}")
    result = await provider.generate(request)
    
    if result.success:
        print(f"✓ Generated: {result.file_path}")
        print(f"  Cost: ${result.cost:.3f}")
        print(f"  Duration: Auto-determined")
    else:
        print(f"✗ Failed: {result.error}")


async def custom_duration_example():
    """Generate sound with specific duration."""
    print("\n=== Custom Duration Example ===")
    
    provider = get_provider("elevenlabs")
    
    # Sound effect with specific duration
    request = GenerationRequest(
        prompt="thunderstorm with heavy rain",
        generation_type=GenerationType.AUDIO,
        parameters={
            "duration_seconds": 15,  # 15 second thunderstorm
            "prompt_influence": 0.7  # Higher influence for more accurate sound
        },
        output_path=Path("output/elevenlabs/thunderstorm_15s.mp3")
    )
    
    print(f"Generating: {request.prompt} (15 seconds)")
    result = await provider.generate(request)
    
    if result.success:
        print(f"✓ Generated: {result.file_path}")
        print(f"  Duration: {result.metadata.get('duration_seconds')}s")
        print(f"  Prompt influence: {result.metadata.get('prompt_influence')}")


async def different_formats_example():
    """Generate sounds in different formats."""
    print("\n=== Different Output Formats ===")
    
    provider = get_provider("elevenlabs")
    
    formats = [
        ("mp3_44100_128", "Standard MP3 (128 kbps)"),
        ("mp3_44100_192", "High-quality MP3 (192 kbps) - Pro tier"),
        ("pcm_44100", "Uncompressed PCM (WAV) - Pro tier")
    ]
    
    for format_code, description in formats:
        request = GenerationRequest(
            prompt="water drops in a cave",
            generation_type=GenerationType.AUDIO,
            parameters={
                "duration_seconds": 5,
                "output_format": format_code
            },
            output_path=Path(f"output/elevenlabs/water_drops.{format_code.split('_')[0]}")
        )
        
        print(f"\nGenerating in {description}...")
        try:
            result = await provider.generate(request)
            if result.success:
                print(f"✓ Generated: {result.file_path}")
                print(f"  Format: {format_code}")
        except Exception as e:
            print(f"✗ Failed: {e}")
            if "Pro tier" in description:
                print("  Note: This format requires a Pro subscription")


async def cinematic_sounds_example():
    """Generate cinematic sound effects for film/video."""
    print("\n=== Cinematic Sound Effects ===")
    
    provider = get_provider("elevenlabs")
    
    # Collection of cinematic sounds
    cinematic_prompts = [
        ("spaceship engine starting up with a deep rumble", "scifi_engine.mp3"),
        ("sword being unsheathed with metallic ring", "sword_unsheath.mp3"),
        ("wooden door creaking open slowly in haunted house", "creaky_door.mp3"),
        ("footsteps on gravel approaching slowly", "footsteps_gravel.mp3"),
        ("magical spell casting with ethereal chimes", "magic_spell.mp3")
    ]
    
    results = []
    
    for prompt, filename in cinematic_prompts:
        request = GenerationRequest(
            prompt=prompt,
            generation_type=GenerationType.AUDIO,
            parameters={
                "prompt_influence": 0.4  # Balanced for cinematic quality
            },
            output_path=Path(f"output/elevenlabs/cinematic/{filename}")
        )
        
        print(f"\nGenerating: {prompt}")
        try:
            result = await provider.generate(request)
            if result.success:
                print(f"✓ Generated: {result.file_path}")
                results.append((prompt, result))
        except Exception as e:
            print(f"✗ Failed: {e}")
    
    # Summary
    print(f"\n\nGenerated {len(results)}/{len(cinematic_prompts)} cinematic sounds")
    total_cost = sum(r[1].cost for r in results if r[1].cost)
    print(f"Total cost: ${total_cost:.2f}")


async def game_audio_example():
    """Generate sound effects for game development."""
    print("\n=== Game Sound Effects ===")
    
    provider = get_provider("elevenlabs")
    
    # Common game sounds
    game_sounds = {
        "coin_collect": "coin pickup with bright chime",
        "jump": "character jump with light whoosh",
        "hit": "impact sound for hitting enemy",
        "powerup": "power-up collection with ascending tones",
        "game_over": "game over sound with descending tones"
    }
    
    for sound_name, prompt in game_sounds.items():
        request = GenerationRequest(
            prompt=prompt,
            generation_type=GenerationType.AUDIO,
            parameters={
                "duration_seconds": 2,  # Short sounds for games
                "prompt_influence": 0.6
            },
            output_path=Path(f"output/elevenlabs/game/{sound_name}.mp3")
        )
        
        print(f"\nGenerating {sound_name}: {prompt}")
        result = await provider.generate(request)
        
        if result.success:
            print(f"✓ Ready for game engine: {result.file_path}")


async def ambient_soundscape_example():
    """Generate ambient soundscapes."""
    print("\n=== Ambient Soundscapes ===")
    
    provider = get_provider("elevenlabs")
    
    # Longer ambient sounds
    soundscapes = [
        {
            "name": "forest_morning",
            "prompt": "peaceful forest ambience with birds chirping and gentle wind",
            "duration": 20,
            "influence": 0.3  # Lower influence for more natural variation
        },
        {
            "name": "city_night",
            "prompt": "urban night ambience with distant traffic and occasional sirens",
            "duration": 22,  # Max duration
            "influence": 0.2
        },
        {
            "name": "beach_waves",
            "prompt": "ocean waves gently crashing on beach with seagulls",
            "duration": 18,
            "influence": 0.25
        }
    ]
    
    for soundscape in soundscapes:
        request = GenerationRequest(
            prompt=soundscape["prompt"],
            generation_type=GenerationType.AUDIO,
            parameters={
                "duration_seconds": soundscape["duration"],
                "prompt_influence": soundscape["influence"]
            },
            output_path=Path(f"output/elevenlabs/ambient/{soundscape['name']}.mp3")
        )
        
        print(f"\nGenerating {soundscape['duration']}s soundscape: {soundscape['name']}")
        result = await provider.generate(request)
        
        if result.success:
            print(f"✓ Created ambient track: {result.file_path}")


async def batch_generation_with_progress():
    """Generate multiple sounds with progress tracking."""
    print("\n=== Batch Generation with Progress ===")
    
    provider = get_provider("elevenlabs")
    
    # List of sounds to generate
    sound_list = [
        "cat meowing softly",
        "keyboard typing quickly",
        "glass breaking dramatically",
        "car engine revving",
        "phone notification sound"
    ]
    
    total = len(sound_list)
    successful = 0
    total_cost = 0.0
    
    for i, prompt in enumerate(sound_list, 1):
        print(f"\n[{i}/{total}] Generating: {prompt}")
        
        request = GenerationRequest(
            prompt=prompt,
            generation_type=GenerationType.AUDIO,
            output_path=Path(f"output/elevenlabs/batch/sound_{i:02d}.mp3")
        )
        
        try:
            result = await provider.generate(request)
            if result.success:
                successful += 1
                total_cost += result.cost or 0
                print(f"✓ Success! Cost: ${result.cost:.3f}")
        except Exception as e:
            print(f"✗ Error: {e}")
    
    print(f"\n=== Batch Complete ===")
    print(f"Generated: {successful}/{total} sounds")
    print(f"Total cost: ${total_cost:.2f}")
    print(f"Average cost: ${total_cost/successful:.3f} per sound")


async def error_handling_example():
    """Demonstrate error handling."""
    print("\n=== Error Handling Example ===")
    
    # Test with missing API key
    try:
        os.environ.pop("ELEVENLABS_API_KEY", None)
        provider = get_provider("elevenlabs")
    except ValueError as e:
        print(f"✓ Caught missing API key: {e}")
    
    # Test with invalid parameters
    os.environ["ELEVENLABS_API_KEY"] = "test-key"
    provider = get_provider("elevenlabs")
    
    request = GenerationRequest(
        prompt="test sound",
        generation_type=GenerationType.IMAGE  # Wrong type!
    )
    
    try:
        await provider.generate(request)
    except Exception as e:
        print(f"✓ Caught wrong generation type: {e}")


async def main():
    """Run all examples."""
    print("ElevenLabs Sound Effects Examples")
    print("=" * 50)
    
    # Check for API key
    if not os.getenv("ELEVENLABS_API_KEY"):
        print("\n⚠️  Please set ELEVENLABS_API_KEY environment variable!")
        print("   Get your API key from: https://elevenlabs.io/")
        return
    
    # Run examples
    await basic_sound_generation()
    await custom_duration_example()
    await different_formats_example()
    await cinematic_sounds_example()
    await game_audio_example()
    await ambient_soundscape_example()
    await batch_generation_with_progress()
    await error_handling_example()
    
    print("\n✅ All examples complete!")


if __name__ == "__main__":
    asyncio.run(main())