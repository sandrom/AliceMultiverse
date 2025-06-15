"""
Example script demonstrating Midjourney integration via proxy API.

Midjourney doesn't have an official API, so we use proxy services like UseAPI.
"""

import asyncio
import os
from pathlib import Path

from alicemultiverse.providers.midjourney_provider import MidjourneyProvider
from alicemultiverse.providers.types import GenerationRequest


async def main():
    """Run Midjourney generation examples."""

    # Option 1: UseAPI (recommended)
    api_key = os.getenv("USEAPI_API_KEY")
    if not api_key:
        print("Please set USEAPI_API_KEY environment variable")
        print("Get your key from: https://useapi.net")
        return

    # Initialize provider
    provider = MidjourneyProvider(
        api_key=api_key,
        proxy_service="useapi"
    )

    # Check status
    status = await provider.check_status()
    print(f"Provider status: {status.value}")

    # Example 1: Basic generation
    print("\n1. Basic Midjourney generation:")
    request = GenerationRequest(
        prompt="A futuristic cityscape at sunset, cyberpunk style --v 6.1 --ar 16:9",
        output_path=Path("output/midjourney/example1.png")
    )

    result = await provider.generate(request)
    print(f"Generated: {result.file_path}")
    print(f"Cost: ${result.cost:.2f}")
    print(f"Time: {result.generation_time:.1f}s")
    print(f"Metadata: {result.metadata}")

    # Example 2: Different model version
    print("\n2. Using Niji model for anime style:")
    request2 = GenerationRequest(
        prompt="A magical forest with glowing flowers, studio ghibli style --niji 6",
        output_path=Path("output/midjourney/example2.png")
    )

    result2 = await provider.generate(request2)
    print(f"Generated: {result2.file_path}")
    print(f"Model: {result2.model}")

    # Example 3: Advanced parameters
    print("\n3. Advanced parameters:")
    request3 = GenerationRequest(
        prompt=(
            "Portrait of a robot philosopher deep in thought "
            "--v 6.1 --q 2 --s 750 --c 20 --no blur, distortion"
        ),
        output_path=Path("output/midjourney/example3.png")
    )

    result3 = await provider.generate(request3)
    print(f"Generated: {result3.file_path}")
    print(f"Parameters: {result3.metadata.get('parameters')}")

    # Example 4: Image-to-image (if you have an image URL)
    # Uncomment if you have an image URL to test with
    # print("\n4. Image-to-image generation:")
    # request4 = GenerationRequest(
    #     prompt="Transform this into a watercolor painting --v 6.1",
    #     reference_assets=["https://example.com/your-image.jpg"],
    #     output_path=Path("output/midjourney/example4.png")
    # )
    # result4 = await provider.generate(request4)
    # print(f"Generated: {result4.file_path}")


async def test_different_proxy_services():
    """Test different proxy service configurations."""

    # GoAPI example
    goapi_key = os.getenv("GOAPI_API_KEY")
    if goapi_key:
        print("\nTesting GoAPI proxy:")
        provider = MidjourneyProvider(
            api_key=goapi_key,
            proxy_service="goapi"
        )

        request = GenerationRequest(
            prompt="A serene mountain landscape at dawn --v 6.1",
            output_path=Path("output/midjourney/goapi-test.png")
        )

        result = await provider.generate(request)
        print(f"Generated via GoAPI: {result.file_path}")

    # Custom proxy example
    custom_url = os.getenv("CUSTOM_MIDJOURNEY_URL")
    custom_key = os.getenv("CUSTOM_MIDJOURNEY_KEY")
    if custom_url and custom_key:
        print("\nTesting custom proxy:")
        provider = MidjourneyProvider(
            api_key=custom_key,
            proxy_service="custom",
            proxy_url=custom_url
        )

        request = GenerationRequest(
            prompt="Abstract art with vibrant colors --v 6.1",
            output_path=Path("output/midjourney/custom-test.png")
        )

        result = await provider.generate(request)
        print(f"Generated via custom proxy: {result.file_path}")


async def test_with_registry():
    """Test using the provider registry."""
    from alicemultiverse.providers import get_provider_async

    # Get provider from registry
    provider = await get_provider_async("midjourney")

    request = GenerationRequest(
        prompt="A steampunk airship flying through clouds --v 6.1 --ar 16:9",
        output_path=Path("output/midjourney/registry-test.png")
    )

    result = await provider.generate(request)
    print(f"Generated via registry: {result.file_path}")


def parse_midjourney_prompts():
    """Show how Midjourney prompts are parsed."""
    from alicemultiverse.providers.midjourney_provider import MidjourneyProvider

    provider = MidjourneyProvider(api_key="dummy")  # Just for parsing

    test_prompts = [
        "A simple landscape",
        "A landscape --v 6",
        "A portrait --ar 9:16 --q 2",
        "Complex scene --v 6.1 --ar 16:9 --s 1000 --c 50 --no blur, artifacts",
        "Anime style character --niji 6",
    ]

    print("\nPrompt parsing examples:")
    for prompt in test_prompts:
        parsed = provider._parse_prompt(prompt)
        print(f"\nOriginal: {prompt}")
        print(f"Base prompt: {parsed['prompt']}")
        print(f"Version: {parsed['version']}")
        print(f"Parameters: {parsed['parameters']}")


if __name__ == "__main__":
    # Run the main example
    asyncio.run(main())

    # Uncomment to test other features
    # asyncio.run(test_different_proxy_services())
    # asyncio.run(test_with_registry())
    # parse_midjourney_prompts()
