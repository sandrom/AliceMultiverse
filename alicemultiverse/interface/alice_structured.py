"""Alice Structured Interface - No natural language processing, only structured queries."""

import logging
import re
from datetime import datetime
from pathlib import Path

from ..core.config import load_config
from ..core.exceptions import ValidationError
from ..organizer.enhanced_organizer import EnhancedMediaOrganizer
from ..projects.service import ProjectService
from ..selections.service import SelectionService
from .rate_limiter import RateLimiter
from .search_handler import OptimizedSearchHandler
from .structured_models import (
    AliceResponse,
    Asset,
    AssetRole,
    GenerationRequest,
    GroupingRequest,
    MediaType,
    OrganizeRequest,
    ProjectRequest,
    RangeFilter,
    SearchFacet,
    SearchFacets,
    SearchRequest,
    SelectionCreateRequest,
    SelectionExportRequest,
    SelectionPurpose,
    SelectionSearchRequest,
    SelectionUpdateRequest,
    SoftDeleteRequest,
    TagUpdateRequest,
    WorkflowRequest,
)
from .validation import (
    validate_asset_role,
    validate_generation_request,
    validate_grouping_request,
    validate_organize_request,
    validate_project_request,
    validate_search_request,
    validate_selection_create_request,
    validate_selection_export_request,
    validate_selection_search_request,
    validate_selection_update_request,
    validate_soft_delete_request,
    validate_tag_update_request,
    validate_workflow_request,
)

logger = logging.getLogger(__name__)


