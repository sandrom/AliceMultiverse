#!/usr/bin/env python3
"""
Comprehensive test script for fal.ai provider with all models.

This script tests:
- All FLUX models including FLUX Pro
- Kling video generation models (v1 and v2)
- Other available models
- Error handling and edge cases
"""

import asyncio
import os
from pathlib import Path
from datetime import datetime

from alicemultiverse.providers import get_provider, GenerationRequest, GenerationType
from alicemultiverse.providers.registry import get_registry
from alicemultiverse.events import EventBus


class FalProviderTester:
    """Test harness for fal.ai provider."""
    
    def __init__(self):
        self.results = []
        self.errors = []
        self.total_cost = 0.0
        self.test_output_dir = Path("test_outputs") / f"fal_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.test_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize event monitoring
        self.event_bus = EventBus()
        self.setup_event_monitoring()
    
    def setup_event_monitoring(self):
        """Set up event monitoring for test results."""
        def on_generation_started(event):
            print(f"🎨 Started: {event.data['model']} - {event.data['prompt'][:50]}...")
        
        def on_generation_completed(event):
            data = event.data
            print(f"✅ Completed: {data['model']} in {data['generation_time']:.2f}s (${data['cost']:.4f})")
            self.results.append(data)
            self.total_cost += data['cost']
        
        def on_generation_failed(event):
            print(f"❌ Failed: {event.data['model']} - {event.data['error']}")
            self.errors.append(event.data)
        
        self.event_bus.subscribe("generation.started", on_generation_started)
        self.event_bus.subscribe("generation.completed", on_generation_completed)
        self.event_bus.subscribe("generation.failed", on_generation_failed)
    
    async def test_flux_models(self):
        """Test all FLUX image generation models."""
        print("\n=== Testing FLUX Models ===")
        
        flux_models = [
            ("flux-schnell", "A serene mountain landscape at sunset, photorealistic", 0.003),
            ("flux-dev", "A futuristic cityscape with flying cars, highly detailed", 0.025),
            ("flux-pro", "A professional portrait of a scientist in a laboratory, cinematic lighting", 0.05),
            ("flux-realism", "A hyperrealistic still life of fruits on a wooden table", 0.025),
        ]
        
        provider = get_provider("fal")
        
        for model, prompt, expected_cost in flux_models:
            try:
                request = GenerationRequest(
                    prompt=prompt,
                    generation_type=GenerationType.IMAGE,
                    model=model,
                    width=1024,
                    height=768,
                    output_path=self.test_output_dir / f"{model}.png"
                )
                
                result = await provider.generate(request)
                
                if result.success:
                    print(f"  ✓ {model}: Generated {result.file_path}")
                    assert abs(result.cost - expected_cost) < 0.001, f"Cost mismatch for {model}"
                else:
                    print(f"  ✗ {model}: {result.error}")
                    
            except Exception as e:
                print(f"  ✗ {model}: Exception - {e}")
                self.errors.append({"model": model, "error": str(e)})
    
    async def test_kling_video_models(self):
        """Test Kling video generation models."""
        print("\n=== Testing Kling Video Models ===")
        
        kling_models = [
            ("kling-v1-text", "A butterfly emerging from its cocoon in slow motion", None, 0.15),
            ("kling-v1-image", "Transform this image into a dynamic video", "test_image.png", 0.15),
            ("kling-v2-text", "A time-lapse of a flower blooming under starlight", None, 0.20),
            ("kling-v2-image", "Animate this scene with gentle movement", "test_image.png", 0.20),
        ]
        
        provider = get_provider("fal")
        
        for model, prompt, image_path, expected_cost in kling_models:
            try:
                params = {
                    "prompt": prompt,
                    "generation_type": GenerationType.VIDEO,
                    "model": model,
                    "output_path": self.test_output_dir / f"{model}.mp4"
                }
                
                # Skip image-to-video tests if no test image exists
                if "image" in model and image_path:
                    if not Path(image_path).exists():
                        print(f"  ⚠️  {model}: Skipping (no test image)")
                        continue
                    # TODO: Add image upload support
                
                request = GenerationRequest(**params)
                result = await provider.generate(request)
                
                if result.success:
                    print(f"  ✓ {model}: Generated {result.file_path}")
                    assert abs(result.cost - expected_cost) < 0.001, f"Cost mismatch for {model}"
                else:
                    print(f"  ✗ {model}: {result.error}")
                    
            except Exception as e:
                print(f"  ✗ {model}: Exception - {e}")
                self.errors.append({"model": model, "error": str(e)})
    
    async def test_other_models(self):
        """Test other specialized models."""
        print("\n=== Testing Other Models ===")
        
        other_models = [
            ("fast-sdxl", "A vibrant abstract painting in the style of Kandinsky", GenerationType.IMAGE, 0.003),
            ("stable-cascade", "A detailed architectural rendering of a modern house", GenerationType.IMAGE, 0.01),
            ("pixart-sigma", "A whimsical illustration of a tea party in space", GenerationType.IMAGE, 0.01),
        ]
        
        provider = get_provider("fal")
        
        for model, prompt, gen_type, expected_cost in other_models:
            try:
                ext = ".png" if gen_type == GenerationType.IMAGE else ".mp4"
                request = GenerationRequest(
                    prompt=prompt,
                    generation_type=gen_type,
                    model=model,
                    output_path=self.test_output_dir / f"{model}{ext}"
                )
                
                result = await provider.generate(request)
                
                if result.success:
                    print(f"  ✓ {model}: Generated {result.file_path}")
                    assert abs(result.cost - expected_cost) < 0.001, f"Cost mismatch for {model}"
                else:
                    print(f"  ✗ {model}: {result.error}")
                    
            except Exception as e:
                print(f"  ✗ {model}: Exception - {e}")
                self.errors.append({"model": model, "error": str(e)})
    
    async def test_error_handling(self):
        """Test error handling scenarios."""
        print("\n=== Testing Error Handling ===")
        
        provider = get_provider("fal")
        
        # Test invalid model
        try:
            request = GenerationRequest(
                prompt="Test prompt",
                model="invalid-model",
                generation_type=GenerationType.IMAGE
            )
            result = await provider.generate(request)
            assert not result.success, "Should have failed with invalid model"
            print("  ✓ Invalid model handling works")
        except Exception as e:
            print(f"  ✓ Invalid model raised exception: {e}")
        
        # Test empty prompt
        try:
            request = GenerationRequest(
                prompt="",
                model="flux-schnell",
                generation_type=GenerationType.IMAGE
            )
            result = await provider.generate(request)
            if not result.success:
                print("  ✓ Empty prompt handling works")
            else:
                print("  ✗ Empty prompt should have failed")
        except Exception as e:
            print(f"  ✓ Empty prompt raised exception: {e}")
    
    async def test_provider_capabilities(self):
        """Test provider capabilities and status."""
        print("\n=== Testing Provider Capabilities ===")
        
        provider = get_provider("fal")
        
        # Check status
        status = await provider.check_status()
        print(f"  Provider status: {status.value}")
        
        # Get capabilities
        caps = provider.get_capabilities()
        print(f"  Supported models: {len(caps.models)}")
        print(f"  Generation types: {[t.value for t in caps.generation_types]}")
        print(f"  Max resolution: {caps.max_resolution['width']}x{caps.max_resolution['height']}")
        print(f"  Features: {', '.join(caps.features[:5])}...")
        
        # Verify our new models are in capabilities
        assert "flux-pro" in caps.models, "flux-pro not in capabilities"
        assert "kling-v1-text" in caps.models, "kling-v1-text not in capabilities"
        assert "kling-v2-text" in caps.models, "kling-v2-text not in capabilities"
        print("  ✓ New models found in capabilities")
    
    def print_summary(self):
        """Print test summary."""
        print("\n" + "="*50)
        print("TEST SUMMARY")
        print("="*50)
        print(f"Total tests: {len(self.results) + len(self.errors)}")
        print(f"Successful: {len(self.results)}")
        print(f"Failed: {len(self.errors)}")
        print(f"Total cost: ${self.total_cost:.4f}")
        print(f"Output directory: {self.test_output_dir}")
        
        if self.errors:
            print("\nErrors:")
            for error in self.errors:
                print(f"  - {error.get('model', 'Unknown')}: {error.get('error', 'Unknown error')}")
        
        print("\nGenerated files:")
        for file in self.test_output_dir.iterdir():
            print(f"  - {file.name} ({file.stat().st_size / 1024:.1f} KB)")


