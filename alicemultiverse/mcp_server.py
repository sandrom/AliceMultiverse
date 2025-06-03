#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for AliceMultiverse

This server exposes Alice's high-level interface to AI assistants.
It does NOT expose direct file access or underlying APIs - only Alice's functions.
"""

import asyncio
import logging
from typing import Any

try:
    from mcp import Server, Tool
    from mcp.server import stdio

    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("MCP package not installed. Install with: pip install mcp")

from .interface import AliceInterface
from .interface.models import OrganizeRequest, SearchRequest, TagRequest
from .interface.image_presentation import ImagePresentationAPI
from .interface.image_presentation_mcp import register_image_presentation_tools
from .interface.video_creation_mcp import register_video_creation_tools
from .storage.duckdb_cache import DuckDBSearchCache
from .storage.duckdb_search import DuckDBSearch
from .core.cost_tracker import get_cost_tracker

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server and alice interface
alice = AliceInterface()

# Initialize image presentation API
storage = DuckDBSearchCache()
image_api = ImagePresentationAPI(storage=storage)

# Initialize DuckDB search for video creation tools
search_db = DuckDBSearch()

if MCP_AVAILABLE:
    server = Server("alice-multiverse")
else:
    # Create a dummy server object for the decorators
    class DummyServer:
        def tool(self):
            def decorator(func):
                return func

            return decorator

    server = DummyServer()

# Register image presentation tools (works with both real and dummy server)
if MCP_AVAILABLE:
    register_image_presentation_tools(server, image_api)
    register_video_creation_tools(server, search_db)


@server.tool()
async def search_assets(
    description: str | None = None,
    style_tags: list[str] | None = None,
    mood_tags: list[str] | None = None,
    subject_tags: list[str] | None = None,
    time_reference: str | None = None,
    min_quality_stars: int | None = None,
    source_types: list[str] | None = None,
    roles: list[str] | None = None,
    limit: int | None = 20,
    sort_by: str | None = "relevance",
) -> dict[str, Any]:
    """
    Search for creative assets using natural language and tags.

    Examples:
    - description: "dark moody portraits with neon lighting"
    - style_tags: ["cyberpunk", "minimalist", "abstract"]
    - mood_tags: ["energetic", "melancholic", "mysterious"]
    - subject_tags: ["portrait", "landscape", "character"]
    - time_reference: "last week", "yesterday", "March 2024"
    - min_quality_stars: 4 (only return 4-5 star assets)
    - roles: ["hero", "b_roll", "reference"]

    Returns asset information without file paths.
    """
    try:
        request = SearchRequest(
            description=description,
            style_tags=style_tags,
            mood_tags=mood_tags,
            subject_tags=subject_tags,
            time_reference=time_reference,
            min_quality_stars=min_quality_stars,
            source_types=source_types,
            roles=roles,
            limit=limit,
            sort_by=sort_by,
        )

        response = alice.search_assets(request)
        return response
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {"success": False, "error": str(e), "message": "Search failed"}


@server.tool()
async def organize_media(
    source_path: str | None = None,
    quality_assessment: bool = True,
    enhanced_metadata: bool = True,
    pipeline: str = "standard",
    watch_mode: bool = False,
) -> dict[str, Any]:
    """
    Organize and analyze media files with quality assessment.

    Parameters:
    - source_path: Source directory (defaults to configured inbox)
    - quality_assessment: Enable BRISQUE quality scoring
    - enhanced_metadata: Extract rich metadata for AI navigation
    - pipeline: Quality pipeline ("basic", "standard", "premium")
    - watch_mode: Continuously monitor for new files

    Returns organization statistics and processed asset information.
    """
    try:
        request = OrganizeRequest(
            source_path=source_path,
            quality_assessment=quality_assessment,
            enhanced_metadata=enhanced_metadata,
            pipeline=pipeline,
            watch_mode=watch_mode,
        )

        response = alice.organize_media(request)
        return response
    except Exception as e:
        logger.error(f"Organization failed: {e}")
        return {"success": False, "error": str(e), "message": "Organization failed"}


@server.tool()
async def tag_assets(
    asset_ids: list[str],
    style_tags: list[str] | None = None,
    mood_tags: list[str] | None = None,
    subject_tags: list[str] | None = None,
    custom_tags: list[str] | None = None,
    role: str | None = None,
) -> dict[str, Any]:
    """
    Add semantic tags to assets for better organization and discovery.

    Parameters:
    - asset_ids: List of asset IDs to tag
    - style_tags: Visual style descriptors
    - mood_tags: Emotional/mood descriptors
    - subject_tags: Subject matter descriptors
    - custom_tags: Custom project-specific tags
    - role: Asset role ("hero", "b_roll", "reference", "alternate")

    Tags help with future discovery and workflow automation.
    """
    try:
        request = TagRequest(
            asset_ids=asset_ids,
            style_tags=style_tags,
            mood_tags=mood_tags,
            subject_tags=subject_tags,
            custom_tags=custom_tags,
            role=role,
        )

        response = alice.tag_assets(request)
        return response
    except Exception as e:
        logger.error(f"Tagging failed: {e}")
        return {"success": False, "error": str(e), "message": "Tagging failed"}


@server.tool()
async def find_similar_assets(
    asset_id: str, threshold: float = 0.8, limit: int = 10
) -> dict[str, Any]:
    """
    Find assets similar to a reference asset.

    Parameters:
    - asset_id: Reference asset ID
    - threshold: Similarity threshold (0.0-1.0, higher = more similar)
    - limit: Maximum number of results

    Finds visually or conceptually similar assets based on metadata and tags.
    """
    try:
        response = alice.find_similar_assets(asset_id, threshold)
        return response
    except Exception as e:
        logger.error(f"Similar search failed: {e}")
        return {"success": False, "error": str(e), "message": "Similar search failed"}


@server.tool()
async def get_asset_info(asset_id: str) -> dict[str, Any]:
    """
    Get detailed information about a specific asset.

    Parameters:
    - asset_id: The unique asset identifier

    Returns comprehensive metadata including prompt, tags, quality, and relationships.
    """
    try:
        response = alice.get_asset_info(asset_id)
        return response
    except Exception as e:
        logger.error(f"Get asset info failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to get asset info"}


@server.tool()
async def assess_quality(asset_ids: list[str], pipeline: str = "standard") -> dict[str, Any]:
    """
    Run quality assessment on specific assets.

    Parameters:
    - asset_ids: List of asset IDs to assess
    - pipeline: Assessment pipeline ("basic", "standard", "premium")

    Returns quality scores and identified issues for each asset.
    """
    try:
        response = alice.assess_quality(asset_ids, pipeline)
        return response
    except Exception as e:
        logger.error(f"Quality assessment failed: {e}")
        return {"success": False, "error": str(e), "message": "Quality assessment failed"}


@server.tool()
async def get_organization_stats() -> dict[str, Any]:
    """
    Get statistics about the organized media collection.

    Returns counts by date, source, quality, and project.
    """
    try:
        response = alice.get_stats()
        return response
    except Exception as e:
        logger.error(f"Get stats failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to get statistics"}


@server.tool()
async def estimate_cost(
    operation: str,
    file_count: int = 1,
    providers: list[str] | None = None,
    detailed: bool = False,
) -> dict[str, Any]:
    """
    Estimate cost for an operation before running it.
    
    Parameters:
    - operation: Type of operation ("organize", "understand", "generate", etc.)
    - file_count: Number of files to process
    - providers: List of providers to use (defaults to configured providers)
    - detailed: Whether detailed analysis is requested
    
    Returns cost estimate with breakdown and budget warnings.
    """
    try:
        cost_tracker = get_cost_tracker()
        
        # Map operation to providers if not specified
        if not providers:
            if operation in ["organize", "understand", "analyze"]:
                # Get configured understanding providers
                from .core.config import load_config
                config = load_config()
                if hasattr(config, "understanding") and hasattr(config.understanding, "providers"):
                    providers = [p["name"] for p in config.understanding.providers]
                else:
                    providers = ["anthropic"]  # Default
            else:
                providers = []
        
        # Get batch estimate
        estimate = cost_tracker.estimate_batch_cost(
            file_count=file_count,
            providers=providers,
            operation=operation,
            detailed=detailed
        )
        
        return {
            "success": True,
            "message": f"Cost estimate for {operation}",
            "data": estimate
        }
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        return {"success": False, "error": str(e), "message": "Cost estimation failed"}


@server.tool()
async def get_spending_report() -> dict[str, Any]:
    """
    Get spending report showing costs by provider and time period.
    
    Returns daily, weekly, monthly spending with budget status.
    """
    try:
        cost_tracker = get_cost_tracker()
        
        # Get spending summary
        summary = cost_tracker.get_spending_summary()
        
        # Get provider comparison
        comparison = cost_tracker.get_provider_comparison()
        
        # Format report
        report = cost_tracker.format_cost_report()
        
        return {
            "success": True,
            "message": "Spending report generated",
            "data": {
                "summary": summary,
                "providers": comparison,
                "formatted_report": report
            }
        }
    except Exception as e:
        logger.error(f"Spending report failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to generate spending report"}


@server.tool()
async def set_budget(
    period: str,
    limit: float,
    alert_threshold: float = 0.8
) -> dict[str, Any]:
    """
    Set a spending budget to control costs.
    
    Parameters:
    - period: Budget period ("daily", "weekly", "monthly", "total")
    - limit: Budget limit in dollars
    - alert_threshold: Alert when spending reaches this fraction (0-1)
    
    Returns confirmation of budget setting.
    """
    try:
        cost_tracker = get_cost_tracker()
        cost_tracker.set_budget(period, limit, alert_threshold)
        
        return {
            "success": True,
            "message": f"Set {period} budget to ${limit:.2f}",
            "data": {
                "period": period,
                "limit": limit,
                "alert_threshold": alert_threshold
            }
        }
    except Exception as e:
        logger.error(f"Set budget failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to set budget"}


def main():
    """Run the MCP server."""
    if not MCP_AVAILABLE:
        logger.error("MCP package is not installed.")
        logger.error("To use the MCP server, install it with: pip install mcp")
        logger.error("")
        logger.error("Alternative: Use the REST API server instead:")
        logger.error("  python -m alicemultiverse.mcp_server_mock")
        return

    logger.info("Starting AliceMultiverse MCP Server...")
    logger.info("Available tools:")
    logger.info("  - search_assets: Find assets using creative concepts")
    logger.info("  - organize_media: Process and organize media files")
    logger.info("  - tag_assets: Add semantic tags to assets")
    logger.info("  - find_similar_assets: Find similar assets")
    logger.info("  - get_asset_info: Get asset details")
    logger.info("  - assess_quality: Run quality assessment")
    logger.info("  - get_organization_stats: Get collection statistics")
    logger.info("  - search_images: Browse images for collaborative selection")
    logger.info("  - track_selection: Record image selection decisions")
    logger.info("  - soft_delete_image: Move unwanted images to sorted folder")
    logger.info("  - get_selection_summary: Get summary of selected images")
    logger.info("  - estimate_cost: Preview costs before running operations")
    logger.info("  - get_spending_report: View spending by provider and time")
    logger.info("  - set_budget: Set spending limits with alerts")
    logger.info("  - analyze_for_video: Analyze image for video generation potential")
    logger.info("  - generate_video_storyboard: Create video storyboard from images")
    logger.info("  - create_kling_prompts: Generate Kling-ready prompts")
    logger.info("  - prepare_flux_keyframes: Create enhanced keyframes with Flux")
    logger.info("  - create_transition_guide: Generate video editing guide")

    # Run the server using stdio transport
    asyncio.run(stdio.run(server))


if __name__ == "__main__":
    main()
