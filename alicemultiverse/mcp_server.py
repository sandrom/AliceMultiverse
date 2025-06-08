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
    from mcp import Server
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
from .interface.analytics_mcp import (
    start_analytics_session as analytics_start_session,
    end_analytics_session as analytics_end_session,
    track_workflow_event as analytics_track_workflow,
    track_export_event as analytics_track_export,
    get_performance_insights as analytics_get_insights,
    get_export_analytics as analytics_get_export_stats,
    get_improvement_suggestions as analytics_get_improvements,
    track_user_action as analytics_track_action
)
from .storage.duckdb_cache import DuckDBSearchCache
from .storage.duckdb_search import DuckDBSearch
from .core.cost_tracker import get_cost_tracker
from .projects.service import ProjectService
from .selections.service import SelectionService
from .selections.models import SelectionPurpose
from .prompts.mcp_tools import PromptMCPTools
from .memory.style_memory_mcp import (
    track_style_preference as memory_track_preference,
    get_style_recommendations as memory_get_recommendations,
    analyze_style_patterns as memory_analyze_patterns,
    start_style_workflow as memory_start_workflow,
    end_style_workflow as memory_end_workflow,
    get_style_evolution as memory_get_evolution,
    suggest_next_action as memory_suggest_action,
    export_style_profile as memory_export_profile,
    import_style_profile as memory_import_profile
)
from .workflows.templates.template_mcp import (
    create_story_arc_video,
    create_documentary_video,
    create_social_media_video,
    create_instagram_reel,
    create_tiktok_video,
    get_platform_specifications,
    suggest_story_structure
)
from .interface.variation_mcp import (
    generate_content_variations,
    track_variation_performance,
    create_variation_group,
    get_variation_insights,
    find_top_variations,
    get_variation_recommendations,
    analyze_variation_success,
    export_variation_analytics
)
from .interface.composition_mcp import (
    analyze_timeline_flow,
    analyze_image_composition,
    analyze_timeline_compositions,
    optimize_timeline,
    suggest_clip_order,
    detect_composition_patterns
)

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

# Initialize selection service
selection_service = SelectionService()

# Initialize prompt tools
prompt_tools = PromptMCPTools()

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
        pass
        
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
async def quick_mark(
    asset_ids: list[str],
    mark_type: str = "favorite",
    project_name: str | None = None
) -> dict[str, Any]:
    """
    Quickly mark assets as favorites or other quick categories.
    
    Parameters:
    - asset_ids: List of asset content hashes to mark
    - mark_type: Type of mark - "favorite", "hero", "maybe", "review"
    - project_name: Optional project to associate with
    
    Fast marking without detailed metadata for rapid triage.
    """
    try:
        # Map mark types to selection purposes
        purpose_map = {
            "favorite": SelectionPurpose.CURATION,
            "hero": SelectionPurpose.PRESENTATION,
            "maybe": SelectionPurpose.REVIEW,
            "review": SelectionPurpose.REVIEW
        }
        purpose = purpose_map.get(mark_type, SelectionPurpose.CURATION)
        
        # Create or get quick selection for today
        from datetime import datetime
        today = datetime.now().strftime("%Y-%m-%d")
        selection_name = f"quick-{mark_type}-{today}"
        
        # Check if selection exists
        existing = None
        selections = selection_service.list_selections(project_name=project_name)
        for sel in selections:
            if sel.name == selection_name:
                existing = sel
                break
        
        # Create selection if it doesn't exist
        if not existing:
            selection = selection_service.create_selection(
                name=selection_name,
                purpose=purpose,
                project_name=project_name,
                description=f"Quick {mark_type} selections for {today}"
            )
        else:
            selection = existing
        
        # Add assets to selection
        added_count = 0
        already_added = []
        
        for asset_id in asset_ids:
            try:
                selection_service.add_asset(
                    selection_id=selection.id,
                    content_hash=asset_id,
                    reason=f"Quick marked as {mark_type}",
                    tags=[mark_type, "quick-mark"]
                )
                added_count += 1
            except Exception as e:
                if "already in selection" in str(e):
                    already_added.append(asset_id)
                else:
                    logger.debug(f"Failed to add asset {asset_id}: {e}")
        
        return {
            "success": True,
            "message": f"Marked {added_count} assets as {mark_type}",
            "data": {
                "selection_id": selection.id,
                "selection_name": selection.name,
                "added_count": added_count,
                "already_added_count": len(already_added),
                "total_in_selection": len(selection.assets)
            }
        }
        
    except Exception as e:
        logger.error(f"Quick mark failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to mark assets"}


@server.tool()
async def list_quick_marks(
    mark_type: str | None = None,
    project_name: str | None = None,
    days_back: int = 7
) -> dict[str, Any]:
    """
    List recent quick marks/favorites.
    
    Parameters:
    - mark_type: Filter by type - "favorite", "hero", "maybe", "review" 
    - project_name: Filter by project
    - days_back: How many days back to look (default 7)
    
    Returns recent quick selections with asset counts.
    """
    try:
        from datetime import datetime, timedelta
        
        # Get all selections
        selections = selection_service.list_selections(project_name=project_name)
        
        # Filter to quick marks
        quick_selections = []
        cutoff_date = datetime.now() - timedelta(days=days_back)
        
        for sel in selections:
            # Check if it's a quick selection
            if not sel.name.startswith("quick-"):
                continue
                
            # Check mark type filter
            if mark_type and f"quick-{mark_type}" not in sel.name:
                continue
                
            # Check date
            if sel.created_at < cutoff_date:
                continue
                
            # Extract mark type from name
            parts = sel.name.split("-")
            if len(parts) >= 2:
                sel_mark_type = parts[1]
            else:
                sel_mark_type = "unknown"
            
            quick_selections.append({
                "id": sel.id,
                "name": sel.name,
                "mark_type": sel_mark_type,
                "project": sel.project_name,
                "created_at": sel.created_at.isoformat(),
                "asset_count": len(sel.assets),
                "description": sel.description
            })
        
        # Sort by creation date descending
        quick_selections.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {
            "success": True,
            "message": f"Found {len(quick_selections)} quick mark collections",
            "data": {
                "selections": quick_selections,
                "days_back": days_back,
                "mark_type_filter": mark_type
            }
        }
        
    except Exception as e:
        logger.error(f"List quick marks failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to list quick marks"}


@server.tool()
async def export_quick_marks(
    selection_id: str,
    export_path: str | None = None,
    copy_files: bool = True
) -> dict[str, Any]:
    """
    Export quick marked assets to a folder.
    
    Parameters:
    - selection_id: ID of the quick selection to export
    - export_path: Where to export (defaults to exports/selection-name/)
    - copy_files: Whether to copy files or just create manifest
    
    Exports marked assets for use in other tools.
    """
    try:
        from pathlib import Path
        
        # Get the selection
        selection = selection_service.get_selection(selection_id)
        if not selection:
            return {
                "success": False,
                "message": f"Selection {selection_id} not found"
            }
        
        # Determine export path
        if not export_path:
            export_path = f"exports/{selection.name}"
        
        export_dir = Path(export_path)
        
        # Export the selection
        manifest_path = selection_service.export_selection(
            selection_id=selection_id,
            export_dir=export_dir,
            copy_files=copy_files
        )
        
        return {
            "success": True,
            "message": f"Exported {len(selection.assets)} assets",
            "data": {
                "export_path": str(export_dir),
                "manifest_path": str(manifest_path),
                "asset_count": len(selection.assets),
                "copy_files": copy_files
            }
        }
        
    except Exception as e:
        logger.error(f"Export quick marks failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to export marks"}


