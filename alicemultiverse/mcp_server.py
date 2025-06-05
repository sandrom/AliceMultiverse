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
from .selections.service import SelectionService
from .selections.models import SelectionPurpose, SelectionStatus

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
        from .understanding.ollama_provider import OllamaImageAnalyzer
        
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

    # Run the server using stdio transport
    asyncio.run(stdio.run(server))


if __name__ == "__main__":
    main()
