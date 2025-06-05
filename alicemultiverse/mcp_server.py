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
from .projects.service import ProjectService

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

# Initialize project service
project_service = ProjectService()

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


@server.tool()
async def create_project(
    name: str,
    description: str = "",
    budget: float | None = None,
    style: str | None = None,
    mood: str | None = None,
    theme: str | None = None
) -> dict[str, Any]:
    """
    Create a new creative project with optional context.
    
    Parameters:
    - name: Project name (will be folder name)
    - description: Project description
    - budget: Optional budget limit for AI generation costs
    - style: Creative style (e.g., "cyberpunk", "minimalist")
    - mood: Desired mood (e.g., "dark", "energetic")
    - theme: Project theme (e.g., "nature", "technology")
    
    Creates project structure with folders for created/selected/rounds/exports.
    """
    try:
        # Build creative context from parameters
        creative_context = {}
        if style:
            creative_context["style"] = style
        if mood:
            creative_context["mood"] = mood
        if theme:
            creative_context["theme"] = theme
            
        project = project_service.create_project(
            name=name,
            description=description,
            budget_total=budget,
            creative_context=creative_context
        )
        
        return {
            "success": True,
            "message": f"Project '{name}' created successfully",
            "data": {
                "name": project.name,
                "path": str(project.path),
                "folders": ["created", "selected", "rounds", "exports"],
                "budget": project.budget.total if project.budget else None,
                "creative_context": project.creative_context
            }
        }
    except Exception as e:
        logger.error(f"Project creation failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to create project"}


@server.tool()
async def list_projects() -> dict[str, Any]:
    """
    List all available projects with their status and budget info.
    
    Returns project names, descriptions, budgets, and file counts.
    """
    try:
        projects = project_service.list_projects()
        
        project_list = []
        for project in projects:
            project_info = {
                "name": project.name,
                "description": project.description,
                "created_at": project.created_at.isoformat() if project.created_at else None,
                "updated_at": project.updated_at.isoformat() if project.updated_at else None,
                "creative_context": project.creative_context
            }
            
            # Add budget info if available
            if project.budget:
                project_info["budget"] = {
                    "total": project.budget.total,
                    "spent": project.budget.spent,
                    "remaining": project.budget.total - project.budget.spent,
                    "alerts_enabled": project.budget.alerts_enabled
                }
            
            project_list.append(project_info)
        
        return {
            "success": True,
            "message": f"Found {len(project_list)} projects",
            "data": project_list
        }
    except Exception as e:
        logger.error(f"List projects failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to list projects"}


@server.tool()
async def get_project_context(name: str) -> dict[str, Any]:
    """
    Get creative context and current status for a specific project.
    
    Parameters:
    - name: Project name
    
    Returns creative context, budget status, and file statistics.
    """
    try:
        project = project_service.get_project(name)
        if not project:
            return {
                "success": False,
                "message": f"Project '{name}' not found"
            }
        
        # Get file statistics if possible
        stats = {}
        if project.path and project.path.exists():
            for folder in ["created", "selected", "rounds", "exports"]:
                folder_path = project.path / folder
                if folder_path.exists():
                    stats[folder] = len(list(folder_path.glob("*")))
        
        response_data = {
            "name": project.name,
            "description": project.description,
            "creative_context": project.creative_context,
            "settings": project.settings,
            "statistics": stats
        }
        
        # Add budget info if available
        if project.budget:
            response_data["budget"] = {
                "total": project.budget.total,
                "spent": project.budget.spent,
                "remaining": project.budget.total - project.budget.spent,
                "percentage_used": (project.budget.spent / project.budget.total * 100) if project.budget.total > 0 else 0
            }
        
        return {
            "success": True,
            "message": f"Project context for '{name}'",
            "data": response_data
        }
    except Exception as e:
        logger.error(f"Get project context failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to get project context"}


