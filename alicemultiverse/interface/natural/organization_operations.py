"""Organization operations for natural language interface."""

import logging

from ...core.ai_errors import AIFriendlyError
from ...organizer.enhanced_organizer import EnhancedMediaOrganizer
from ..models import GroupRequest, OrganizeRequest, TagRequest
from .base import AliceResponse

logger = logging.getLogger(__name__)


class OrganizationOperationsMixin:
    """Mixin for media organization operations."""

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

            # TODO: Review unreachable code - # Update config based on request
            # TODO: Review unreachable code - if request.get("source_path"):
            # TODO: Review unreachable code - self.config.paths.inbox = request["source_path"]
            # TODO: Review unreachable code - if request.get("quality_assessment"):
            # TODO: Review unreachable code - # Quality assessment deprecated - ignored
            # TODO: Review unreachable code - pass
            # TODO: Review unreachable code - if request.get("understanding"):
            # TODO: Review unreachable code - self.config.processing.understanding = True
            # TODO: Review unreachable code - if request.get("watch_mode"):
            # TODO: Review unreachable code - self.config.processing.watch = True

            # TODO: Review unreachable code - # Recreate organizer with updated config
            # TODO: Review unreachable code - self.organizer = EnhancedMediaOrganizer(self.config)

            # TODO: Review unreachable code - # Run organization
            # TODO: Review unreachable code - success = self.organizer.organize()

            # TODO: Review unreachable code - # Get summary
            # TODO: Review unreachable code - summary = self.organizer.get_organization_summary()

            # TODO: Review unreachable code - # Persist to database
            # TODO: Review unreachable code - if success:
            # TODO: Review unreachable code - self._persist_organized_assets()

            # TODO: Review unreachable code - return AliceResponse(
            # TODO: Review unreachable code - success=success,
            # TODO: Review unreachable code - message=summary,
            # TODO: Review unreachable code - data={
            # TODO: Review unreachable code - "stats": self.organizer.stats,
            # TODO: Review unreachable code - "metadata_count": len(self.organizer.metadata_cache.get_all_metadata()),
            # TODO: Review unreachable code - },
            # TODO: Review unreachable code - error=None,
            # TODO: Review unreachable code - )

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
            # TODO: Review unreachable code - self._ensure_organizer()

            # TODO: Review unreachable code - success_count = 0
            # TODO: Review unreachable code - tags = request["tags"]

            # TODO: Review unreachable code - # If we have the asset repository, use it for structured tags
            # TODO: Review unreachable code - if self.asset_repo and isinstance(tags, dict):
            # TODO: Review unreachable code - # New structured format
            # TODO: Review unreachable code - for asset_id in request["asset_ids"]:
            # TODO: Review unreachable code - asset_success = True
            # TODO: Review unreachable code - for tag_type, tag_values in tags.items():
            # TODO: Review unreachable code - for tag_value in tag_values:
            # TODO: Review unreachable code - if not self.asset_repo.add_tag(
            # TODO: Review unreachable code - content_hash=asset_id,
            # TODO: Review unreachable code - tag_type=tag_type,
            # TODO: Review unreachable code - tag_value=tag_value,
            # TODO: Review unreachable code - source="ai"
            # TODO: Review unreachable code - ):
            # TODO: Review unreachable code - asset_success = False
            # TODO: Review unreachable code - break
            # TODO: Review unreachable code - if not asset_success:
            # TODO: Review unreachable code - break
            # TODO: Review unreachable code - if asset_success:
            # TODO: Review unreachable code - success_count += 1
            # TODO: Review unreachable code - else:
            # TODO: Review unreachable code - # Legacy format or no database
            # TODO: Review unreachable code - tag_type = request.get("tag_type", "custom")
            # TODO: Review unreachable code - tag_list = tags if isinstance(tags, list) else []

            # TODO: Review unreachable code - for asset_id in request["asset_ids"]:
            # TODO: Review unreachable code - if self.organizer.tag_asset(asset_id, tag_list, tag_type):
            # TODO: Review unreachable code - success_count += 1

            # TODO: Review unreachable code - return AliceResponse(
            # TODO: Review unreachable code - success=success_count > 0,
            # TODO: Review unreachable code - message=f"Tagged {success_count}/{len(request['asset_ids'])} assets",
            # TODO: Review unreachable code - data={"tagged_count": success_count},
            # TODO: Review unreachable code - error=None,
            # TODO: Review unreachable code - )

        except Exception as e:
            logger.error(f"Tagging failed: {e}")
            return AliceResponse(success=False, message="Tagging failed", data=None, error=str(e))

    # TODO: Review unreachable code - def group_assets(self, request: GroupRequest) -> AliceResponse:
    # TODO: Review unreachable code - """Group assets together.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - request: Grouping request

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Response indicating success
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if self.initialization_error:
    # TODO: Review unreachable code - raise self.initialization_error
    # TODO: Review unreachable code - self._ensure_organizer()

    # TODO: Review unreachable code - success = self.organizer.group_assets(request["asset_ids"], request["group_name"])

    # TODO: Review unreachable code - return AliceResponse(
    # TODO: Review unreachable code - success=success,
    # TODO: Review unreachable code - message=f"Grouped {len(request['asset_ids'])} assets as '{request['group_name']}'",
    # TODO: Review unreachable code - data={"group_name": request["group_name"]},
    # TODO: Review unreachable code - error=None,
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Grouping failed: {e}")
    # TODO: Review unreachable code - return AliceResponse(success=False, message="Grouping failed", data=None, error=str(e))
