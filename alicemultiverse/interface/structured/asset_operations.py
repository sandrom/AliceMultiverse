"""Asset operations for structured interface."""

import logging
from pathlib import Path

from ...core.exceptions import ValidationError
from ..structured_models import (
    AliceResponse,
    AssetRole,
    SearchFacet,
    SearchFacets,
    SearchRequest,
    SoftDeleteRequest,
)
from ..validation import (
    validate_asset_role,
    validate_search_request,
    validate_soft_delete_request,
)

logger = logging.getLogger(__name__)


class AssetOperationsMixin:
    """Mixin for asset-related operations."""

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

            # Asset ID is content_hash - this is by design
            # Using content hash ensures assets maintain identity when moved
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

            # Use content hash as asset ID
            content_hash = asset_id

            # Set the role using DuckDB through search handler
            success = self.search_handler.search_db.set_asset_role(content_hash, role.value)

            if not success:
                logger.warning(f"Failed to set role for asset {asset_id}")

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
            from ...organizer.soft_delete import SoftDeleteManager

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
                # Asset ID is content_hash - this is by design
                # Content hash is our asset ID - allows files to move freely
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
                    # Remove location from search index
                    self.search_handler.search_db.remove_location(content_hash, file_path)
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
                message="Soft delete operation failed",
                data=None,
                error=str(e)
            )
