"""Example of using AliceMultiverse with enhanced metadata."""

from pathlib import Path
from alicemultiverse.metadata.models import SearchQuery


def main():
    """Demonstrate enhanced metadata usage."""
    print("AliceMultiverse Enhanced Metadata Example\n")
    print("=" * 50)
    
    print("\n1. ORGANIZE WITH ENHANCED METADATA:")
    print("   alice --enhanced-metadata")
    print("   This extracts rich metadata including prompts, style tags, and relationships")
    
    print("\n2. COMMAND LINE USAGE:")
    print("   # Basic organization with metadata")
    print("   alice --enhanced-metadata")
    print("")
    print("   # With quality assessment")
    print("   alice --enhanced-metadata --quality")
    print("")
    print("   # With pipeline processing")
    print("   alice --enhanced-metadata --pipeline brisque-sightengine")
    
    print("\n3. PROGRAMMATIC USAGE (for AI integration):")
    print("   ```python")
    print("   from alicemultiverse.organizer.enhanced_organizer import EnhancedMediaOrganizer")
    print("   from alicemultiverse.core.config import load_config")
    print("")
    print("   # Initialize")
    print("   config = load_config()")
    print("   config.enhanced_metadata = True")
    print("   organizer = EnhancedMediaOrganizer(config)")
    print("")
    print("   # Search for assets")
    print("   cyberpunk_images = organizer.search_assets(")
    print("       style_tags=['cyberpunk'],")
    print("       min_stars=4,")
    print("       limit=10")
    print("   )")
    print("")
    print("   # Find similar assets")
    print("   similar = organizer.find_similar(asset_id, threshold=0.7)")
    print("")
    print("   # Tag assets")
    print("   organizer.tag_asset(asset_id, ['hero-shot', 'approved'], 'custom_tags')")
    print("   ```")
    
    print("\n4. AI ASSISTANT WORKFLOW:")
    print("   User: 'Find neon cyberpunk portraits from last week'")
    print("   ")
    print("   AI would call:")
    print("   ```python")
    print("   results = organizer.search_assets(")
    print("       timeframe_start=datetime.now() - timedelta(days=7),")
    print("       style_tags=['cyberpunk', 'neon'],")
    print("       subject_tags=['portrait']")
    print("   )")
    print("   ```")
    
    print("\n5. METADATA STRUCTURE:")
    print("   Each asset has:")
    print("   - Unique ID (content hash)")
    print("   - Generation parameters (prompt, model, seed)")
    print("   - Semantic tags (style, mood, subject, colors)")
    print("   - Relationships (parent, variations, similar)")
    print("   - Quality metrics (BRISQUE, stars, AI defects)")
    print("   - Creative role (hero, b-roll, reference, etc.)")
    print("   - Project context")
    
    print("\n6. BENEFITS:")
    print("   - AI can find assets by creative concepts, not file paths")
    print("   - Automatic relationship detection (variations, similar assets)")
    print("   - Rich semantic search capabilities")
    print("   - Preserves all generation parameters for reuse")
    print("   - Enables long-term project continuity")
    
    print("\n" + "=" * 50)
    print("This is the foundation for Alice to become the intelligent")
    print("orchestration layer between AI assistants and creative tools!")


if __name__ == "__main__":
    main()