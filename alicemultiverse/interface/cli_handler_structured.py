"""CLI handler for the Alice structured interface command."""

import json
import logging
from argparse import Namespace
from typing import Any

from ..core.logging import setup_logging
from .alice_structured import AliceStructuredInterface
from .structured_models import (
    AssetRole,
    DateRange,
    MediaType,
    OrganizeRequest,
    SearchFilters,
    SearchRequest,
    SortField,
    TagUpdateRequest,
)

logger = logging.getLogger(__name__)


def run_interface_command(args: Namespace) -> int:
    """Handle the interface subcommand.
    
    Args:
        args: Parsed command-line arguments
        
    Returns:
        Exit code (0 for success)
    """
    # Setup logging
    setup_logging(level="INFO")
    
    if args.demo:
        return run_demo()
    else:
        # Interactive mode could be added here later
        logger.info("Alice Structured Interface")
        logger.info("=========================")
        logger.info("")
        logger.info(
            "The Alice structured interface provides type-safe, structured APIs for "
            "AI assistants to interact with the media organization system."
        )
        logger.info("")
        logger.info("Key principles:")
        logger.info("  - NO natural language processing in Alice")
        logger.info("  - All queries use structured parameters")
        logger.info("  - Type-safe enums for fixed values")
        logger.info("  - Clear separation between technical and semantic metadata")
        logger.info("")
        logger.info("Run with --demo to see example structured API calls.")
        logger.info("")
        logger.info("Available API methods:")
        logger.info("  - search_assets: Find assets with structured filters")
        logger.info("  - organize_media: Process and organize media files")
        logger.info("  - update_tags: Add/remove/set tags on assets")
        logger.info("  - group_assets: Create asset groups")
        logger.info("  - get_asset_by_id: Retrieve specific asset metadata")
        logger.info("  - set_asset_role: Assign creative roles to assets")
        return 0


