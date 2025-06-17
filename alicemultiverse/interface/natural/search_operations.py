"""Search operations for natural language interface."""

import logging

from ...core.ai_errors import AIFriendlyError
from ...assets.metadata.models import AssetRole
from ..models import SearchRequest
from .base import AliceResponse

logger = logging.getLogger(__name__)


class SearchOperationsMixin:
    """Mixin for search-related operations."""
    
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
            self._ensure_organizer()

            # Find the reference asset first
            reference_asset = None
            all_metadata = self.organizer.metadata_cache.get_all_metadata()

            for file_path, metadata in all_metadata.items():
                if metadata.get("asset_id") == asset_id or metadata.get("file_hash") == asset_id:
                    reference_asset = metadata
                    reference_asset["file_path"] = str(file_path)
                    break

            if not reference_asset:
                return AliceResponse(
                    success=False,
                    message=f"Reference asset {asset_id} not found",
                    data=None,
                    error="Asset not found"
                )

            # Build similarity query based on reference asset
            similar_query = SearchRequest(
                style_tags=reference_asset.get("style_tags", []),
                mood_tags=reference_asset.get("mood_tags", []),
                subject_tags=reference_asset.get("subject_tags", []),
                source_types=[reference_asset.get("source_type", "unknown")],
                limit=10
            )

            # Search for similar assets
            search_response = self.search_assets(similar_query)

            if search_response["success"]:
                # Filter out the reference asset itself
                similar_assets = [
                    asset for asset in search_response["data"]
                    if asset["id"] != asset_id
                ]

                return AliceResponse(
                    success=True,
                    message=f"Found {len(similar_assets)} similar assets",
                    data={
                        "reference": self._simplify_asset_info(reference_asset),
                        "similar": similar_assets
                    },
                    error=None
                )
            else:
                return search_response

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