#!/usr/bin/env python3
"""
MCP (Model Context Protocol) Server for AliceMultiverse

This server exposes Alice's high-level interface to AI assistants.
It does NOT expose direct file access or underlying APIs - only Alice's functions.
"""

import asyncio
import json
import logging
from typing import Dict, Any, List, Optional

try:
    from mcp import Server, Tool
    from mcp.server import stdio
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    logger = logging.getLogger(__name__)
    logger.warning("MCP package not installed. Install with: pip install mcp")

from .interface import AliceInterface
from .interface.models import (
    SearchRequest, OrganizeRequest, TagRequest
)
from .metadata.models import AssetRole

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize server and alice interface
alice = AliceInterface()

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


@server.tool()
async def search_assets(
    description: Optional[str] = None,
    style_tags: Optional[List[str]] = None,
    mood_tags: Optional[List[str]] = None,
    subject_tags: Optional[List[str]] = None,
    time_reference: Optional[str] = None,
    min_quality_stars: Optional[int] = None,
    source_types: Optional[List[str]] = None,
    roles: Optional[List[str]] = None,
    limit: Optional[int] = 20,
    sort_by: Optional[str] = "relevance"
) -> Dict[str, Any]:
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
            sort_by=sort_by
        )
        
        response = alice.search_assets(request)
        return response
    except Exception as e:
        logger.error(f"Search failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Search failed"
        }


@server.tool()
async def organize_media(
    source_path: Optional[str] = None,
    quality_assessment: bool = True,
    enhanced_metadata: bool = True,
    pipeline: str = "standard",
    watch_mode: bool = False
) -> Dict[str, Any]:
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
            watch_mode=watch_mode
        )
        
        response = alice.organize_media(request)
        return response
    except Exception as e:
        logger.error(f"Organization failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Organization failed"
        }


@server.tool()
async def tag_assets(
    asset_ids: List[str],
    style_tags: Optional[List[str]] = None,
    mood_tags: Optional[List[str]] = None,
    subject_tags: Optional[List[str]] = None,
    custom_tags: Optional[List[str]] = None,
    role: Optional[str] = None
) -> Dict[str, Any]:
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
            role=role
        )
        
        response = alice.tag_assets(request)
        return response
    except Exception as e:
        logger.error(f"Tagging failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Tagging failed"
        }


@server.tool()
async def find_similar_assets(
    asset_id: str,
    threshold: float = 0.8,
    limit: int = 10
) -> Dict[str, Any]:
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
        return {
            "success": False,
            "error": str(e),
            "message": "Similar search failed"
        }


@server.tool()
async def get_asset_info(
    asset_id: str
) -> Dict[str, Any]:
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
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get asset info"
        }


@server.tool()
async def assess_quality(
    asset_ids: List[str],
    pipeline: str = "standard"
) -> Dict[str, Any]:
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
        return {
            "success": False,
            "error": str(e),
            "message": "Quality assessment failed"
        }


@server.tool()
async def get_organization_stats() -> Dict[str, Any]:
    """
    Get statistics about the organized media collection.
    
    Returns counts by date, source, quality, and project.
    """
    try:
        response = alice.get_stats()
        return response
    except Exception as e:
        logger.error(f"Get stats failed: {e}")
        return {
            "success": False,
            "error": str(e),
            "message": "Failed to get statistics"
        }


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
    
    # Run the server using stdio transport
    asyncio.run(stdio.run(server))


if __name__ == "__main__":
    main()