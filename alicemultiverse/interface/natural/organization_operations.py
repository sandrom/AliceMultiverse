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

            # Update config based on request
            if request.get("source_path"):
                self.config.paths.inbox = request["source_path"]
            if request.get("quality_assessment"):
                # Quality assessment deprecated - ignored
                pass
            if request.get("understanding"):
                self.config.processing.understanding = True
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