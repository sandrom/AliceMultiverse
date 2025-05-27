#!/usr/bin/env python3
"""
Example of using the fal.ai provider for AI image generation.

This example demonstrates:
- Registering API keys
- Generating images with different models
- Handling generation events
- Cost tracking
"""

import asyncio
from alicemultiverse.providers import registry, GenerationRequest, GenerationType
from alicemultiverse.events import EventBus


async def monitor_events():
    """Monitor generation events."""
    bus = EventBus()
    
    def on_generation_started(event):
        print(f"🎨 Generation started: {event.data['prompt'][:50]}...")
    
    def on_generation_completed(event):
        data = event.data
        print(f"✅ Generation completed:")
        print(f"   - Model: {data['model']}")
        print(f"   - Time: {data['generation_time']:.2f}s")
        print(f"   - Cost: ${data['cost']:.4f}")
        print(f"   - File: {data['file_path']}")
    
    def on_generation_failed(event):
        print(f"❌ Generation failed: {event.data['error']}")
    
    bus.subscribe("generation.started", on_generation_started)
    bus.subscribe("generation.completed", on_generation_completed)
    bus.subscribe("generation.failed", on_generation_failed)


async def generate_with_flux_schnell():
    """Generate an image with FLUX Schnell (fast model)."""
    print("\n=== FLUX Schnell (Fast) ===")
    
    provider = registry.get_provider("fal")
    
    request = GenerationRequest(
        prompt="A serene Japanese garden with cherry blossoms, koi pond, and traditional bridge, photorealistic, golden hour lighting",
        generation_type=GenerationType.IMAGE,
        model="flux-schnell",  # Fast model (~2s)
        parameters={
            "width": 1024,
            "height": 768
        }
    )
    
    result = await provider.generate(request)
    
    if result.success:
        print(f"Image saved to: {result.file_path}")
    else:
        print(f"Generation failed: {result.error}")
    
    return result


async def generate_with_flux_dev():
    """Generate an image with FLUX Dev (quality model)."""
    print("\n=== FLUX Dev (Quality) ===")
    
    provider = registry.get_provider("fal")
    
    request = GenerationRequest(
        prompt="A cyberpunk street scene with neon signs, rain-slicked streets, and futuristic vehicles, highly detailed, cinematic lighting",
        generation_type=GenerationType.IMAGE,
        model="flux-dev",  # Quality model (~10s)
        parameters={
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 50,  # More steps for better quality
            "guidance_scale": 3.5
        }
    )
    
    result = await provider.generate(request)
    
    if result.success:
        print(f"Image saved to: {result.file_path}")
    else:
        print(f"Generation failed: {result.error}")
    
    return result


async def generate_with_flux_realism():
    """Generate an image with FLUX Realism (photorealistic model)."""
    print("\n=== FLUX Realism (Photorealistic) ===")
    
    provider = registry.get_provider("fal")
    
    request = GenerationRequest(
        prompt="Professional headshot of a business executive in a modern office, natural lighting, shallow depth of field",
        generation_type=GenerationType.IMAGE,
        model="flux-realism",  # Photorealistic model
        parameters={
            "width": 768,
            "height": 1024,
            "num_images": 2  # Generate 2 variations
        }
    )
    
    result = await provider.generate(request)
    
    if result.success:
        print(f"Image saved to: {result.file_path}")
    else:
        print(f"Generation failed: {result.error}")
    
    return result


async def generate_with_flux_pro():
    """Generate an image with FLUX Pro (highest quality model)."""
    print("\n=== FLUX Pro (Premium Quality) ===")
    
    provider = registry.get_provider("fal")
    
    request = GenerationRequest(
        prompt="Award-winning photograph of a majestic eagle soaring through a dramatic sunset sky, professional wildlife photography, National Geographic style",
        generation_type=GenerationType.IMAGE,
        model="flux-pro",  # Premium model
        parameters={
            "width": 1024,
            "height": 1024,
            "num_inference_steps": 50,
            "guidance_scale": 3.5
        }
    )
    
    result = await provider.generate(request)
    
    if result.success:
        print(f"Image saved to: {result.file_path}")
    else:
        print(f"Generation failed: {result.error}")
    
    return result