@server.tool()
async def analyze_images_optimized(
    image_paths: list[str] | None = None,
    project_name: str | None = None,
    provider: str | None = None,
    similarity_threshold: float = 0.9,
    use_progressive: bool = True,
    max_cost: float | None = None,
    show_details: bool = False
) -> dict[str, Any]:
    """
    Analyze images with cost optimization through similarity detection.
    
    Parameters:
    - image_paths: List of image paths to analyze (or use project)
    - project_name: Analyze all images in a project
    - provider: Specific provider to use (or auto-select cheapest)
    - similarity_threshold: How similar images must be to share analysis (0-1)
    - use_progressive: Start with cheap providers, escalate if needed
    - max_cost: Maximum cost limit for the batch
    - show_details: Include detailed analysis
    
    Groups similar images and analyzes representatives to save costs.
    """
    try:
        from pathlib import Path
        from .understanding.analyzer import ImageAnalyzer
        from .understanding.optimized_batch_analyzer import OptimizedBatchAnalyzer
        from .understanding.batch_analyzer import BatchAnalysisRequest
        
        # Convert string paths to Path objects
        if image_paths:
            paths = [Path(p) for p in image_paths]
        else:
            paths = None
        
        # Create analyzer and batch request
        analyzer = ImageAnalyzer()
        optimizer = OptimizedBatchAnalyzer(
            analyzer=analyzer,
            similarity_threshold=similarity_threshold,
            use_progressive_providers=use_progressive
        )
        
        # Build batch request
        request = BatchAnalysisRequest(
            image_paths=paths,
            project_id=project_name,  # Will be handled by project lookup
            provider=provider,
            detailed=show_details,
            max_cost=max_cost,
            extract_tags=True,
            show_progress=False  # No progress in MCP
        )
        
        # Run optimized analysis
        results, stats = await optimizer.analyze_batch_optimized(request)
        
        # Format results
        analyzed_images = []
        for img_path, result in results:
            if result:
                analyzed_images.append({
                    "path": str(img_path),
                    "description": result.description,
                    "tags": result.tags,
                    "provider": result.provider,
                    "cost": result.cost,
                    "confidence": getattr(result, 'confidence_score', 1.0)
                })
        
        return {
            "success": True,
            "message": f"Analyzed {stats.images_analyzed} unique images, applied to {stats.total_images} total",
            "data": {
                "results": analyzed_images,
                "optimization_stats": {
                    "total_images": stats.total_images,
                    "unique_groups": stats.unique_groups,
                    "images_analyzed": stats.images_analyzed,
                    "images_reused": stats.images_reused,
                    "api_calls_saved": stats.api_calls_saved,
                    "cost_saved": round(stats.cost_saved, 4),
                    "total_cost": round(stats.total_cost, 4),
                    "savings_percentage": round((stats.cost_saved / (stats.total_cost + stats.cost_saved) * 100) if stats.total_cost > 0 else 0, 1)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Optimized analysis failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to analyze images"}


@server.tool()
async def estimate_analysis_cost(
    image_count: int,
    provider: str | None = None,
    detailed: bool = False,
    with_optimization: bool = True,
    similarity_rate: float = 0.3
) -> dict[str, Any]:
    """
    Estimate cost for analyzing a batch of images.
    
    Parameters:
    - image_count: Number of images to analyze
    - provider: Specific provider (or compare all)
    - detailed: Whether detailed analysis is requested
    - with_optimization: Include similarity optimization estimate
    - similarity_rate: Estimated rate of similar images (0-1)
    
    Returns cost estimates with and without optimization.
    """
    try:
        from .understanding.analyzer import ImageAnalyzer
        
        analyzer = ImageAnalyzer()
        available_providers = analyzer.get_available_providers()
        
        estimates = {}
        
        # Get base costs per provider
        for prov in available_providers:
            if provider and prov != provider:
                continue
                
            if prov in analyzer.analyzers:
                cost_per_image = analyzer.analyzers[prov].estimate_cost(detailed)
                base_cost = cost_per_image * image_count
                
                # Calculate optimized cost
                if with_optimization:
                    # Estimate unique images after similarity grouping
                    unique_images = int(image_count * (1 - similarity_rate))
                    optimized_cost = cost_per_image * unique_images
                    savings = base_cost - optimized_cost
                else:
                    optimized_cost = base_cost
                    savings = 0
                
                estimates[prov] = {
                    "cost_per_image": cost_per_image,
                    "base_cost": round(base_cost, 4),
                    "optimized_cost": round(optimized_cost, 4),
                    "savings": round(savings, 4),
                    "savings_percentage": round((savings / base_cost * 100) if base_cost > 0 else 0, 1)
                }
        
        # Find cheapest option
        if estimates:
            cheapest = min(estimates.items(), key=lambda x: x[1]["optimized_cost"])
            cheapest_provider = cheapest[0]
        else:
            cheapest_provider = None
        
        return {
            "success": True,
            "message": f"Cost estimate for {image_count} images",
            "data": {
                "image_count": image_count,
                "estimates": estimates,
                "cheapest_provider": cheapest_provider,
                "similarity_rate": similarity_rate,
                "with_optimization": with_optimization
            }
        }
        
    except Exception as e:
        logger.error(f"Cost estimation failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to estimate costs"}


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


@server.tool()
async def check_ollama_status() -> dict[str, Any]:
    """
    Check if Ollama is running and what vision models are available.
    
    Returns information about local vision model availability.
    """
    try:
        from .understanding.ollama_provider import OllamaImageAnalyzer
        
        analyzer = OllamaImageAnalyzer()
        is_available = await analyzer.check_availability()
        
        if is_available:
            # Get available models
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get("http://localhost:11434/api/tags") as response:
                    if response.status == 200:
                        data = await response.json()
                        models = data.get("models", [])
                        vision_models = [m["name"] for m in models if any(
                            keyword in m["name"].lower() 
                            for keyword in ["llava", "bakllava", "phi3"]
                        )]
                        
                        return {
                            "success": True,
                            "message": "Ollama is running with vision models available",
                            "data": {
                                "available": True,
                                "vision_models": vision_models,
                                "recommended": OllamaImageAnalyzer.get_recommended_model("general"),
                                "capabilities": {
                                    "free": True,
                                    "private": True,
                                    "supports_batch": False,
                                    "speed": "fast"
                                }
                            }
                        }
        
        return {
            "success": True,
            "message": "Ollama is not available",
            "data": {
                "available": False,
                "install_instructions": "Install Ollama from https://ollama.ai, then run: ollama pull llava"
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to check Ollama status: {e}")
        return {"success": False, "error": str(e), "message": "Failed to check Ollama status"}


@server.tool()
async def analyze_with_local(
    image_paths: list[str],
    model: str = "llava:latest",
    fallback_to_cloud: bool = True,
    cloud_provider: str | None = None
) -> dict[str, Any]:
    """
    Analyze images using local Ollama models.
    
    Parameters:
    - image_paths: List of image paths to analyze
    - model: Ollama vision model to use (llava:latest, llava:13b, etc.)
    - fallback_to_cloud: If local fails, use cloud provider
    - cloud_provider: Specific cloud provider for fallback
    
    Free, private analysis using local vision models.
    """
    try:
        from pathlib import Path
        from .understanding.analyzer import ImageAnalyzer
        
        results = []
        failed_local = []
        
        # Try local analysis first
        analyzer = ImageAnalyzer()
        
        # Check if Ollama is available
        if "ollama" in analyzer.get_available_providers():
            for image_path in image_paths:
                try:
                    result = await analyzer.analyze(
                        Path(image_path),
                        provider="ollama",
                        extract_tags=True,
                        generate_prompt=True
                    )
                    
                    results.append({
                        "path": image_path,
                        "success": True,
                        "provider": "ollama",
                        "model": model,
                        "description": result.description,
                        "tags": result.tags,
                        "cost": 0.0,
                        "local": True
                    })
                    
                except Exception as e:
                    logger.warning(f"Local analysis failed for {image_path}: {e}")
                    failed_local.append(image_path)
        else:
            # Ollama not available, all images fail local
            failed_local = image_paths
        
        # Fallback to cloud if needed
        if failed_local and fallback_to_cloud:
            for image_path in failed_local:
                try:
                    result = await analyzer.analyze(
                        Path(image_path),
                        provider=cloud_provider,  # Will use cheapest if None
                        extract_tags=True,
                        generate_prompt=True
                    )
                    
                    results.append({
                        "path": image_path,
                        "success": True,
                        "provider": result.provider,
                        "model": result.model,
                        "description": result.description,
                        "tags": result.tags,
                        "cost": result.cost,
                        "local": False
                    })
                    
                except Exception as e:
                    logger.error(f"Cloud analysis also failed for {image_path}: {e}")
                    results.append({
                        "path": image_path,
                        "success": False,
                        "error": str(e),
                        "local": False
                    })
        
        # Calculate stats
        local_count = sum(1 for r in results if r.get("local", False))
        cloud_count = sum(1 for r in results if r.get("success") and not r.get("local", False))
        failed_count = sum(1 for r in results if not r.get("success"))
        total_cost = sum(r.get("cost", 0) for r in results)
        
        return {
            "success": True,
            "message": f"Analyzed {len(results)} images ({local_count} local, {cloud_count} cloud)",
            "data": {
                "results": results,
                "stats": {
                    "total": len(image_paths),
                    "local_analyzed": local_count,
                    "cloud_analyzed": cloud_count,
                    "failed": failed_count,
                    "total_cost": round(total_cost, 4),
                    "savings": round(local_count * 0.001, 4)  # Estimate cloud cost savings
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Hybrid analysis failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to analyze images"}


@server.tool()
async def pull_ollama_model(
    model: str = "llava:latest"
) -> dict[str, Any]:
    """
    Download an Ollama vision model for local analysis.
    
    Parameters:
    - model: Model to download (llava:latest, llava:13b, bakllava:latest, etc.)
    
    Downloads vision models for free, private image analysis.
    """
    try:
        from .understanding.ollama_provider import OllamaImageAnalyzer
        
        analyzer = OllamaImageAnalyzer(model=model)
        
        # Check if already available
        if await analyzer.check_availability():
            return {
                "success": True,
                "message": f"Model {model} is already available",
                "data": {"model": model, "status": "ready"}
            }
        
        # Pull the model
        logger.info(f"Pulling Ollama model {model}...")
        success = await analyzer.pull_model(model)
        
        if success:
            return {
                "success": True,
                "message": f"Successfully pulled model {model}",
                "data": {"model": model, "status": "downloaded"}
            }
        else:
            return {
                "success": False,
                "message": f"Failed to pull model {model}",
                "data": {"model": model, "status": "failed"}
            }
            
    except Exception as e:
        logger.error(f"Failed to pull Ollama model: {e}")
        return {"success": False, "error": str(e), "message": "Failed to pull model"}


@server.tool()
async def analyze_with_hierarchy(
    image_paths: list[str],
    project_id: str | None = None,
    expand_tags: bool = True,
    auto_cluster: bool = True
) -> dict[str, Any]:
    """
    Analyze images with intelligent tag hierarchies.
    
    Parameters:
    - image_paths: List of image paths to analyze
    - project_id: Optional project for project-specific tags
    - expand_tags: Include parent/related tags from hierarchy
    - auto_cluster: Group similar tags automatically
    
    Provides semantic relationships and tag organization.
    """
    try:
        from pathlib import Path
        from .understanding.enhanced_analyzer import EnhancedImageAnalyzer
        
        analyzer = EnhancedImageAnalyzer()
        results = []
        
        for image_path in image_paths:
            try:
                enhanced = await analyzer.analyze_with_hierarchy(
                    Path(image_path),
                    project_id=project_id,
                    expand_tags=expand_tags,
                    cluster_tags=auto_cluster
                )
                
                results.append({
                    "path": image_path,
                    "success": True,
                    "tags": enhanced["normalized_tags"],
                    "expanded_tags": enhanced.get("expanded_tags", []),
                    "hierarchical_tags": enhanced.get("hierarchical_tags", {}),
                    "tag_clusters": enhanced.get("tag_clusters", []),
                    "suggested_tags": enhanced.get("suggested_tags", []),
                    "coherence_score": enhanced.get("tag_statistics", {}).get("coherence_score", 0)
                })
                
            except Exception as e:
                logger.error(f"Failed to analyze {image_path}: {e}")
                results.append({
                    "path": image_path,
                    "success": False,
                    "error": str(e)
                })
        
        # Get overall insights
        successful = [r for r in results if r.get("success")]
        insights = analyzer.get_tag_insights() if successful else {}
        
        return {
            "success": True,
            "message": f"Analyzed {len(successful)} images with tag hierarchies",
            "data": {
                "results": results,
                "insights": insights,
                "stats": {
                    "total_images": len(image_paths),
                    "successful": len(successful),
                    "unique_tags": len(set(
                        tag for r in successful 
                        for tag in r.get("tags", [])
                    ))
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Hierarchical analysis failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to analyze with hierarchy"}


@server.tool()
async def create_tag_mood_board(
    name: str,
    tags: list[str] | None = None,
    image_paths: list[str] | None = None,
    colors: list[str] | None = None,
    description: str = ""
) -> dict[str, Any]:
    """
    Create a mood board from tags and images.
    
    Parameters:
    - name: Mood board name
    - tags: Tags to include in mood board
    - image_paths: Reference images
    - colors: Hex color codes
    - description: Board description
    
    Mood boards help organize creative concepts.
    """
    try:
        from .understanding.enhanced_analyzer import EnhancedImageAnalyzer
        
        analyzer = EnhancedImageAnalyzer()
        
        # Create mood board
        board = analyzer.taxonomy.create_mood_board(name, description)
        
        # Add elements
        if tags or image_paths or colors:
            analyzer.taxonomy.add_to_mood_board(
                board.id,
                tags=tags,
                colors=colors,
                reference_images=image_paths
            )
        
        # Analyze mood board
        analysis = analyzer.taxonomy.analyze_mood_board(board.id)
        
        return {
            "success": True,
            "message": f"Created mood board '{name}'",
            "data": {
                "board_id": board.id,
                "name": board.name,
                "description": board.description,
                "tag_count": len(board.tags),
                "color_count": len(board.colors),
                "image_count": len(board.reference_images),
                "analysis": analysis
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to create mood board: {e}")
        return {"success": False, "error": str(e), "message": "Failed to create mood board"}


@server.tool()
async def get_tag_insights() -> dict[str, Any]:
    """
    Get insights about tag usage patterns and relationships.
    
    Returns tag statistics, co-occurrence patterns, and trends.
    """
    try:
        from .understanding.enhanced_analyzer import EnhancedImageAnalyzer
        
        analyzer = EnhancedImageAnalyzer()
        insights = analyzer.get_tag_insights()
        
        return {
            "success": True,
            "message": "Tag insights retrieved",
            "data": insights
        }
        
    except Exception as e:
        logger.error(f"Failed to get tag insights: {e}")
        return {"success": False, "error": str(e), "message": "Failed to get insights"}


@server.tool()
async def batch_cluster_images(
    image_paths: list[str] | None = None,
    project_name: str | None = None,
    min_cluster_size: int = 3,
    provider: str | None = None
) -> dict[str, Any]:
    """
    Analyze and cluster images by tag similarity.
    
    Parameters:
    - image_paths: Images to cluster (or use project)
    - project_name: Cluster all images in project
    - min_cluster_size: Minimum images per cluster
    - provider: Analysis provider to use
    
    Groups similar images for better organization.
    """
    try:
        from pathlib import Path
        from .understanding.enhanced_analyzer import EnhancedImageAnalyzer
        
        # Get image paths
        if project_name and not image_paths:
            # TODO: Get images from project
            return {
                "success": False,
                "message": "Project-based clustering not yet implemented"
            }
        
        if not image_paths:
            return {
                "success": False,
                "message": "No images provided"
            }
        
        analyzer = EnhancedImageAnalyzer()
        
        # Analyze and cluster
        batch_result = await analyzer.analyze_batch_with_clustering(
            [Path(p) for p in image_paths],
            provider=provider,
            auto_cluster=True,
            min_cluster_size=min_cluster_size
        )
        
        return {
            "success": True,
            "message": f"Clustered {batch_result['images_analyzed']} images",
            "data": {
                "image_clusters": batch_result["image_clusters"],
                "common_themes": batch_result["common_themes"],
                "tag_frequency": dict(batch_result["tag_frequency"]),
                "stats": {
                    "total_images": len(image_paths),
                    "analyzed": batch_result["images_analyzed"],
                    "failed": batch_result["images_failed"],
                    "clusters_found": len(batch_result["image_clusters"])
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Batch clustering failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to cluster images"}


@server.tool()
async def suggest_tags_for_project(
    project_id: str,
    existing_tags: list[str] | None = None
) -> dict[str, Any]:
    """
    Suggest additional tags for a project based on existing ones.
    
    Parameters:
    - project_id: Project identifier
    - existing_tags: Current project tags (auto-detected if not provided)
    
    Helps build comprehensive tag sets for projects.
    """
    try:
        from .understanding.enhanced_analyzer import EnhancedImageAnalyzer
        
        analyzer = EnhancedImageAnalyzer()
        
        # Get existing tags if not provided
        if not existing_tags:
            existing_tags = list(analyzer.taxonomy.get_project_tags(project_id))
        
        if not existing_tags:
            return {
                "success": True,
                "message": "No existing tags to base suggestions on",
                "data": {"suggestions": []}
            }
        
        # Get suggestions
        suggestions = analyzer.taxonomy.suggest_project_tags(project_id, existing_tags)
        
        # Get related tags for each suggestion
        detailed_suggestions = []
        for tag in suggestions:
            related = analyzer.taxonomy.hierarchy.get_related(tag, max_depth=1)
            detailed_suggestions.append({
                "tag": tag,
                "category": analyzer.taxonomy.hierarchy.nodes.get(tag, {}).category
                           if tag in analyzer.taxonomy.hierarchy.nodes else None,
                "related_tags": [t for t, score in related.items() if score > 0.5][:5]
            })
        
        return {
            "success": True,
            "message": f"Generated {len(suggestions)} tag suggestions",
            "data": {
                "current_tags": existing_tags,
                "suggestions": detailed_suggestions,
                "tag_hierarchy": {
                    tag: analyzer.taxonomy.hierarchy.get_ancestors(tag)
                    for tag in existing_tags
                    if analyzer.taxonomy.hierarchy.get_ancestors(tag)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Failed to suggest tags: {e}")
        return {"success": False, "error": str(e), "message": "Failed to suggest tags"}


@server.tool()
async def analyze_style_similarity(
    image_paths: list[str],
    extract_fingerprints: bool = True,
    find_clusters: bool = True,
    min_cluster_size: int = 3
) -> dict[str, Any]:
    """
    Analyze visual style similarity between images.
    
    Parameters:
    - image_paths: List of images to analyze
    - extract_fingerprints: Extract detailed style fingerprints
    - find_clusters: Auto-group by visual style
    - min_cluster_size: Minimum images per style group
    
    Extracts visual DNA including colors, composition, lighting.
    """
    try:
        from pathlib import Path
        from .understanding.style_clustering import StyleClusteringSystem
        
        system = StyleClusteringSystem()
        results = []
        
        # Extract style fingerprints
        for image_path in image_paths:
            try:
                fp = await system.analyze_image_style(Path(image_path))
                
                result = {
                    "path": image_path,
                    "success": True,
                    "style_tags": fp.style_tags,
                    "color_palette": {
                        "dominant_colors": [
                            f"rgb{color}" for color in fp.color_palette.dominant_colors[:3]
                        ],
                        "temperature": fp.color_palette.temperature,
                        "saturation": fp.color_palette.saturation,
                        "brightness": fp.color_palette.brightness
                    },
                    "composition": {
                        "type": fp.composition.complexity,
                        "balance": fp.composition.balance_type,
                        "rule_of_thirds": fp.composition.rule_of_thirds,
                        "negative_space": fp.composition.negative_space_ratio
                    },
                    "lighting": {
                        "mood": fp.lighting.mood_lighting,
                        "contrast": fp.lighting.contrast_level,
                        "direction": fp.lighting.light_direction,
                        "time_of_day": fp.lighting.time_of_day
                    },
                    "texture": {
                        "type": fp.texture.overall_texture,
                        "grain": fp.texture.grain_level,
                        "detail": fp.texture.detail_density
                    }
                }
                results.append(result)
                
            except Exception as e:
                logger.error(f"Failed to analyze {image_path}: {e}")
                results.append({
                    "path": image_path,
                    "success": False,
                    "error": str(e)
                })
        
        # Find style clusters
        clusters = []
        if find_clusters and len([r for r in results if r["success"]]) >= min_cluster_size:
            style_clusters = await system.cluster_by_style(
                [Path(p) for p in image_paths],
                min_cluster_size=min_cluster_size
            )
            
            for cluster in style_clusters:
                clusters.append({
                    "id": cluster.id,
                    "name": cluster.name,
                    "size": cluster.size,
                    "images": cluster.images,
                    "centroid": cluster.centroid_image,
                    "coherence": cluster.coherence_score,
                    "style_summary": cluster.style_summary
                })
        
        return {
            "success": True,
            "message": f"Analyzed {len(results)} images for style",
            "data": {
                "fingerprints": results,
                "style_clusters": clusters,
                "stats": {
                    "total_images": len(image_paths),
                    "analyzed": len([r for r in results if r["success"]]),
                    "clusters_found": len(clusters)
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Style analysis failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to analyze style"}


@server.tool()
async def find_similar_style(
    reference_image: str,
    search_in: list[str] | None = None,
    similarity_threshold: float = 0.8,
    max_results: int = 10
) -> dict[str, Any]:
    """
    Find images with similar visual style to reference.
    
    Parameters:
    - reference_image: Image to match style
    - search_in: Images to search (or use all analyzed)
    - similarity_threshold: Minimum similarity (0-1)
    - max_results: Maximum results to return
    
    "More like this" for visual style.
    """
    try:
        from pathlib import Path
        from .understanding.style_clustering import StyleClusteringSystem
        
        system = StyleClusteringSystem()
        
        # Analyze reference
        reference_fp = await system.analyze_image_style(Path(reference_image))
        
        # If search_in provided, analyze those first
        if search_in:
            for image_path in search_in:
                try:
                    await system.analyze_image_style(Path(image_path))
                except Exception as e:
                    logger.warning(f"Failed to analyze {image_path}: {e}")
        
        # Find similar
        similar = await system.find_similar_styles(
            Path(reference_image),
            similarity_threshold=similarity_threshold,
            max_results=max_results
        )
        
        # Format results
        results = []
        for image_path, score in similar:
            if image_path in system.fingerprints:
                fp = system.fingerprints[image_path]
                results.append({
                    "path": image_path,
                    "similarity_score": score,
                    "style_match": {
                        "color_match": fp.color_palette.temperature == reference_fp.color_palette.temperature,
                        "lighting_match": fp.lighting.mood_lighting == reference_fp.lighting.mood_lighting,
                        "composition_match": fp.composition.complexity == reference_fp.composition.complexity
                    },
                    "style_tags": fp.style_tags
                })
        
        return {
            "success": True,
            "message": f"Found {len(results)} similar images",
            "data": {
                "reference": {
                    "path": reference_image,
                    "style_tags": reference_fp.style_tags,
                    "dominant_color": f"rgb{reference_fp.color_palette.dominant_colors[0]}" if reference_fp.color_palette.dominant_colors else None
                },
                "similar_images": results
            }
        }
        
    except Exception as e:
        logger.error(f"Similar style search failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to find similar styles"}


@server.tool()
async def extract_style_prompts(
    image_paths: list[str] | None = None,
    cluster_id: str | None = None
) -> dict[str, Any]:
    """
    Extract style transfer hints and reusable prompts.
    
    Parameters:
    - image_paths: Images to analyze for style
    - cluster_id: Or use existing style cluster
    
    Identifies prompt fragments that recreate the style.
    """
    try:
        from pathlib import Path
        from .understanding.style_clustering import StyleClusteringSystem
        
        system = StyleClusteringSystem()
        
        # Get or create cluster
        if cluster_id and cluster_id in system.clusters:
            cluster = system.clusters[cluster_id]
        elif image_paths:
            # Create temporary cluster
            clusters = await system.cluster_by_style(
                [Path(p) for p in image_paths],
                min_cluster_size=1
            )
            cluster = clusters[0] if clusters else None
        else:
            return {
                "success": False,
                "message": "Provide either image_paths or cluster_id"
            }
        
        if not cluster:
            return {
                "success": False,
                "message": "No style cluster found"
            }
        
        # Extract hints
        hints = system.extract_style_transfer_hints(cluster)
        
        # Format results
        formatted_hints = []
        for hint in hints:
            formatted_hints.append({
                "source_image": hint.source_image,
                "prompt_fragments": hint.prompt_fragments,
                "style_elements": hint.style_elements,
                "color_palette": [f"rgb{color}" for color in hint.color_palette],
                "technical_params": hint.technical_params,
                "confidence": hint.success_rate
            })
        
        # Combine best fragments
        all_fragments = []
        for hint in hints:
            all_fragments.extend(hint.prompt_fragments)
        
        # Count frequency
        from collections import Counter
        fragment_counts = Counter(all_fragments)
        top_fragments = [f for f, _ in fragment_counts.most_common(10)]
        
        return {
            "success": True,
            "message": f"Extracted {len(hints)} style transfer hints",
            "data": {
                "style_hints": formatted_hints,
                "combined_prompt": ", ".join(top_fragments[:5]),
                "key_elements": {
                    "colors": list(set(h.style_elements.get("color_scheme", "") for h in hints)),
                    "lighting": list(set(h.style_elements.get("lighting", "") for h in hints)),
                    "composition": list(set(h.style_elements.get("composition", "") for h in hints))
                },
                "cluster_info": {
                    "name": cluster.name,
                    "coherence": cluster.coherence_score,
                    "size": cluster.size
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Style prompt extraction failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to extract prompts"}


@server.tool()
async def build_style_collections(
    min_collection_size: int = 5,
    coherence_threshold: float = 0.7
) -> dict[str, Any]:
    """
    Build automatic collections based on visual style.
    
    Parameters:
    - min_collection_size: Minimum images per collection
    - coherence_threshold: Minimum style coherence
    
    Creates collections like "Warm Dramatic", "Cool Minimalist".
    """
    try:
        from .understanding.style_clustering import StyleClusteringSystem
        
        system = StyleClusteringSystem()
        
        # Build collections
        collections = system.build_auto_collections(min_collection_size)
        
        # Format results
        formatted_collections = []
        for name, images in collections.items():
            # Calculate style compatibility
            if len(images) >= 2:
                from pathlib import Path
                compatibility = system.get_style_compatibility(
                    [Path(img) for img in images[:10]]  # Sample for speed
                )
            else:
                compatibility = 1.0
            
            if compatibility >= coherence_threshold:
                formatted_collections.append({
                    "name": name,
                    "size": len(images),
                    "images": images[:20],  # Limit for response size
                    "compatibility_score": compatibility,
                    "sample_image": images[0] if images else None
                })
        
        # Sort by size
        formatted_collections.sort(key=lambda x: x["size"], reverse=True)
        
        return {
            "success": True,
            "message": f"Created {len(formatted_collections)} style collections",
            "data": {
                "collections": formatted_collections,
                "stats": {
                    "total_collections": len(formatted_collections),
                    "total_images": sum(c["size"] for c in formatted_collections),
                    "avg_collection_size": sum(c["size"] for c in formatted_collections) / len(formatted_collections) if formatted_collections else 0
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Collection building failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to build collections"}


@server.tool()
async def check_style_compatibility(
    image_paths: list[str]
) -> dict[str, Any]:
    """
    Check if images work well together stylistically.
    
    Parameters:
    - image_paths: Images to check compatibility
    
    Useful for curating cohesive sets.
    """
    try:
        from pathlib import Path
        from .understanding.style_clustering import StyleClusteringSystem
        
        system = StyleClusteringSystem()
        
        # Analyze all images
        paths = [Path(p) for p in image_paths]
        for path in paths:
            try:
                await system.analyze_image_style(path)
            except Exception as e:
                logger.warning(f"Failed to analyze {path}: {e}")
        
        # Calculate overall compatibility
        overall_score = system.get_style_compatibility(paths)
        
        # Find style outliers
        outliers = []
        if len(paths) > 2:
            for i, path in enumerate(paths):
                # Check compatibility without this image
                other_paths = paths[:i] + paths[i+1:]
                score_without = system.get_style_compatibility(other_paths)
                
                if score_without > overall_score * 1.2:  # 20% improvement
                    outliers.append({
                        "path": str(path),
                        "impact": score_without - overall_score
                    })
        
        # Get pairwise compatibility for details
        pairwise = []
        for i in range(len(paths)):
            for j in range(i + 1, len(paths)):
                if str(paths[i]) in system.fingerprints and str(paths[j]) in system.fingerprints:
                    fp1 = system.fingerprints[str(paths[i])]
                    fp2 = system.fingerprints[str(paths[j])]
                    score = fp1.similarity_score(fp2)
                    
                    pairwise.append({
                        "image1": str(paths[i]),
                        "image2": str(paths[j]),
                        "compatibility": score
                    })
        
        # Sort pairwise by compatibility
        pairwise.sort(key=lambda x: x["compatibility"], reverse=True)
        
        return {
            "success": True,
            "message": f"Analyzed compatibility of {len(paths)} images",
            "data": {
                "overall_compatibility": overall_score,
                "compatibility_rating": (
                    "excellent" if overall_score > 0.8 else
                    "good" if overall_score > 0.6 else
                    "moderate" if overall_score > 0.4 else
                    "low"
                ),
                "outliers": outliers,
                "best_pairs": pairwise[:5],
                "worst_pairs": pairwise[-5:] if len(pairwise) > 5 else [],
                "recommendation": (
                    "This set has excellent style coherence!" if overall_score > 0.8 else
                    "This set works well together." if overall_score > 0.6 else
                    "Consider removing outliers for better coherence." if outliers else
                    "These images have diverse styles - consider grouping by style."
                )
            }
        }
        
    except Exception as e:
        logger.error(f"Compatibility check failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to check compatibility"}


@server.tool()
async def analyze_music(
    audio_path: str,
    detect_sections: bool = True,
    extract_mood: bool = True
) -> dict[str, Any]:
    """
    Analyze music track for beat detection and mood analysis.
    
    Parameters:
    - audio_path: Path to audio file (mp3, wav, m4a, etc.)
    - detect_sections: Detect musical sections (verse, chorus, etc.)
    - extract_mood: Analyze mood and energy levels
    
    Returns beat timing, BPM, mood analysis, and section markers.
    """
    try:
        # Import music analyzer directly to avoid workflow module issues
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "music_analyzer", 
            Path(__file__).parent / "workflows" / "music_analyzer.py"
        )
        music_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(music_module)
        
        analyzer = music_module.MusicAnalyzer()
        audio_file = Path(audio_path)
        
        if not audio_file.exists():
            return {
                "success": False,
                "error": "Audio file not found",
                "message": f"File not found: {audio_path}"
            }
        
        # Analyze the music
        analysis = await analyzer.analyze(
            audio_file,
            analyze_beats=True,
            analyze_sections=detect_sections,
            analyze_mood=extract_mood
        )
        
        return {
            "success": True,
            "message": f"Analyzed music: {audio_file.name}",
            "data": {
                "file": str(audio_file),
                "duration": analysis.duration,
                "beat_info": {
                    "bpm": analysis.beat_info.tempo,
                    "beat_count": len(analysis.beat_info.beats),
                    "time_signature": analysis.beat_info.time_signature,
                    "downbeats": analysis.beat_info.downbeats[:10],  # First 10
                    "beat_times": analysis.beat_info.beats[:20]  # First 20
                },
                "mood": {
                    "energy": analysis.mood.energy,
                    "valence": analysis.mood.valence,
                    "intensity": analysis.mood.intensity,
                    "category": analysis.mood.get_mood_category(),
                    "tags": analysis.mood.mood_tags
                },
                "sections": [
                    {
                        "name": s.name,
                        "start": s.start_time,
                        "end": s.end_time,
                        "duration": s.duration
                    }
                    for s in analysis.sections
                ] if detect_sections else []
            }
        }
        
    except Exception as e:
        logger.error(f"Music analysis failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to analyze music"}


@server.tool()
async def sync_images_to_music(
    audio_path: str,
    image_paths: list[str],
    sync_mode: str = "beat",
    transition_duration: float = 0.5
) -> dict[str, Any]:
    """
    Create a synchronized timeline matching images to music.
    
    Parameters:
    - audio_path: Path to audio file
    - image_paths: List of image paths to sync
    - sync_mode: "beat" (change on beat), "measure" (change on downbeat), or "section"
    - transition_duration: Transition time between images (seconds)
    
    Returns timeline with image timings synced to music.
    """
    try:
        # Import music analyzer
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "music_analyzer", 
            Path(__file__).parent / "workflows" / "music_analyzer.py"
        )
        music_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(music_module)
        
        analyzer = music_module.MusicAnalyzer()
        audio_file = Path(audio_path)
        
        # Analyze music
        analysis = await analyzer.analyze(audio_file, analyze_beats=True)
        
        # Get sync points based on mode
        if sync_mode == "beat":
            sync_points = analysis.beat_info.beats
        elif sync_mode == "measure":
            sync_points = analysis.beat_info.downbeats
        elif sync_mode == "section":
            sync_points = [s.start_time for s in analysis.sections]
        else:
            sync_points = analysis.beat_info.beats
        
        # Create timeline
        timeline = []
        image_duration = analysis.duration / len(image_paths)
        
        for i, image_path in enumerate(image_paths):
            # Find nearest sync point
            target_time = i * image_duration
            nearest_sync = min(sync_points, key=lambda x: abs(x - target_time))
            
            timeline.append({
                "image": image_path,
                "start_time": nearest_sync,
                "duration": image_duration,
                "transition": {
                    "type": "crossfade",
                    "duration": transition_duration
                },
                "beat_aligned": True
            })
        
        # Adjust durations to avoid gaps
        for i in range(len(timeline) - 1):
            timeline[i]["duration"] = timeline[i + 1]["start_time"] - timeline[i]["start_time"]
        timeline[-1]["duration"] = analysis.duration - timeline[-1]["start_time"]
        
        return {
            "success": True,
            "message": f"Created timeline with {len(timeline)} images synced to music",
            "data": {
                "audio": str(audio_file),
                "total_duration": analysis.duration,
                "bpm": analysis.beat_info.tempo,
                "sync_mode": sync_mode,
                "timeline": timeline,
                "export_hints": {
                    "davinci_resolve": "Import as XML with beat markers",
                    "capcut": "Use JSON timeline for precise sync"
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Music sync failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to sync images to music"}


@server.tool()
async def suggest_cuts_for_mood(
    audio_path: str,
    target_mood: str = "auto",
    cut_frequency: str = "medium"
) -> dict[str, Any]:
    """
    Suggest cut points based on music mood and energy.
    
    Parameters:
    - audio_path: Path to audio file
    - target_mood: Desired mood ("energetic", "calm", "dramatic", "auto")
    - cut_frequency: "fast" (many cuts), "medium", or "slow" (few cuts)
    
    Returns suggested cut points with mood-based recommendations.
    """
    try:
        # Import music analyzer
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "music_analyzer", 
            Path(__file__).parent / "workflows" / "music_analyzer.py"
        )
        music_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(music_module)
        
        analyzer = music_module.MusicAnalyzer()
        audio_file = Path(audio_path)
        
        # Analyze music
        analysis = await analyzer.analyze(
            audio_file, 
            analyze_beats=True,
            analyze_sections=True,
            analyze_mood=True
        )
        
        # Determine cut frequency multiplier
        freq_multiplier = {
            "fast": 2.0,
            "medium": 1.0,
            "slow": 0.5
        }.get(cut_frequency, 1.0)
        
        # Get base cut points
        cut_points = []
        
        # Add section transitions
        for section in analysis.sections:
            cut_points.append({
                "time": section.start_time,
                "type": "section_change",
                "strength": 1.0,
                "reason": f"New section: {section.name}"
            })
        
        # Add beat-based cuts based on mood
        if target_mood == "auto":
            target_mood = analysis.mood.get_mood_category()
        
        if target_mood in ["energetic", "upbeat", "intense"]:
            # More frequent cuts on strong beats
            for i, (beat, strength) in enumerate(zip(
                analysis.beat_info.beats, 
                analysis.beat_info.beat_strength
            )):
                if strength > 0.7 and i % int(4 / freq_multiplier) == 0:
                    cut_points.append({
                        "time": beat,
                        "type": "strong_beat",
                        "strength": strength,
                        "reason": "Strong beat for energy"
                    })
        else:
            # Fewer cuts, focus on downbeats
            for i, downbeat in enumerate(analysis.beat_info.downbeats):
                if i % int(8 / freq_multiplier) == 0:
                    cut_points.append({
                        "time": downbeat,
                        "type": "downbeat",
                        "strength": 0.8,
                        "reason": "Measure boundary for flow"
                    })
        
        # Sort by time
        cut_points.sort(key=lambda x: x["time"])
        
        # Generate recommendations
        recommendations = []
        if analysis.mood.energy > 0.7:
            recommendations.append("High energy detected - consider fast cuts and dynamic transitions")
        if analysis.mood.valence < 0.4:
            recommendations.append("Melancholic mood - use longer shots and subtle transitions")
        if len(analysis.sections) > 5:
            recommendations.append("Multiple sections detected - emphasize section changes")
        
        return {
            "success": True,
            "message": f"Generated {len(cut_points)} cut suggestions for {target_mood} mood",
            "data": {
                "audio": str(audio_file),
                "duration": analysis.duration,
                "detected_mood": analysis.mood.get_mood_category(),
                "target_mood": target_mood,
                "cut_count": len(cut_points),
                "cuts_per_minute": len(cut_points) / (analysis.duration / 60),
                "cut_points": cut_points[:50],  # Limit to first 50
                "recommendations": recommendations,
                "mood_analysis": {
                    "energy": analysis.mood.energy,
                    "valence": analysis.mood.valence,
                    "intensity": analysis.mood.intensity
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Cut suggestion failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to suggest cuts"}


@server.tool()
async def export_timeline(
    timeline_data: dict,
    output_formats: list[str] = ["edl", "xml", "capcut"],
    generate_proxies: bool = False,
    proxy_resolution: list[int] | None = None
) -> dict[str, Any]:
    """
    Export a timeline to various video editor formats.
    
    Parameters:
    - timeline_data: Timeline dict with clips, duration, etc.
    - output_formats: List of formats - "edl", "xml", "capcut"
    - generate_proxies: Create low-res proxy files for editing
    - proxy_resolution: [width, height] for proxies (default [1280, 720])
    
    Returns paths to exported files and proxy mappings.
    """
    try:
        from .workflows.video_export import (
            Timeline, TimelineClip, VideoExportManager
        )
        
        # Parse timeline data
        timeline = Timeline(
            name=timeline_data.get("name", "Untitled"),
            duration=timeline_data.get("duration", 60.0),
            frame_rate=timeline_data.get("frame_rate", 30.0),
            resolution=tuple(timeline_data.get("resolution", [1920, 1080]))
        )
        
        # Add clips
        for clip_data in timeline_data.get("clips", []):
            clip = TimelineClip(
                asset_path=Path(clip_data["path"]),
                start_time=clip_data["start_time"],
                duration=clip_data["duration"],
                in_point=clip_data.get("in_point", 0.0),
                out_point=clip_data.get("out_point"),
                transition_in=clip_data.get("transition_in"),
                transition_in_duration=clip_data.get("transition_in_duration", 0.5),
                beat_aligned=clip_data.get("beat_aligned", False),
                sync_point=clip_data.get("sync_point")
            )
            timeline.clips.append(clip)
        
        # Add markers
        timeline.markers = timeline_data.get("markers", [])
        timeline.metadata = timeline_data.get("metadata", {})
        
        # Export
        export_manager = VideoExportManager()
        output_dir = Path.home() / "Documents" / "AliceExports" / timeline.name
        
        results = await export_manager.export_timeline(
            timeline,
            output_dir,
            formats=output_formats,
            generate_proxies=generate_proxies,
            proxy_resolution=tuple(proxy_resolution) if proxy_resolution else (1280, 720)
        )
        
        return {
            "success": results["success"],
            "message": f"Exported timeline to {len(results['exports'])} formats",
            "data": {
                "exports": {
                    fmt: str(path) for fmt, path in results["exports"].items()
                },
                "proxies": {
                    src: str(proxy) for src, proxy in results["proxies"].items()
                },
                "output_directory": str(output_dir)
            }
        }
        
    except Exception as e:
        logger.error(f"Timeline export failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to export timeline"}


@server.tool()
async def create_video_timeline(
    image_paths: list[str],
    audio_path: str | None = None,
    duration_per_image: float = 2.0,
    transition_type: str = "crossfade",
    transition_duration: float = 0.5,
    sync_to_beat: bool = False,
    export_formats: list[str] = ["xml", "capcut"]
) -> dict[str, Any]:
    """
    Create a video timeline from images and optionally sync to music.
    
    Parameters:
    - image_paths: List of image paths in order
    - audio_path: Optional audio file for music sync
    - duration_per_image: Seconds per image (if not syncing to beat)
    - transition_type: Type of transition between images
    - transition_duration: Transition length in seconds
    - sync_to_beat: If True and audio provided, sync cuts to beats
    - export_formats: Formats to export ("edl", "xml", "capcut")
    
    Creates and exports a complete timeline ready for editing.
    """
    try:
        from .workflows.video_export import (
            Timeline, TimelineClip, VideoExportManager
        )
        
        # Calculate total duration
        if audio_path and Path(audio_path).exists():
            # Get audio duration
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "music_analyzer", 
                Path(__file__).parent / "workflows" / "music_analyzer.py"
            )
            music_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(music_module)
            
            analyzer = music_module.MusicAnalyzer()
            analysis = await analyzer.analyze(Path(audio_path), analyze_beats=sync_to_beat)
            total_duration = analysis.duration
            
            # Get sync points if requested
            sync_points = []
            if sync_to_beat:
                sync_points = analysis.beat_info.beats
        else:
            total_duration = len(image_paths) * duration_per_image
            sync_points = []
        
        # Create timeline
        timeline = Timeline(
            name=f"Alice_Timeline_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            duration=total_duration,
            frame_rate=30.0,
            resolution=(1920, 1080)
        )
        
        # Add audio track
        if audio_path:
            timeline.audio_tracks.append({
                "path": audio_path,
                "start_time": 0,
                "duration": total_duration,
                "volume": 1.0
            })
        
        # Calculate clip timings
        if sync_to_beat and sync_points:
            # Distribute images across beat points
            images_per_beat = max(1, len(sync_points) // len(image_paths))
            current_time = 0.0
            
            for i, image_path in enumerate(image_paths):
                # Find appropriate beat point
                beat_index = min(i * images_per_beat, len(sync_points) - 1)
                start_time = sync_points[beat_index] if beat_index < len(sync_points) else current_time
                
                # Calculate duration to next beat or end
                if i < len(image_paths) - 1 and beat_index + images_per_beat < len(sync_points):
                    end_time = sync_points[beat_index + images_per_beat]
                else:
                    end_time = total_duration if i == len(image_paths) - 1 else start_time + duration_per_image
                
                duration = end_time - start_time
                
                clip = TimelineClip(
                    asset_path=Path(image_path),
                    start_time=start_time,
                    duration=duration,
                    transition_in=transition_type if i > 0 else None,
                    transition_in_duration=transition_duration if i > 0 else 0,
                    beat_aligned=True,
                    sync_point=sync_points[beat_index] if beat_index < len(sync_points) else None
                )
                timeline.clips.append(clip)
                current_time = end_time
                
                # Add beat marker
                if clip.sync_point:
                    timeline.markers.append({
                        "time": clip.sync_point,
                        "name": f"Beat {beat_index + 1}",
                        "type": "beat"
                    })
        else:
            # Simple sequential timeline
            current_time = 0.0
            for i, image_path in enumerate(image_paths):
                clip = TimelineClip(
                    asset_path=Path(image_path),
                    start_time=current_time,
                    duration=duration_per_image,
                    transition_in=transition_type if i > 0 else None,
                    transition_in_duration=transition_duration if i > 0 else 0
                )
                timeline.clips.append(clip)
                current_time += duration_per_image - (transition_duration if i < len(image_paths) - 1 else 0)
        
        # Add mood metadata if we analyzed audio
        if audio_path and sync_to_beat:
            timeline.metadata["mood"] = analysis.mood.get_mood_category()
            timeline.metadata["bpm"] = analysis.beat_info.tempo
        
        # Export timeline
        export_manager = VideoExportManager()
        output_dir = Path.home() / "Documents" / "AliceExports" / timeline.name
        
        results = await export_manager.export_timeline(
            timeline,
            output_dir,
            formats=export_formats,
            generate_proxies=True
        )
        
        # Build timeline data for response
        timeline_data = {
            "name": timeline.name,
            "duration": timeline.duration,
            "frame_rate": timeline.frame_rate,
            "resolution": list(timeline.resolution),
            "clips": [
                {
                    "path": str(clip.asset_path),
                    "start_time": clip.start_time,
                    "duration": clip.duration,
                    "transition_in": clip.transition_in,
                    "beat_aligned": clip.beat_aligned
                }
                for clip in timeline.clips
            ],
            "markers": timeline.markers,
            "metadata": timeline.metadata
        }
        
        return {
            "success": True,
            "message": f"Created timeline with {len(timeline.clips)} clips",
            "data": {
                "timeline": timeline_data,
                "exports": {
                    fmt: str(path) for fmt, path in results["exports"].items()
                },
                "output_directory": str(output_dir),
                "sync_info": {
                    "beat_synced": sync_to_beat and bool(sync_points),
                    "beat_count": len(sync_points) if sync_points else 0,
                    "bpm": timeline.metadata.get("bpm"),
                    "mood": timeline.metadata.get("mood")
                }
            }
        }
        
    except Exception as e:
        logger.error(f"Timeline creation failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to create timeline"}


@server.tool()
async def generate_veo3_video(
    prompt: str,
    duration: int = 5,
    aspect_ratio: str = "16:9",
    enable_audio: bool = False,
    enable_speech: bool = False,
    output_path: str | None = None
) -> dict[str, Any]:
    """
    Generate a video using Google Veo 3 via fal.ai.
    
    Veo 3 features:
    - State-of-the-art video quality with realistic physics
    - Native audio generation (ambient sounds, music, effects)
    - Speech capabilities with accurate lip sync
    - 5-8 second video generation
    
    Parameters:
    - prompt: Text description of the video to generate
    - duration: Video length in seconds (5-8)
    - aspect_ratio: Video aspect ratio (16:9, 9:16, 1:1)
    - enable_audio: Generate native audio with the video
    - enable_speech: Enable speech generation (requires enable_audio=True)
    - output_path: Optional output directory path
    
    Note: Costs $0.50/second without audio, $0.75/second with audio.
    """
    try:
        from .providers.fal_provider import FalProvider
        from .providers.types import GenerationRequest, GenerationType
        from pathlib import Path
        
        # Validate parameters
        if duration < 5 or duration > 8:
            return {
                "success": False,
                "message": "Duration must be between 5 and 8 seconds for Veo 3"
            }
            
        if enable_speech and not enable_audio:
            enable_audio = True  # Speech requires audio
            
        # Set output path
        if output_path:
            output_dir = Path(output_path)
        else:
            output_dir = Path.home() / "Documents" / "AliceGenerated" / "veo3"
            
        # Initialize provider
        provider = FalProvider()
        await provider.initialize()
        
        # Create generation request
        request = GenerationRequest(
            prompt=prompt,
            model="veo-3",
            generation_type=GenerationType.VIDEO,
            output_path=output_dir,
            parameters={
                "duration": duration,
                "aspect_ratio": aspect_ratio,
                "enable_audio": enable_audio
            }
        )
        
        # Estimate cost
        cost_per_second = 0.75 if enable_audio else 0.50
        estimated_cost = cost_per_second * duration
        
        # Generate video
        result = await provider.generate(request)
        
        # Clean up
        await provider.cleanup()
        
        if result.success:
            return {
                "success": True,
                "message": f"Generated Veo 3 video successfully",
                "data": {
                    "file_path": str(result.file_path),
                    "cost": result.cost or estimated_cost,
                    "duration": duration,
                    "has_audio": enable_audio,
                    "has_speech": enable_speech,
                    "aspect_ratio": aspect_ratio,
                    "model": "veo-3",
                    "provider": "fal.ai",
                    "features": [
                        "state-of-the-art quality",
                        "realistic physics",
                        "native audio" if enable_audio else "no audio",
                        "speech with lip sync" if enable_speech else "no speech"
                    ]
                }
            }
        else:
            return {
                "success": False,
                "message": f"Video generation failed: {result.error}",
                "error": result.error
            }
            
    except Exception as e:
        logger.error(f"Veo 3 video generation failed: {e}")
        return {"success": False, "error": str(e), "message": "Failed to generate Veo 3 video"}


@server.tool()
async def prompt_find_effective(
    category: str | None = None,
    style: str | None = None,
    min_success_rate: float = 0.7
) -> dict[str, Any]:
    """
    Find effective prompts for a specific use case.
    
    Parameters:
    - category: Type of generation (image_generation, video_generation, etc.)
    - style: Visual style (cyberpunk, photorealistic, etc.)
    - min_success_rate: Minimum success rate threshold (0-1)
    
    Returns prompts with high success rates and usage recommendations.
    """
    return await prompt_tools.find_effective_prompts(
        category=category,
        style=style,
        min_success_rate=min_success_rate
    )


@server.tool()
async def prompt_search(
    query: str,
    project: str | None = None,
    limit: int = 20
) -> dict[str, Any]:
    """
    Search for prompts containing specific terms or concepts.
    
    Parameters:
    - query: Search query for finding prompts
    - project: Filter by project name
    - limit: Maximum results to return
    
    Returns prompts matching the search criteria.
    """
    return await prompt_tools.search_prompts(
        query=query,
        project=project,
        limit=limit
    )


@server.tool()
async def prompt_create(
    text: str,
    category: str,
    providers: list[str],
    project: str | None = None,
    tags: list[str] | None = None,
    style: str | None = None,
    description: str | None = None
) -> dict[str, Any]:
    """
    Create a new prompt with metadata for tracking.
    
    Parameters:
    - text: The prompt text
    - category: Category (image_generation, video_generation, etc.)
    - providers: List of provider names (midjourney, flux, etc.)
    - project: Project name for organization
    - tags: List of descriptive tags
    - style: Visual style (cyberpunk, photorealistic, etc.)
    - description: What this prompt is good for
    
    Creates and saves prompt to project if specified.
    """
    return await prompt_tools.create_prompt(
        text=text,
        category=category,
        providers=providers,
        project=project,
        tags=tags,
        style=style,
        description=description
    )


@server.tool()
async def prompt_track_usage(
    prompt_id: str,
    provider: str,
    success: bool,
    cost: float | None = None,
    notes: str | None = None
) -> dict[str, Any]:
    """
    Track usage of a prompt for effectiveness analysis.
    
    Parameters:
    - prompt_id: Prompt ID (supports partial matching)
    - provider: Provider used for generation
    - success: Whether generation was successful
    - cost: Cost of generation in dollars
    - notes: Additional notes about the result
    
    Updates prompt statistics and success rates.
    """
    return await prompt_tools.track_prompt_usage(
        prompt_id=prompt_id,
        provider=provider,
        success=success,
        cost=cost,
        notes=notes
    )


@server.tool()
async def prompt_get_project(
    project_name: str
) -> dict[str, Any]:
    """
    Get all prompts for a project with insights.
    
    Parameters:
    - project_name: Name of the project
    
    Returns prompts and statistics for the project.
    """
    return await prompt_tools.get_project_prompts(project_name)


@server.tool()
async def prompt_suggest_improvements(
    prompt_id: str
) -> dict[str, Any]:
    """
    Get improvement suggestions for a prompt.
    
    Parameters:
    - prompt_id: Prompt ID (supports partial matching)
    
    Returns suggestions based on performance analysis.
    """
    return await prompt_tools.suggest_improvements(prompt_id)


@server.tool()
async def prompt_render_template(
    template_name: str,
    variables: dict[str, str],
    save_as_prompt: bool = False,
    project: str | None = None
) -> dict[str, Any]:
    """
    Render a prompt template with variables.
    
    Parameters:
    - template_name: Name of the template (landscape, portrait, etc.)
    - variables: Variable values for the template
    - save_as_prompt: Whether to save the rendered result
    - project: Project to save to if saving
    
    Returns rendered prompt text.
    """
    return await prompt_tools.render_template(
        template_name=template_name,
        variables=variables,
        save_as_prompt=save_as_prompt,
        project=project
    )


# Analytics Tools

@server.tool()
async def start_analytics_session() -> dict[str, Any]:
    """
    Start a new analytics session to track performance.
    
    Begins tracking workflow metrics, export patterns, and user behavior.
    All subsequent operations will be tracked until session ends.
    
    Returns session ID and start time.
    """
    return await analytics_start_session()


@server.tool()
async def end_analytics_session() -> dict[str, Any]:
    """
    End the current analytics session and get summary.
    
    Stops tracking and provides session metrics including:
    - Workflows completed/failed
    - Total exports and API calls
    - Popular features used
    - Common errors encountered
    
    Returns complete session summary.
    """
    return await analytics_end_session()


@server.tool()
async def track_workflow_event(
    workflow_id: str,
    event_type: str,
    data: dict[str, Any]
) -> dict[str, Any]:
    """
    Track a workflow event for performance analysis.
    
    Parameters:
    - workflow_id: Unique workflow identifier
    - event_type: Type of event (start, update, complete, fail)
    - data: Event data (workflow_type, metadata, updates, etc.)
    
    Used internally to track workflow performance.
    """
    return await analytics_track_workflow(workflow_id, event_type, data)


@server.tool()
async def track_export_event(
    export_id: str,
    timeline_id: str,
    format: str,
    platform: str | None = None,
    metrics: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Track an export operation for analytics.
    
    Parameters:
    - export_id: Unique export identifier
    - timeline_id: Associated timeline ID
    - format: Export format (edl, xml, json, capcut)
    - platform: Target platform if applicable
    - metrics: Export metrics (duration, success, file_size, etc.)
    
    Records detailed export metrics for analysis.
    """
    return await analytics_track_export(
        export_id=export_id,
        timeline_id=timeline_id,
        format=format,
        platform=platform,
        metrics=metrics
    )


@server.tool()
async def get_performance_insights(
    time_range_days: int = 30,
    workflow_type: str | None = None
) -> dict[str, Any]:
    """
    Get performance insights and improvement opportunities.
    
    Parameters:
    - time_range_days: Days to analyze (default 30)
    - workflow_type: Filter by specific workflow type
    
    Returns:
    - Success rates and average durations
    - Common errors and their frequencies
    - Resource usage statistics
    - Actionable improvement suggestions
    """
    return await analytics_get_insights(
        time_range_days=time_range_days,
        workflow_type=workflow_type
    )


@server.tool()
async def get_export_analytics(
    format: str | None = None,
    platform: str | None = None,
    time_range_days: int = 30
) -> dict[str, Any]:
    """
    Get detailed export analytics and patterns.
    
    Parameters:
    - format: Filter by export format (edl, xml, json, capcut)
    - platform: Filter by target platform
    - time_range_days: Days to analyze
    
    Returns:
    - Export statistics by format and platform
    - Workflow patterns (exports per timeline, iterations)
    - Quality trends over time
    - User satisfaction metrics
    """
    return await analytics_get_export_stats(
        format=format,
        platform=platform,
        time_range_days=time_range_days
    )


@server.tool()
async def get_improvement_suggestions(
    max_suggestions: int = 10
) -> dict[str, Any]:
    """
    Get prioritized improvement suggestions based on usage.
    
    Parameters:
    - max_suggestions: Maximum suggestions to return
    
    Returns actionable improvements categorized by:
    - Workflow efficiency
    - Performance optimization
    - Quality enhancement
    - Error reduction
    
    Each suggestion includes priority, impact, and implementation steps.
    """
    return await analytics_get_improvements(max_suggestions=max_suggestions)


@server.tool()
async def track_user_action(
    action: str,
    metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Track a user action for behavior analysis.
    
    Parameters:
    - action: Action type (adjustment, preview, redo, etc.)
    - metadata: Additional context about the action
    
    Helps identify patterns in user behavior for optimization.
    """
    return await analytics_track_action(action=action, metadata=metadata)


# Style Memory & Learning Tools

@server.tool()
async def track_style_preference(
    preference_type: str,
    value: str,
    project: str | None = None,
    tags: list[str] | None = None,
    context: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Track a style preference choice.
    
    Parameters:
    - preference_type: Type of preference (color_palette, composition, lighting, texture, mood, subject, technique, transition, pacing, effect)
    - value: The chosen value
    - project: Optional project context
    - tags: Optional descriptive tags
    - context: Optional additional context
    
    Tracks preferences to learn your personal style over time.
    """
    return await memory_track_preference(
        preference_type=preference_type,
        value=value,
        project=project,
        tags=tags,
        context=context
    )


@server.tool()
async def get_style_recommendations(
    context: dict[str, Any] | None = None,
    types: list[str] | None = None,
    limit: int = 5
) -> list[dict[str, Any]]:
    """
    Get personalized style recommendations.
    
    Parameters:
    - context: Optional context (project, time, etc.)
    - types: Recommendation types (preset, variation, exploration, trending)
    - limit: Maximum recommendations
    
    Returns recommendations based on your style history and patterns.
    """
    return await memory_get_recommendations(
        context=context,
        types=types,
        limit=limit
    )


@server.tool()
async def analyze_style_patterns(
    time_range_days: int = 30
) -> dict[str, Any]:
    """
    Analyze style patterns and generate insights.
    
    Parameters:
    - time_range_days: Days to analyze
    
    Returns:
    - Detected patterns (co-occurrence, temporal, project-specific)
    - Actionable insights with priorities
    - Style evolution trends
    """
    return await memory_analyze_patterns(time_range_days=time_range_days)


@server.tool()
async def start_style_workflow(
    workflow_type: str,
    project: str | None = None
) -> dict[str, Any]:
    """
    Start tracking a style workflow.
    
    Parameters:
    - workflow_type: Type (image_generation, video_creation, timeline_editing, export, organization, search)
    - project: Optional project context
    
    Begins tracking choices and outcomes for learning.
    """
    return await memory_start_workflow(
        workflow_type=workflow_type,
        project=project
    )


@server.tool()
async def end_style_workflow(
    workflow_id: str,
    successful: bool,
    quality_score: float | None = None,
    user_rating: int | None = None,
    notes: str | None = None
) -> dict[str, Any]:
    """
    End a style workflow and get summary.
    
    Parameters:
    - workflow_id: Workflow to end
    - successful: Whether workflow was successful
    - quality_score: Optional quality score (0-1)
    - user_rating: Optional user rating (1-5)
    - notes: Optional notes
    
    Completes tracking and updates learning models.
    """
    return await memory_end_workflow(
        workflow_id=workflow_id,
        successful=successful,
        quality_score=quality_score,
        user_rating=user_rating,
        notes=notes
    )


@server.tool()
async def get_style_evolution(
    days: int = 30,
    preference_type: str | None = None
) -> list[dict[str, Any]]:
    """
    Get style evolution over time.
    
    Parameters:
    - days: Number of days to analyze
    - preference_type: Optional specific type to track
    
    Shows how your style preferences have changed.
    """
    return await memory_get_evolution(
        days=days,
        preference_type=preference_type
    )


@server.tool()
async def suggest_next_style_action(
    current_preferences: dict[str, str]
) -> dict[str, Any]:
    """
    Get next best action suggestion based on current preferences.
    
    Parameters:
    - current_preferences: Current preference selections (type->value mapping)
    
    Suggests what to add or change for better results.
    """
    return await memory_suggest_action(current_preferences=current_preferences)


@server.tool()
async def export_style_profile() -> dict[str, Any]:
    """
    Export complete style profile.
    
    Returns your full style history, preferences, and patterns.
    Useful for backup or sharing across devices.
    """
    return await memory_export_profile()


@server.tool()
async def import_style_profile(
    profile_data: dict[str, Any]
) -> dict[str, Any]:
    """
    Import a style profile.
    
    Parameters:
    - profile_data: Profile data to import
    
    Restores a previously exported style profile.
    """
    return await memory_import_profile(profile_data=profile_data)


# Template Workflow Tools

@server.tool()
async def create_story_arc_video(
    images: list[str],
    structure: str = "three_act",
    duration: float = 60.0,
    narrative_tags: dict[str, list[str]] | None = None,
    emotion_curve: str = "standard",
    music_file: str | None = None,
    voiceover_markers: bool = False,
    export_formats: list[str] | None = None
) -> dict[str, Any]:
    """
    Create a narrative-driven video with story structure.
    
    Parameters:
    - images: List of image paths
    - structure: Story structure (three_act, five_act, heros_journey, kishoten, circular)
    - duration: Target duration in seconds
    - narrative_tags: Story elements per image
    - emotion_curve: Emotional progression (standard, intense, gentle)
    - music_file: Optional music for pacing
    - voiceover_markers: Add voiceover timing markers
    - export_formats: Export formats (edl, xml, json)
    
    Creates videos following classic narrative structures with appropriate pacing.
    """
    return await create_story_arc_video(
        images=images,
        structure=structure,
        duration=duration,
        narrative_tags=narrative_tags,
        emotion_curve=emotion_curve,
        music_file=music_file,
        voiceover_markers=voiceover_markers,
        export_formats=export_formats
    )


@server.tool()
async def create_documentary_video(
    images: list[str],
    duration: float = 120.0,
    narrative_tags: dict[str, list[str]] | None = None,
    music_file: str | None = None,
    voiceover_markers: bool = True,
    export_formats: list[str] | None = None
) -> dict[str, Any]:
    """
    Create a documentary-style video.
    
    Parameters:
    - images: List of image paths
    - duration: Target duration in seconds
    - narrative_tags: Evidence/testimony tags
    - music_file: Optional background music
    - voiceover_markers: Add narration markers (default True)
    - export_formats: Export formats
    
    Optimized for information delivery and evidence presentation.
    """
    return await create_documentary_video(
        images=images,
        duration=duration,
        narrative_tags=narrative_tags,
        music_file=music_file,
        voiceover_markers=voiceover_markers,
        export_formats=export_formats
    )


@server.tool()
async def create_social_media_video(
    platform: str,
    images: list[str],
    music_file: str | None = None,
    caption: str | None = None,
    hashtags: list[str] | None = None,
    style: str = "trending",
    duration: float | None = None,
    auto_optimize: bool = True
) -> dict[str, Any]:
    """
    Create a social media optimized video.
    
    Parameters:
    - platform: Target platform (instagram_reel, tiktok, youtube_shorts, etc.)
    - images: List of image paths
    - music_file: Optional music track
    - caption: Post caption/description
    - hashtags: List of hashtags
    - style: Content style (trending, educational, entertaining)
    - duration: Optional duration (uses platform optimal if not set)
    - auto_optimize: Automatically optimize for engagement
    
    Platform-specific optimizations for maximum engagement.
    """
    return await create_social_media_video(
        platform=platform,
        images=images,
        music_file=music_file,
        caption=caption,
        hashtags=hashtags,
        style=style,
        duration=duration,
        auto_optimize=auto_optimize
    )


@server.tool()
async def create_instagram_reel(
    images: list[str],
    music_file: str,
    caption: str | None = None,
    hashtags: list[str] | None = None,
    effects: list[str] | None = None,
    duration: float = 15.0
) -> dict[str, Any]:
    """
    Create an Instagram Reel with optimizations.
    
    Parameters:
    - images: List of image paths
    - music_file: Music track (required for Reels)
    - caption: Reel caption
    - hashtags: Hashtags for discovery
    - effects: Instagram effects to apply
    - duration: Reel duration (max 90 seconds)
    
    Includes Instagram-specific features and trending elements.
    """
    return await create_instagram_reel(
        images=images,
        music_file=music_file,
        caption=caption,
        hashtags=hashtags,
        effects=effects,
        duration=duration
    )


@server.tool()
async def create_tiktok_video(
    images: list[str],
    music_file: str | None = None,
    caption: str | None = None,
    hashtags: list[str] | None = None,
    challenges: list[str] | None = None,
    duet_ready: bool = False,
    duration: float = 30.0
) -> dict[str, Any]:
    """
    Create a TikTok video with trend integration.
    
    Parameters:
    - images: List of image paths
    - music_file: Optional trending sound
    - caption: Video caption
    - hashtags: Trending hashtags
    - challenges: Hashtag challenges to join
    - duet_ready: Prepare for duet format
    - duration: Video duration (max 180 seconds)
    
    Optimized for TikTok algorithm with trend integration.
    """
    return await create_tiktok_video(
        images=images,
        music_file=music_file,
        caption=caption,
        hashtags=hashtags,
        challenges=challenges,
        duet_ready=duet_ready,
        duration=duration
    )


@server.tool()
async def get_platform_specifications(
    platform: str | None = None
) -> dict[str, Any]:
    """
    Get specifications for social media platforms.
    
    Parameters:
    - platform: Specific platform or None for all
    
    Returns platform specs including:
    - Aspect ratio and resolution
    - Duration limits and optimal length
    - Safe zones for UI elements
    - Supported features
    """
    return await get_platform_specifications(platform=platform)


@server.tool()
async def suggest_story_structure(
    images: list[str],
    theme: str | None = None
) -> dict[str, Any]:
    """
    Suggest appropriate story structure based on content.
    
    Parameters:
    - images: List of image paths
    - theme: Optional theme hint
    
    Analyzes content and suggests narrative structures with reasoning.
    """
    return await suggest_story_structure(images=images, theme=theme)


# Variation Tools

@server.tool()
async def generate_content_variations(
    base_content_id: str,
    original_prompt: str,
    provider: str = "fal",
    model: str | None = None,
    variation_types: list[str] | None = None,
    strategy: str = "performance_based",
    max_variations: int = 5,
    output_dir: str | None = None
) -> dict[str, Any]:
    """
    Generate smart variations of successful content.
    
    Creates multiple variations using different styles, moods, colors, 
    compositions, and other parameters based on past performance.
    
    Parameters:
    - base_content_id: ID of the base content to vary
    - original_prompt: Original generation prompt
    - provider: Provider to use (default: fal)
    - model: Optional model override
    - variation_types: Types to vary (style, mood, color, composition, etc.)
    - strategy: Selection strategy (performance_based, systematic, exploration)
    - max_variations: Maximum number of variations to generate
    - output_dir: Output directory for variations
    
    Returns generation results with costs and paths.
    """
    return await generate_content_variations(
        base_content_id=base_content_id,
        original_prompt=original_prompt,
        provider=provider,
        model=model,
        variation_types=variation_types,
        strategy=strategy,
        max_variations=max_variations,
        output_dir=output_dir
    )


@server.tool()
async def track_variation_performance(
    content_id: str,
    metrics: dict[str, Any]
) -> dict[str, Any]:
    """
    Track performance metrics for content variations.
    
    Record views, engagement, play duration, and other metrics
    to learn what variations work best.
    
    Parameters:
    - content_id: Content or variation ID
    - metrics: Performance metrics (views, likes, shares, play_duration, etc.)
    
    Returns updated performance summary.
    """
    return await track_variation_performance(
        content_id=content_id,
        metrics=metrics
    )


@server.tool()
async def create_variation_group(
    base_content_id: str,
    variation_ids: list[str],
    tags: list[str] | None = None,
    metadata: dict[str, Any] | None = None
) -> dict[str, Any]:
    """
    Create a group of related content variations.
    
    Groups variations together for comparative analysis and
    A/B testing insights.
    
    Parameters:
    - base_content_id: ID of the base content
    - variation_ids: IDs of all variations
    - tags: Optional tags for categorization
    - metadata: Optional metadata
    
    Returns group info with performance comparison.
    """
    return await create_variation_group(
        base_content_id=base_content_id,
        variation_ids=variation_ids,
        tags=tags,
        metadata=metadata
    )


@server.tool()
async def get_variation_insights(
    time_window_days: int | None = None
) -> dict[str, Any]:
    """
    Get insights about variation performance.
    
    Analyzes variation performance to identify successful patterns,
    trending variations, and improvement opportunities.
    
    Parameters:
    - time_window_days: Optional time window for analysis
    
    Returns insights including trends and averages.
    """
    return await get_variation_insights(time_window_days=time_window_days)


@server.tool()
async def find_top_variations(
    metric: str = "engagement_rate",
    limit: int = 10,
    min_views: int = 100
) -> dict[str, Any]:
    """
    Find top performing content variations.
    
    Identifies variations with best performance across chosen metrics.
    
    Parameters:
    - metric: Metric to sort by (engagement_rate, views, play_duration)
    - limit: Maximum results
    - min_views: Minimum views threshold
    
    Returns ranked list of top variations.
    """
    return await find_top_variations(
        metric=metric,
        limit=limit,
        min_views=min_views
    )


@server.tool()
async def get_variation_recommendations(
    content_type: str = "image",
    limit: int = 5
) -> dict[str, Any]:
    """
    Get recommended variations based on past success.
    
    Suggests variation types and strategies that have worked well
    for similar content.
    
    Parameters:
    - content_type: Type of content (image, video)
    - limit: Maximum recommendations
    
    Returns recommended variation templates.
    """
    return await get_variation_recommendations(
        content_type=content_type,
        limit=limit
    )


@server.tool()
async def analyze_variation_success(
    variation_id: str,
    base_content_id: str,
    variation_type: str,
    performance_metrics: dict[str, float]
) -> dict[str, Any]:
    """
    Analyze and record variation success.
    
    Updates learning system with variation performance to improve
    future recommendations.
    
    Parameters:
    - variation_id: Variation ID
    - base_content_id: Base content ID
    - variation_type: Type of variation applied
    - performance_metrics: Performance data
    
    Returns success analysis with updated recommendations.
    """
    return await analyze_variation_success(
        variation_id=variation_id,
        base_content_id=base_content_id,
        variation_type=variation_type,
        performance_metrics=performance_metrics
    )


@server.tool()
async def export_variation_analytics(
    output_dir: str | None = None
) -> dict[str, Any]:
    """
    Export variation analytics data.
    
    Exports comprehensive analytics about variation performance
    for external analysis or reporting.
    
    Parameters:
    - output_dir: Optional output directory
    
    Returns export path and summary statistics.
    """
    return await export_variation_analytics(output_dir=output_dir)


# Composition Analysis Tools

@server.tool()
async def analyze_timeline_flow(
    timeline_data: dict[str, Any],
    target_mood: str | None = None,
    target_energy: str | None = None
) -> dict[str, Any]:
    """
    Analyze timeline flow and detect pacing/rhythm issues.
    
    Examines clip sequences for flow problems like jarring transitions,
    energy drops, inconsistent pacing, and narrative breaks.
    
    Parameters:
    - timeline_data: Timeline with duration and clips array
    - target_mood: Target mood (upbeat, dramatic, calm)
    - target_energy: Energy curve (rising_action, steady, climactic)
    
    Returns flow health score, issues, and improvement suggestions.
    """
    return await analyze_timeline_flow(
        timeline_data=timeline_data,
        target_mood=target_mood,
        target_energy=target_energy
    )


@server.tool()
async def analyze_image_composition(
    image_path: str
) -> dict[str, Any]:
    """
    Analyze visual composition of an image.
    
    Evaluates rule of thirds, golden ratio, symmetry, balance,
    leading lines, depth, and focus clarity.
    
    Parameters:
    - image_path: Path to image file
    
    Returns composition metrics, type, and improvement suggestions.
    """
    return await analyze_image_composition(image_path=image_path)


@server.tool()
async def analyze_timeline_compositions(
    timeline_data: dict[str, Any],
    sample_rate: float = 0.2
) -> dict[str, Any]:
    """
    Analyze composition quality across timeline clips.
    
    Samples clips to assess overall composition consistency
    and quality distribution.
    
    Parameters:
    - timeline_data: Timeline with clips
    - sample_rate: Fraction of clips to analyze (0-1)
    
    Returns average metrics and composition distribution.
    """
    return await analyze_timeline_compositions(
        timeline_data=timeline_data,
        sample_rate=sample_rate
    )


@server.tool()
async def optimize_timeline(
    timeline_data: dict[str, Any],
    strategy: str = "balanced",
    preserve_clips: list[int] | None = None,
    target_duration: float | None = None
) -> dict[str, Any]:
    """
    Optimize timeline based on flow analysis.
    
    Applies suggested improvements while respecting constraints
    and optimization strategy.
    
    Parameters:
    - timeline_data: Timeline to optimize
    - strategy: Optimization approach (minimal, balanced, aggressive)
    - preserve_clips: Clip indices that must not be modified
    - target_duration: Optional target duration in seconds
    
    Returns optimized timeline with change report.
    """
    return await optimize_timeline(
        timeline_data=timeline_data,
        strategy=strategy,
        preserve_clips=preserve_clips,
        target_duration=target_duration
    )


@server.tool()
async def suggest_clip_order(
    clip_paths: list[str],
    target_flow: str = "rising_action"
) -> dict[str, Any]:
    """
    Suggest optimal clip order based on composition analysis.
    
    Analyzes visual energy and composition to create desired
    flow patterns.
    
    Parameters:
    - clip_paths: List of image/video paths
    - target_flow: Desired energy pattern (rising_action, climactic, etc.)
    
    Returns suggested order with energy curve and reasoning.
    """
    return await suggest_clip_order(
        clip_paths=clip_paths,
        target_flow=target_flow
    )


@server.tool()
async def detect_composition_patterns(
    project_name: str | None = None,
    limit: int = 100
) -> dict[str, Any]:
    """
    Detect composition patterns in image collection.
    
    Analyzes composition trends, quality distribution, and
    common issues across a project or collection.
    
    Parameters:
    - project_name: Optional project filter
    - limit: Maximum images to analyze
    
    Returns patterns, quality metrics, and recommendations.
    """
    return await detect_composition_patterns(
        project_name=project_name,
        limit=limit
    )
    
    @server.tool()
    async def find_duplicates_advanced(
        directory: str,
        similarity_threshold: float = 0.9,
        include_similar: bool = True,
        recursive: bool = True,
        extensions: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Find duplicate and similar images using perceptual hashing.
        
        Goes beyond exact duplicates to find visually similar images using:
        - Multiple perceptual hash algorithms (average, perceptual, difference, wavelet)
        - Color histogram analysis
        - Visual feature extraction (edges, texture, brightness)
        
        Parameters:
        - directory: Directory to scan
        - similarity_threshold: Similarity score threshold (0.8-1.0)
        - include_similar: Find similar images, not just exact duplicates
        - recursive: Scan subdirectories
        - extensions: Image extensions to scan (default: common formats)
        
        Returns duplicate groups with similarity scores and space savings.
        """
        from .deduplication import DuplicateFinder
        
        try:
            scan_dir = Path(directory).expanduser().resolve()
            if not scan_dir.exists():
                return {
                    "success": False,
                    "error": "Directory not found",
                    "message": f"Directory does not exist: {directory}"
                }
            
            # Create finder
            finder = DuplicateFinder(similarity_threshold=similarity_threshold)
            
            # Scan directory
            exact_count, similar_count = finder.scan_directory(
                scan_dir,
                recursive=recursive,
                extensions=set(extensions) if extensions else None
            )
            
            # Get report
            report = finder.get_duplicate_report()
            
            # Add summary
            report['summary'] = {
                'exact_duplicates_found': exact_count,
                'similar_images_found': similar_count if include_similar else 0,
                'total_duplicates': exact_count + (similar_count if include_similar else 0),
                'potential_space_savings_mb': report['potential_savings'] / 1_000_000
            }
            
            return {
                "success": True,
                "message": f"Found {exact_count} exact duplicates and {similar_count} similar images",
                "data": report
            }
            
        except Exception as e:
            logger.error(f"Duplicate detection failed: {e}")
            return {"success": False, "error": str(e), "message": "Failed to find duplicates"}
    
    @server.tool()
    async def remove_duplicates(
        duplicate_report: dict[str, Any],
        strategy: str = "safe",
        backup_dir: str | None = None,
        dry_run: bool = True
    ) -> dict[str, Any]:
        """
        Remove duplicate images based on scan results.
        
        Parameters:
        - duplicate_report: Report from find_duplicates_advanced
        - strategy: Removal strategy (safe=exact only, aggressive=include similar)
        - backup_dir: Optional backup directory (moves instead of deleting)
        - dry_run: If True, only preview what would be removed
        
        Returns removal statistics.
        """
        from .deduplication import DuplicateFinder
        
        try:
            # Recreate finder from report
            finder = DuplicateFinder()
            
            # Restore state from report
            # This is a simplified version - in production, save/load full state
            for group in duplicate_report.get('exact_duplicates', {}).get('groups', []):
                master = Path(group['master'])
                duplicates = [Path(p) for p in group['duplicates']]
                file_hash = group.get('hash', 'unknown')
                finder.exact_duplicates[file_hash] = [master] + duplicates
            
            # Configure removal
            remove_similar = strategy == "aggressive"
            backup_path = Path(backup_dir) if backup_dir else None
            
            # Remove duplicates
            stats = finder.remove_duplicates(
                dry_run=dry_run,
                backup_dir=backup_path,
                remove_similar=remove_similar
            )
            
            return {
                "success": True,
                "message": f"{'Would remove' if dry_run else 'Removed'} {stats['exact_removed']} duplicates",
                "data": {
                    "stats": stats,
                    "space_freed_mb": stats['space_freed'] / 1_000_000,
                    "dry_run": dry_run,
                    "backup_location": str(backup_path) if backup_path else None
                }
            }
            
        except Exception as e:
            logger.error(f"Duplicate removal failed: {e}")
            return {"success": False, "error": str(e), "message": "Failed to remove duplicates"}
    
    @server.tool()
    async def build_similarity_index(
        directories: list[str],
        output_path: str | None = None,
        index_type: str = "IVF"
    ) -> dict[str, Any]:
        """
        Build fast similarity search index for image collection.
        
        Creates a FAISS index for lightning-fast similarity searches across
        thousands of images. Useful for finding similar shots, variations,
        or inspiration from your collection.
        
        Parameters:
        - directories: List of directories to index
        - output_path: Where to save the index (default: ~/.alice/similarity_index)
        - index_type: Index type (Flat=exact, IVF=fast, HNSW=balanced)
        
        Returns index statistics and save location.
        """
        from .deduplication import SimilarityIndex
        
        try:
            # Collect all images
            image_paths = []
            for directory in directories:
                scan_dir = Path(directory).expanduser().resolve()
                if scan_dir.exists():
                    for ext in ['.jpg', '.jpeg', '.png', '.webp']:
                        image_paths.extend(scan_dir.rglob(f"*{ext}"))
                        image_paths.extend(scan_dir.rglob(f"*{ext.upper()}"))
            
            if not image_paths:
                return {
                    "success": False,
                    "message": "No images found in specified directories"
                }
            
            # Create index
            index = SimilarityIndex(index_type=index_type)
            
            # Build index
            cache_dir = Path.home() / ".alice" / "cache" / "similarity"
            indexed_count = index.build_index(image_paths, cache_dir=cache_dir)
            
            # Save index
            if output_path:
                index_path = Path(output_path)
            else:
                index_path = Path.home() / ".alice" / "similarity_index"
            
            index_path.parent.mkdir(parents=True, exist_ok=True)
            index.save_index(index_path)
            
            return {
                "success": True,
                "message": f"Built similarity index for {indexed_count} images",
                "data": {
                    "total_images": len(image_paths),
                    "indexed_images": indexed_count,
                    "index_type": index_type,
                    "index_location": str(index_path),
                    "cache_location": str(cache_dir)
                }
            }
            
        except Exception as e:
            logger.error(f"Index building failed: {e}")
            return {"success": False, "error": str(e), "message": "Failed to build similarity index"}
    
    @server.tool()
    async def search_similar_advanced(
        query_image: str,
        index_path: str | None = None,
        k: int = 20,
        min_similarity: float = 0.7
    ) -> dict[str, Any]:
        """
        Find visually similar images using similarity index.
        
        Ultra-fast similarity search across your entire collection using
        the pre-built index. Great for finding variations, similar compositions,
        or images with matching visual styles.
        
        Parameters:
        - query_image: Path to query image
        - index_path: Path to similarity index (uses default if not specified)
        - k: Number of results to return
        - min_similarity: Minimum similarity score (0-1)
        
        Returns similar images with similarity scores.
        """
        from .deduplication import SimilarityIndex
        
        try:
            query_path = Path(query_image).expanduser().resolve()
            if not query_path.exists():
                return {
                    "success": False,
                    "error": "Query image not found",
                    "message": f"Image does not exist: {query_image}"
                }
            
            # Load index
            if index_path:
                idx_path = Path(index_path)
            else:
                idx_path = Path.home() / ".alice" / "similarity_index"
            
            if not idx_path.with_suffix('.faiss').exists():
                return {
                    "success": False,
                    "error": "Index not found",
                    "message": "Please build similarity index first with build_similarity_index"
                }
            
            # Create and load index
            index = SimilarityIndex()
            index.load_index(idx_path)
            
            # Search
            results = index.search(query_path, k=k, include_self=False)
            
            # Filter by similarity
            filtered_results = [
                {
                    "path": str(r.path),
                    "similarity": round(r.similarity, 3),
                    "distance": round(r.distance, 3)
                }
                for r in results
                if r.similarity >= min_similarity
            ]
            
            return {
                "success": True,
                "message": f"Found {len(filtered_results)} similar images",
                "data": {
                    "query_image": str(query_path),
                    "results": filtered_results,
                    "total_searched": index.index.ntotal if index.index else 0
                }
            }
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return {"success": False, "error": str(e), "message": "Failed to search similar images"}
    
    @server.tool()
    async def find_image_clusters(
        index_path: str | None = None,
        min_cluster_size: int = 3,
        max_distance: float = 0.5
    ) -> dict[str, Any]:
        """
        Automatically find clusters of similar images.
        
        Discovers groups of visually similar images in your collection.
        Useful for finding duplicate sessions, similar shots, or
        organizing by visual style.
        
        Parameters:
        - index_path: Path to similarity index
        - min_cluster_size: Minimum images per cluster
        - max_distance: Maximum distance within cluster (lower = more similar)
        
        Returns clusters of similar images.
        """
        from .deduplication import SimilarityIndex
        
        try:
            # Load index
            if index_path:
                idx_path = Path(index_path)
            else:
                idx_path = Path.home() / ".alice" / "similarity_index"
            
            if not idx_path.with_suffix('.faiss').exists():
                return {
                    "success": False,
                    "error": "Index not found",
                    "message": "Please build similarity index first"
                }
            
            # Create and load index
            index = SimilarityIndex()
            index.load_index(idx_path)
            
            # Find clusters
            clusters = index.find_clusters(
                min_cluster_size=min_cluster_size,
                max_distance=max_distance
            )
            
            # Format results
            formatted_clusters = []
            for i, cluster in enumerate(clusters):
                formatted_clusters.append({
                    "cluster_id": i + 1,
                    "size": len(cluster),
                    "images": cluster[:20]  # Limit for response size
                })
            
            return {
                "success": True,
                "message": f"Found {len(clusters)} image clusters",
                "data": {
                    "clusters": formatted_clusters,
                    "total_clusters": len(clusters),
                    "total_images_clustered": sum(len(c) for c in clusters),
                    "settings": {
                        "min_cluster_size": min_cluster_size,
                        "max_distance": max_distance
                    }
                }
            }
            
        except Exception as e:
            logger.error(f"Cluster finding failed: {e}")
            return {"success": False, "error": str(e), "message": "Failed to find clusters"}
    
    @server.tool()
    async def list_plugins() -> dict[str, Any]:
        """
        List all available plugins.
        
        Returns information about installed and available plugins including:
        - Name, version, type, and description
        - Initialization status
        - Dependencies
        
        Plugins extend Alice's functionality with custom providers, effects,
        analyzers, exporters, and workflows.
        """
        from .plugins.registry import get_registry
        
        try:
            registry = get_registry()
            plugin_info = registry.get_plugin_info()
            
            # Group by type
            by_type = {}
            for info in plugin_info:
                plugin_type = info["type"]
                if plugin_type not in by_type:
                    by_type[plugin_type] = []
                by_type[plugin_type].append(info)
            
            return {
                "success": True,
                "message": f"Found {len(plugin_info)} plugins",
                "data": {
                    "plugins": plugin_info,
                    "by_type": by_type,
                    "plugin_paths": [str(p) for p in registry.loader.plugin_paths]
                }
            }
        except Exception as e:
            logger.error(f"Failed to list plugins: {e}")
            return {"success": False, "error": str(e), "message": "Failed to list plugins"}
    
    @server.tool()
    async def load_plugin(
        plugin_path: str,
        initialize: bool = True
    ) -> dict[str, Any]:
        """
        Load a plugin from file or module.
        
        Parameters:
        - plugin_path: Path to plugin file or module name
        - initialize: Whether to initialize the plugin immediately
        
        Supports loading from:
        - Python files (e.g., /path/to/my_plugin.py)
        - Installed packages (e.g., alice-plugin-example)
        """
        from .plugins.registry import get_registry
        
        try:
            registry = get_registry()
            path = Path(plugin_path)
            
            # Determine if it's a file or module
            if path.exists() and path.suffix == ".py":
                # Load from file
                plugin = registry.loader.load_plugin_from_file(path)
            else:
                # Try as module name
                plugin = registry.loader.load_plugin_from_module(plugin_path)
            
            if plugin is None:
                return {
                    "success": False,
                    "message": f"Could not load plugin from: {plugin_path}"
                }
            
            # Register the plugin
            success = registry.register_plugin(plugin, initialize=initialize)
            
            return {
                "success": success,
                "message": f"Loaded plugin: {plugin.metadata.name} v{plugin.metadata.version}",
                "data": {
                    "name": plugin.metadata.name,
                    "version": plugin.metadata.version,
                    "type": plugin.metadata.type.value,
                    "description": plugin.metadata.description,
                    "initialized": success and initialize
                }
            }
        except Exception as e:
            logger.error(f"Failed to load plugin: {e}")
            return {"success": False, "error": str(e), "message": "Failed to load plugin"}
    
    @server.tool()
    async def use_plugin_provider(
        plugin_name: str,
        prompt: str,
        model: str | None = None,
        parameters: dict[str, Any] | None = None,
        output_path: str | None = None
    ) -> dict[str, Any]:
        """
        Generate content using a plugin provider.
        
        Parameters:
        - plugin_name: Name of the plugin provider
        - prompt: Generation prompt
        - model: Model to use (plugin-specific)
        - parameters: Additional parameters
        - output_path: Where to save the result
        
        Plugin providers can be custom AI services, local models, or
        specialized generators not included in the core system.
        """
        from .plugins.registry import get_plugin
        from .plugins.base import PluginType
        from .plugins.provider_adapter import PluginProviderAdapter
        from .providers.types import GenerationRequest, GenerationType
        
        try:
            # Get the plugin
            plugin = get_plugin(plugin_name)
            if plugin is None:
                return {
                    "success": False,
                    "message": f"Plugin not found or not initialized: {plugin_name}"
                }
            
            # Verify it's a provider plugin
            if plugin.metadata.type != PluginType.PROVIDER:
                return {
                    "success": False,
                    "message": f"Plugin {plugin_name} is not a provider plugin"
                }
            
            # Create adapter
            adapter = PluginProviderAdapter(plugin)
            
            # Create generation request
            request = GenerationRequest(
                prompt=prompt,
                model=model or "default",
                generation_type=GenerationType.IMAGE,  # TODO: make configurable
                output_path=Path(output_path) if output_path else None,
                parameters=parameters
            )
            
            # Generate
            result = await adapter.generate(request)
            
            if result.success:
                return {
                    "success": True,
                    "message": f"Generated using {plugin_name}",
                    "data": {
                        "file_path": str(result.file_path),
                        "cost": result.cost,
                        "metadata": result.metadata
                    }
                }
            else:
                return {
                    "success": False,
                    "message": f"Generation failed: {result.error}",
                    "error": result.error
                }
                
        except Exception as e:
            logger.error(f"Plugin provider error: {e}")
            return {"success": False, "error": str(e), "message": "Failed to use plugin provider"}
    
    @server.tool()
    async def apply_plugin_effect(
        plugin_name: str,
        input_path: str,
        output_path: str | None = None,
        parameters: dict[str, Any] | None = None
    ) -> dict[str, Any]:
        """
        Apply a plugin effect to an image or video.
        
        Parameters:
        - plugin_name: Name of the effect plugin
        - input_path: Path to input file
        - output_path: Where to save result (auto-generated if not provided)
        - parameters: Effect parameters (plugin-specific)
        
        Effect plugins can provide filters, transformations, enhancements,
        and other post-processing capabilities.
        """
        from .plugins.registry import get_plugin
        from .plugins.base import PluginType
        
        try:
            # Get the plugin
            plugin = get_plugin(plugin_name)
            if plugin is None:
                return {
                    "success": False,
                    "message": f"Plugin not found or not initialized: {plugin_name}"
                }
            
            # Verify it's an effect plugin
            if plugin.metadata.type != PluginType.EFFECT:
                return {
                    "success": False,
                    "message": f"Plugin {plugin_name} is not an effect plugin"
                }
            
            # Set up paths
            input_file = Path(input_path).expanduser().resolve()
            if not input_file.exists():
                return {
                    "success": False,
                    "message": f"Input file not found: {input_path}"
                }
            
            if output_path:
                output_file = Path(output_path).expanduser().resolve()
            else:
                # Auto-generate output path
                output_file = input_file.parent / f"{input_file.stem}_{plugin_name}{input_file.suffix}"
            
            # Apply effect
            result_path = await plugin.apply(input_file, output_file, parameters or {})
            
            return {
                "success": True,
                "message": f"Applied {plugin_name} effect",
                "data": {
                    "input_path": str(input_file),
                    "output_path": str(result_path),
                    "plugin": plugin_name,
                    "parameters": parameters
                }
            }
            
        except Exception as e:
            logger.error(f"Plugin effect error: {e}")
            return {"success": False, "error": str(e), "message": "Failed to apply plugin effect"}
    
    @server.tool()
    async def create_plugin_template(
        plugin_type: str,
        plugin_name: str,
        output_dir: str | None = None
    ) -> dict[str, Any]:
        """
        Create a plugin template to start developing your own plugin.
        
        Parameters:
        - plugin_type: Type of plugin (provider, effect, analyzer, exporter, workflow)
        - plugin_name: Name for your plugin
        - output_dir: Where to create the plugin (default: ~/.alice/plugins)
        
        Creates a fully functional plugin template with:
        - Proper structure and metadata
        - Example implementation
        - Configuration schema
        - Documentation
        """
        from .plugins.base import PluginType
        
        try:
            # Validate plugin type
            try:
                plugin_type_enum = PluginType(plugin_type)
            except ValueError:
                return {
                    "success": False,
                    "message": f"Invalid plugin type: {plugin_type}. Valid types: {[t.value for t in PluginType]}"
                }
            
            # Set output directory
            if output_dir:
                output_path = Path(output_dir).expanduser().resolve()
            else:
                output_path = Path.home() / ".alice" / "plugins"
            
            output_path.mkdir(parents=True, exist_ok=True)
            
            # Create plugin file
            plugin_file = output_path / f"{plugin_name}.py"
            
            # Generate template based on type
            template = _generate_plugin_template(plugin_type_enum, plugin_name)
            
            # Write template
            plugin_file.write_text(template)
            
            # Create example config
            config_file = output_path / f"{plugin_name}_config.yaml"
            config_template = _generate_plugin_config_template(plugin_type_enum, plugin_name)
            config_file.write_text(config_template)
            
            return {
                "success": True,
                "message": f"Created {plugin_type} plugin template",
                "data": {
                    "plugin_file": str(plugin_file),
                    "config_file": str(config_file),
                    "next_steps": [
                        f"1. Edit {plugin_file} to implement your plugin",
                        f"2. Configure settings in {config_file}",
                        f"3. Load with: load_plugin('{plugin_file}')",
                        "4. Test your plugin functionality"
                    ]
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to create plugin template: {e}")
            return {"success": False, "error": str(e), "message": "Failed to create plugin template"}
    
    @server.tool()
    async def start_timeline_preview(
        timeline_data: dict[str, Any],
        port: int = 8001
    ) -> dict[str, Any]:
        """
        Start web-based timeline preview server for interactive editing.
        
        Opens a browser-based interface for timeline editing with:
        - Visual timeline with drag-and-drop clip reordering
        - Real-time video playback preview with frame caching
        - Transition visualization
        - Beat marker display
        - Keyboard shortcuts (Space, arrows, Home/End)
        - Export to EDL/XML/CapCut formats
        
        Parameters:
        - timeline_data: Timeline dict with clips, duration, etc.
        - port: Server port (default 8001)
        
        Returns preview URL and session ID to open in browser.
        """
        from .interface.timeline_preview import TimelinePreviewServer
        import httpx
        import asyncio
        import threading
        import uvicorn
        
        # Create server instance
        server_instance = TimelinePreviewServer()
        
        # Start server in background thread
        def run_server():
            config = uvicorn.Config(
                app=server_instance.app,
                host="0.0.0.0",
                port=port,
                log_level="info"
            )
            uvicorn.run(server_instance.app, host="0.0.0.0", port=port)
        
        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()
        
        # Wait a moment for server to start
        await asyncio.sleep(1)
        
        # Create preview session
        async with httpx.AsyncClient(base_url=f"http://localhost:{port}") as client:
            try:
                response = await client.post("/session/create", json=timeline_data)
                
                if response.status_code == 200:
                    session_data = response.json()
                    session_id = session_data["session_id"]
                    
                    return {
                        "status": "success",
                        "preview_url": f"http://localhost:{port}/?session={session_id}",
                        "session_id": session_id,
                        "message": "Preview server started. Open the URL in your browser.",
                        "features": [
                            "Video playback with frame caching",
                            "Drag-and-drop clip reordering", 
                            "Keyboard shortcuts (Space to play/pause)",
                            "Export to EDL/XML/CapCut",
                            "Real-time WebSocket updates",
                            "Undo/redo support"
                        ]
                    }
                else:
                    return {
                        "status": "error",
                        "message": f"Failed to create preview session: {response.status_code}"
                    }
            except Exception as e:
                return {
                    "status": "error",
                    "message": f"Failed to start preview server: {str(e)}"
                }


def _generate_plugin_template(plugin_type: PluginType, plugin_name: str) -> str:
    """Generate plugin template code."""
    if plugin_type == PluginType.PROVIDER:
        return f'''"""Custom provider plugin for {plugin_name}."""

import logging
from typing import Any, Dict, List

from alicemultiverse.plugins.base import ProviderPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class {plugin_name.title().replace("_", "")}Plugin(ProviderPlugin):
    """Custom provider plugin implementation."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="{plugin_name}",
            version="1.0.0",
            type=PluginType.PROVIDER,
            description="Custom provider for generating content",
            author="Your Name",
            dependencies=[],
            config_schema={{
                "api_key": {{"type": "string", "required": True}},
                "endpoint": {{"type": "string", "default": "https://api.example.com"}}
            }}
        )
    
    async def initialize(self) -> bool:
        """Initialize the provider."""
        if not self.config.get("api_key"):
            logger.error("API key required")
            return False
        
        self.api_key = self.config["api_key"]
        self.endpoint = self.config.get("endpoint", "https://api.example.com")
        self._initialized = True
        return True
    
    async def cleanup(self):
        """Clean up resources."""
        self._initialized = False
    
    async def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content."""
        # TODO: Implement your generation logic
        return {{
            "success": True,
            "file_path": "/path/to/generated/file",
            "cost": 0.01,
            "metadata": {{"model": request.get("model", "default")}}
        }}
    
    def get_supported_models(self) -> List[str]:
        """Return supported models."""
        return ["default", "pro"]
    
    def estimate_cost(self, request: Dict[str, Any]) -> float:
        """Estimate generation cost."""
        return 0.01
'''
    
    elif plugin_type == PluginType.EFFECT:
        return f'''"""Custom effect plugin for {plugin_name}."""

import logging
from pathlib import Path
from typing import Any, Dict, List

from alicemultiverse.plugins.base import EffectPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class {plugin_name.title().replace("_", "")}Plugin(EffectPlugin):
    """Custom effect plugin implementation."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="{plugin_name}",
            version="1.0.0",
            type=PluginType.EFFECT,
            description="Custom effect for processing images",
            author="Your Name",
            dependencies=["pillow"],
            config_schema={{
                "intensity": {{"type": "number", "default": 1.0, "minimum": 0, "maximum": 2}}
            }}
        )
    
    async def initialize(self) -> bool:
        """Initialize the effect."""
        self.intensity = self.config.get("intensity", 1.0)
        self._initialized = True
        return True
    
    async def cleanup(self):
        """Clean up resources."""
        self._initialized = False
    
    async def apply(self, input_path: Path, output_path: Path, parameters: Dict[str, Any]) -> Path:
        """Apply effect to image."""
        from PIL import Image
        
        # Load image
        image = Image.open(input_path)
        
        # TODO: Apply your effect
        # Example: adjust brightness
        intensity = parameters.get("intensity", self.intensity)
        
        # Save result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        image.save(output_path)
        
        return output_path
    
    def get_supported_formats(self) -> List[str]:
        """Return supported formats."""
        return [".jpg", ".jpeg", ".png", ".webp"]
'''
    
    else:
        # Generic template for other types
        return f'''"""Custom {plugin_type.value} plugin for {plugin_name}."""

import logging
from typing import Any, Dict

from alicemultiverse.plugins.base import Plugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class {plugin_name.title().replace("_", "")}Plugin(Plugin):
    """Custom {plugin_type.value} plugin implementation."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="{plugin_name}",
            version="1.0.0",
            type=PluginType.{plugin_type.name},
            description="Custom {plugin_type.value} plugin",
            author="Your Name",
            dependencies=[],
            config_schema={{}}
        )
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self._initialized = True
        return True
    
    async def cleanup(self):
        """Clean up resources."""
        self._initialized = False
    
    # TODO: Implement {plugin_type.value}-specific methods
'''


def _generate_plugin_config_template(plugin_type: PluginType, plugin_name: str) -> str:
    """Generate plugin configuration template."""
    if plugin_type == PluginType.PROVIDER:
        return f'''# Configuration for {plugin_name} plugin

# API credentials
api_key: "your-api-key-here"

# API endpoint (optional)
endpoint: "https://api.example.com"

# Supported generation types
supported_types:
  - image
  - video

# Default parameters
defaults:
  model: "default"
  quality: "high"
'''
    elif plugin_type == PluginType.EFFECT:
        return f'''# Configuration for {plugin_name} plugin

# Effect parameters
intensity: 1.0
quality: "high"

# Processing options
preserve_metadata: true
auto_backup: false
'''
    else:
        return f'''# Configuration for {plugin_name} plugin

# Add your configuration options here
enabled: true
'''


# Mobile Companion Tools

@server.tool()
async def start_mobile_server(
    host: str = "0.0.0.0",
    port: int = 8080,
    generate_token: bool = True
) -> dict[str, Any]:
    """Start the mobile companion server for remote timeline control."""
    from alicemultiverse.mobile.server import MobileServer
    from alicemultiverse.mobile.token_manager import TokenManager
    import socket
    import threading
    
    # Get local IP
    def get_local_ip():
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        try:
            s.connect(("8.8.8.8", 80))
            ip = s.getsockname()[0]
        except:
            ip = "localhost"
        finally:
            s.close()
        return ip
    
    local_ip = get_local_ip()
    
    # Generate token if requested
    token = None
    if generate_token:
        manager = TokenManager()
        token = manager.generate_token("mcp-session", expires_hours=24)
    
    # Start server in background thread
    server = MobileServer(host=host, port=port)
    
    def run_server():
        import asyncio
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        server.run()
    
    thread = threading.Thread(target=run_server, daemon=True)
    thread.start()
    
    result = {
        "status": "started",
        "local_url": f"http://localhost:{port}",
        "mobile_url": f"http://{local_ip}:{port}",
        "local_ip": local_ip
    }
    
    if token:
        result["access_token"] = token
        result["token_message"] = "Save this token - you'll need it to connect from your mobile device"
    
    return result


@server.tool()
async def generate_mobile_token(
    name: str = "mobile-access",
    expires_hours: int = 24
) -> dict[str, Any]:
    """Generate an access token for mobile companion app."""
    from alicemultiverse.mobile.token_manager import TokenManager
    
    manager = TokenManager()
    token = manager.generate_token(name, expires_hours)
    
    return {
        "token": token,
        "name": name,
        "expires_hours": expires_hours,
        "message": f"Token expires in {expires_hours} hours. Use this to authenticate from your mobile device."
    }


@server.tool()
async def list_mobile_tokens() -> dict[str, Any]:
    """List all active mobile access tokens."""
    from alicemultiverse.mobile.token_manager import TokenManager
    
    manager = TokenManager()
    tokens = manager.list_tokens()
    
    return {
        "tokens": tokens,
        "count": len(tokens)
    }


@server.tool()
async def add_timeline_to_mobile(
    timeline_name: str,
    clip_paths: list[str],
    clip_durations: list[float] | None = None
) -> dict[str, Any]:
    """Add a timeline to the mobile companion server."""
    from alicemultiverse.interface.timeline_preview import Timeline, TimelineClip
    from pathlib import Path
    import uuid
    
    # Create timeline
    timeline = Timeline(name=timeline_name)
    
    # Default duration if not provided
    if not clip_durations:
        clip_durations = [3.0] * len(clip_paths)
    
    # Add clips
    for i, (path, duration) in enumerate(zip(clip_paths, clip_durations)):
        clip = TimelineClip(
            id=str(uuid.uuid4()),
            file_path=Path(path),
            duration=duration
        )
        timeline.add_clip(clip)
    
    # Add to server if running
    # Note: In a real implementation, we'd need to track the server instance
    timeline_id = str(uuid.uuid4())
    
    return {
        "timeline_id": timeline_id,
        "timeline_name": timeline_name,
        "clip_count": len(clip_paths),
        "total_duration": timeline.duration,
        "message": "Timeline created. Start mobile server to make it available."
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
    logger.info("  - quick_mark: Fast mark assets as favorites/hero/maybe")
    logger.info("  - list_quick_marks: View recent quick selections")
    logger.info("  - export_quick_marks: Export marked assets to folder")
    logger.info("  - analyze_images_optimized: Analyze with similarity detection")
    logger.info("  - estimate_analysis_cost: Estimate costs with optimization")
    logger.info("  - check_ollama_status: Check local vision model availability")
    logger.info("  - analyze_with_local: Analyze using free local models")
    logger.info("  - pull_ollama_model: Download vision models for local use")
    logger.info("  - analyze_with_hierarchy: Analyze with tag relationships")
    logger.info("  - create_tag_mood_board: Create mood boards from tags")
    logger.info("  - get_tag_insights: View tag patterns and trends")
    logger.info("  - batch_cluster_images: Auto-group similar images")
    logger.info("  - suggest_tags_for_project: Get smart tag suggestions")
    logger.info("  - analyze_style_similarity: Extract visual style fingerprints")
    logger.info("  - find_similar_style: Find visually similar images")
    logger.info("  - extract_style_prompts: Get reusable style prompts")
    logger.info("  - build_style_collections: Auto-create style collections")
    logger.info("  - check_style_compatibility: Check visual coherence")
    logger.info("  - analyze_music: Analyze audio for beats, BPM, and mood")
    logger.info("  - sync_images_to_music: Create beat-synced image timelines")
    logger.info("  - suggest_cuts_for_mood: Get mood-based edit suggestions")
    logger.info("  - export_timeline: Export to DaVinci/CapCut formats")
    logger.info("  - create_video_timeline: Build complete video from images")
    logger.info("  - prompt_find_effective: Find high-performing prompts")
    logger.info("  - prompt_search: Search prompts by terms or concepts")
    logger.info("  - prompt_create: Create and track new prompts")
    logger.info("  - prompt_track_usage: Record prompt usage results")
    logger.info("  - prompt_get_project: Get project prompts with insights")
    logger.info("  - prompt_suggest_improvements: Get prompt optimization tips")
    logger.info("  - prompt_render_template: Use prompt templates")
    logger.info("  - start_analytics_session: Begin tracking performance metrics")
    logger.info("  - end_analytics_session: Stop tracking and get session summary")
    logger.info("  - get_performance_insights: View performance stats and improvements")
    logger.info("  - get_export_analytics: Analyze export patterns and quality")
    logger.info("  - get_improvement_suggestions: Get actionable optimization tips")
    logger.info("  - generate_content_variations: Generate smart variations of successful content")
    logger.info("  - track_variation_performance: Track performance metrics for variations")
    logger.info("  - create_variation_group: Create groups of related variations")
    logger.info("  - get_variation_insights: Get insights about variation performance")
    logger.info("  - find_top_variations: Find top performing content variations")
    logger.info("  - get_variation_recommendations: Get recommended variations")
    logger.info("  - analyze_variation_success: Analyze and record variation success")
    logger.info("  - export_variation_analytics: Export variation analytics data")
    logger.info("  - analyze_timeline_flow: Analyze timeline pacing and rhythm issues")
    logger.info("  - analyze_image_composition: Analyze visual composition metrics")
    logger.info("  - analyze_timeline_compositions: Check composition across clips")
    logger.info("  - optimize_timeline: Auto-optimize timeline based on flow analysis")
    logger.info("  - suggest_clip_order: Get optimal clip ordering suggestions")
    logger.info("  - detect_composition_patterns: Find composition trends in collection")
    logger.info("  - start_timeline_preview: Launch interactive web timeline editor with video preview")
    logger.info("  - find_duplicates_advanced: Find exact and similar images with perceptual hashing")
    logger.info("  - remove_duplicates: Remove duplicate images with backup option")
    logger.info("  - build_similarity_index: Build fast similarity search index")
    logger.info("  - search_similar_advanced: Ultra-fast similarity search")
    logger.info("  - find_image_clusters: Auto-discover clusters of similar images")
    logger.info("  - list_plugins: List all available plugins")
    logger.info("  - load_plugin: Load a plugin from file or module")
    logger.info("  - use_plugin_provider: Generate content with plugin provider")
    logger.info("  - apply_plugin_effect: Apply plugin effect to images")
    logger.info("  - create_plugin_template: Create template for new plugin")
    logger.info("  - start_mobile_server: Launch mobile companion server for remote control")
    logger.info("  - generate_mobile_token: Create secure access token for mobile app")
    logger.info("  - list_mobile_tokens: View all active mobile access tokens")
    logger.info("  - add_timeline_to_mobile: Add timeline for mobile editing")

    # Run the server using stdio transport
    asyncio.run(stdio.run(server))


if __name__ == "__main__":
    main()