class AliceStructuredInterface:
    """Structured interface for AI assistants to interact with AliceMultiverse.
    
    This interface accepts ONLY structured queries - no natural language processing.
    All NLP should happen at the AI assistant layer before calling these methods.
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize Alice structured interface.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = load_config(config_path)
        self.config.enhanced_metadata = True  # Always use enhanced metadata
        self.organizer = None
        self._ensure_organizer()
        
        # Initialize rate limiter
        self.rate_limiter = RateLimiter()
        
        # Initialize optimized search handler with config
        self.search_handler = OptimizedSearchHandler(config=self.config)
        
        # Initialize project and selection services
        self.project_service = ProjectService(config=self.config)
        self.selection_service = SelectionService(project_service=self.project_service)

    def _ensure_organizer(self) -> None:
        """Ensure organizer is initialized."""
        if not self.organizer:
            self.organizer = EnhancedMediaOrganizer(self.config)

    def _parse_iso_date(self, date_str: str) -> datetime:
        """Parse ISO 8601 date string."""
        try:
            return datetime.fromisoformat(date_str.replace('Z', '+00:00'))
        except ValueError:
            # Try parsing just the date part
            return datetime.strptime(date_str[:10], "%Y-%m-%d")

    def _apply_range_filter(self, value: float, range_filter: RangeFilter) -> bool:
        """Check if value falls within range filter."""
        if range_filter.get("min") is not None and value < range_filter["min"]:
            return False
        if range_filter.get("max") is not None and value > range_filter["max"]:
            return False
        return True

    def _matches_pattern(self, text: str, pattern: str) -> bool:
        """Check if text matches regex pattern."""
        try:
            return bool(re.search(pattern, text, re.IGNORECASE))
        except re.error:
            logger.warning(f"Invalid regex pattern: {pattern}")
            return False

    def _convert_to_asset(self, metadata: dict) -> Asset:
        """Convert internal metadata to API Asset format."""
        return Asset(
            content_hash=metadata.get("content_hash", ""),
            file_path=metadata.get("file_path", ""),
            media_type=MediaType(metadata.get("media_type", "unknown")),
            file_size=metadata.get("file_size", 0),
            tags=self._collect_all_tags(metadata),
            ai_source=metadata.get("source_type"),
            quality_rating=metadata.get("quality_stars"),
            created_at=metadata.get("created_at", datetime.now()).isoformat(),
            modified_at=metadata.get("modified_at", datetime.now()).isoformat(),
            discovered_at=metadata.get("discovered_at", datetime.now()).isoformat(),
            metadata={
                "dimensions": {
                    "width": metadata.get("width"),
                    "height": metadata.get("height"),
                } if metadata.get("width") else None,
                "prompt": metadata.get("prompt"),
                "generation_params": metadata.get("generation_params", {}),
            }
        )

    def _collect_all_tags(self, metadata: dict) -> list[str]:
        """Collect all tags from different tag categories."""
        all_tags = []
        for tag_type in ["style_tags", "mood_tags", "subject_tags", "custom_tags"]:
            all_tags.extend(metadata.get(tag_type, []))
        return list(set(all_tags))  # Remove duplicates

    def search_assets(self, request: SearchRequest, client_id: str = "default") -> AliceResponse:
        """Search for assets using structured queries only.
        
        Args:
            request: Structured search request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with search results
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "search")
            
            # Validate request
            request = validate_search_request(request)
            
            # Use optimized search handler
            response_data = self.search_handler.search_assets(request)
            
            return AliceResponse(
                success=True,
                message=f"Found {response_data['total_count']} assets",
                data=response_data,
                error=None
            )

        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Search failed",
                data=None,
                error=str(e)
            )

    def _calculate_facets(self, results: list[dict]) -> SearchFacets:
        """Calculate facets from search results."""
        tag_counts = {}
        source_counts = {}
        quality_counts = {}
        type_counts = {}

        for asset in results:
            # Count tags
            for tag in self._collect_all_tags(asset):
                tag_counts[tag] = tag_counts.get(tag, 0) + 1

            # Count sources
            source = asset.get("source_type", "unknown")
            source_counts[source] = source_counts.get(source, 0) + 1

            # Count quality ratings
            quality = asset.get("quality_stars", 0)
            quality_counts[str(quality)] = quality_counts.get(str(quality), 0) + 1

            # Count media types
            media_type = asset.get("media_type", "unknown")
            type_counts[media_type] = type_counts.get(media_type, 0) + 1

        return SearchFacets(
            tags=[
                SearchFacet(value=tag, count=count)
                for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
            ],
            ai_sources=[
                SearchFacet(value=source, count=count)
                for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
            ],
            quality_ratings=[
                SearchFacet(value=rating, count=count)
                for rating, count in sorted(quality_counts.items())
            ],
            media_types=[
                SearchFacet(value=media_type, count=count)
                for media_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
            ]
        )

    def organize_media(self, request: OrganizeRequest, client_id: str = "default") -> AliceResponse:
        """Organize media files with structured parameters only.
        
        Args:
            request: Structured organization request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with organization results
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "organize")
            
            # Validate request
            request = validate_organize_request(request)
            
            # Update config based on request
            if request.get("source_path"):
                self.config.paths.inbox = request["source_path"]
            if request.get("destination_path"):
                self.config.paths.organized = request["destination_path"]
            if request.get("quality_assessment") is not None:
                self.config.processing.quality = request["quality_assessment"]
            if request.get("pipeline"):
                self.config.pipeline.mode = request["pipeline"]
            if request.get("watch_mode") is not None:
                self.config.processing.watch = request["watch_mode"]
            if request.get("move_files") is not None:
                self.config.processing.move = request["move_files"]

            # Recreate organizer with updated config
            self.organizer = EnhancedMediaOrganizer(self.config)

            # Run organization
            success = self.organizer.organize()

            # Get summary statistics
            stats = self.organizer.stats

            return AliceResponse(
                success=success,
                message=f"Processed {stats.get('processed', 0)} files",
                data={
                    "stats": stats,
                    "metadata_count": len(self.organizer.metadata_cache.get_all_metadata()),
                },
                error=None
            )

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Organization failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Organization failed",
                data=None,
                error=str(e)
            )

    def update_tags(self, request: TagUpdateRequest, client_id: str = "default") -> AliceResponse:
        """Update asset tags with structured operations.
        
        Args:
            request: Tag update request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response indicating success
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "update_tags")
            
            # Validate request
            request = validate_tag_update_request(request)
            
            self._ensure_organizer()

            success_count = 0

            for asset_id in request["asset_ids"]:
                # Asset ID should be content_hash for now
                content_hash = asset_id
                
                # Get current asset metadata
                search_request = SearchRequest(
                    filters={"content_hash": content_hash},
                    limit=1
                )
                search_response = self.search_handler.search(search_request)
                
                if not search_response.assets:
                    continue
                    
                asset = search_response.assets[0]
                current_tags = set(asset.tags)

                # Apply tag operations
                if request.get("set_tags") is not None:
                    # Replace all tags
                    new_tags = request["set_tags"]
                else:
                    # Add/remove operations
                    new_tags = current_tags.copy()

                    if request.get("add_tags"):
                        new_tags.update(request["add_tags"])

                    if request.get("remove_tags"):
                        new_tags.difference_update(request["remove_tags"])

                    new_tags = list(new_tags)

                # Re-index asset with updated tags
                # Create metadata dict for re-indexing
                metadata = {
                    "content_hash": asset.content_hash,
                    "file_path": asset.file_path,
                    "file_size": asset.file_size,
                    "media_type": asset.media_type.value,
                    "ai_source": asset.ai_source,
                    "tags": new_tags,
                    "quality_rating": asset.quality_rating,
                    "created_at": asset.created_at,
                    "modified_at": asset.modified_at,
                    "discovered_at": asset.discovered_at,
                }
                
                # Re-index in search DB (will update existing entry)
                self.search_handler.search_db.index_asset(metadata)
                success_count += 1

            return AliceResponse(
                success=success_count > 0,
                message=f"Updated {success_count}/{len(request['asset_ids'])} assets",
                data={"updated_count": success_count},
                error=None
            )

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Tag update failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Tag update failed",
                data=None,
                error=str(e)
            )

    def group_assets(self, request: GroupingRequest, client_id: str = "default") -> AliceResponse:
        """Group assets together with structured parameters.
        
        Args:
            request: Grouping request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response indicating success
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "group_assets")
            
            # Validate request
            request = validate_grouping_request(request)
            
            self._ensure_organizer()

            success = self.organizer.group_assets(
                request["asset_ids"],
                request["group_name"]
            )

            # Add group metadata if provided
            if success and request.get("group_metadata"):
                # This would store additional group metadata
                # Implementation depends on metadata storage strategy
                pass

            return AliceResponse(
                success=success,
                message=f"Grouped {len(request['asset_ids'])} assets",
                data={
                    "group_name": request["group_name"],
                    "asset_count": len(request["asset_ids"])
                },
                error=None
            )

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Grouping failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Grouping failed",
                data=None,
                error=str(e)
            )

    def manage_project(self, request: ProjectRequest, client_id: str = "default") -> AliceResponse:
        """Manage projects with structured operations.
        
        Args:
            request: Project management request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with project operation result
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "manage_project")
            
            # Validate request
            request = validate_project_request(request)
            
            # Placeholder for future project management
            return AliceResponse(
                success=False,
                message="Project management not yet implemented",
                data=None,
                error="This feature will be implemented with the project management system"
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )

    def execute_workflow(self, request: WorkflowRequest, client_id: str = "default") -> AliceResponse:
        """Execute workflows with structured parameters.
        
        Args:
            request: Workflow execution request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with workflow result
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "execute_workflow")
            
            # Validate request
            request = validate_workflow_request(request)
            
            # Placeholder for future workflow engine
            return AliceResponse(
                success=False,
                message="Workflow execution not yet implemented",
                data=None,
                error="This feature will be implemented with the workflow engine"
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )

    def generate_content(self, request: GenerationRequest, client_id: str = "default") -> AliceResponse:
        """Generate content with structured parameters.
        
        Args:
            request: Generation request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with generation result
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "generate_content")
            
            # Validate request
            request = validate_generation_request(request)
            
            # Placeholder for future generation capabilities
            return AliceResponse(
                success=False,
                message="Content generation not yet implemented",
                data=None,
                error="This feature will be implemented when generation services are integrated"
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )

    def soft_delete_assets(self, request: SoftDeleteRequest, client_id: str = "default") -> AliceResponse:
        """Soft delete assets by moving them to sorted-out folder.
        
        Args:
            request: Soft delete request with asset IDs and category
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with deletion results
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "soft_delete")
            
            # Validate request
            request = validate_soft_delete_request(request)
            
            # Import soft delete manager
            from ..organizer.soft_delete import SoftDeleteManager
            
            # Get sorted-out path from config or use default
            sorted_out_path = "sorted-out"
            if hasattr(self.config, 'storage') and hasattr(self.config.storage, 'sorted_out_path'):
                sorted_out_path = self.config.storage.sorted_out_path
            
            soft_delete_manager = SoftDeleteManager(sorted_out_path)
            
            self._ensure_organizer()
            
            success_count = 0
            failed_count = 0
            moved_files = []
            failed_files = []
            
            for asset_id in request["asset_ids"]:
                # Asset ID should be content_hash for now
                # TODO: Add proper asset ID support in search index
                content_hash = asset_id
                
                # Search for asset by content hash
                # Access search_db through the search handler
                search_request = SearchRequest(
                    filters={"content_hash": content_hash},
                    limit=1
                )
                search_response = self.search_handler.search(search_request)
                search_results = search_response.assets
                if not search_results:
                    failed_files.append(asset_id)
                    failed_count += 1
                    continue
                
                asset = search_results[0]
                file_path = Path(asset.file_path)
                
                # Check if file exists
                if not file_path.exists():
                    failed_files.append(asset_id)
                    failed_count += 1
                    continue
                
                # Convert Asset object to dict for soft delete
                asset_data = {
                    "content_hash": asset.content_hash,
                    "file_path": asset.file_path,
                    "media_type": asset.media_type.value,
                    "ai_source": asset.ai_source,
                    "tags": asset.tags,
                    "quality_rating": asset.quality_rating,
                }
                
                # Soft delete the file
                new_path = soft_delete_manager.soft_delete(
                    file_path=file_path,
                    category=request["category"],
                    reason=request.get("reason"),
                    metadata=asset_data
                )
                
                if new_path:
                    moved_files.append(str(new_path))
                    success_count += 1
                    # TODO: Remove from search index or mark as deleted
                else:
                    failed_files.append(asset_id)
                    failed_count += 1
            
            return AliceResponse(
                success=success_count > 0,
                message=f"Soft deleted {success_count}/{len(request['asset_ids'])} assets",
                data={
                    "moved_count": success_count,
                    "failed_count": failed_count,
                    "moved_files": moved_files,
                    "failed_assets": failed_files,
                    "category": request["category"]
                },
                error=None
            )
            
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Soft delete failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Soft delete failed",
                data=None,
                error=str(e)
            )

    def get_asset_by_id(self, asset_id: str, client_id: str = "default") -> AliceResponse:
        """Get a specific asset by ID.
        
        Args:
            asset_id: Asset identifier
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with asset information
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "get_asset")
            
            # Asset ID should be content_hash for now
            # TODO: Add proper asset ID support in search index
            content_hash = asset_id
            
            # Search for asset by content hash
            search_request = SearchRequest(
                filters={"content_hash": content_hash},
                limit=1
            )
            search_response = self.search_handler.search(search_request)
            
            if not search_response.assets:
                return AliceResponse(
                    success=False,
                    message="Asset not found",
                    data=None,
                    error=f"No asset found with ID: {asset_id}"
                )

            asset = search_response.assets[0]

            return AliceResponse(
                success=True,
                message="Asset retrieved",
                data=asset,
                error=None
            )

        except Exception as e:
            logger.error(f"Asset retrieval failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Asset retrieval failed",
                data=None,
                error=str(e)
            )

    def set_asset_role(self, asset_id: str, role: AssetRole, client_id: str = "default") -> AliceResponse:
        """Set asset role with structured enum.
        
        Args:
            asset_id: Asset identifier
            role: Asset role enum value
            client_id: Client identifier for rate limiting
            
        Returns:
            Response indicating success
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "set_asset_role")
            
            # Validate role
            role = validate_asset_role(role)
            
            # TODO: Implement asset role setting in search index
            # For now, asset roles are not supported in the new architecture
            success = False
            logger.warning("Asset role setting not yet implemented in search-based architecture")

            return AliceResponse(
                success=success,
                message=f"Set role to '{role.value}'" if success else "Failed to set role",
                data={
                    "asset_id": asset_id,
                    "role": role.value
                },
                error=None
            )

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Role setting failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Role setting failed",
                data=None,
                error=str(e)
            )

    def create_selection(self, request: SelectionCreateRequest, client_id: str = "default") -> AliceResponse:
        """Create a new selection for a project.
        
        Args:
            request: Selection creation request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with created selection
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "create_selection")
            
            # Validate request
            request = validate_selection_create_request(request)
            
            # Create selection
            selection = self.selection_service.create_selection(
                project_id=request["project_id"],
                name=request["name"],
                purpose=request.get("purpose", SelectionPurpose.CURATION),
                description=request.get("description"),
                criteria=request.get("criteria"),
                constraints=request.get("constraints"),
                tags=request.get("tags"),
                metadata=request.get("metadata"),
            )
            
            if selection:
                return AliceResponse(
                    success=True,
                    message=f"Created selection '{selection.name}'",
                    data={
                        "selection_id": selection.id,
                        "name": selection.name,
                        "purpose": selection.purpose.value,
                        "status": selection.status.value,
                        "created_at": selection.created_at.isoformat(),
                    },
                    error=None
                )
            else:
                return AliceResponse(
                    success=False,
                    message="Failed to create selection",
                    data=None,
                    error="Project not found or creation failed"
                )
                
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Selection creation failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Selection creation failed",
                data=None,
                error=str(e)
            )

    def update_selection(self, request: SelectionUpdateRequest, client_id: str = "default") -> AliceResponse:
        """Update a selection (add/remove items, change status, etc).
        
        Args:
            request: Selection update request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with updated selection
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "update_selection")
            
            # Validate request
            request = validate_selection_update_request(request)
            
            # Get project ID from selection
            selection = None
            project_id = None
            
            # First, find the selection to get project ID
            for project in self.project_service.list_projects():
                test_selection = self.selection_service.get_selection(
                    project["id"], request["selection_id"]
                )
                if test_selection:
                    selection = test_selection
                    project_id = project["id"]
                    break
            
            if not selection:
                return AliceResponse(
                    success=False,
                    message="Selection not found",
                    data=None,
                    error=f"Selection '{request['selection_id']}' not found"
                )
            
            # Process updates
            updated = False
            
            # Add items
            if request.get("add_items"):
                result = self.selection_service.add_items_to_selection(
                    project_id=project_id,
                    selection_id=request["selection_id"],
                    items=request["add_items"],
                    notes=request.get("notes")
                )
                if result:
                    selection = result
                    updated = True
            
            # Remove items
            if request.get("remove_items"):
                result = self.selection_service.remove_items_from_selection(
                    project_id=project_id,
                    selection_id=request["selection_id"],
                    asset_hashes=request["remove_items"],
                    reason=request.get("notes")
                )
                if result:
                    selection = result
                    updated = True
            
            # Update status
            if request.get("update_status"):
                result = self.selection_service.update_selection_status(
                    project_id=project_id,
                    selection_id=request["selection_id"],
                    status=request["update_status"],
                    notes=request.get("notes")
                )
                if result:
                    selection = result
                    updated = True
            
            if updated and selection:
                return AliceResponse(
                    success=True,
                    message="Selection updated successfully",
                    data={
                        "selection_id": selection.id,
                        "name": selection.name,
                        "status": selection.status.value,
                        "item_count": len(selection.items),
                        "updated_at": selection.updated_at.isoformat(),
                    },
                    error=None
                )
            else:
                return AliceResponse(
                    success=False,
                    message="No updates performed",
                    data=None,
                    error="No valid update operations provided"
                )
                
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Selection update failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Selection update failed",
                data=None,
                error=str(e)
            )

    def search_selections(self, request: SelectionSearchRequest, client_id: str = "default") -> AliceResponse:
        """Search for selections in a project.
        
        Args:
            request: Selection search request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with matching selections
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "search_selections")
            
            # Validate request
            request = validate_selection_search_request(request)
            
            # Search selections
            selections = self.selection_service.list_selections(
                project_id=request["project_id"],
                status=request.get("status"),
                purpose=request.get("purpose")
            )
            
            # Filter by containing asset if requested
            if request.get("containing_asset"):
                selections = [
                    s for s in selections
                    if request["containing_asset"] in s.get_asset_hashes()
                ]
            
            # Format response
            selection_data = []
            for selection in selections:
                stats = self.selection_service.get_selection_statistics(
                    request["project_id"], selection.id
                )
                selection_data.append({
                    "selection_id": selection.id,
                    "name": selection.name,
                    "purpose": selection.purpose.value,
                    "status": selection.status.value,
                    "description": selection.description,
                    "item_count": stats.get("item_count", 0),
                    "created_at": selection.created_at.isoformat(),
                    "updated_at": selection.updated_at.isoformat(),
                    "tags": selection.tags,
                })
            
            return AliceResponse(
                success=True,
                message=f"Found {len(selection_data)} selections",
                data={
                    "selections": selection_data,
                    "total_count": len(selection_data),
                },
                error=None
            )
                
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Selection search failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Selection search failed",
                data=None,
                error=str(e)
            )

    def export_selection(self, request: SelectionExportRequest, client_id: str = "default") -> AliceResponse:
        """Export a selection to a directory.
        
        Args:
            request: Selection export request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with export status
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "export_selection")
            
            # Validate request
            request = validate_selection_export_request(request)
            
            # Find the selection to get project ID
            selection = None
            project_id = None
            
            for project in self.project_service.list_projects():
                test_selection = self.selection_service.get_selection(
                    project["id"], request["selection_id"]
                )
                if test_selection:
                    selection = test_selection
                    project_id = project["id"]
                    break
            
            if not selection:
                return AliceResponse(
                    success=False,
                    message="Selection not found",
                    data=None,
                    error=f"Selection '{request['selection_id']}' not found"
                )
            
            # Export selection
            success = self.selection_service.export_selection(
                project_id=project_id,
                selection_id=request["selection_id"],
                export_path=Path(request["export_path"]),
                export_settings=request.get("export_settings")
            )
            
            if success:
                return AliceResponse(
                    success=True,
                    message=f"Exported selection to {request['export_path']}",
                    data={
                        "selection_id": selection.id,
                        "name": selection.name,
                        "export_path": request["export_path"],
                        "item_count": len(selection.items),
                    },
                    error=None
                )
            else:
                return AliceResponse(
                    success=False,
                    message="Export failed",
                    data=None,
                    error="Failed to export selection"
                )
                
        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Selection export failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Selection export failed",
                data=None,
                error=str(e)
            )

    def get_selection(self, project_id: str, selection_id: str, client_id: str = "default") -> AliceResponse:
        """Get detailed information about a selection.
        
        Args:
            project_id: Project ID or name
            selection_id: Selection ID
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with selection details
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "get_selection")
            
            # Get selection
            selection = self.selection_service.get_selection(project_id, selection_id)
            
            if not selection:
                return AliceResponse(
                    success=False,
                    message="Selection not found",
                    data=None,
                    error=f"Selection '{selection_id}' not found in project '{project_id}'"
                )
            
            # Get statistics
            stats = self.selection_service.get_selection_statistics(project_id, selection_id)
            
            # Format selection data
            selection_data = {
                "selection_id": selection.id,
                "project_id": selection.project_id,
                "name": selection.name,
                "purpose": selection.purpose.value,
                "status": selection.status.value,
                "description": selection.description,
                "criteria": selection.criteria,
                "constraints": selection.constraints,
                "created_at": selection.created_at.isoformat(),
                "updated_at": selection.updated_at.isoformat(),
                "created_by": selection.created_by,
                "tags": selection.tags,
                "metadata": selection.metadata,
                "statistics": stats,
                "items": [
                    {
                        "asset_hash": item.asset_hash,
                        "file_path": item.file_path,
                        "added_at": item.added_at.isoformat(),
                        "selection_reason": item.selection_reason,
                        "quality_notes": item.quality_notes,
                        "usage_notes": item.usage_notes,
                        "tags": item.tags,
                        "role": item.role,
                        "sequence_order": item.sequence_order,
                    }
                    for item in selection.items
                ],
                "groups": selection.groups,
                "sequence": selection.sequence,
                "export_history": selection.export_history,
            }
            
            return AliceResponse(
                success=True,
                message=f"Retrieved selection '{selection.name}'",
                data=selection_data,
                error=None
            )
                
        except Exception as e:
            logger.error(f"Get selection failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Get selection failed",
                data=None,
                error=str(e)
            )
    
    def find_similar_to_selection(
        self, 
        project_id: str, 
        selection_id: str,
        threshold: int = 10,
        limit: int = 50,
        exclude_existing: bool = True,
        client_id: str = "default"
    ) -> AliceResponse:
        """Find images similar to those in a selection.
        
        Uses perceptual hashing to find visually similar images.
        
        Args:
            project_id: Project ID or name
            selection_id: Selection ID
            threshold: Maximum Hamming distance (0-64, lower is more similar)
            limit: Maximum results to return
            exclude_existing: Whether to exclude items already in selection
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with similar images sorted by recommendation score
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "find_similar")
            
            # Find similar images
            similar_images = self.selection_service.find_similar_to_selection(
                project_id=project_id,
                selection_id=selection_id,
                threshold=threshold,
                limit=limit,
                exclude_existing=exclude_existing
            )
            
            if not similar_images:
                return AliceResponse(
                    success=True,
                    message="No similar images found",
                    data={
                        "selection_id": selection_id,
                        "results": [],
                        "parameters": {
                            "threshold": threshold,
                            "limit": limit,
                            "exclude_existing": exclude_existing
                        }
                    },
                    error=None
                )
            
            # Format results
            results = []
            for img in similar_images:
                result = {
                    "asset": {
                        "content_hash": img["content_hash"],
                        "file_path": img["file_path"],
                        "ai_source": img.get("ai_source"),
                        "quality_rating": img.get("quality_rating"),
                        "created_at": img.get("created_at"),
                        "tags": img.get("tags", []),
                    },
                    "similarity": {
                        "min_distance": img["min_distance"],
                        "recommendation_score": img["recommendation_score"],
                        "similar_to_count": len(img.get("similar_to", [])),
                        "similar_to_items": img.get("similar_to_items", [])
                    }
                }
                results.append(result)
            
            return AliceResponse(
                success=True,
                message=f"Found {len(results)} similar images",
                data={
                    "selection_id": selection_id,
                    "results": results,
                    "parameters": {
                        "threshold": threshold,
                        "limit": limit,
                        "exclude_existing": exclude_existing
                    }
                },
                error=None
            )
            
        except Exception as e:
            logger.error(f"Find similar to selection failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Find similar images failed",
                data=None,
                error=str(e)
            )
