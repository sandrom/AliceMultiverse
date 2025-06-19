"""Optimized search handler for Alice interface."""

import logging
from datetime import datetime
from pathlib import Path

from ..storage.file_cache import FileCache
from ..storage.unified_duckdb import DuckDBSearch
from .structured_models import (
    Asset,
    MediaType,
    SearchFacet,
    SearchFacets,
    SearchRequest,
    SearchResponse,
)

logger = logging.getLogger(__name__)


class OptimizedSearchHandler:
    """Handles search operations with database optimization."""

    def __init__(self, db_path: str = None, config=None) -> None:
        """Initialize search handler.

        Args:
            db_path: Path to DuckDB database file. If None, uses config or local test path.
            config: Optional configuration object
        """
        # Initialize DuckDB search
        if not db_path:
            if config and hasattr(config, 'storage') and hasattr(config.storage, 'search_db'):
                db_path = config.storage.search_db
            else:
                # Default to data directory
                db_path = "data/search.duckdb"

        # Ensure parent directory exists
        db_path = Path(db_path)
        db_path.parent.mkdir(parents=True, exist_ok=True)

        self.search_db = DuckDBSearch(db_path)

        # Initialize file-based cache (simpler for personal tool)
        self.cache = FileCache(
            prefix="alice_search",
            ttl=300  # 5 minutes for search results
        )

        logger.info(f"Search handler initialized with DuckDB at {db_path}")

    def search_assets(self, request: SearchRequest) -> SearchResponse:
        """Execute optimized search query.

        Args:
            request: Search request

        Returns:
            Search response with results
        """
        start_time = datetime.now()

        # Check cache first
        cache_key = self._build_cache_key(request)
        cached_result = self.cache.get_search_results(cache_key)

        if cached_result:
            logger.debug("Cache hit for search query")
            # Convert cached database models back to API format
            api_results = []
            for asset_data in cached_result.get("results", []):
                # asset_data is already a dictionary from DuckDB
                api_results.append(self._convert_db_to_api_asset(asset_data))

            return SearchResponse(
                total_count=cached_result.get("total_count", 0),
                results=api_results,
                facets=cached_result.get("facets", SearchFacets()),
                query_time_ms=1  # Indicate cache hit with fast response
            )

        filters = request.get("filters", {})

        # Build database query parameters
        db_params = {
            "limit": min(request.get("limit", 50), 1000),
            "offset": request.get("offset", 0),
        }

        # Map filters to database parameters
        if filters.get("media_type"):
            # Handle both enum and string values
            media_type = filters["media_type"]
            if db_params is not None:
                db_params["media_type"] = media_type.value if hasattr(media_type, 'value') else media_type

        if filters.get("quality_rating"):
            quality_range = filters["quality_rating"]
            if quality_range.get("min"):
                if db_params is not None:
                    db_params["min_rating"] = quality_range["min"]

        if filters.get("ai_source"):
            # Handle both single and multiple sources
            sources = filters["ai_source"]
            if isinstance(sources, str) or isinstance(sources, list):
                if db_params is not None:
                    db_params["ai_source"] = sources
            # DuckDB supports multiple sources in one query

        # Handle tag filters
        if filters.get("tags") or filters.get("any_tags"):
            # Combine all tags for now
            all_tags = []
            if filters.get("tags"):
                all_tags.extend(filters["tags"])
            if filters.get("any_tags"):
                all_tags.extend(filters["any_tags"])

            # Convert to dict format for advanced tag handling
            if all_tags:
                # For now, treat all as custom tags
                if db_params is not None:
                    db_params["tags"] = {"custom": all_tags}
                db_params["tag_mode"] = "any" if filters.get("any_tags") else "all"

        # Execute search with DuckDB
        try:
            assets, total_count = self.search_db.search(
                filters=filters,
                sort_by=request.get("sort_by", "created_at"),
                order=request.get("order", "desc"),
                limit=db_params["limit"],
                offset=db_params["offset"]
            )
        except Exception as e:
            logger.error(f"Search failed: {e}")
            assets = []
            total_count = 0

        # Convert database models to API models
        api_results = []
        for db_asset in assets:
            api_asset = self._convert_db_to_api_asset(db_asset)

            # Apply additional filters that database doesn't support
            if self._apply_additional_filters(api_asset, filters):
                api_results.append(api_asset)

        # Calculate facets from results
        facets = self._calculate_facets(assets)

        # Calculate query time
        query_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)

        response = SearchResponse(
            total_count=total_count,
            results=api_results,
            facets=facets,
            query_time_ms=query_time_ms
        )

        # Cache the results
        if self.cache.is_available and len(assets) > 0:
            # Prepare serializable version of results
            cache_data = {
                "results": [self._serialize_db_asset(asset) for asset in assets],
                "total_count": total_count,
                "facets": facets
            }
            self.cache.cache_search_results(cache_key, cache_data["results"], total_count)

        return response

    # TODO: Review unreachable code - def _convert_db_to_api_asset(self, db_asset: dict) -> Asset:
    # TODO: Review unreachable code - """Convert database asset to API asset model.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - db_asset: Database asset dictionary from DuckDB

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - API asset model
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # DuckDB returns a dictionary, not an object
    # TODO: Review unreachable code - tags = db_asset.get("tags", [])

    # TODO: Review unreachable code - # Extract metadata
    # TODO: Review unreachable code - metadata = db_asset.get("metadata", {})
    # TODO: Review unreachable code - generation_params = db_asset.get("generation_params", {})

    # TODO: Review unreachable code - # Get dimensions
    # TODO: Review unreachable code - dimensions = db_asset.get("dimensions")
    # TODO: Review unreachable code - if not dimensions and db_asset.get("width") and db_asset.get("height"):
    # TODO: Review unreachable code - dimensions = {
    # TODO: Review unreachable code - "width": db_asset["width"],
    # TODO: Review unreachable code - "height": db_asset["height"]
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - return Asset(
    # TODO: Review unreachable code - content_hash=db_asset["content_hash"],
    # TODO: Review unreachable code - file_path=db_asset.get("file_path", ""),
    # TODO: Review unreachable code - media_type=MediaType(db_asset.get("media_type", "unknown")),
    # TODO: Review unreachable code - file_size=db_asset.get("file_size", 0),
    # TODO: Review unreachable code - tags=tags,
    # TODO: Review unreachable code - ai_source=db_asset.get("ai_source"),
    # TODO: Review unreachable code - quality_rating=db_asset.get("quality_rating"),
    # TODO: Review unreachable code - created_at=db_asset.get("created_at", datetime.now().isoformat()),
    # TODO: Review unreachable code - modified_at=db_asset.get("modified_at", datetime.now().isoformat()),
    # TODO: Review unreachable code - discovered_at=db_asset.get("discovered_at", datetime.now().isoformat()),
    # TODO: Review unreachable code - metadata={
    # TODO: Review unreachable code - "dimensions": dimensions,
    # TODO: Review unreachable code - "prompt": db_asset.get("prompt") or metadata.get("prompt") or generation_params.get("prompt"),
    # TODO: Review unreachable code - "generation_params": generation_params,
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _apply_additional_filters(self, asset: Asset, filters: dict) -> bool:
    # TODO: Review unreachable code - """Apply filters that aren't supported by database query.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - asset: API asset model
    # TODO: Review unreachable code - filters: Filter criteria

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - True if asset passes all filters
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # File format filter
    # TODO: Review unreachable code - if filters.get("file_formats"):
    # TODO: Review unreachable code - file_ext = Path(asset["file_path"]).suffix[1:].lower()
    # TODO: Review unreachable code - if file_ext not in filters["file_formats"]:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - # File size filter
    # TODO: Review unreachable code - if filters.get("file_size"):
    # TODO: Review unreachable code - size_range = filters["file_size"]
    # TODO: Review unreachable code - if size_range.get("min") and asset["file_size"] < size_range["min"]:
    # TODO: Review unreachable code - return False
    # TODO: Review unreachable code - if size_range.get("max") and asset["file_size"] > size_range["max"]:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - # Dimension filters
    # TODO: Review unreachable code - if filters.get("dimensions"):
    # TODO: Review unreachable code - dims = filters["dimensions"]
    # TODO: Review unreachable code - metadata = asset.get("metadata", {})
    # TODO: Review unreachable code - dimensions = metadata.get("dimensions", {})

    # TODO: Review unreachable code - if dims.get("width"):
    # TODO: Review unreachable code - width = dimensions.get("width", 0)
    # TODO: Review unreachable code - if dims is not None and dims["width"].get("min") and width < dims["width"]["min"]:
    # TODO: Review unreachable code - return False
    # TODO: Review unreachable code - if dims is not None and dims["width"].get("max") and width > dims["width"]["max"]:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - if dims.get("height"):
    # TODO: Review unreachable code - height = dimensions.get("height", 0)
    # TODO: Review unreachable code - if dims is not None and dims["height"].get("min") and height < dims["height"]["min"]:
    # TODO: Review unreachable code - return False
    # TODO: Review unreachable code - if dims is not None and dims["height"].get("max") and height > dims["height"]["max"]:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - # Filename pattern filter
    # TODO: Review unreachable code - if filters.get("filename_pattern"):
    # TODO: Review unreachable code - import re
    # TODO: Review unreachable code - filename = Path(asset["file_path"]).name
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if not re.search(filters["filename_pattern"], filename, re.IGNORECASE):
    # TODO: Review unreachable code - return False
    # TODO: Review unreachable code - except re.error:
    # TODO: Review unreachable code - logger.warning(f"Invalid regex pattern: {filters['filename_pattern']}")

    # TODO: Review unreachable code - # Prompt keywords filter
    # TODO: Review unreachable code - if filters.get("prompt_keywords"):
    # TODO: Review unreachable code - prompt = (asset.get("metadata", {}).get("prompt") or "").lower()
    # TODO: Review unreachable code - if not all(keyword.lower() in prompt for keyword in filters["prompt_keywords"]):
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - def _calculate_facets(self, assets: list[dict]) -> SearchFacets:
    # TODO: Review unreachable code - """Calculate facets from database results.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - assets: Database asset dictionaries from DuckDB

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Search facets
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # For better performance, get facets directly from DuckDB
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - return self.search_db.get_facets(filters=None)
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.warning(f"Failed to get facets from DuckDB: {e}")

    # TODO: Review unreachable code - # Fallback to calculating from results
    # TODO: Review unreachable code - tag_counts = {}
    # TODO: Review unreachable code - source_counts = {}
    # TODO: Review unreachable code - quality_counts = {}
    # TODO: Review unreachable code - type_counts = {}

    # TODO: Review unreachable code - for asset in assets:
    # TODO: Review unreachable code - # Count tags
    # TODO: Review unreachable code - for tag in asset.get("tags", []):
    # TODO: Review unreachable code - tag_counts[tag] = tag_counts.get(tag, 0) + 1

    # TODO: Review unreachable code - # Count sources
    # TODO: Review unreachable code - ai_source = asset.get("ai_source")
    # TODO: Review unreachable code - if ai_source:
    # TODO: Review unreachable code - source_counts[ai_source] = source_counts.get(ai_source, 0) + 1

    # TODO: Review unreachable code - # Count quality ratings
    # TODO: Review unreachable code - rating = asset.get("quality_rating")
    # TODO: Review unreachable code - if rating is not None:
    # TODO: Review unreachable code - # Convert to star rating
    # TODO: Review unreachable code - if rating >= 80:
    # TODO: Review unreachable code - star_rating = "5"
    # TODO: Review unreachable code - elif rating >= 60:
    # TODO: Review unreachable code - star_rating = "4"
    # TODO: Review unreachable code - elif rating >= 40:
    # TODO: Review unreachable code - star_rating = "3"
    # TODO: Review unreachable code - elif rating >= 20:
    # TODO: Review unreachable code - star_rating = "2"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - star_rating = "1"
    # TODO: Review unreachable code - quality_counts[star_rating] = quality_counts.get(star_rating, 0) + 1

    # TODO: Review unreachable code - # Count media types
    # TODO: Review unreachable code - media_type = asset.get("media_type")
    # TODO: Review unreachable code - if media_type:
    # TODO: Review unreachable code - type_counts[media_type] = type_counts.get(media_type, 0) + 1

    # TODO: Review unreachable code - return SearchFacets(
    # TODO: Review unreachable code - tags=[
    # TODO: Review unreachable code - SearchFacet(value=tag, count=count)
    # TODO: Review unreachable code - for tag, count in sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)[:20]
    # TODO: Review unreachable code - ],
    # TODO: Review unreachable code - ai_sources=[
    # TODO: Review unreachable code - SearchFacet(value=source, count=count)
    # TODO: Review unreachable code - for source, count in sorted(source_counts.items(), key=lambda x: x[1], reverse=True)
    # TODO: Review unreachable code - ],
    # TODO: Review unreachable code - quality_ratings=[
    # TODO: Review unreachable code - SearchFacet(value=rating, count=count)
    # TODO: Review unreachable code - for rating, count in sorted(quality_counts.items())
    # TODO: Review unreachable code - ],
    # TODO: Review unreachable code - media_types=[
    # TODO: Review unreachable code - SearchFacet(value=media_type, count=count)
    # TODO: Review unreachable code - for media_type, count in sorted(type_counts.items(), key=lambda x: x[1], reverse=True)
    # TODO: Review unreachable code - ]
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def _build_cache_key(self, request: SearchRequest) -> dict:
    # TODO: Review unreachable code - """Build cache key from search request.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - request: Search request

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Cache key dictionary
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Extract relevant parts for caching
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "filters": request.get("filters", {}),
    # TODO: Review unreachable code - "sort_by": request.get("sort_by", "created"),
    # TODO: Review unreachable code - "order": request.get("order", "desc"),
    # TODO: Review unreachable code - "limit": request.get("limit", 50),
    # TODO: Review unreachable code - "offset": request.get("offset", 0)
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - def _serialize_db_asset(self, asset: dict) -> dict:
    # TODO: Review unreachable code - """Serialize database asset for caching.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - asset: Database asset dictionary from DuckDB

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Serializable dictionary
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # DuckDB already returns a dictionary, just ensure timestamps are serializable
    # TODO: Review unreachable code - serialized = asset.copy()

    # TODO: Review unreachable code - # Convert datetime objects to ISO format strings for JSON serialization
    # TODO: Review unreachable code - for field in ["created_at", "modified_at", "discovered_at", "first_seen", "last_seen"]:
    # TODO: Review unreachable code - if field in serialized and hasattr(serialized[field], "isoformat"):
    # TODO: Review unreachable code - serialized[field] = serialized[field].isoformat()

    # TODO: Review unreachable code - return serialized

    # TODO: Review unreachable code - def rebuild_index(self, paths: list[Path]) -> int:
    # TODO: Review unreachable code - """Rebuild the search index from files.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - paths: List of paths to scan for media files

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Number of files indexed
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Clear Redis cache since we're rebuilding
    # TODO: Review unreachable code - self.cache.clear_namespace("search")

    # TODO: Review unreachable code - # Rebuild DuckDB index
    # TODO: Review unreachable code - return self.search_db.rebuild_from_files(paths)

    # TODO: Review unreachable code - def index_asset(self, metadata: dict) -> None:
    # TODO: Review unreachable code - """Index a single asset.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - metadata: Asset metadata to index
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Clear relevant cache entries
    # TODO: Review unreachable code - self.cache.clear_namespace("search")

    # TODO: Review unreachable code - # Index in DuckDB
    # TODO: Review unreachable code - self.search_db.index_asset(metadata)

    # TODO: Review unreachable code - def get_statistics(self) -> dict:
    # TODO: Review unreachable code - """Get search index statistics.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dictionary with statistics
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - return self.search_db.get_statistics()
