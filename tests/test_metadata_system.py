"""Test the enhanced metadata system."""

import json
from datetime import datetime, timedelta

from alicemultiverse.metadata.models import AssetMetadata, AssetRole, SearchQuery
from alicemultiverse.metadata.search import AssetSearchEngine


def create_sample_metadata():
    """Create sample metadata for testing."""
    return {
        "asset_001": AssetMetadata(
            asset_id="asset_001",
            file_path="/projects/cyberpunk/hero_portrait_001.png",
            file_name="hero_portrait_001.png",
            file_size=2048000,
            mime_type="image/png",
            created_at=datetime.now() - timedelta(days=7),
            modified_at=datetime.now() - timedelta(days=7),
            imported_at=datetime.now() - timedelta(days=7),
            project_id="cyberpunk_video",
            project_phase="production",
            session_id="session_20241020",
            source_type="flux",
            generation_params={"model": "flux-dev", "steps": 50},
            prompt="cyberpunk portrait of a hacker, neon lights, dark mood",
            model="flux-dev",
            seed=12345,
            style_tags=["cyberpunk", "portrait", "neon"],
            mood_tags=["dark", "mysterious"],
            subject_tags=["portrait", "person"],
            color_tags=["blue", "purple", "black"],
            technical_tags=["high-quality"],
            custom_tags=[],
            parent_id=None,
            variation_of=None,
            similar_to=["asset_002", "asset_003"],
            referenced_by=[],
            grouped_with=["asset_002"],
            quality_score=85.5,
            quality_stars=5,
            technical_scores={"sharpness": 0.9, "exposure": 0.85},
            ai_defects=[],
            role=AssetRole.HERO,
            description="Main character portrait for opening scene",
            notes="Client loved the neon effect",
            approved=True,
            flagged=False,
            timecode=None,
            beat_aligned=None,
            scene_number=1,
            lyrics_line=None,
        ),
        "asset_002": AssetMetadata(
            asset_id="asset_002",
            file_path="/projects/cyberpunk/hero_portrait_002.png",
            file_name="hero_portrait_002.png",
            file_size=2148000,
            mime_type="image/png",
            created_at=datetime.now() - timedelta(days=7),
            modified_at=datetime.now() - timedelta(days=7),
            imported_at=datetime.now() - timedelta(days=7),
            project_id="cyberpunk_video",
            project_phase="production",
            session_id="session_20241020",
            source_type="flux",
            generation_params={"model": "flux-dev", "steps": 50},
            prompt="cyberpunk portrait variation, more blue tones",
            model="flux-dev",
            seed=12346,
            style_tags=["cyberpunk", "portrait", "neon"],
            mood_tags=["dark", "intense"],
            subject_tags=["portrait", "person"],
            color_tags=["blue", "cyan"],
            technical_tags=["high-quality"],
            custom_tags=[],
            parent_id="asset_001",
            variation_of="asset_001",
            similar_to=["asset_001"],
            referenced_by=[],
            grouped_with=["asset_001"],
            quality_score=82.0,
            quality_stars=4,
            technical_scores={"sharpness": 0.85, "exposure": 0.8},
            ai_defects=[],
            role=AssetRole.HERO,
            description="Variation with more blue tones",
            notes=None,
            approved=False,
            flagged=False,
            timecode=None,
            beat_aligned=None,
            scene_number=1,
            lyrics_line=None,
        ),
        "asset_003": AssetMetadata(
            asset_id="asset_003",
            file_path="/projects/cyberpunk/cityscape_001.png",
            file_name="cityscape_001.png",
            file_size=3048000,
            mime_type="image/png",
            created_at=datetime.now() - timedelta(days=30),
            modified_at=datetime.now() - timedelta(days=30),
            imported_at=datetime.now() - timedelta(days=30),
            project_id="cyberpunk_video",
            project_phase="concept",
            session_id="session_20241001",
            source_type="midjourney",
            generation_params={"version": "5.2"},
            prompt="futuristic cyberpunk cityscape, neon signs, rain",
            model="mj-5.2",
            seed=None,
            style_tags=["cyberpunk", "futuristic"],
            mood_tags=["atmospheric", "moody"],
            subject_tags=["cityscape", "urban"],
            color_tags=["neon", "purple", "pink"],
            technical_tags=[],
            custom_tags=["establishing-shot"],
            parent_id=None,
            variation_of=None,
            similar_to=["asset_001"],
            referenced_by=[],
            grouped_with=[],
            quality_score=78.0,
            quality_stars=4,
            technical_scores={"sharpness": 0.75, "exposure": 0.9},
            ai_defects=["slight-blur-in-background"],
            role=AssetRole.B_ROLL,
            description="Establishing shot of the city",
            notes="Good for background, needs upscaling",
            approved=True,
            flagged=False,
            timecode="00:00:10",
            beat_aligned=True,
            scene_number=1,
            lyrics_line="In the neon-lit streets",
        ),
    }


