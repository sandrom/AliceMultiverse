"""Demonstration of generation tracking and recreation capabilities."""

import asyncio
import json
from pathlib import Path
from alicemultiverse.providers import get_provider, GenerationRequest, GenerationType
from alicemultiverse.providers.generation_tracker import get_generation_tracker
from alicemultiverse.metadata.embedder import MetadataEmbedder


async def demonstrate_generation_tracking():
    """Show how generation context is tracked and can be used for recreation."""
    
    print("Generation Tracking Demo")
    print("=" * 60)
    
    # 1. Generate an image with full context
    print("\n1. Generating image with tracked context...")
    
    provider = get_provider("fal")
    
    request = GenerationRequest(
        prompt="A majestic dragon perched on a crystal mountain at sunset, digital art style",
        generation_type=GenerationType.IMAGE,
        model="flux-schnell",
        parameters={
            "num_inference_steps": 4,
            "guidance_scale": 0,
            "num_images": 1,
            "image_size": {
                "width": 1024,
                "height": 1024
            },
            "seed": 42  # For reproducibility
        },
        project_id="demo-project-001",
        output_path=Path("output/tracked_dragon.png")
    )
    
    try:
        result = await provider.generate(request)
        print(f"✓ Generated: {result.file_path}")
        print(f"  Asset ID: {result.asset_id}")
        print(f"  Cost: ${result.cost:.3f}")
        
        # 2. Inspect what was stored
        print("\n2. Inspecting stored metadata...")
        
        # Check embedded metadata
        embedder = MetadataEmbedder()
        embedded = embedder.extract_metadata(result.file_path)
        
        if embedded and 'generation_params' in embedded:
            params = json.loads(embedded['generation_params'])
            print("\n  Embedded in file:")
            print(f"    - Prompt: {params['prompt'][:50]}...")
            print(f"    - Model: {params['model']}")
            print(f"    - Provider: {params['provider']}")
            print(f"    - Seed: {params['parameters'].get('seed', 'N/A')}")
        
        # Check sidecar file
        sidecar_path = result.file_path.with_suffix('.png.json')
        if sidecar_path.exists():
            print("\n  Sidecar JSON file:")
            with open(sidecar_path) as f:
                sidecar = json.load(f)
            print(f"    - Full context preserved")
            print(f"    - Keys: {', '.join(sidecar.keys())}")
        
        # 3. Demonstrate recreation
        print("\n3. Recreating from stored context...")
        
        tracker = get_generation_tracker()
        
        # Get the generation context
        context = await tracker.get_generation_context(result.asset_id)
        if context:
            print("\n  Retrieved context from database:")
            print(f"    - Original prompt: {context['prompt'][:50]}...")
            print(f"    - Original seed: {context['parameters'].get('seed', 'N/A')}")
            
            # Create recreation request
            recreation_request = await tracker.recreate_generation(result.asset_id)
            if recreation_request:
                recreation_request.output_path = Path("output/recreated_dragon.png")
                
                print("\n  Recreating with same parameters...")
                recreated = await provider.generate(recreation_request)
                
                print(f"✓ Recreated: {recreated.file_path}")
                print(f"  Should be identical due to same seed")
        
    except Exception as e:
        print(f"✗ Error: {e}")
    
    # 4. Multi-reference example with full tracking
    print("\n\n4. Multi-reference generation with relationship tracking...")
    
    # First create some reference images
    reference_paths = []
    reference_ids = []
    
    styles = ["oil painting", "watercolor", "pencil sketch"]
    for i, style in enumerate(styles):
        ref_request = GenerationRequest(
            prompt=f"A dragon head in {style} style",
            generation_type=GenerationType.IMAGE,
            model="flux-schnell",
            parameters={
                "num_inference_steps": 4,
                "seed": 100 + i
            },
            output_path=Path(f"output/reference_{i}_{style.replace(' ', '_')}.png")
        )
        
        ref_result = await provider.generate(ref_request)
        reference_paths.append(str(ref_result.file_path))
        reference_ids.append(ref_result.asset_id)
        print(f"  ✓ Reference {i+1}: {style} (ID: {ref_result.asset_id[:8]}...)")
    
    # Now create a multi-reference generation
    multi_request = GenerationRequest(
        prompt="Create a dragon combining all three art styles seamlessly",
        generation_type=GenerationType.IMAGE,
        model="flux-kontext-pro-multi",
        reference_assets=reference_paths,
        reference_weights=[1.0, 1.5, 0.5],  # Emphasize watercolor
        parameters={
            "num_inference_steps": 28,
            "guidance_scale": 3.5
        },
        project_id="demo-project-001",
        output_path=Path("output/multi_style_dragon.png")
    )
    
    try:
        multi_result = await provider.generate(multi_request)
        print(f"\n✓ Multi-reference generation complete: {multi_result.file_path}")
        
        # Check the stored relationships
        context = await tracker.get_generation_context(multi_result.asset_id)
        if context and 'source_images' in context:
            print("\n  Tracked relationships:")
            for i, source in enumerate(context['source_images']):
                print(f"    - Reference {i+1}: {source['prompt'][:40]}...")
                print(f"      Model: {source['model']}, ID: {source['asset_id'][:8]}...")
        
    except Exception as e:
        print(f"✗ Multi-reference error: {e}")
    
    # 5. Show complete tracking across a workflow
    print("\n\n5. Complete workflow tracking example...")
    
    # Image -> Video workflow
    video_request = GenerationRequest(
        prompt="Make the dragon fly majestically through clouds",
        generation_type=GenerationType.VIDEO,
        model="svd",  # Stable Video Diffusion
        reference_assets=[reference_ids[0]],  # Use first reference
        parameters={
            "motion_bucket_id": 127,
            "fps": 7,
            "num_frames": 25
        },
        project_id="demo-project-001",
        output_path=Path("output/dragon_flight.mp4")
    )
    
    try:
        video_result = await provider.generate(video_request)
        print(f"✓ Video generated: {video_result.file_path}")
        
        # The video metadata will contain reference to source image
        video_context = await tracker.get_generation_context(video_result.asset_id)
        if video_context and 'source_images' in video_context:
            print("\n  Video tracks its source image:")
            print(f"    - Source prompt: {video_context['source_images'][0]['prompt']}")
            print(f"    - Complete chain preserved for recreation")
        
    except Exception as e:
        print(f"✗ Video generation error: {e}")
    
    print("\n" + "=" * 60)
    print("Demo complete! Check the output folder for generated files.")
    print("\nKey features demonstrated:")
    print("- All prompts and settings embedded in files")
    print("- Sidecar JSON files for easy access")
    print("- Database tracking with relationships")
    print("- Complete recreation capability")
    print("- Multi-reference relationship tracking")
    print("- Workflow chain preservation")


async def show_cli_usage():
    """Show how to use the CLI for recreation."""
    
    print("\n\nCLI Usage Examples:")
    print("=" * 60)
    
    print("\n# Inspect a file's generation metadata:")
    print("alice recreate inspect output/tracked_dragon.png")
    
    print("\n# Recreate a generation from its ID:")
    print("alice recreate recreate <asset_id>")
    
    print("\n# Recreate with different model:")
    print("alice recreate recreate <asset_id> --model flux-pro --output new_version.png")
    
    print("\n# Catalog all generations in a directory:")
    print("alice recreate catalog output/ --recursive")
    
    print("\n# Dry run to see what would be recreated:")
    print("alice recreate recreate <asset_id> --dry-run")


if __name__ == "__main__":
    # Create output directory
    Path("output").mkdir(exist_ok=True)
    
    # Run the demo
    print("Starting Generation Tracking Demo...\n")
    asyncio.run(demonstrate_generation_tracking())
    
    # Show CLI usage
    asyncio.run(show_cli_usage())