async def generate_with_kling_text():
    """Generate a video with Kling text-to-video."""
    print("\n=== Kling v2 Text-to-Video ===")
    
    provider = registry.get_provider("fal")
    
    request = GenerationRequest(
        prompt="A graceful dancer performing ballet in a moonlit forest, ethereal atmosphere with fireflies floating around",
        generation_type=GenerationType.VIDEO,
        model="kling-v2-text",  # Latest Kling text-to-video
        parameters={
            "duration": "5",
            "aspect_ratio": "16:9",
            "cfg_scale": 0.5
        }
    )
    
    result = await provider.generate(request)
    
    if result.success:
        print(f"Video saved to: {result.file_path}")
    else:
        print(f"Generation failed: {result.error}")
    
    return result


async def generate_with_kling_elements():
    """Generate a video with Kling elements (special effects)."""
    print("\n=== Kling Elements (Special Effects) ===")
    
    provider = registry.get_provider("fal")
    
    request = GenerationRequest(
        prompt="Create a magical transformation effect with sparkling particles",
        generation_type=GenerationType.VIDEO,
        model="kling-elements",
        parameters={
            "effect": "heart_gesture",  # Special effect type
            "duration": "5",
            "aspect_ratio": "16:9"
        }
    )
    
    result = await provider.generate(request)
    
    if result.success:
        print(f"Video saved to: {result.file_path}")
    else:
        print(f"Generation failed: {result.error}")
    
    return result


async def check_provider_status():
    """Check fal.ai provider status."""
    provider = registry.get_provider("fal")
    status = await provider.check_status()
    print(f"Provider status: {status.value}")
    
    # Get capabilities
    caps = provider.get_capabilities()
    print(f"\nSupported models: {', '.join(caps.models)}")
    print(f"Max resolution: {caps.max_resolution['width']}x{caps.max_resolution['height']}")
    print(f"Features: {', '.join(caps.features)}")


async def main():
    """Run the example."""
    print("=== fal.ai Provider Example ===")
    
    # Check if API key is set
    api_key = registry._api_keys.get("fal")
    if not api_key:
        print("\n⚠️  No fal.ai API key found!")
        print("Please run: alice keys setup")
        print("Or set FAL_KEY environment variable")
        return
    
    # Start event monitoring
    await monitor_events()
    
    # Check provider status
    await check_provider_status()
    
    # Generate images with different models
    results = []
    
    # Fast generation
    result = await generate_with_flux_schnell()
    if result.success:
        results.append(result)
    
    # Quality generation (comment out to save costs)
    # result = await generate_with_flux_dev()
    # if result.success:
    #     results.append(result)
    
    # Photorealistic generation (comment out to save costs)
    # result = await generate_with_flux_realism()
    # if result.success:
    #     results.append(result)
    
    # Premium FLUX Pro generation (comment out to save costs)
    # result = await generate_with_flux_pro()
    # if result.success:
    #     results.append(result)
    
    # Kling video generation (comment out to save costs)
    # result = await generate_with_kling_text()
    # if result.success:
    #     results.append(result)
    
    # Kling elements (special effects) generation (comment out to save costs)
    # result = await generate_with_kling_elements()
    # if result.success:
    #     results.append(result)
    
    # Summary
    if results:
        print(f"\n=== Summary ===")
        print(f"Generated {len(results)} images")
        total_cost = sum(r.cost for r in results)
        total_time = sum(r.generation_time for r in results)
        print(f"Total cost: ${total_cost:.4f}")
        print(f"Total time: {total_time:.2f}s")
        
        print(f"\nGenerated files:")
        for r in results:
            print(f"  - {r.file_path}")


if __name__ == "__main__":
    # Initialize registry with API key (if available from environment)
    import os
    if fal_key := os.getenv("FAL_KEY"):
        registry.register_api_key("fal", fal_key)
    
    asyncio.run(main())