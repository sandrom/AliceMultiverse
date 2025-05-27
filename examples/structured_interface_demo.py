"""Demo of the Alice Structured Interface without requiring actual media files."""

import logging
from alicemultiverse.interface import (
    AliceStructuredInterface,
    SearchRequest,
    SearchFilters,
    MediaType,
    SortField,
    DateRange,
    TagUpdateRequest,
    AssetRole,
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


def main():
    """Run a demonstration of the structured interface."""
    logger.info("Alice Structured Interface Demo")
    logger.info("==============================")
    logger.info("")
    
    # Note: In a real scenario, you'd have the interface connected to actual media
    logger.info("This demo shows how to use the structured API.")
    logger.info("All queries use typed parameters - no natural language!")
    logger.info("")
    
    # Example 1: Basic search by media type and tags
    logger.info("1. Search for cyberpunk portraits:")
    search_request = SearchRequest(
        filters=SearchFilters(
            media_type=MediaType.IMAGE,
            tags=["cyberpunk", "portrait"],  # AND operation - both tags required
            quality_rating={"min": 4}  # Only 4-5 star images
        ),
        sort_by=SortField.QUALITY_RATING,
        order="desc",
        limit=10
    )
    logger.info(f"   Request: {search_request}")
    logger.info("")
    
    # Example 2: Complex multi-filter search
    logger.info("2. Complex search with multiple filters:")
    complex_request = SearchRequest(
        filters=SearchFilters(
            media_type=MediaType.IMAGE,
            any_tags=["fantasy", "scifi", "cyberpunk"],  # OR - at least one required
            exclude_tags=["sketch", "wip"],  # NOT - none of these
            date_range=DateRange(
                start="2024-01-01",
                end="2024-12-31"
            ),
            ai_source=["stable-diffusion", "midjourney"],
            dimensions={
                "width": {"min": 1024},
                "aspect_ratio": {"min": 1.0, "max": 2.0}
            }
        )
    )
    logger.info(f"   Request: {complex_request}")
    logger.info("")
    
    # Example 3: Search by file attributes
    logger.info("3. Search for specific files:")
    file_search = SearchRequest(
        filters=SearchFilters(
            file_formats=["png", "jpg"],
            file_size={"min": 1048576, "max": 10485760},  # 1MB - 10MB
            filename_pattern=r"portrait_\d{3}\.png",  # portrait_001.png pattern
            has_metadata=["prompt", "seed"]  # Must have these metadata fields
        )
    )
    logger.info(f"   Request: {file_search}")
    logger.info("")
    
    # Example 4: Tag operations
    logger.info("4. Tag update operations:")
    
    # Add tags
    add_tags_request = TagUpdateRequest(
        asset_ids=["asset_001", "asset_002"],
        add_tags=["approved", "hero-shot", "campaign-2024"]
    )
    logger.info(f"   Add tags: {add_tags_request}")
    
    # Remove tags
    remove_tags_request = TagUpdateRequest(
        asset_ids=["asset_003"],
        remove_tags=["wip", "draft"]
    )
    logger.info(f"   Remove tags: {remove_tags_request}")
    
    # Replace all tags
    set_tags_request = TagUpdateRequest(
        asset_ids=["asset_004"],
        set_tags=["final", "published", "website"]
    )
    logger.info(f"   Set tags: {set_tags_request}")
    logger.info("")
    
    # Example 5: Future tag:value pairs (not yet implemented)
    logger.info("5. Future: Tag:value pair searches")
    logger.info("   Soon you'll be able to search like this:")
    logger.info("   filters={")
    logger.info('       "tag_values": {')
    logger.info('           "subject": "portrait",')
    logger.info('           "style": ["cyberpunk", "noir"],')
    logger.info('           "lighting": "neon",')
    logger.info('           "mood": "mysterious"')
    logger.info("       }")
    logger.info("   }")
    logger.info("")
    
    # Key benefits
    logger.info("Key Benefits of Structured API:")
    logger.info("- Type safety with enums and typed dictionaries")
    logger.info("- No ambiguity in query interpretation")
    logger.info("- Better performance through direct queries")
    logger.info("- Predictable, testable behavior")
    logger.info("- Natural language stays at AI layer")
    logger.info("")
    
    # API comparison
    logger.info("API Comparison:")
    logger.info("")
    logger.info("❌ Old Natural Language API:")
    logger.info('   alice.search("dark cyberpunk portraits from last week")')
    logger.info("")
    logger.info("✅ New Structured API:")
    logger.info('   alice.search_assets(SearchRequest(')
    logger.info('       filters=SearchFilters(')
    logger.info('           media_type=MediaType.IMAGE,')
    logger.info('           tags=["cyberpunk", "portrait"],')
    logger.info('           mood_tags=["dark"],')
    logger.info('           date_range=DateRange(start="2024-05-20")')
    logger.info('       )')
    logger.info('   ))')
    logger.info("")
    
    # Integration note
    logger.info("Integration with AI Assistants:")
    logger.info("- Claude/ChatGPT parse user's natural language")
    logger.info("- They convert it to structured API calls")
    logger.info("- Alice processes structured queries efficiently")
    logger.info("- Results returned in consistent format")
    logger.info("")
    
    logger.info("Demo complete! 🎉")


if __name__ == "__main__":
    main()