"""Optimized search handler for Alice interface."""

import logging
import os
from datetime import datetime
from pathlib import Path

# PostgreSQL removed - using DuckDB for search
# from ..database.repository import AssetRepository
# from ..database.models import Asset as DBAsset
from ..database.cache import RedisCache
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
    
    def __init__(self):
        """Initialize search handler."""
        # PostgreSQL removed - would use DuckDB for search
        # self.repo = AssetRepository()
        
        # Initialize Redis cache
        self.cache = RedisCache(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            password=os.getenv("REDIS_PASSWORD"),
            prefix="alice",
            ttl=300  # 5 minutes for search results
        )
        
        # TODO: Initialize DuckDB connection for search
        logger.warning("Search functionality needs to be reimplemented with DuckDB")
    
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
            logger.debug(f"Cache hit for search query")
            # Convert cached database models back to API format
            api_results = []
            for asset_data in cached_result.get("results", []):
                # Reconstruct minimal DBAsset for conversion
                db_asset = type('DBAsset', (), asset_data)()
                api_results.append(self._convert_db_to_api_asset(db_asset))
            
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
            db_params["media_type"] = filters["media_type"].value
        
        if filters.get("quality_rating"):
            quality_range = filters["quality_rating"]
            if quality_range.get("min"):
                db_params["min_rating"] = quality_range["min"]
        
        if filters.get("ai_source"):
            # Handle both single and multiple sources
            sources = filters["ai_source"]
            if isinstance(sources, str):
                db_params["source_type"] = sources
            elif isinstance(sources, list) and len(sources) == 1:
                db_params["source_type"] = sources[0]
            # Note: Current repository doesn't support multiple sources in one query
        
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
        
        # TODO: Execute search with DuckDB
        # For now, return empty results until DuckDB integration is complete
        logger.warning("Search not yet implemented with DuckDB")
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
            db_asset: Database asset model
            
        Returns:
            API asset model
        """
        # Collect all tags
        tags = []
        for tag in db_asset.tags:
            tags.append(tag.tag_value)
        
        # Extract metadata
        metadata = db_asset.embedded_metadata or {}
        generation_params = db_asset.generation_params or {}
        
        return Asset(
            content_hash=db_asset.content_hash,
            file_path=db_asset.file_path or "",
            media_type=MediaType(db_asset.media_type or "unknown"),
            file_size=db_asset.file_size or 0,
            tags=tags,
            ai_source=db_asset.source_type,
            quality_rating=db_asset.rating,
            created_at=db_asset.first_seen.isoformat() if db_asset.first_seen else datetime.now().isoformat(),
            modified_at=db_asset.last_seen.isoformat() if db_asset.last_seen else datetime.now().isoformat(),
            discovered_at=db_asset.first_seen.isoformat() if db_asset.first_seen else datetime.now().isoformat(),
            metadata={
                "dimensions": {
                    "width": db_asset.width,
                    "height": db_asset.height,
                } if db_asset.width and db_asset.height else None,
                "prompt": metadata.get("prompt") or generation_params.get("prompt"),
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
            assets: Database asset models
            
        Returns:
            Search facets
        """
        tag_counts = {}
        source_counts = {}
        quality_counts = {}
        type_counts = {}
        
        for asset in assets:
            # Count tags
            for tag in asset.tags:
                key = f"{tag.tag_type}:{tag.tag_value}"
                tag_counts[key] = tag_counts.get(key, 0) + 1
            
            # Count sources
            if asset.source_type:
                source_counts[asset.source_type] = source_counts.get(asset.source_type, 0) + 1
            
            # Count quality ratings
            if asset.rating:
                quality_counts[str(asset.rating)] = quality_counts.get(str(asset.rating), 0) + 1
            
            # Count media types
            if asset.media_type:
                type_counts[asset.media_type] = type_counts.get(asset.media_type, 0) + 1
        
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
            asset: Database asset
            
        Returns:
            Serializable dictionary
        """
        return {
            "content_hash": asset.content_hash,
            "file_path": asset.file_path,
            "media_type": asset.media_type,
            "file_size": asset.file_size,
            "width": asset.width,
            "height": asset.height,
            "source_type": asset.source_type,
            "rating": asset.rating,
            "first_seen": asset.first_seen.isoformat() if asset.first_seen else None,
            "last_seen": asset.last_seen.isoformat() if asset.last_seen else None,
            "tags": [{"tag_type": t.tag_type, "tag_value": t.tag_value} for t in asset.tags],
            "embedded_metadata": asset.embedded_metadata,
            "generation_params": asset.generation_params
        }