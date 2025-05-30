#!/usr/bin/env python3
"""Example usage of Google AI provider for Imagen and Veo generation."""

import asyncio
import os
from pathlib import Path
from PIL import Image
import io

from alicemultiverse.providers import get_provider
from alicemultiverse.providers.types import GenerationRequest, GenerationType
from alicemultiverse.providers.google_ai_provider import GoogleAIProvider, GoogleAIBackend


async def imagen_text_to_image_example():
    """Generate images from text prompts using Imagen 3."""
    print("\n=== Imagen 3 Text-to-Image Example ===")
    
    provider = get_provider("google-ai")
    
    # Single high-quality image
    request = GenerationRequest(
        prompt="A majestic snow leopard resting on a rocky outcrop at sunset, "
               "photorealistic wildlife photography style",
        generation_type=GenerationType.IMAGE,
        model="imagen-3",
        parameters={
            "number_of_images": 1,
            "aspect_ratio": "16:9",
            "negative_prompt": "cartoon, illustration, low quality",
        }
    )
    
    print(f"Generating: {request.prompt}")
    result = await provider.generate(request)
    
    if result.success:
        print(f"Success! Image saved to: {result.file_path}")
        print(f"Cost: ${result.cost}")
        print(f"Metadata: {result.metadata}")
    else:
        print(f"Error: {result.error}")


async def imagen_batch_generation_example():
    """Generate multiple image variations."""
    print("\n=== Imagen 3 Batch Generation Example ===")
    
    provider = get_provider("google-ai")
    
    # Generate 4 variations
    request = GenerationRequest(
        prompt="A cozy coffee shop interior with warm lighting, "
               "plants, and vintage furniture",
        generation_type=GenerationType.IMAGE,
        model="imagen-3",
        parameters={
            "number_of_images": 4,  # Maximum allowed
            "aspect_ratio": "1:1",   # Square for social media
            "seed": 42,              # For consistency
        }
    )
    
    print(f"Generating 4 variations...")
    result = await provider.generate(request)
    
    if result.success:
        print(f"Generated {request.parameters['number_of_images']} images")
        print(f"Total cost: ${result.cost}")


async def imagen_style_examples():
    """Generate images in different styles."""
    print("\n=== Imagen 3 Style Examples ===")
    
    provider = get_provider("google-ai")
    
    styles = [
        ("photorealistic", "photorealistic 8k professional photography"),
        ("oil painting", "oil painting on canvas, brushstrokes visible"),
        ("watercolor", "delicate watercolor painting, soft colors"),
        ("3d render", "3d rendered, octane render, ray tracing"),
    ]
    
    base_prompt = "A red fox in an autumn forest"
    
    for style_name, style_modifier in styles:
        request = GenerationRequest(
            prompt=f"{base_prompt}, {style_modifier}",
            generation_type=GenerationType.IMAGE,
            model="imagen-3",
            parameters={
                "number_of_images": 1,
                "aspect_ratio": "4:3",
            }
        )
        
        print(f"Generating {style_name} style...")
        result = await provider.generate(request)
        
        if result.success:
            print(f"✓ {style_name} completed")


async def veo_text_to_video_example():
    """Generate video from text prompt using Veo 2."""
    print("\n=== Veo 2 Text-to-Video Example ===")
    
    provider = get_provider("google-ai")
    
    # Generate an 8-second video
    request = GenerationRequest(
        prompt="A time-lapse of clouds moving over mountain peaks, "
               "dramatic lighting, cinematic",
        generation_type=GenerationType.VIDEO,
        model="veo-2",
        parameters={
            "aspect_ratio": "16:9",
            "negative_prompt": "static, still image",
        }
    )
    
    print(f"Generating video: {request.prompt}")
    print("This may take 30-60 seconds...")
    
    result = await provider.generate(request)
    
    if result.success:
        print(f"Success! Video saved to: {result.file_path}")
        print(f"Cost: ${result.cost}")
        print("Duration: 8 seconds")
    else:
        print(f"Error: {result.error}")


async def veo_image_to_video_example():
    """Animate a still image using Veo 2."""
    print("\n=== Veo 2 Image-to-Video Example ===")
    
    # Check if we have an input image
    input_image = Path("sunset.jpg")
    if not input_image.exists():
        print("Please provide a sunset.jpg file for this example")
        return
    
    provider = get_provider("google-ai")
    
    # Load the image
    with open(input_image, "rb") as f:
        image_data = f.read()
    
    # Animate the image
    request = GenerationRequest(
        prompt="Gentle waves lapping on the shore, birds flying across the sky",
        generation_type=GenerationType.VIDEO,
        model="veo-2",
        reference_assets=[str(input_image)],
        parameters={
            "image_data": image_data,
            "aspect_ratio": "16:9",
        }
    )
    
    print(f"Animating image with prompt: {request.prompt}")
    result = await provider.generate(request)
    
    if result.success:
        print(f"Success! Animated video saved to: {result.file_path}")
    else:
        print(f"Error: {result.error}")


async def vertex_ai_example():
    """Example using Vertex AI backend instead of Gemini."""
    print("\n=== Vertex AI Backend Example ===")
    
    # Check for Vertex AI requirements
    project_id = os.getenv("GOOGLE_CLOUD_PROJECT")
    if not project_id:
        print("Please set GOOGLE_CLOUD_PROJECT environment variable")
        return
    
    # Initialize with Vertex backend
    provider = GoogleAIProvider(
        backend=GoogleAIBackend.VERTEX,
        project_id=project_id,
        location="us-central1"
    )
    
    await provider.initialize()
    
    request = GenerationRequest(
        prompt="A futuristic space station orbiting Earth",
        generation_type=GenerationType.IMAGE,
        model="imagen-3",
        parameters={
            "number_of_images": 1,
            "aspect_ratio": "16:9",
        }
    )
    
    print(f"Generating via Vertex AI: {request.prompt}")
    result = await provider._generate(request)
    
    if result.success:
        print(f"Success! Backend: {result.metadata['backend']}")


async def cost_estimation_example():
    """Demonstrate cost estimation before generation."""
    print("\n=== Cost Estimation Example ===")
    
    provider = get_provider("google-ai")
    
    # Different request configurations
    requests = [
        GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.IMAGE,
            model="imagen-3",
            parameters={"number_of_images": 1}
        ),
        GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.IMAGE,
            model="imagen-3",
            parameters={"number_of_images": 4}
        ),
        GenerationRequest(
            prompt="Test",
            generation_type=GenerationType.VIDEO,
            model="veo-2",
        ),
    ]
    
    total_cost = 0
    for i, request in enumerate(requests, 1):
        cost = await provider.estimate_cost(request)
        total_cost += cost
        gen_type = request.generation_type.value
        num = request.parameters.get("number_of_images", 1) if gen_type == "image" else 1
        print(f"Request {i}: ${cost:.2f} - {gen_type} x{num}")
    
    print(f"\nTotal estimated cost: ${total_cost:.2f}")


async def main():
    """Run all examples."""
    # Check for API credentials
    if not os.getenv("GOOGLE_AI_API_KEY") and not os.getenv("GEMINI_API_KEY"):
        print("Please set GOOGLE_AI_API_KEY or GEMINI_API_KEY environment variable")
        print("Get your API key from: https://aistudio.google.com/")
        return
    
    try:
        # Run examples
        await imagen_text_to_image_example()
        await cost_estimation_example()
        
        # These take longer
        # await imagen_batch_generation_example()
        # await imagen_style_examples()
        # await veo_text_to_video_example()
        
        # These require additional setup
        # await veo_image_to_video_example()
        # await vertex_ai_example()
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(main())