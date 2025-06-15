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

    def __init__(self, db_path: str = None, config=None):
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
            db_params["media_type"] = media_type.value if hasattr(media_type, 'value') else media_type

        if filters.get("quality_rating"):
            quality_range = filters["quality_rating"]
            if quality_range.get("min"):
                db_params["min_rating"] = quality_range["min"]

        if filters.get("ai_source"):
            # Handle both single and multiple sources
            sources = filters["ai_source"]
            if isinstance(sources, str) or isinstance(sources, list):
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

    def _convert_db_to_api_asset(self, db_asset: dict) -> Asset:
        """Convert database asset to API asset model.
        
        Args:
            db_asset: Database asset dictionary from DuckDB
            
        Returns:
            API asset model
        """
        # DuckDB returns a dictionary, not an object
        tags = db_asset.get("tags", [])

        # Extract metadata
        metadata = db_asset.get("metadata", {})
        generation_params = db_asset.get("generation_params", {})

        # Get dimensions
        dimensions = db_asset.get("dimensions")
        if not dimensions and db_asset.get("width") and db_asset.get("height"):
            dimensions = {
                "width": db_asset["width"],
                "height": db_asset["height"]
            }

        return Asset(
            content_hash=db_asset["content_hash"],
            file_path=db_asset.get("file_path", ""),
            media_type=MediaType(db_asset.get("media_type", "unknown")),
            file_size=db_asset.get("file_size", 0),
            tags=tags,
            ai_source=db_asset.get("ai_source"),
            quality_rating=db_asset.get("quality_rating"),
            created_at=db_asset.get("created_at", datetime.now().isoformat()),
            modified_at=db_asset.get("modified_at", datetime.now().isoformat()),
            discovered_at=db_asset.get("discovered_at", datetime.now().isoformat()),
            metadata={
                "dimensions": dimensions,
                "prompt": db_asset.get("prompt") or metadata.get("prompt") or generation_params.get("prompt"),
                "generation_params": generation_params,
            }
        )

    def _apply_additional_filters(self, asset: Asset, filters: dict) -> bool:
        """Apply filters that aren't supported by database query.
        
        Args:
            asset: API asset model
            filters: Filter criteria
            
        Returns:
            True if asset passes all filters
        """
        # File format filter
        if filters.get("file_formats"):
            file_ext = Path(asset["file_path"]).suffix[1:].lower()
            if file_ext not in filters["file_formats"]:
                return False

        # File size filter
        if filters.get("file_size"):
            size_range = filters["file_size"]
            if size_range.get("min") and asset["file_size"] < size_range["min"]:
                return False
            if size_range.get("max") and asset["file_size"] > size_range["max"]:
                return False

        # Dimension filters
        if filters.get("dimensions"):
            dims = filters["dimensions"]
            metadata = asset.get("metadata", {})
            dimensions = metadata.get("dimensions", {})

            if dims.get("width"):
                width = dimensions.get("width", 0)
                if dims["width"].get("min") and width < dims["width"]["min"]:
                    return False
                if dims["width"].get("max") and width > dims["width"]["max"]:
                    return False

            if dims.get("height"):
                height = dimensions.get("height", 0)
                if dims["height"].get("min") and height < dims["height"]["min"]:
                    return False
                if dims["height"].get("max") and height > dims["height"]["max"]:
                    return False

        # Filename pattern filter
        if filters.get("filename_pattern"):
            import re
            filename = Path(asset["file_path"]).name
            try:
                if not re.search(filters["filename_pattern"], filename, re.IGNORECASE):
                    return False
            except re.error:
                logger.warning(f"Invalid regex pattern: {filters['filename_pattern']}")

        # Prompt keywords filter
        if filters.get("prompt_keywords"):
            prompt = (asset.get("metadata", {}).get("prompt") or "").lower()
            if not all(keyword.lower() in prompt for keyword in filters["prompt_keywords"]):
                return False

        return True

    def _calculate_facets(self, assets: list[dict]) -> SearchFacets:
        """Calculate facets from database results.
        
        Args:
            assets: Database asset dictionaries from DuckDB
            
        Returns:
            Search facets
        """
        # For better performance, get facets directly from DuckDB
        try:
            return self.search_db.get_facets(filters=None)
        except Exception as e:
            logger.warning(f"Failed to get facets from DuckDB: {e}")

            # Fallback to calculating from results
            tag_counts = {}
            source_counts = {}
            quality_counts = {}
            type_counts = {}

            for asset in assets:
                # Count tags
                for tag in asset.get("tags", []):
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

                # Count sources
                ai_source = asset.get("ai_source")
                if ai_source:
                    source_counts[ai_source] = source_counts.get(ai_source, 0) + 1

                # Count quality ratings
                rating = asset.get("quality_rating")
                if rating is not None:
                    # Convert to star rating
                    if rating >= 80:
                        star_rating = "5"
                    elif rating >= 60:
                        star_rating = "4"
                    elif rating >= 40:
                        star_rating = "3"
                    elif rating >= 20:
                        star_rating = "2"
                    else:
                        star_rating = "1"
                    quality_counts[star_rating] = quality_counts.get(star_rating, 0) + 1

                # Count media types
                media_type = asset.get("media_type")
                if media_type:
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

    def _build_cache_key(self, request: SearchRequest) -> dict:
        """Build cache key from search request.
        
        Args:
            request: Search request
            
        Returns:
            Cache key dictionary
        """
        # Extract relevant parts for caching
        return {
            "filters": request.get("filters", {}),
            "sort_by": request.get("sort_by", "created"),
            "order": request.get("order", "desc"),
            "limit": request.get("limit", 50),
            "offset": request.get("offset", 0)
        }

    def _serialize_db_asset(self, asset: dict) -> dict:
        """Serialize database asset for caching.
        
        Args:
            asset: Database asset dictionary from DuckDB
            
        Returns:
            Serializable dictionary
        """
        # DuckDB already returns a dictionary, just ensure timestamps are serializable
        serialized = asset.copy()

        # Convert datetime objects to ISO format strings for JSON serialization
        for field in ["created_at", "modified_at", "discovered_at", "first_seen", "last_seen"]:
            if field in serialized and hasattr(serialized[field], "isoformat"):
                serialized[field] = serialized[field].isoformat()

        return serialized

    def rebuild_index(self, paths: list[Path]) -> int:
        """Rebuild the search index from files.
        
        Args:
            paths: List of paths to scan for media files
            
        Returns:
            Number of files indexed
        """
        # Clear Redis cache since we're rebuilding
        self.cache.clear_namespace("search")

        # Rebuild DuckDB index
        return self.search_db.rebuild_from_files(paths)

    def index_asset(self, metadata: dict) -> None:
        """Index a single asset.
        
        Args:
            metadata: Asset metadata to index
        """
        # Clear relevant cache entries
        self.cache.clear_namespace("search")

        # Index in DuckDB
        self.search_db.index_asset(metadata)

    def get_statistics(self) -> dict:
        """Get search index statistics.
        
        Returns:
            Dictionary with statistics
        """
        return self.search_db.get_statistics()