@server.tool()
async def find_duplicates(
    check_similar: bool = False,
    similarity_threshold: float = 0.95,
    limit: int = 100
) -> dict[str, Any]:
    """
    Find duplicate or near-duplicate assets in your collection.
    
    Parameters:
    - check_similar: If True, use perceptual hashing to find similar (not just identical) images
    - similarity_threshold: For similar images, how similar (0.0-1.0, higher = more similar)
    - limit: Maximum number of duplicate sets to return
    
    Returns groups of duplicate/similar assets with their locations and sizes.
    """
    try:
        # Get all assets from the search cache
        all_assets = []
        
        # Query the DuckDB cache for all assets with hashes
        conn = storage.get_connection()
        cursor = conn.cursor()
        
        if check_similar:
            # Get assets with perceptual hashes
            cursor.execute("""
                SELECT content_hash, file_path, file_size, 
                       perceptual_hash, difference_hash, average_hash
                FROM assets 
                WHERE perceptual_hash IS NOT NULL
                ORDER BY file_path
            """)
        else:
            # Get all assets for exact duplicate check
            cursor.execute("""
                SELECT content_hash, file_path, file_size
                FROM assets
                ORDER BY file_path
            """)
        
        rows = cursor.fetchall()
        
        # Group by hash
        if check_similar:
            # TODO: Implement perceptual hash similarity comparison
            # For now, we'll just return a message that this feature is coming
            return {
                "success": True,
                "message": "Similar image detection coming soon",
                "data": {
                    "note": "Currently only exact duplicates are detected. Perceptual similarity search is in development."
                }
            }
        else:
            # Group by content hash for exact duplicates
            hash_groups = {}
            for row in rows:
                content_hash, file_path, file_size = row
                if content_hash not in hash_groups:
                    hash_groups[content_hash] = []
                hash_groups[content_hash].append({
                    "path": file_path,
                    "size": file_size
                })
            
            # Filter to only groups with duplicates
            duplicate_groups = []
            total_wasted_space = 0
            
            for content_hash, files in hash_groups.items():
                if len(files) > 1:
                    # Calculate wasted space (all but one copy)
                    wasted = sum(f["size"] for f in files[1:])
                    total_wasted_space += wasted
                    
                    duplicate_groups.append({
                        "hash": content_hash,
                        "count": len(files),
                        "files": files,
                        "wasted_space": wasted
                    })
            
            # Sort by wasted space descending
            duplicate_groups.sort(key=lambda x: x["wasted_space"], reverse=True)
            
            # Limit results
            duplicate_groups = duplicate_groups[:limit]
            
            return {
                "success": True,
                "message": f"Found {len(duplicate_groups)} sets of duplicates",
                "data": {
                    "duplicate_groups": duplicate_groups,
                    "total_duplicate_sets": len(hash_groups),
                    "total_wasted_space": total_wasted_space,
                    "total_wasted_space_mb": round(total_wasted_space / 1024 / 1024, 2)
                }
            }
            
    except Exception as e:
        logger.error(f"Find duplicates failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to find duplicates"}


@server.tool()
async def update_project_context(
    name: str,
    style: str | None = None,
    mood: str | None = None,
    theme: str | None = None,
    notes: str | None = None
) -> dict[str, Any]:
    """
    Update creative context for an existing project.
    
    Parameters:
    - name: Project name
    - style: Update creative style
    - mood: Update mood
    - theme: Update theme
    - notes: Add creative notes
    
    Updates are merged with existing context.
    """
    try:
        project = project_service.get_project(name)
        if not project:
            return {
                "success": False,
                "message": f"Project '{name}' not found"
            }
        
        # Build context updates
        context_updates = {}
        if style is not None:
            context_updates["style"] = style
        if mood is not None:
            context_updates["mood"] = mood
        if theme is not None:
            context_updates["theme"] = theme
        if notes is not None:
            context_updates["notes"] = notes
        
        # Update project context
        updated_project = project_service.update_project_context(name, context_updates)
        
        return {
            "success": True,
            "message": f"Updated context for project '{name}'",
            "data": {
                "name": updated_project.name,
                "creative_context": updated_project.creative_context
            }
        }
    except Exception as e:
        logger.error(f"Update project context failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to update project context"}


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
    logger.info("  - create_project: Create new creative project with context")
    logger.info("  - list_projects: List all projects with status and budget")
    logger.info("  - get_project_context: Get project creative context and status")
    logger.info("  - update_project_context: Update project creative context")
    logger.info("  - find_duplicates: Find exact duplicate files in collection")

    # Run the server using stdio transport
    asyncio.run(stdio.run(server))


if __name__ == "__main__":
    main()
