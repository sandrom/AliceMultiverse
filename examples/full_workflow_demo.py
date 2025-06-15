#!/usr/bin/env python3
"""
Full workflow demonstration: From chaos to organized creative projects.

This example demonstrates the complete AliceMultiverse workflow:
1. Organize media with AI understanding
2. Search by semantic tags
3. Find similar images
4. Create project selections
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from alicemultiverse.core.config import load_config
from alicemultiverse.organizer.media_organizer import MediaOrganizer
from alicemultiverse.storage.unified_duckdb import DuckDBSearch


def step_1_organize_media(inbox_path: str, output_path: str):
    """Step 1: Organize media with AI understanding."""
    print("\n" + "="*70)
    print("STEP 1: ORGANIZE MEDIA WITH AI UNDERSTANDING")
    print("="*70)

    # Load config and override paths
    config = load_config()
    config.paths.inbox = inbox_path
    config.paths.organized = output_path
    config.processing.understanding = True  # Enable AI understanding
    config.processing.force_reindex = True  # Force fresh analysis

    # Create organizer
    organizer = MediaOrganizer(config)

    print(f"\nOrganizing files from: {inbox_path}")
    print(f"Output directory: {output_path}")
    print("AI Understanding: ENABLED")
    print("\nThis will:")
    print("- Detect AI source (Midjourney, DALL-E, etc.)")
    print("- Generate semantic tags (style, mood, subject, etc.)")
    print("- Calculate perceptual hashes for similarity search")
    print("- Index everything in DuckDB for fast search")

    # Run organization
    success = organizer.organize()

    if success:
        print("\n✅ Organization complete!")
        organizer._log_statistics()
    else:
        print("\n❌ Organization failed!")

    return success


def step_2_search_by_tags():
    """Step 2: Search organized media by semantic tags."""
    print("\n" + "="*70)
    print("STEP 2: SEARCH BY SEMANTIC TAGS")
    print("="*70)

    db = DuckDBSearch("data/search.duckdb")

    # Example searches
    searches = [
        {
            "name": "Futuristic Portraits",
            "filters": {"tags": ["futuristic", "portrait"]}
        },
        {
            "name": "Cinematic Mood Images",
            "filters": {"tags": ["cinematic"], "any_tags": ["dramatic", "moody"]}
        },
        {
            "name": "Colorful Fashion",
            "filters": {"any_tags": ["fashion", "style"], "tags": ["colorful"]}
        }
    ]

    for search in searches:
        print(f"\n🔍 Searching for: {search['name']}")
        results, total = db.search(search['filters'], limit=3)
        print(f"Found {total} matching images")

        for asset in results:
            print(f"  • {Path(asset['file_path']).name}")
            if asset.get('tags'):
                # Show first few tags
                all_tags = []
                for category, tag_list in asset['tags'].items():
                    all_tags.extend(tag_list[:2])
                print(f"    Tags: {', '.join(all_tags[:8])}")


def step_3_find_similar_images():
    """Step 3: Find similar images using perceptual hashing."""
    print("\n" + "="*70)
    print("STEP 3: FIND SIMILAR IMAGES")
    print("="*70)

    db = DuckDBSearch("data/search.duckdb")

    # Get a sample image to find similar ones
    results, _ = db.search({"media_type": "image"}, limit=1)

    if not results:
        print("No images found in database!")
        return

    sample_asset = results[0]
    sample_path = Path(sample_asset['file_path'])

    print(f"\n🎯 Finding images similar to: {sample_path.name}")

    # Get the perceptual hash
    hashes = db.get_perceptual_hash(sample_asset['content_hash'])

    if hashes['phash']:
        print(f"Perceptual hash: {hashes['phash']}")

        # Find similar images
        similar = db.find_similar_by_phash(hashes['phash'], threshold=15)

        print(f"\nFound {len(similar)} similar images:")
        for content_hash, file_path, distance in similar[:5]:
            print(f"  • Distance {distance}: {Path(file_path).name}")


def step_4_creative_workflow():
    """Step 4: Demonstrate creative workflow support."""
    print("\n" + "="*70)
    print("STEP 4: CREATIVE WORKFLOW EXAMPLE")
    print("="*70)

    print("\n🎨 Example: Creating a 'Cyberpunk Portrait' Collection")

    db = DuckDBSearch("data/search.duckdb")

    # Search for cyberpunk portraits
    filters = {
        "any_tags": ["cyberpunk", "futuristic", "neon"],
        "tags": ["portrait"]
    }

    results, total = db.search(filters, limit=10)
    print(f"\nFound {total} cyberpunk portraits")

    # Simulate selection process
    selected = []
    for i, asset in enumerate(results[:5]):
        print(f"\n{i+1}. {Path(asset['file_path']).name}")
        if asset.get('tags'):
            style_tags = asset['tags'].get('style', [])
            mood_tags = asset['tags'].get('mood', [])
            print(f"   Style: {', '.join(style_tags[:3])}")
            print(f"   Mood: {', '.join(mood_tags[:3])}")
        selected.append(asset)

    print(f"\n✅ Selected {len(selected)} images for the collection")
    print("\nNext steps in a full workflow:")
    print("- Export selected images to project folder")
    print("- Generate prompts for variations")
    print("- Create style guide from selections")
    print("- Use for video storyboarding")


def main():
    """Run the full workflow demonstration."""
    print("="*70)
    print("ALICEMULTIVERSE FULL WORKFLOW DEMONSTRATION")
    print("Transform chaos → organized library → creative projects")
    print("="*70)

    # Check for command line arguments
    if len(sys.argv) < 3:
        print("\nUsage: python full_workflow_demo.py <inbox_path> <output_path>")
        print("\nExample:")
        print("  python full_workflow_demo.py ~/Downloads/AI-Images ~/Pictures/AI-Organized")
        print("\nNote: This will organize files and run AI analysis (costs apply)")
        return

    inbox_path = sys.argv[1]
    output_path = sys.argv[2]

    # Verify paths
    if not Path(inbox_path).exists():
        print(f"\nError: Inbox path doesn't exist: {inbox_path}")
        return

    # Check for API keys
    if not os.getenv("ANTHROPIC_API_KEY"):
        print("\n⚠️  Warning: No Anthropic API key found!")
        print("Run 'alice keys setup' to configure API keys for AI understanding")
        print("Continuing without AI understanding...\n")

    # Run workflow steps
    try:
        # Step 1: Organize
        if step_1_organize_media(inbox_path, output_path):
            # Step 2: Search by tags
            step_2_search_by_tags()

            # Step 3: Find similar
            step_3_find_similar_images()

            # Step 4: Creative workflow
            step_4_creative_workflow()

            print("\n" + "="*70)
            print("🎉 DEMONSTRATION COMPLETE!")
            print("="*70)
            print("\nYou've seen how AliceMultiverse can:")
            print("✅ Organize media with AI understanding")
            print("✅ Search by semantic tags")
            print("✅ Find similar images")
            print("✅ Support creative workflows")
            print("\nTry the other demo scripts:")
            print("- python examples/semantic_search_demo.py")
            print("- python examples/similarity_search_demo.py <image_path>")

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