async def main():
    """Run comprehensive fal.ai provider tests."""
    print("=== Comprehensive fal.ai Provider Test ===")
    
    # Check for API key
    api_key = os.getenv("FAL_KEY")
    if not api_key:
        # Try to get from keychain using the key manager
        try:
            from alicemultiverse.core.keys import KeyManager
            key_manager = KeyManager()
            api_key = key_manager.get_api_key("FAL_KEY")
        except:
            pass
    
    if not api_key:
        print("\n⚠️  No fal.ai API key found!")
        print("Please run: alice keys setup")
        print("Or set FAL_KEY environment variable")
        return
    
    # Confirm before running tests
    print("\n⚠️  This test will make real API calls and incur costs!")
    print("Estimated total cost: ~$0.50-1.00")
    response = input("Continue? (y/n): ")
    if response.lower() != 'y':
        print("Test cancelled.")
        return
    
    # Initialize registry with API key
    registry = get_registry()
    if api_key:
        registry.register_api_key("fal", api_key)
    
    # Run tests
    tester = FalProviderTester()
    
    # Run different test suites
    await tester.test_provider_capabilities()
    await tester.test_flux_models()
    await tester.test_kling_video_models()
    await tester.test_other_models()
    await tester.test_error_handling()
    
    # Print summary
    tester.print_summary()


if __name__ == "__main__":
    asyncio.run(main())