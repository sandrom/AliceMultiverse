"""Search operations for natural language interface."""
from typing import TYPE_CHECKING, Any

import logging

from ...assets.metadata.models import AssetRole
from ...core.ai_errors import AIFriendlyError
from ..models import SearchRequest
from .base import AliceResponse

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from ...core.protocols import HasOrganizer, HasSearchHandler

class SearchOperationsMixin:
    """Mixin for search-related operations."""

    if TYPE_CHECKING:
        # Type hints for mypy
        search_handler: Any
        organizer: Any


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
            # TODO: Review unreachable code - self._ensure_organizer()

            # TODO: Review unreachable code - # Build search query
            # TODO: Review unreachable code - query_params = {}

            # TODO: Review unreachable code - # Handle natural language description
            # TODO: Review unreachable code - if request.get("description"):
            # TODO: Review unreachable code - # Use description search if search engine is available
            # TODO: Review unreachable code - if self.organizer.search_engine:
            # TODO: Review unreachable code - results = self.organizer.search_engine.search_by_description(
            # TODO: Review unreachable code - request["description"], limit=request.get("limit", 20)
            # TODO: Review unreachable code - )
            # TODO: Review unreachable code - else:
            # TODO: Review unreachable code - # Fallback to basic search
            # TODO: Review unreachable code - results = []
            # TODO: Review unreachable code - else:
            # TODO: Review unreachable code - # Build structured query
            # TODO: Review unreachable code - if request.get("time_reference"):
            # TODO: Review unreachable code - start_time = self._parse_time_reference(request["time_reference"])
            # TODO: Review unreachable code - if start_time:
            # TODO: Review unreachable code - query_params["timeframe_start"] = start_time

            # TODO: Review unreachable code - # Add tag filters
            # TODO: Review unreachable code - if request.get("style_tags"):
            # TODO: Review unreachable code - query_params["style_tags"] = request["style_tags"]
            # TODO: Review unreachable code - if request.get("mood_tags"):
            # TODO: Review unreachable code - query_params["mood_tags"] = request["mood_tags"]
            # TODO: Review unreachable code - if request.get("subject_tags"):
            # TODO: Review unreachable code - query_params["subject_tags"] = request["subject_tags"]

            # TODO: Review unreachable code - # Add other filters
            # TODO: Review unreachable code - if request.get("source_types"):
            # TODO: Review unreachable code - query_params["source_types"] = request["source_types"]
            # TODO: Review unreachable code - if request.get("min_quality_stars"):
            # TODO: Review unreachable code - query_params["min_stars"] = request["min_quality_stars"]
            # TODO: Review unreachable code - if request.get("roles"):
            # TODO: Review unreachable code - query_params["roles"] = [AssetRole(r) for r in request["roles"]]

            # TODO: Review unreachable code - # Add options
            # TODO: Review unreachable code - query_params["sort_by"] = request.get("sort_by", "relevance")
            # TODO: Review unreachable code - query_params["limit"] = request.get("limit", 20)

            # TODO: Review unreachable code - # Try database search first
            # TODO: Review unreachable code - # Build structured tags for database search
            # TODO: Review unreachable code - structured_tags = {}
            # TODO: Review unreachable code - if request.get("style_tags"):
            # TODO: Review unreachable code - structured_tags["style"] = request.get("style_tags", [])
            # TODO: Review unreachable code - if request.get("mood_tags"):
            # TODO: Review unreachable code - structured_tags["mood"] = request.get("mood_tags", [])
            # TODO: Review unreachable code - if request.get("subject_tags"):
            # TODO: Review unreachable code - structured_tags["subject"] = request.get("subject_tags", [])

            # TODO: Review unreachable code - db_results = self._search_database(
            # TODO: Review unreachable code - tags=structured_tags if structured_tags else None,
            # TODO: Review unreachable code - tag_mode=request.get("tag_mode", "any"),
            # TODO: Review unreachable code - source_types=request.get("source_types"),
            # TODO: Review unreachable code - min_quality=request.get("min_quality_stars"),
            # TODO: Review unreachable code - roles=request.get("roles"),
            # TODO: Review unreachable code - limit=request.get("limit", 20)
            # TODO: Review unreachable code - )

            # TODO: Review unreachable code - # Fallback to organizer search if available
            # TODO: Review unreachable code - if not db_results and self.organizer.search_engine:
            # TODO: Review unreachable code - results = self.organizer.search_assets(**query_params)
            # TODO: Review unreachable code - else:
            # TODO: Review unreachable code - results = db_results

            # TODO: Review unreachable code - # Simplify results for AI
            # TODO: Review unreachable code - simplified_results = [self._simplify_asset_info(asset) for asset in results]

            # TODO: Review unreachable code - return AliceResponse(
            # TODO: Review unreachable code - success=True,
            # TODO: Review unreachable code - message=f"Found {len(results)} assets",
            # TODO: Review unreachable code - data=simplified_results,
            # TODO: Review unreachable code - error=None,
            # TODO: Review unreachable code - )

        except Exception as e:
            logger.error(f"Search failed: {e}")
            friendly = AIFriendlyError.make_friendly(e, {"operation": "search", "request": request})
            return AliceResponse(
                success=False,
                message=friendly["error"],
                data={"suggestions": friendly["suggestions"]},
                error=friendly["technical_details"]
            )

    def find_similar_assets(self, asset_id: str, threshold: float = 0.7) -> AliceResponse:
        """Find assets similar to a given asset.

        Args:
            asset_id: ID of the reference asset
            threshold: Similarity threshold (0-1)

        Returns:
            Response with similar assets
        """
        try:
            if self.initialization_error:
                raise self.initialization_error
            # TODO: Review unreachable code - self._ensure_organizer()

            # TODO: Review unreachable code - # Find the reference asset first
            # TODO: Review unreachable code - reference_asset = None
            # TODO: Review unreachable code - all_metadata = self.organizer.metadata_cache.get_all_metadata()

            # TODO: Review unreachable code - for file_path, metadata in all_metadata.items():
            # TODO: Review unreachable code - if metadata.get("asset_id") == asset_id or metadata.get("file_hash") == asset_id:
            # TODO: Review unreachable code - reference_asset = metadata
            # TODO: Review unreachable code - reference_asset["file_path"] = str(file_path)
            # TODO: Review unreachable code - break

            # TODO: Review unreachable code - if not reference_asset:
            # TODO: Review unreachable code - return AliceResponse(
            # TODO: Review unreachable code - success=False,
            # TODO: Review unreachable code - message=f"Reference asset {asset_id} not found",
            # TODO: Review unreachable code - data=None,
            # TODO: Review unreachable code - error="Asset not found"
            # TODO: Review unreachable code - )

            # TODO: Review unreachable code - # Build similarity query based on reference asset
            # TODO: Review unreachable code - similar_query = SearchRequest(
            # TODO: Review unreachable code - style_tags=reference_asset.get("style_tags", []),
            # TODO: Review unreachable code - mood_tags=reference_asset.get("mood_tags", []),
            # TODO: Review unreachable code - subject_tags=reference_asset.get("subject_tags", []),
            # TODO: Review unreachable code - source_types=[reference_asset.get("source_type", "unknown")],
            # TODO: Review unreachable code - limit=10
            # TODO: Review unreachable code - )

            # TODO: Review unreachable code - # Search for similar assets
            # TODO: Review unreachable code - search_response = self.search_assets(similar_query)

            # TODO: Review unreachable code - if search_response is not None and search_response["success"]:
            # TODO: Review unreachable code - # Filter out the reference asset itself
            # TODO: Review unreachable code - similar_assets = [
            # TODO: Review unreachable code - asset for asset in search_response["data"]
            # TODO: Review unreachable code - if asset is not None and asset["id"] != asset_id
            # TODO: Review unreachable code - ]

            # TODO: Review unreachable code - return AliceResponse(
            # TODO: Review unreachable code - success=True,
            # TODO: Review unreachable code - message=f"Found {len(similar_assets)} similar assets",
            # TODO: Review unreachable code - data={
            # TODO: Review unreachable code - "reference": self._simplify_asset_info(reference_asset),
            # TODO: Review unreachable code - "similar": similar_assets
            # TODO: Review unreachable code - },
            # TODO: Review unreachable code - error=None
            # TODO: Review unreachable code - )
            # TODO: Review unreachable code - else:
            # TODO: Review unreachable code - return search_response

        except Exception as e:
            logger.error(f"Similar search failed: {e}")
            friendly = AIFriendlyError.make_friendly(
                e, {"operation": "find_similar", "asset_id": asset_id}
            )
            return AliceResponse(
                success=False,
                message=friendly["error"],
                data={"suggestions": friendly["suggestions"]},
                error=friendly["technical_details"]
            )
