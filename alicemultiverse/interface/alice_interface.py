"""Alice Interface - The intelligent orchestration layer for AI assistants."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

from ..core.ai_errors import AIFriendlyError
from ..core.config import load_config
from ..database.config import init_db
from ..database.repository import AssetRepository, ProjectRepository
from ..events.base import get_event_bus
from ..metadata.models import AssetRole
from ..organizer.enhanced_organizer import EnhancedMediaOrganizer
from ..projects import ProjectService
from .models import (
    AssetInfo,
    GenerateRequest,
    GroupRequest,
    OrganizeRequest,
    ProjectContextRequest,
    SearchRequest,
    TagRequest,
)

# Since AliceResponse is a TypedDict, we need to create dicts not instances
def AliceResponse(success: bool, message: str, data: Any = None, error: str = None) -> dict:
    """Create an AliceResponse dict."""
    return {
        "success": success,
        "message": message,
        "data": data,
        "error": error
    }

logger = logging.getLogger(__name__)


class AliceInterface:
    """Primary interface for AI assistants to interact with AliceMultiverse.

    This class provides high-level functions that AI can call using natural
    language concepts, while Alice handles all technical complexity.
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize Alice interface.

        Args:
            config_path: Optional path to configuration file
        """
        self.config = load_config(config_path)
        self.config.enhanced_metadata = True  # Always use enhanced metadata
        self.organizer = None
        self.initialization_error = None
        
        try:
            self._ensure_organizer()
        except Exception as e:
            # Store error for later - allow interface to be created
            self.initialization_error = e
            logger.warning(f"Failed to initialize organizer: {e}")
        
        # Initialize database
        db_session = init_db()
        self.asset_repo = AssetRepository()
        self.project_repo = ProjectRepository()
        
        # Initialize project service with event bus
        event_bus = get_event_bus()
        self.project_service = ProjectService(db_session, event_bus)
        logger.info("Database and services initialized")

    def _ensure_organizer(self):
        """Ensure organizer is initialized."""
        if not self.organizer:
            self.organizer = EnhancedMediaOrganizer(self.config)
            # Ensure search engine is initialized
            if not self.organizer.search_engine:
                self.organizer._update_search_engine()

    def _parse_time_reference(self, time_ref: str) -> datetime | None:
        """Parse natural language time references.

        Args:
            time_ref: Natural language time like "last week", "yesterday"

        Returns:
            Datetime object or None
        """
        now = datetime.now()
        time_ref = time_ref.lower()

        if "yesterday" in time_ref:
            return now - timedelta(days=1)
        elif "last week" in time_ref:
            return now - timedelta(weeks=1)
        elif "last month" in time_ref:
            return now - timedelta(days=30)
        elif "today" in time_ref:
            return now.replace(hour=0, minute=0, second=0)

        # Try to parse month names
        months = [
            "january",
            "february",
            "march",
            "april",
            "may",
            "june",
            "july",
            "august",
            "september",
            "october",
            "november",
            "december",
        ]
        for i, month in enumerate(months):
            if month in time_ref:
                # Assume current year
                return datetime(now.year, i + 1, 1)

        return None

    def _simplify_asset_info(self, asset: dict) -> AssetInfo:
        """Convert full metadata to simplified info for AI.

        Args:
            asset: Full asset metadata

        Returns:
            Simplified asset information
        """
        # Combine all tags
        all_tags = (
            asset.get("style_tags", [])
            + asset.get("mood_tags", [])
            + asset.get("subject_tags", [])
            + asset.get("custom_tags", [])
        )

        # Build relationships
        relationships = {}
        if asset.get("parent_id"):
            relationships["parent"] = [asset["parent_id"]]
        if asset.get("similar_to"):
            relationships["similar"] = asset["similar_to"]
        if asset.get("grouped_with"):
            relationships["grouped"] = asset["grouped_with"]

        return {
            "id": asset.get("asset_id", asset.get("file_hash", "unknown")),
            "filename": asset.get("file_name", asset.get("filename", "unknown")),
            "prompt": asset.get("prompt"),
            "tags": all_tags,
            "quality_stars": asset.get("quality_stars", asset.get("quality_star")),
            "role": (
                asset.get("role", AssetRole.WIP).value
                if hasattr(asset.get("role"), "value")
                else str(asset.get("role", "wip"))
            ),
            "created": asset.get("created_at", asset.get("date_taken", datetime.now().isoformat())),
            "source": asset.get("source_type", asset.get("ai_source", "unknown")),
            "relationships": relationships,
        }

    # === Core Functions for AI ===

    def search_assets(self, request: SearchRequest) -> AliceResponse:
        """Search for assets based on creative criteria.

        This is the primary way AI finds existing assets.

        Args:
            request: Search request with criteria

        Returns:
            Response with matching assets
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            # Build search query
            query_params = {}

            # Handle natural language description
            if request.get("description"):
                # Use description search if search engine is available
                if self.organizer.search_engine:
                    results = self.organizer.search_engine.search_by_description(
                        request["description"], limit=request.get("limit", 20)
                    )
                else:
                    # Fallback to basic search
                    results = []
            else:
                # Build structured query
                if request.get("time_reference"):
                    start_time = self._parse_time_reference(request["time_reference"])
                    if start_time:
                        query_params["timeframe_start"] = start_time

                # Add tag filters
                if request.get("style_tags"):
                    query_params["style_tags"] = request["style_tags"]
                if request.get("mood_tags"):
                    query_params["mood_tags"] = request["mood_tags"]
                if request.get("subject_tags"):
                    query_params["subject_tags"] = request["subject_tags"]

                # Add other filters
                if request.get("source_types"):
                    query_params["source_types"] = request["source_types"]
                if request.get("min_quality_stars"):
                    query_params["min_stars"] = request["min_quality_stars"]
                if request.get("roles"):
                    query_params["roles"] = [AssetRole(r) for r in request["roles"]]

                # Add options
                query_params["sort_by"] = request.get("sort_by", "relevance")
                query_params["limit"] = request.get("limit", 20)

                # Try database search first
                # Build structured tags for database search
                structured_tags = {}
                if request.get("style_tags"):
                    structured_tags["style"] = request.get("style_tags", [])
                if request.get("mood_tags"):
                    structured_tags["mood"] = request.get("mood_tags", [])
                if request.get("subject_tags"):
                    structured_tags["subject"] = request.get("subject_tags", [])
                
                db_results = self._search_database(
                    tags=structured_tags if structured_tags else None,
                    tag_mode=request.get("tag_mode", "any"),
                    source_types=request.get("source_types"),
                    min_quality=request.get("min_quality_stars"),
                    roles=request.get("roles"),
                    limit=request.get("limit", 20)
                )
                
                # Fallback to organizer search if available
                if not db_results and self.organizer.search_engine:
                    results = self.organizer.search_assets(**query_params)
                else:
                    results = db_results

            # Simplify results for AI
            simplified_results = [self._simplify_asset_info(asset) for asset in results]

            return AliceResponse(
                success=True,
                message=f"Found {len(results)} assets",
                data=simplified_results,
                error=None,
            )

        except Exception as e:
            logger.error(f"Search failed: {e}")
            friendly = AIFriendlyError.make_friendly(e, {"operation": "search", "request": request})
            return AliceResponse(
                success=False, 
                message=friendly["error"],
                data={"suggestions": friendly["suggestions"]},
                error=friendly["technical_details"]
            )

    def generate_content(self, request: GenerateRequest) -> AliceResponse:
        """Generate new content based on prompt and references.

        This is a placeholder for future implementation when generation
        capabilities are added.

        Args:
            request: Generation request

        Returns:
            Response with generation result
        """
        try:
            # This would integrate with fal.ai, ComfyUI, etc.
            # For now, return a placeholder response

            return AliceResponse(
                success=False,
                message="Content generation not yet implemented",
                data=None,
                error="This feature will be implemented when generation services are integrated",
            )

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return AliceResponse(
                success=False, message="Generation failed", data=None, error=str(e)
            )

    def organize_media(self, request: OrganizeRequest) -> AliceResponse:
        """Organize media files with optional enhancements.

        Args:
            request: Organization request

        Returns:
            Response with organization results
        """
        try:
            # Check for initialization error
            if self.initialization_error:
                raise self.initialization_error
                
            # Update config based on request
            if request.get("source_path"):
                self.config.paths.inbox = request["source_path"]
            if request.get("quality_assessment"):
                self.config.processing.quality = True
            if request.get("pipeline"):
                self.config.pipeline.mode = request["pipeline"]
            if request.get("watch_mode"):
                self.config.processing.watch = True

            # Recreate organizer with updated config
            self.organizer = EnhancedMediaOrganizer(self.config)

            # Run organization
            success = self.organizer.organize()

            # Get summary
            summary = self.organizer.get_organization_summary()
            
            # Persist to database
            if success:
                self._persist_organized_assets()

            return AliceResponse(
                success=success,
                message=summary,
                data={
                    "stats": self.organizer.stats,
                    "metadata_count": len(self.organizer.metadata_cache.get_all_metadata()),
                },
                error=None,
            )

        except Exception as e:
            logger.error(f"Organization failed: {e}")
            friendly = AIFriendlyError.make_friendly(e, {"operation": "organize", "request": request})
            return AliceResponse(
                success=False,
                message=friendly["error"],
                data={"suggestions": friendly["suggestions"]},
                error=friendly["technical_details"]
            )

    def tag_assets(self, request: TagRequest) -> AliceResponse:
        """Add tags to assets.

        Args:
            request: Tagging request with either:
                - tags: list[str] for legacy single-type tags
                - tags: dict[str, list[str]] for structured tags like {"style": ["cyberpunk"], "mood": ["dark"]}

        Returns:
            Response indicating success
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            success_count = 0
            tags = request["tags"]
            
            # If we have the asset repository, use it for structured tags
            if self.asset_repo and isinstance(tags, dict):
                # New structured format
                for asset_id in request["asset_ids"]:
                    asset_success = True
                    for tag_type, tag_values in tags.items():
                        for tag_value in tag_values:
                            if not self.asset_repo.add_tag(
                                content_hash=asset_id,
                                tag_type=tag_type,
                                tag_value=tag_value,
                                source="ai"
                            ):
                                asset_success = False
                                break
                        if not asset_success:
                            break
                    if asset_success:
                        success_count += 1
            else:
                # Legacy format or no database
                tag_type = request.get("tag_type", "custom")
                tag_list = tags if isinstance(tags, list) else []
                
                for asset_id in request["asset_ids"]:
                    if self.organizer.tag_asset(asset_id, tag_list, tag_type):
                        success_count += 1

            return AliceResponse(
                success=success_count > 0,
                message=f"Tagged {success_count}/{len(request['asset_ids'])} assets",
                data={"tagged_count": success_count},
                error=None,
            )

        except Exception as e:
            logger.error(f"Tagging failed: {e}")
            return AliceResponse(success=False, message="Tagging failed", data=None, error=str(e))

    def group_assets(self, request: GroupRequest) -> AliceResponse:
        """Group assets together.

        Args:
            request: Grouping request

        Returns:
            Response indicating success
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            success = self.organizer.group_assets(request["asset_ids"], request["group_name"])

            return AliceResponse(
                success=success,
                message=f"Grouped {len(request['asset_ids'])} assets as '{request['group_name']}'",
                data={"group_name": request["group_name"]},
                error=None,
            )

        except Exception as e:
            logger.error(f"Grouping failed: {e}")
            return AliceResponse(success=False, message="Grouping failed", data=None, error=str(e))

    def get_project_context(self, request: ProjectContextRequest) -> AliceResponse:
        """Get project context and statistics.

        Args:
            request: Context request

        Returns:
            Response with project context
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            context = self.organizer.get_project_context()

            # Add recent assets if requested
            if request.get("include_recent_assets"):
                recent = self.organizer.search_assets(sort_by="created", limit=10)
                context["recent_assets"] = [self._simplify_asset_info(asset) for asset in recent]

            return AliceResponse(
                success=True, message="Project context retrieved", data=context, error=None
            )

        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return AliceResponse(
                success=False, message="Context retrieval failed", data=None, error=str(e)
            )

    def find_similar_assets(self, asset_id: str, threshold: float = 0.7) -> AliceResponse:
        """Find assets similar to a reference.

        Args:
            asset_id: Reference asset ID
            threshold: Similarity threshold (0-1)

        Returns:
            Response with similar assets
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            similar = self.organizer.find_similar(asset_id, threshold)
            simplified = [self._simplify_asset_info(asset) for asset in similar]

            return AliceResponse(
                success=True,
                message=f"Found {len(similar)} similar assets",
                data=simplified,
                error=None,
            )

        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return AliceResponse(
                success=False, message="Similarity search failed", data=None, error=str(e)
            )

    def set_asset_role(self, asset_id: str, role: str) -> AliceResponse:
        """Set the creative role of an asset.

        Args:
            asset_id: Asset ID
            role: Role name (hero, b_roll, reference, etc.)

        Returns:
            Response indicating success
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            role_enum = AssetRole(role)
            success = self.organizer.set_asset_role(asset_id, role_enum)

            return AliceResponse(
                success=success,
                message=f"Set role to '{role}'" if success else "Failed to set role",
                data={"asset_id": asset_id, "role": role},
                error=None,
            )

        except Exception as e:
            logger.error(f"Role setting failed: {e}")
            return AliceResponse(
                success=False, message="Role setting failed", data=None, error=str(e)
            )

    def get_asset_info(self, asset_id: str) -> AliceResponse:
        """Get detailed information about a specific asset.

        Args:
            asset_id: The unique asset identifier

        Returns:
            Comprehensive metadata including prompt, tags, quality, and relationships
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            # Get asset metadata from cache
            # Try the metadata index first
            metadata = self.organizer.metadata_cache._unified.metadata_index.get(asset_id)
            if not metadata:
                return AliceResponse(
                    success=False,
                    message=f"Asset not found: {asset_id}",
                    data=None,
                    error="Asset not found"
                )

            # Convert to simplified format
            asset_info = self._simplify_asset_info(metadata)

            return AliceResponse(
                success=True,
                message="Asset information retrieved",
                data={"asset": asset_info},
                error=None
            )

        except Exception as e:
            logger.error(f"Get asset info failed: {e}")
            friendly = AIFriendlyError.make_friendly(e, {"operation": "get_info", "asset_id": asset_id})
            return AliceResponse(
                success=False,
                message=friendly["error"],
                data={"suggestions": friendly["suggestions"]},
                error=friendly["technical_details"]
            )

    def assess_quality(self, asset_ids: list[str], pipeline: str = "standard") -> AliceResponse:
        """Run quality assessment on specific assets.

        Args:
            asset_ids: List of asset IDs to assess
            pipeline: Assessment pipeline ("basic", "standard", "premium")

        Returns:
            Quality scores and identified issues for each asset
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            results = []
            for asset_id in asset_ids:
                metadata = self.organizer.metadata_cache._unified.metadata_index.get(asset_id)
                if metadata:
                    # Extract quality info if available
                    quality_info = {
                        "asset_id": asset_id,
                        "brisque_score": metadata.get("brisque_score"),
                        "quality_star": metadata.get("quality_star"),
                        "pipeline_scores": metadata.get("pipeline_scores", {}),
                        "issues": metadata.get("quality_issues", [])
                    }
                    results.append(quality_info)
                else:
                    results.append({
                        "asset_id": asset_id,
                        "error": "Asset not found"
                    })

            return AliceResponse(
                success=True,
                message=f"Assessed {len(results)} assets with {pipeline} pipeline",
                data={"quality_results": results, "pipeline": pipeline},
                error=None
            )

        except Exception as e:
            logger.error(f"Quality assessment failed: {e}")
            return AliceResponse(
                success=False, message="Quality assessment failed", data=None, error=str(e)
            )

    def get_stats(self) -> AliceResponse:
        """Get statistics about the organized media collection.

        Returns:
            Counts by date, source, quality, and project
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            self._ensure_organizer()

            # Get all cached metadata
            all_metadata = list(self.organizer.metadata_cache._unified.metadata_index.values())

            # Calculate statistics
            stats = {
                "total_assets": len(all_metadata),
                "by_source": {},
                "by_quality": {"5-star": 0, "4-star": 0, "3-star": 0, "2-star": 0, "1-star": 0},
                "by_project": {},
                "by_date": {},
                "media_types": {"image": 0, "video": 0},
            }

            for metadata in all_metadata:
                # Count by source
                source = metadata.get("ai_source", "unknown")
                stats["by_source"][source] = stats["by_source"].get(source, 0) + 1

                # Count by quality
                quality = metadata.get("quality_star")
                if quality:
                    key = f"{quality}-star"
                    if key in stats["by_quality"]:
                        stats["by_quality"][key] += 1

                # Count by project
                project = metadata.get("project", "untitled")
                stats["by_project"][project] = stats["by_project"].get(project, 0) + 1

                # Count by date
                date_taken = metadata.get("date_taken")
                if date_taken:
                    date_str = date_taken.split("T")[0]  # Get just the date part
                    stats["by_date"][date_str] = stats["by_date"].get(date_str, 0) + 1

                # Count by media type
                media_type = metadata.get("media_type", "image")
                if media_type in stats["media_types"]:
                    stats["media_types"][media_type] += 1

            return AliceResponse(
                success=True,
                message="Collection statistics retrieved",
                data=stats,
                error=None
            )

        except Exception as e:
            logger.error(f"Get stats failed: {e}")
            return AliceResponse(
                success=False, message="Failed to get statistics", data=None, error=str(e)
            )
    
    def _persist_organized_assets(self) -> None:
        """Persist organized assets to database."""
        try:
            # Get all metadata from the cache
            all_metadata = self.organizer.metadata_cache._unified.metadata_index
            
            for content_hash, metadata in all_metadata.items():
                # Determine media type
                media_type = metadata.get("media_type", "image")
                file_path = metadata.get("file_path", "")
                
                # Create or update asset in database
                asset = self.asset_repo.create_or_update_asset(
                    content_hash=content_hash,
                    file_path=file_path,
                    media_type=media_type,
                    metadata=metadata,
                    project_id=metadata.get("project")
                )
                
                # Add tags if present
                if metadata.get("style_tags"):
                    for tag in metadata["style_tags"]:
                        self.asset_repo.add_tag(content_hash, "style", tag, source="auto")
                        
                if metadata.get("mood_tags"):
                    for tag in metadata["mood_tags"]:
                        self.asset_repo.add_tag(content_hash, "mood", tag, source="auto")
                        
                if metadata.get("subject_tags"):
                    for tag in metadata["subject_tags"]:
                        self.asset_repo.add_tag(content_hash, "subject", tag, source="auto")
                        
                logger.debug(f"Persisted asset to database: {content_hash}")
                
            logger.info(f"Persisted {len(all_metadata)} assets to database")
            
        except Exception as e:
            logger.error(f"Failed to persist assets to database: {e}")
            # Don't fail the operation if database persistence fails
    
    def _search_database(
        self,
        tags: list[str] | dict[str, list[str]] | None = None,
        tag_mode: str = "any",
        source_types: list[str] | None = None,
        min_quality: int | None = None,
        roles: list[str] | None = None,
        limit: int = 20
    ) -> list[dict]:
        """Search for assets in the database.
        
        Args:
            tags: Either a list of tags (legacy) or dict mapping tag types to values
            tag_mode: "any" (OR) or "all" (AND) for tag matching
            source_types: Filter by AI source types
            min_quality: Minimum quality rating
            roles: Filter by asset roles
            limit: Maximum results
            
        Returns:
            List of asset metadata dictionaries
        """
        try:
            # Search database
            assets = self.asset_repo.search(
                tags=tags,
                tag_mode=tag_mode,
                source_type=source_types[0] if source_types else None,
                min_rating=min_quality,
                role=roles[0] if roles else None,
                limit=limit
            )
            
            # Convert to metadata format
            results = []
            for asset in assets:
                metadata = asset.embedded_metadata or {}
                metadata.update({
                    "file_hash": asset.content_hash,
                    "filename": Path(asset.file_path).name if asset.file_path else "unknown",
                    "file_path": asset.file_path,
                    "ai_source": asset.source_type,
                    "quality_star": asset.rating,
                    "project": asset.project_id,
                    "media_type": asset.media_type,
                })
                results.append(metadata)
                
            return results
            
        except Exception as e:
            logger.error(f"Database search failed: {e}")
            return []
    
    # Project Management Methods
    
    def create_project(
        self,
        name: str,
        description: str | None = None,
        budget: float | None = None,
        creative_context: dict[str, Any] | None = None
    ) -> AliceResponse:
        """Create a new project for organizing creative work.
        
        Args:
            name: Project name
            description: Optional project description
            budget: Optional budget limit in USD
            creative_context: Optional creative context (style preferences, characters, etc.)
            
        Returns:
            Response with created project details
        """
        try:
            project = self.project_service.create_project(
                name=name,
                description=description,
                budget_total=budget,
                creative_context=creative_context
            )
            
            return AliceResponse(
                success=True,
                message=f"Created project '{name}'",
                data={
                    "project_id": project.id,
                    "name": project.name,
                    "budget": project.budget_total,
                    "status": project.status
                },
                error=None
            )
            
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            friendly = AIFriendlyError.make_friendly(e, {"operation": "create_project", "name": name})
            return AliceResponse(
                success=False,
                message=friendly["error"],
                data={"suggestions": friendly["suggestions"]},
                error=friendly["technical_details"]
            )
    
    def update_project_context(
        self,
        project_id: str,
        creative_context: dict[str, Any]
    ) -> AliceResponse:
        """Update project creative context (style, characters, etc.).
        
        Args:
            project_id: Project ID
            creative_context: New context to merge with existing
            
        Returns:
            Response with updated project details
        """
        try:
            project = self.project_service.update_project_context(
                project_id=project_id,
                creative_context=creative_context
            )
            
            if not project:
                return AliceResponse(
                    success=False,
                    message=f"Project not found: {project_id}",
                    data=None,
                    error="Project not found"
                )
            
            return AliceResponse(
                success=True,
                message="Updated project context",
                data={
                    "project_id": project.id,
                    "creative_context": project.creative_context
                },
                error=None
            )
            
        except Exception as e:
            logger.error(f"Project update failed: {e}")
            return AliceResponse(
                success=False,
                message="Failed to update project",
                data=None,
                error=str(e)
            )
    
    def get_project_budget_status(self, project_id: str) -> AliceResponse:
        """Get project budget status and cost breakdown.
        
        Args:
            project_id: Project ID
            
        Returns:
            Response with budget details and statistics
        """
        try:
            stats = self.project_service.get_project_stats(project_id)
            
            if not stats:
                return AliceResponse(
                    success=False,
                    message=f"Project not found: {project_id}",
                    data=None,
                    error="Project not found"
                )
            
            return AliceResponse(
                success=True,
                message="Retrieved project budget status",
                data=stats,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Failed to get project stats: {e}")
            return AliceResponse(
                success=False,
                message="Failed to retrieve budget status",
                data=None,
                error=str(e)
            )
    
    def list_projects(self, status: str | None = None) -> AliceResponse:
        """List all projects, optionally filtered by status.
        
        Args:
            status: Optional status filter (active, paused, completed, archived)
            
        Returns:
            Response with list of projects
        """
        try:
            projects = self.project_service.list_projects(status=status)
            
            project_list = []
            for project in projects:
                project_list.append({
                    "project_id": project.id,
                    "name": project.name,
                    "description": project.description,
                    "status": project.status,
                    "budget_total": project.budget_total,
                    "budget_spent": project.budget_spent,
                    "created_at": project.created_at.isoformat() if project.created_at else None
                })
            
            return AliceResponse(
                success=True,
                message=f"Found {len(projects)} projects",
                data={"projects": project_list},
                error=None
            )
            
        except Exception as e:
            logger.error(f"Failed to list projects: {e}")
            return AliceResponse(
                success=False,
                message="Failed to list projects",
                data=None,
                error=str(e)
            )
    
    def track_generation_cost(
        self,
        project_id: str,
        provider: str,
        model: str,
        cost: float,
        request_type: str = "image",
        prompt: str | None = None,
        result_assets: list[str] | None = None
    ) -> AliceResponse:
        """Track AI generation cost for a project.
        
        Args:
            project_id: Project ID
            provider: Provider name (fal, openai, anthropic)
            model: Model name
            cost: Cost in USD
            request_type: Type of request (image, video, vision, text)
            prompt: Optional prompt used
            result_assets: Optional list of resulting asset content hashes
            
        Returns:
            Response with generation tracking details
        """
        try:
            generation = self.project_service.track_generation(
                project_id=project_id,
                provider=provider,
                model=model,
                cost=cost,
                request_type=request_type,
                prompt=prompt,
                result_assets=result_assets
            )
            
            # Get updated project stats
            stats = self.project_service.get_project_stats(project_id)
            
            return AliceResponse(
                success=True,
                message="Tracked generation cost",
                data={
                    "generation_id": generation.id,
                    "cost": generation.cost,
                    "budget_remaining": stats["budget"]["remaining"] if stats else None,
                    "project_status": stats["status"] if stats else None
                },
                error=None
            )
            
        except ValueError as e:
            # Project not found
            return AliceResponse(
                success=False,
                message=str(e),
                data=None,
                error="Project not found"
            )
        except Exception as e:
            logger.error(f"Failed to track generation: {e}")
            return AliceResponse(
                success=False,
                message="Failed to track generation cost",
                data=None,
                error=str(e)
            )