def run_demo() -> int:
    """Run a demonstration of structured API usage."""
    logger.info("Alice Structured Interface Demo")
    logger.info("==============================")
    logger.info("")
    logger.info("This demo shows structured API calls without natural language.")
    logger.info("")
    
    # Initialize interface
    alice = AliceStructuredInterface()
    
    # Demo 1: Structured search for cyberpunk portraits
    logger.info("1. Search for cyberpunk portraits (structured query)")
    request = SearchRequest(
        filters=SearchFilters(
            media_type=MediaType.IMAGE,
            tags=["cyberpunk", "portrait"],  # AND operation
            quality_rating={"min": 4},  # 4-5 star images only
        ),
        sort_by=SortField.QUALITY_RATING,
        order="desc",
        limit=5
    )
    response = alice.search_assets(request)
    _print_response("Structured Search Results", response)
    
    # Demo 2: Search with multiple filter types
    logger.info("\n2. Complex search with multiple filters")
    request = SearchRequest(
        filters=SearchFilters(
            media_type=MediaType.IMAGE,
            any_tags=["fantasy", "scifi", "cyberpunk"],  # OR operation
            exclude_tags=["sketch", "wip"],  # NOT operation
            date_range=DateRange(
                start="2024-01-01",
                end="2024-12-31"
            ),
            ai_source=["stable-diffusion", "midjourney"],
            dimensions={
                "width": {"min": 1024},  # Minimum 1024px wide
                "aspect_ratio": {"min": 1.0, "max": 2.0}  # Between square and 2:1
            }
        ),
        sort_by=SortField.CREATED_DATE,
        order="desc",
        limit=10
    )
    response = alice.search_assets(request)
    _print_response("Complex Search Results", response)
    
    # Demo 3: Organize media with specific pipeline
    logger.info("\n3. Organize media with quality assessment pipeline")
    request = OrganizeRequest(
        quality_assessment=True,
        pipeline="brisque-sightengine",
        watch_mode=False,
        move_files=False  # Copy, don't move
    )
    response = alice.organize_media(request)
    _print_response("Organization Results", response)
    
    # Demo 4: Update tags on assets
    logger.info("\n4. Update tags on assets (structured operations)")
    # In a real scenario, we'd have asset IDs from search results
    asset_ids = ["asset_001", "asset_002", "asset_003"]
    
    # Add tags
    request = TagUpdateRequest(
        asset_ids=asset_ids,
        add_tags=["hero-shot", "campaign-2024", "approved"]
    )
    response = alice.update_tags(request)
    _print_response("Tag Addition Results", response)
    
    # Remove tags
    request = TagUpdateRequest(
        asset_ids=asset_ids,
        remove_tags=["wip", "draft"]
    )
    response = alice.update_tags(request)
    _print_response("Tag Removal Results", response)
    
    # Demo 5: Search with file-specific filters
    logger.info("\n5. Search for large PNG files with specific naming pattern")
    request = SearchRequest(
        filters=SearchFilters(
            media_type=MediaType.IMAGE,
            file_formats=["png"],
            file_size={"min": 5242880},  # > 5MB
            filename_pattern=r"cyberpunk_\d{3}\.png",  # cyberpunk_001.png pattern
            has_metadata=["prompt", "seed", "cfg_scale"]  # Must have generation params
        ),
        sort_by=SortField.FILE_SIZE,
        order="desc"
    )
    response = alice.search_assets(request)
    _print_response("File-specific Search Results", response)
    
    # Demo 6: Set asset roles
    logger.info("\n6. Set asset roles (structured enum values)")
    if asset_ids:
        response = alice.set_asset_role(asset_ids[0], AssetRole.HERO)
        _print_response("Set Role Results", response)
    
    # Demo 7: Search with prompt keywords
    logger.info("\n7. Search for assets with specific prompt keywords")
    request = SearchRequest(
        filters=SearchFilters(
            media_type=MediaType.IMAGE,
            prompt_keywords=["dragon", "fantasy", "epic"],  # All must be in prompt
            quality_rating={"min": 3}
        ),
        limit=20
    )
    response = alice.search_assets(request)
    _print_response("Prompt Keyword Search Results", response)
    
    logger.info("\n" + "=" * 70)
    logger.info("Demo complete!")
    logger.info("")
    logger.info("Key differences from natural language interface:")
    logger.info("  - All parameters are strongly typed")
    logger.info("  - No ambiguity in query interpretation")
    logger.info("  - Predictable, testable behavior")
    logger.info("  - Better performance through direct database queries")
    logger.info("  - Natural language processing happens at AI assistant layer")
    
    return 0


def _print_response(title: str, response: Any) -> None:
    """Pretty print an Alice response."""
    logger.info(f"\n   Alice Response - {title}:")
    logger.info(f"   Success: {response.get('success', False)}")
    
    if "message" in response:
        logger.info(f"   Message: {response['message']}")
    
    if response.get("data"):
        # Handle search responses specially
        if isinstance(response["data"], dict) and "results" in response["data"]:
            data = response["data"]
            logger.info(f"   Total Count: {data.get('total_count', 0)}")
            logger.info(f"   Query Time: {data.get('query_time_ms', 0)}ms")
            
            if data.get("results"):
                logger.info(f"   Results: {len(data['results'])} items")
                for i, result in enumerate(data["results"][:3]):  # Show first 3
                    logger.info(f"     [{i+1}] {result.get('file_path', 'Unknown')}")
                    logger.info(f"         Type: {result.get('media_type', 'unknown')}")
                    logger.info(f"         Tags: {', '.join(result.get('tags', []))}")
                    if result.get("quality_rating"):
                        logger.info(f"         Quality: {result['quality_rating']} stars")
                if len(data["results"]) > 3:
                    logger.info(f"     ... and {len(data['results']) - 3} more")
            
            # Show facets if available
            if data.get("facets"):
                logger.info("   Facets:")
                for facet_type, facet_values in data["facets"].items():
                    if facet_values:
                        logger.info(f"     {facet_type}:")
                        for facet in facet_values[:5]:  # Top 5
                            logger.info(f"       - {facet['value']}: {facet['count']}")
        else:
            # Format other data nicely
            formatted = json.dumps(response["data"], indent=4, default=str)
            for line in formatted.split("\n"):
                logger.info(f"   {line}")
    
    if response.get("error"):
        logger.error(f"   Error: {response['error']}")