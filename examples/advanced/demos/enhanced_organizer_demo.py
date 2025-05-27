"""Test the enhanced organizer with metadata integration."""

import shutil
import tempfile
from pathlib import Path

from alicemultiverse.core.config import load_config
from alicemultiverse.metadata.models import AssetRole
from alicemultiverse.organizer.enhanced_organizer import EnhancedMediaOrganizer


def create_test_environment():
    """Create a temporary test environment with sample files."""
    # Create temp directories
    temp_dir = tempfile.mkdtemp()
    inbox = Path(temp_dir) / "inbox"
    organized = Path(temp_dir) / "organized"

    # Create project folder
    project_dir = inbox / "cyberpunk_project"
    project_dir.mkdir(parents=True)

    # Create some test images with AI-style names
    test_files = [
        "hero_portrait_midjourney_v5.png",
        "hero_portrait_v2_midjourney.png",
        "cityscape_flux_dev.png",
        "character_test_stablediffusion.png",
        "final_scene_dalle3.png",
    ]

    # Create actual image files
    from PIL import Image

    for i, filename in enumerate(test_files):
        file_path = project_dir / filename
        # Create a simple colored image
        img = Image.new("RGB", (100, 100), color=(i * 50, i * 40, i * 30))

        # Add some metadata to PNG files
        if filename.endswith(".png"):
            from PIL import PngImagePlugin

            info = PngImagePlugin.PngInfo()
            if "midjourney" in filename:
                info.add_text("prompt", "cyberpunk hero portrait, neon lights")
            elif "flux" in filename:
                info.add_text("prompt", "futuristic cityscape with neon signs")
            elif "dalle" in filename:
                info.add_text("prompt", "final scene dramatic lighting")
            img.save(file_path, "PNG", pnginfo=info)
        else:
            img.save(file_path)

    return temp_dir, inbox, organized


def test_enhanced_organization():
    """Test enhanced organization with metadata."""
    print("=== Testing Enhanced Organizer ===\n")

    # Create test environment
    temp_dir, inbox, organized = create_test_environment()

    try:
        # Load default config and override paths
        config = load_config()
        config.paths.inbox = str(inbox)
        config.paths.organized = str(organized)
        config.processing.quality = False
        config.processing.force_reindex = False
        config.project_id = "cyberpunk_video"
        config.enhanced_metadata = True

        # Create enhanced organizer
        organizer = EnhancedMediaOrganizer(config)

        # Run organization
        print("1. Organizing files with enhanced metadata...")
        success = organizer.organize()
        print(f"   Organization {'successful' if success else 'failed'}")

        # Force metadata index update
        organizer._update_search_engine()
        print(f"   Metadata entries: {len(organizer.metadata_cache.get_all_metadata())}")

        # Test search functionality
        print("\n2. Testing search capabilities:")

        # Search by source type
        print("\n   a) Search for Midjourney images:")
        results = organizer.search_assets(source_types=["midjourney"], limit=10)
        for asset in results:
            print(f"      - {asset['file_name']} (tags: {asset.get('style_tags', [])})")

        # Search by filename pattern (hero images)
        print("\n   b) Search for hero images:")
        results = organizer.search_assets(any_tags=["hero"], limit=10)
        if not results and organizer.search_engine:
            # Try description search
            results = organizer.search_engine.search_by_description("hero", limit=10)

        for asset in results:
            print(f"      - {asset['file_name']} (role: {asset.get('role', 'unknown')})")

        # Find variations
        print("\n   c) Find variations:")
        # First get all assets
        all_assets = list(organizer.metadata_cache.get_all_metadata().values())
        if all_assets:
            # Find assets that are variations
            for asset in all_assets:
                if asset.get("parent_id"):
                    print(f"      - {asset['file_name']} is a variation of {asset['parent_id']}")

        # Test tagging
        print("\n3. Testing tagging functionality:")
        if all_assets:
            first_asset = all_assets[0]
            asset_id = first_asset["asset_id"]

            # Add tags
            success = organizer.tag_asset(asset_id, ["neon", "cyberpunk"], "style_tags")
            print(f"   Added style tags: {'success' if success else 'failed'}")

            success = organizer.tag_asset(asset_id, ["test-tag"], "custom_tags")
            print(f"   Added custom tag: {'success' if success else 'failed'}")

            # Set role
            success = organizer.set_asset_role(asset_id, AssetRole.HERO)
            print(f"   Set asset role to HERO: {'success' if success else 'failed'}")

        # Test grouping
        print("\n4. Testing asset grouping:")
        if len(all_assets) >= 2:
            asset_ids = [asset["asset_id"] for asset in all_assets[:2]]
            success = organizer.group_assets(asset_ids, "hero_variations")
            print(f"   Grouped assets: {'success' if success else 'failed'}")

        # Get project context
        print("\n5. Project context:")
        context = organizer.get_project_context()
        print(f"   Total assets: {context['total_assets']}")
        print(f"   Assets by source: {context['assets_by_source']}")
        print(f"   Favorite styles: {context['favorite_styles']}")

        # Show summary
        print("\n6. Organization summary:")
        print(organizer.get_organization_summary())

        # Demonstrate AI workflow
        print("\n\n=== AI Workflow Simulation ===")
        print("User: 'Find hero images from Midjourney'\n")

        # AI would translate this to:
        # First search by source and description
        results = organizer.search_engine.search_by_description("hero", limit=10)
        # Filter to only midjourney
        results = [r for r in results if r.get("source_type") == "midjourney"]

        print(f"AI: Found {len(results)} matching assets:")
        for asset in results:
            print(f"   - {asset['file_name']}")
            if asset.get("prompt"):
                print(f"     Prompt: {asset['prompt']}")
            print(f"     Tags: {asset.get('style_tags', [])}")

    finally:
        # Cleanup
        shutil.rmtree(temp_dir)
        print("\n\nTest environment cleaned up.")


if __name__ == "__main__":
    test_enhanced_organization()
