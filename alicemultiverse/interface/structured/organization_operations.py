"""Organization operations for structured interface."""

import logging

from ...core.exceptions import ValidationError
from ...organizer.enhanced_organizer import EnhancedMediaOrganizer
from ..structured_models import (
    AliceResponse,
    GroupingRequest,
    OrganizeRequest,
    SearchRequest,
    TagUpdateRequest,
)
from ..validation import (
    validate_grouping_request,
    validate_organize_request,
    validate_tag_update_request,
)

logger = logging.getLogger(__name__)


class OrganizationOperationsMixin:
    """Mixin for media organization operations."""

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
                # Quality assessment deprecated - ignored
                pass
            if request.get("understanding") is not None:
                self.config.processing.understanding = request["understanding"]
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