def test_search_functionality():
    """Test various search scenarios."""
    # Create sample data
    metadata_store = create_sample_metadata()
    search_engine = AssetSearchEngine(metadata_store)

    print("=== Testing Asset Search System ===\n")

    # Test 1: Search by timeframe (last month)
    print("1. Search for assets from last month:")
    query = SearchQuery(
        timeframe_start=datetime.now() - timedelta(days=35), timeframe_end=datetime.now(), limit=10
    )
    results = search_engine.search_assets(query)
    print(f"   Found {len(results)} assets")
    for asset in results:
        print(f"   - {asset['file_name']} (created {asset['created_at'].strftime('%Y-%m-%d')})")

    # Test 2: Search by style and mood
    print("\n2. Search for cyberpunk assets with dark mood:")
    query = SearchQuery(style_tags=["cyberpunk"], mood_tags=["dark"], limit=10)
    results = search_engine.search_assets(query)
    print(f"   Found {len(results)} assets")
    for asset in results:
        print(f"   - {asset['file_name']}: {asset['prompt']}")

    # Test 3: Find variations
    print("\n3. Find variations of asset_001:")
    query = SearchQuery(variations_of="asset_001", limit=10)
    results = search_engine.search_assets(query)
    print(f"   Found {len(results)} variations")
    for asset in results:
        print(f"   - {asset['file_name']}: {asset['description']}")

    # Test 4: Find similar assets
    print("\n4. Find assets similar to asset_001:")
    similar = search_engine.find_similar_assets("asset_001", similarity_threshold=0.5)
    print(f"   Found {len(similar)} similar assets")
    for asset in similar:
        print(f"   - {asset['file_name']} (source: {asset['source_type']})")

    # Test 5: Natural language search
    print("\n5. Search by description 'neon portrait':")
    results = search_engine.search_by_description("neon portrait", limit=5)
    print(f"   Found {len(results)} matching assets")
    for asset in results:
        print(f"   - {asset['file_name']}: {asset['prompt']}")

    # Test 6: Complex query - AI perspective
    print("\n6. AI searching for 'cyberpunk portraits from last week with high quality':")
    query = SearchQuery(
        timeframe_start=datetime.now() - timedelta(days=14),
        style_tags=["cyberpunk"],
        subject_tags=["portrait"],
        min_stars=4,
        exclude_defects=True,
        approved_only=False,  # AI can see unapproved too
        sort_by="quality",
    )
    results = search_engine.search_assets(query)
    print(f"   Found {len(results)} assets matching criteria")
    for asset in results:
        print(
            f"   - {asset['file_name']} ({asset['quality_stars']} stars, "
            f"{'approved' if asset['approved'] else 'pending'})"
        )

    # Test 7: Finding assets for a specific scene
    print("\n7. Find all assets for scene 1:")
    # This would be done by filtering in a real implementation
    scene_assets = []
    for asset_id, metadata in metadata_store.items():
        if metadata.get("scene_number") == 1:
            scene_assets.append(metadata)

    print(f"   Found {len(scene_assets)} assets for scene 1")
    for asset in scene_assets:
        print(f"   - {asset['file_name']} (role: {asset['role'].value})")


def demonstrate_ai_workflow():
    """Demonstrate how AI would use these functions."""
    metadata_store = create_sample_metadata()
    search_engine = AssetSearchEngine(metadata_store)

    print("\n\n=== AI Workflow Example ===")
    print("User: 'Generate a cyberpunk portrait with the neon style from last month'\n")

    print("AI Step 1: Translate 'last month' to timeframe")
    print("   search_assets(timeframe_start='2024-09-20', style_tags=['cyberpunk', 'neon'])")

    query = SearchQuery(
        timeframe_start=datetime.now() - timedelta(days=35),
        style_tags=["cyberpunk", "neon"],
        subject_tags=["portrait"],
    )
    results = search_engine.search_assets(query)

    print(f"\nAI Step 2: Found {len(results)} matching reference assets")
    if results:
        reference = results[0]
        print(f"   Selected: {reference['file_name']} as style reference")
        print(f"   Style tags: {reference['style_tags']}")
        print(f"   Generation params: {json.dumps(reference['generation_params'], indent=2)}")

        print("\nAI Step 3: Extract style parameters and generate new image")
        print("   generate_image(")
        print("       prompt='cyberpunk portrait in neon style',")
        print(f"       style_reference='{reference['asset_id']}',")
        print(f"       model='{reference['model']}',")
        print(f"       parameters={reference['generation_params']}")
        print("   )")

        print("\nAI Step 4: Tag and organize the new asset")
        print("   tag_asset(new_asset_id, tags=['cyberpunk', 'neon', 'portrait'])")
        print("   set_asset_role(new_asset_id, role='wip')")
        print("   group_assets([new_asset_id, reference_asset_id], 'cyberpunk_portraits')")


if __name__ == "__main__":
    test_search_functionality()
    demonstrate_ai_workflow()
