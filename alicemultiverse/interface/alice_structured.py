"""Alice Structured Interface - No natural language processing, only structured queries."""

import logging
import re
from datetime import datetime
from pathlib import Path

from ..core.config import load_config
from ..core.exceptions import ValidationError
from ..metadata.models import AssetRole as MetadataAssetRole
from ..organizer.enhanced_organizer import EnhancedMediaOrganizer
from .rate_limiter import RateLimiter
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
    SearchResponse,
    SortField,
    SortOrder,
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
            
            self._ensure_organizer()
            start_time = datetime.now()

            filters = request.get("filters", {})

            # Build internal query parameters
            query_params = {}

            # Apply media type filter
            if filters.get("media_type"):
                query_params["media_types"] = [filters["media_type"]]

            # Apply date range filter
            if filters.get("date_range"):
                date_range = filters["date_range"]
                if date_range.get("start"):
                    query_params["timeframe_start"] = self._parse_iso_date(date_range["start"])
                if date_range.get("end"):
                    query_params["timeframe_end"] = self._parse_iso_date(date_range["end"])

            # Apply quality rating filter
            if filters.get("quality_rating"):
                quality_range = filters["quality_rating"]
                if quality_range.get("min"):
                    query_params["min_stars"] = quality_range["min"]
                if quality_range.get("max"):
                    query_params["max_stars"] = quality_range["max"]

            # Apply source filter
            if filters.get("ai_source"):
                query_params["source_types"] = filters["ai_source"]

            # Apply tag filters
            if filters.get("tags"):
                query_params["all_tags"] = filters["tags"]  # AND operation
            if filters.get("any_tags"):
                query_params["any_tags"] = filters["any_tags"]  # OR operation
            if filters.get("exclude_tags"):
                query_params["exclude_tags"] = filters["exclude_tags"]  # NOT operation

            # Apply sorting
            sort_by = request.get("sort_by", SortField.CREATED_DATE)
            order = request.get("order", SortOrder.DESC)
            query_params["sort_by"] = sort_by
            query_params["ascending"] = (order == SortOrder.ASC)

            # Apply pagination
            query_params["limit"] = min(request.get("limit", 50), 1000)
            query_params["offset"] = request.get("offset", 0)

            # Execute search
            results = self.organizer.search_assets(**query_params)

            # Apply additional filters that aren't supported by the current search
            filtered_results = []
            for asset in results:
                # File format filter
                if filters.get("file_formats"):
                    file_ext = Path(asset.get("file_path", "")).suffix[1:].lower()
                    if file_ext not in filters["file_formats"]:
                        continue

                # File size filter
                if filters.get("file_size"):
                    if not self._apply_range_filter(
                        asset.get("file_size", 0),
                        filters["file_size"]
                    ):
                        continue

                # Dimension filters
                if filters.get("dimensions"):
                    dims = filters["dimensions"]
                    if dims.get("width") and not self._apply_range_filter(
                        asset.get("width", 0), dims["width"]
                    ):
                        continue
                    if dims.get("height") and not self._apply_range_filter(
                        asset.get("height", 0), dims["height"]
                    ):
                        continue
                    if dims.get("aspect_ratio"):
                        width = asset.get("width", 1)
                        height = asset.get("height", 1)
                        aspect_ratio = width / height if height > 0 else 0
                        if not self._apply_range_filter(aspect_ratio, dims["aspect_ratio"]):
                            continue

                # Filename pattern filter
                if filters.get("filename_pattern"):
                    if not self._matches_pattern(
                        asset.get("file_name", ""),
                        filters["filename_pattern"]
                    ):
                        continue

                # Prompt keywords filter
                if filters.get("prompt_keywords"):
                    prompt = asset.get("prompt", "").lower()
                    if not all(keyword.lower() in prompt for keyword in filters["prompt_keywords"]):
                        continue

                # Has metadata filter
                if filters.get("has_metadata"):
                    if not all(key in asset for key in filters["has_metadata"]):
                        continue

                # Content hash filter
                if filters.get("content_hash"):
                    if asset.get("content_hash") != filters["content_hash"]:
                        continue

                filtered_results.append(asset)

            # Convert to API format
            api_results = [self._convert_to_asset(asset) for asset in filtered_results]

            # Calculate facets if requested (simplified version)
            facets = self._calculate_facets(filtered_results)

            # Calculate query time
            query_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

            response_data = SearchResponse(
                total_count=len(api_results),
                results=api_results,
                facets=facets,
                query_time_ms=query_time_ms
            )

            return AliceResponse(
                success=True,
                message=f"Found {len(api_results)} assets",
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
                # Get current asset metadata
                metadata = self.organizer.metadata_cache.get_metadata_by_id(asset_id)
                if not metadata:
                    continue

                # Apply tag operations
                if request.get("set_tags") is not None:
                    # Replace all tags
                    metadata["custom_tags"] = request["set_tags"]
                else:
                    # Add/remove operations
                    current_tags = set(metadata.get("custom_tags", []))

                    if request.get("add_tags"):
                        current_tags.update(request["add_tags"])

                    if request.get("remove_tags"):
                        current_tags.difference_update(request["remove_tags"])

                    metadata["custom_tags"] = list(current_tags)

                # Save updated metadata
                if self.organizer.metadata_cache.update_metadata(asset_id, metadata):
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
            
            self._ensure_organizer()

            metadata = self.organizer.metadata_cache.get_metadata_by_id(asset_id)
            if not metadata:
                return AliceResponse(
                    success=False,
                    message="Asset not found",
                    data=None,
                    error=f"No asset found with ID: {asset_id}"
                )

            asset = self._convert_to_asset(metadata)

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
            
            self._ensure_organizer()

            # Convert to internal enum
            metadata_role = MetadataAssetRole(role.value)
            success = self.organizer.set_asset_role(asset_id, metadata_role)

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
