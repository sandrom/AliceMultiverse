"""Demo of video creation workflow from selected images."""

import asyncio
from pathlib import Path
from typing import List

from alicemultiverse.workflows.video_creation import (
    VideoCreationWorkflow,
    VideoStoryboard,
    CameraMotion,
)
from alicemultiverse.storage.duckdb_search import DuckDBSearch
from alicemultiverse.providers import get_provider
from alicemultiverse.providers.types import GenerationRequest, GenerationType


async def demo_video_creation():
    """Demonstrate the video creation workflow."""
    
    # Initialize components
    search_db = DuckDBSearch()
    workflow = VideoCreationWorkflow(search_db)
    
    print("=== Video Creation Workflow Demo ===\n")
    
    # Step 1: Search for images to use
    print("1. Searching for cyberpunk images...")
    results, total = search_db.search({
        "tags": ["cyberpunk", "neon", "futuristic"],
        "limit": 10
    })
    
    if not results:
        print("No images found. Please run organization with understanding first.")
        return
    
    print(f"Found {len(results)} suitable images")
    
    # Extract image hashes
    image_hashes = [r["content_hash"] for r in results[:8]]  # Use first 8
    
    # Step 2: Analyze images for video potential
    print("\n2. Analyzing images for video potential...")
    for i, img_hash in enumerate(image_hashes[:3]):  # Show first 3
        analysis = await workflow.analyze_image_for_video(img_hash)
        print(f"\nImage {i+1}:")
        print(f"  - Suggested motion: {analysis['suggested_motion'].value}")
        print(f"  - Motion keywords: {', '.join(analysis['motion_keywords'][:3])}")
        print(f"  - Composition: {analysis['composition']['has_character']} character, "
              f"{analysis['composition']['is_landscape']} landscape")
    
    # Step 3: Generate storyboard
    print("\n3. Generating video storyboard...")
    storyboard = await workflow.generate_video_prompts(
        image_hashes=image_hashes,
        style="cinematic",
        target_duration=30,
        enhance_with_ai=False
    )
    
    print(f"\nStoryboard created: {storyboard.project_name}")
    print(f"Total duration: {storyboard.total_duration} seconds")
    print(f"Number of shots: {len(storyboard.shots)}")
    
    # Show some shots
    print("\nSample shots:")
    for i, shot in enumerate(storyboard.shots[:3]):
        print(f"\nShot {i+1}:")
        print(f"  Duration: {shot.duration}s")
        print(f"  Camera: {shot.camera_motion.value}")
        print(f"  Prompt preview: {shot.prompt[:80]}...")
    
    # Step 4: Create Kling requests
    print("\n4. Creating Kling generation requests...")
    kling_requests = workflow.create_kling_requests(
        storyboard,
        model="kling-v2.1-pro-text"
    )
    
    print(f"Created {len(kling_requests)} Kling requests")
    print("\nFirst request details:")
    req = kling_requests[0]
    print(f"  Model: {req.model}")
    print(f"  Duration: {req.parameters['duration']}s")
    print(f"  Camera motion: {req.parameters['camera_motion']}")
    print(f"  Prompt: {req.prompt[:100]}...")
    
    # Step 5: Prepare Flux keyframes
    print("\n5. Preparing Flux keyframes...")
    modifications = {
        "0": "Add dramatic rain and lightning effects",
        "2": "Enhance neon glow and add motion blur"
    }
    
    flux_requests = await workflow.prepare_keyframes_with_flux(
        storyboard,
        modifications
    )
    
    total_keyframes = sum(len(reqs) for reqs in flux_requests.values())
    print(f"Prepared {total_keyframes} Flux keyframes across {len(flux_requests)} shots")
    
    # Step 6: Create transition guide
    print("\n6. Creating transition guide...")
    guide = workflow.create_transition_guide(storyboard)
    print("Transition guide preview:")
    print(guide.split("\n\n")[0])  # Show header
    
    # Step 7: Save storyboard
    output_dir = Path("storyboards")
    output_dir.mkdir(exist_ok=True)
    output_path = output_dir / f"{storyboard.project_name}.json"
    storyboard.save(output_path)
    print(f"\n7. Storyboard saved to: {output_path}")
    
    # Cost estimation
    kling_cost = len(kling_requests) * 0.35  # Pro model cost
    flux_cost = total_keyframes * 0.07
    total_cost = kling_cost + flux_cost
    
    print(f"\n=== Cost Estimate ===")
    print(f"Kling video generation: ${kling_cost:.2f}")
    print(f"Flux keyframe enhancement: ${flux_cost:.2f}")
    print(f"Total estimated cost: ${total_cost:.2f}")
    
    print("\n=== Demo Complete ===")
    print("\nNext steps:")
    print("1. Review and edit the storyboard JSON if needed")
    print("2. Use the Kling requests to generate videos")
    print("3. Apply Flux enhancements to key shots")
    print("4. Follow the transition guide for editing")


async def demo_video_styles():
    """Demo different video styles."""
    search_db = DuckDBSearch()
    workflow = VideoCreationWorkflow(search_db)
    
    print("\n=== Video Style Comparison ===\n")
    
    # Get some test images
    results, _ = search_db.search({"limit": 5})
    if not results:
        print("No images found.")
        return
    
    image_hashes = [r["content_hash"] for r in results]
    
    # Generate storyboards in different styles
    styles = ["cinematic", "documentary", "music_video", "narrative", "abstract"]
    
    for style in styles:
        print(f"\n{style.upper()} Style:")
        storyboard = await workflow.generate_video_prompts(
            image_hashes=image_hashes,
            style=style,
            target_duration=20
        )
        
        # Show characteristics
        shot = storyboard.shots[0]
        print(f"  Shot duration: {shot.duration}s")
        print(f"  Camera tendency: {shot.camera_motion.value}")
        print(f"  Style notes: {', '.join(shot.style_notes[:2])}")
        print(f"  Prompt style: {shot.prompt[:60]}...")


async def demo_camera_motion_analysis():
    """Demo camera motion analysis for different image types."""
    search_db = DuckDBSearch()
    workflow = VideoCreationWorkflow(search_db)
    
    print("\n=== Camera Motion Analysis ===\n")
    
    # Define test scenarios
    test_tags = [
        (["portrait", "person", "face"], "Character portrait"),
        (["landscape", "vista", "scenery"], "Wide landscape"),
        (["architecture", "building", "city"], "Architecture"),
        (["abstract", "pattern", "texture"], "Abstract art"),
        (["action", "motion", "movement"], "Action scene")
    ]
    
    for tags, description in test_tags:
        # Search for images with these tags
        results, _ = search_db.search({"tags": tags, "limit": 1})
        
        if results:
            img_hash = results[0]["content_hash"]
            analysis = await workflow.analyze_image_for_video(img_hash)
            
            print(f"\n{description}:")
            print(f"  Suggested camera: {analysis['suggested_motion'].value}")
            print(f"  Reasoning: {analysis['composition']}")
            print(f"  Motion keywords: {analysis['motion_keywords']}")


if __name__ == "__main__":
    print("Video Creation Workflow Demo")
    print("=" * 50)
    
    # Run demos
    asyncio.run(demo_video_creation())
    
    # Uncomment to run additional demos:
    # asyncio.run(demo_video_styles())
    # asyncio.run(demo_camera_motion_analysis())