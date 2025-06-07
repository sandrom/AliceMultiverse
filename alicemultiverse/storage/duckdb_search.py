"""DuckDB-based search implementation for AliceMultiverse.

This module provides search functionality using DuckDB as the backend,
replacing the PostgreSQL implementation. It supports full-text search,
tag-based filtering, and faceted search results.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union, Set

import duckdb

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class DuckDBSearch:
    """DuckDB-based search implementation for assets."""
    
    def __init__(self, db_path: Union[str, Path] = None):
        """Initialize DuckDB search database.
        
        Args:
            db_path: Path to DuckDB database file. If None, uses in-memory database.
        """
        self.db_path = Path(db_path) if db_path else None
        
        # Initialize connection
        if self.db_path:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)
            self.conn = duckdb.connect(str(self.db_path))
        else:
            self.conn = duckdb.connect()
        
        self.create_schema()
        logger.info(f"DuckDB search initialized: {'in-memory' if not db_path else db_path}")
    
    def create_schema(self):
        """Create database schema for search."""
        # Main assets table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                content_hash VARCHAR PRIMARY KEY,
                file_path VARCHAR NOT NULL,
                media_type VARCHAR NOT NULL,
                file_size BIGINT NOT NULL,
                width INTEGER,
                height INTEGER,
                ai_source VARCHAR,
                quality_rating DOUBLE,
                created_at TIMESTAMP NOT NULL,
                modified_at TIMESTAMP NOT NULL,
                discovered_at TIMESTAMP NOT NULL,
                
                -- Metadata as JSON for flexibility
                metadata JSON,
                generation_params JSON,
                
                -- For fast text search
                prompt TEXT,
                description TEXT
            )
        """)
        
        # Tags table with arrays for efficient searching
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_tags (
                content_hash VARCHAR PRIMARY KEY,
                tags VARCHAR[],
                
                -- Tag categories as separate arrays for faceting
                style_tags VARCHAR[],
                mood_tags VARCHAR[],
                subject_tags VARCHAR[],
                color_tags VARCHAR[],
                technical_tags VARCHAR[],
                object_tags VARCHAR[],
                custom_tags VARCHAR[],
                
                -- For tag:value pairs (future)
                tag_values JSON,
                
                FOREIGN KEY (content_hash) REFERENCES assets(content_hash)
            )
        """)
        
        # Perceptual hashes table for similarity search
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS perceptual_hashes (
                content_hash VARCHAR PRIMARY KEY,
                phash VARCHAR,       -- Perceptual hash (DCT-based)
                dhash VARCHAR,       -- Difference hash
                ahash VARCHAR,       -- Average hash
                
                FOREIGN KEY (content_hash) REFERENCES assets(content_hash)
            )
        """)
        
        # Create indexes for performance
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_media_type ON assets(media_type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_source ON assets(ai_source)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_quality_rating ON assets(quality_rating)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON assets(created_at)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_modified_at ON assets(modified_at)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_file_size ON assets(file_size)")
        
        # Create full-text search index on text fields
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt ON assets(prompt)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_description ON assets(description)")
        
        # Create indexes for perceptual hashes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_phash ON perceptual_hashes(phash)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_dhash ON perceptual_hashes(dhash)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ahash ON perceptual_hashes(ahash)")
        
        logger.debug("DuckDB schema created")
    
    def index_asset(self, metadata: Dict[str, Any]) -> None:
        """Add or update an asset in the search index.
        
        Args:
            metadata: Asset metadata dictionary
        """
        # Extract basic fields
        content_hash = metadata["content_hash"]
        file_path = metadata.get("file_path", "")
        media_type = metadata.get("media_type", "unknown")
        # Handle MediaType enum
        if hasattr(media_type, 'value'):
            media_type = media_type.value
        file_size = metadata.get("file_size", 0)
        
        # Extract dimensions
        dimensions = metadata.get("dimensions", {})
        width = dimensions.get("width")
        height = dimensions.get("height")
        
        # Extract other fields
        ai_source = metadata.get("ai_source") or metadata.get("source_type")
        quality_rating = metadata.get("quality_rating") or metadata.get("rating")
        
        # Extract timestamps
        created_at = self._parse_timestamp(metadata.get("created_at"))
        modified_at = self._parse_timestamp(metadata.get("modified_at"))
        discovered_at = self._parse_timestamp(metadata.get("discovered_at")) or created_at
        
        # Extract text fields for search
        prompt = metadata.get("prompt", "")
        if not prompt and metadata.get("generation_params"):
            prompt = metadata["generation_params"].get("prompt", "")
        
        description = metadata.get("description", "")
        if not description and metadata.get("understanding"):
            description = metadata["understanding"].get("description", "")
        
        # Prepare metadata JSON (excluding fields we store separately)
        metadata_json = {
            k: v for k, v in metadata.items()
            if k not in ["content_hash", "file_path", "media_type", "file_size",
                         "width", "height", "ai_source", "quality_rating",
                         "created_at", "modified_at", "discovered_at",
                         "tags", "prompt", "description", "generation_params"]
        }
        
        # Insert or update asset
        self.conn.execute("""
            INSERT INTO assets (
                content_hash, file_path, media_type, file_size,
                width, height, ai_source, quality_rating,
                created_at, modified_at, discovered_at,
                metadata, generation_params, prompt, description
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (content_hash) DO UPDATE SET
                file_path = EXCLUDED.file_path,
                media_type = EXCLUDED.media_type,
                file_size = EXCLUDED.file_size,
                width = EXCLUDED.width,
                height = EXCLUDED.height,
                ai_source = EXCLUDED.ai_source,
                quality_rating = EXCLUDED.quality_rating,
                created_at = EXCLUDED.created_at,
                modified_at = EXCLUDED.modified_at,
                discovered_at = EXCLUDED.discovered_at,
                metadata = EXCLUDED.metadata,
                generation_params = EXCLUDED.generation_params,
                prompt = EXCLUDED.prompt,
                description = EXCLUDED.description
        """, [
            content_hash, file_path, media_type, file_size,
            width, height, ai_source, quality_rating,
            created_at, modified_at, discovered_at,
            json.dumps(metadata_json) if metadata_json else None,
            json.dumps(metadata.get("generation_params")) if metadata.get("generation_params") else None,
            prompt, description
        ])
        
        # Process and store tags
        self._index_tags(content_hash, metadata.get("tags", []))
        
        logger.debug(f"Indexed asset: {content_hash}")
    
    def _index_tags(self, content_hash: str, tags: Union[List[str], Dict[str, List[str]]]) -> None:
        """Index tags for an asset.
        
        Args:
            content_hash: Asset content hash
            tags: Either a list of tags or a dict of tag categories
        """
        # Normalize tags to dict format
        if isinstance(tags, list):
            tags_dict = {"custom": tags}
        else:
            tags_dict = tags
        
        # Collect all tags
        all_tags = []
        style_tags = tags_dict.get("style", [])
        mood_tags = tags_dict.get("mood", [])
        subject_tags = tags_dict.get("subject", [])
        color_tags = tags_dict.get("color", [])
        technical_tags = tags_dict.get("technical", [])
        object_tags = tags_dict.get("objects", [])
        custom_tags = tags_dict.get("custom", [])
        
        # Combine all tags
        for tag_list in [style_tags, mood_tags, subject_tags, color_tags, 
                        technical_tags, object_tags, custom_tags]:
            all_tags.extend(tag_list)
        
        # Store tags
        self.conn.execute("""
            INSERT INTO asset_tags (
                content_hash, tags, style_tags, mood_tags, subject_tags,
                color_tags, technical_tags, object_tags, custom_tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (content_hash) DO UPDATE SET
                tags = EXCLUDED.tags,
                style_tags = EXCLUDED.style_tags,
                mood_tags = EXCLUDED.mood_tags,
                subject_tags = EXCLUDED.subject_tags,
                color_tags = EXCLUDED.color_tags,
                technical_tags = EXCLUDED.technical_tags,
                object_tags = EXCLUDED.object_tags,
                custom_tags = EXCLUDED.custom_tags
        """, [
            content_hash, all_tags, style_tags, mood_tags, subject_tags,
            color_tags, technical_tags, object_tags, custom_tags
        ])
    
    def search(self, filters: Dict[str, Any] = None, 
              sort_by: str = "created_at", 
              order: str = "desc",
              limit: int = 50, 
              offset: int = 0) -> Tuple[List[Dict[str, Any]], int]:
        """Search assets with filters.
        
        Args:
            filters: Search filters
            sort_by: Sort field
            order: Sort order (asc/desc)
            limit: Maximum results
            offset: Result offset
            
        Returns:
            Tuple of (results, total_count)
        """
        # Build query
        query_parts = ["SELECT a.*, t.tags FROM assets a"]
        query_parts.append("LEFT JOIN asset_tags t ON a.content_hash = t.content_hash")
        
        where_conditions = []
        params = []
        
        if filters:
            # Media type filter
            if filters.get("media_type"):
                where_conditions.append("a.media_type = ?")
                params.append(filters["media_type"])
            
            # File format filter
            if filters.get("file_formats"):
                format_conditions = []
                for fmt in filters["file_formats"]:
                    format_conditions.append("a.file_path LIKE ?")
                    params.append(f"%.{fmt}")
                where_conditions.append(f"({' OR '.join(format_conditions)})")
            
            # File size filter
            if filters.get("file_size"):
                size_range = filters["file_size"]
                if size_range.get("min") is not None:
                    where_conditions.append("a.file_size >= ?")
                    params.append(size_range["min"])
                if size_range.get("max") is not None:
                    where_conditions.append("a.file_size <= ?")
                    params.append(size_range["max"])
            
            # Dimension filters
            if filters.get("dimensions"):
                dims = filters["dimensions"]
                if dims.get("width"):
                    if dims["width"].get("min") is not None:
                        where_conditions.append("a.width >= ?")
                        params.append(dims["width"]["min"])
                    if dims["width"].get("max") is not None:
                        where_conditions.append("a.width <= ?")
                        params.append(dims["width"]["max"])
                if dims.get("height"):
                    if dims["height"].get("min") is not None:
                        where_conditions.append("a.height >= ?")
                        params.append(dims["height"]["min"])
                    if dims["height"].get("max") is not None:
                        where_conditions.append("a.height <= ?")
                        params.append(dims["height"]["max"])
            
            # Quality rating filter
            if filters.get("quality_rating"):
                rating_range = filters["quality_rating"]
                if rating_range.get("min") is not None:
                    where_conditions.append("a.quality_rating >= ?")
                    params.append(rating_range["min"])
                if rating_range.get("max") is not None:
                    where_conditions.append("a.quality_rating <= ?")
                    params.append(rating_range["max"])
            
            # AI source filter
            if filters.get("ai_source"):
                sources = filters["ai_source"]
                if isinstance(sources, str):
                    sources = [sources]
                placeholders = ",".join(["?" for _ in sources])
                where_conditions.append(f"a.ai_source IN ({placeholders})")
                params.extend(sources)
            
            # Tag filters
            self._add_tag_filters(filters, where_conditions, params)
            
            # Date range filter
            if filters.get("date_range"):
                date_range = filters["date_range"]
                if date_range.get("start"):
                    where_conditions.append("a.created_at >= ?")
                    params.append(self._parse_timestamp(date_range["start"]))
                if date_range.get("end"):
                    where_conditions.append("a.created_at <= ?")
                    params.append(self._parse_timestamp(date_range["end"]))
            
            # Filename pattern filter
            if filters.get("filename_pattern"):
                where_conditions.append("regexp_matches(a.file_path, ?, 'i')")
                params.append(filters["filename_pattern"])
            
            # Prompt keywords filter
            if filters.get("prompt_keywords"):
                keyword_conditions = []
                for keyword in filters["prompt_keywords"]:
                    keyword_conditions.append("a.prompt ILIKE ?")
                    params.append(f"%{keyword}%")
                where_conditions.append(f"({' AND '.join(keyword_conditions)})")
        
        # Add WHERE clause
        if where_conditions:
            query_parts.append(f"WHERE {' AND '.join(where_conditions)}")
        
        # Count total results
        count_query = query_parts.copy()
        count_query[0] = "SELECT COUNT(*) FROM assets a"
        total_count = self.conn.execute(" ".join(count_query), params).fetchone()[0]
        
        # Add ORDER BY
        sort_field = self._map_sort_field(sort_by)
        query_parts.append(f"ORDER BY {sort_field} {order.upper()}")
        
        # Add LIMIT and OFFSET
        query_parts.append("LIMIT ? OFFSET ?")
        params.extend([limit, offset])
        
        # Execute search query
        results = self.conn.execute(" ".join(query_parts), params).fetchall()
        
        # Convert results to dictionaries
        assets = []
        for row in results:
            asset = self._row_to_asset(row)
            assets.append(asset)
        
        return assets, total_count
    
    def _add_tag_filters(self, filters: Dict[str, Any], 
                        where_conditions: List[str], 
                        params: List[Any]) -> None:
        """Add tag-related filters to the query.
        
        Args:
            filters: Search filters
            where_conditions: List to append conditions to
            params: List to append parameters to
        """
        # AND operation tags
        if filters.get("tags"):
            for tag in filters["tags"]:
                where_conditions.append("list_contains(t.tags, ?)")
                params.append(tag)
        
        # OR operation tags
        if filters.get("any_tags"):
            or_conditions = []
            for tag in filters["any_tags"]:
                or_conditions.append("list_contains(t.tags, ?)")
                params.append(tag)
            if or_conditions:
                where_conditions.append(f"({' OR '.join(or_conditions)})")
        
        # NOT operation tags
        if filters.get("exclude_tags"):
            for tag in filters["exclude_tags"]:
                where_conditions.append("NOT list_contains(t.tags, ?)")
                params.append(tag)
    
    def get_facets(self, filters: Dict[str, Any] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get facet counts for search results.
        
        Args:
            filters: Optional filters to apply before counting
            
        Returns:
            Search facets with counts
        """
        # Base query for facets
        base_conditions = []
        base_params = []
        
        # Apply basic filters (not tag filters) for facet calculation
        if filters:
            if filters.get("media_type"):
                base_conditions.append("a.media_type = ?")
                base_params.append(filters["media_type"])
            
            if filters.get("ai_source"):
                sources = filters["ai_source"]
                if isinstance(sources, str):
                    sources = [sources]
                placeholders = ",".join(["?" for _ in sources])
                base_conditions.append(f"a.ai_source IN ({placeholders})")
                base_params.extend(sources)
        
        where_clause = f"WHERE {' AND '.join(base_conditions)}" if base_conditions else ""
        
        # Get tag facets
        tag_query = f"""
            SELECT tag, COUNT(*) as count
            FROM (
                SELECT unnest(t.tags) as tag
                FROM assets a
                LEFT JOIN asset_tags t ON a.content_hash = t.content_hash
                {where_clause}
            ) tag_list
            WHERE tag IS NOT NULL
            GROUP BY tag
            ORDER BY count DESC
            LIMIT 20
        """
        tag_results = self.conn.execute(tag_query, base_params).fetchall()
        tag_facets = [{"value": tag, "count": count} for tag, count in tag_results if tag]
        
        # Get AI source facets
        source_query = f"""
            SELECT ai_source, COUNT(*) as count
            FROM assets a
            {where_clause}
            WHERE ai_source IS NOT NULL
            GROUP BY ai_source
            ORDER BY count DESC
        """
        source_results = self.conn.execute(source_query, base_params).fetchall()
        source_facets = [{"value": source, "count": count} for source, count in source_results]
        
        # Get quality rating facets
        rating_query = f"""
            SELECT 
                CASE 
                    WHEN quality_rating >= 80 THEN '5'
                    WHEN quality_rating >= 60 THEN '4'
                    WHEN quality_rating >= 40 THEN '3'
                    WHEN quality_rating >= 20 THEN '2'
                    ELSE '1'
                END as rating,
                COUNT(*) as count
            FROM assets a
            {where_clause}
            WHERE quality_rating IS NOT NULL
            GROUP BY rating
            ORDER BY rating DESC
        """
        rating_results = self.conn.execute(rating_query, base_params).fetchall()
        rating_facets = [{"value": rating, "count": count} for rating, count in rating_results]
        
        # Get media type facets
        type_query = f"""
            SELECT media_type, COUNT(*) as count
            FROM assets a
            {where_clause}
            GROUP BY media_type
            ORDER BY count DESC
        """
        type_results = self.conn.execute(type_query, base_params).fetchall()
        type_facets = [{"value": media_type, "count": count} for media_type, count in type_results]
        
        return {
            "tags": tag_facets,
            "ai_sources": source_facets,
            "quality_ratings": rating_facets,
            "media_types": type_facets
        }
    
    
    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        """Parse various timestamp formats.
        
        Args:
            value: Timestamp value (string, datetime, or None)
            
        Returns:
            datetime object or None
        """
        if not value:
            return None
        
        if isinstance(value, datetime):
            return value
        
        if isinstance(value, str):
            try:
                # Try ISO format first
                return datetime.fromisoformat(value.replace('Z', '+00:00'))
            except:
                try:
                    # Try other common formats
                    return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
                except:
                    logger.warning(f"Could not parse timestamp: {value}")
                    return None
        
        return None
    
    def _map_sort_field(self, field: str) -> str:
        """Map API sort field to database column.
        
        Args:
            field: API sort field name
            
        Returns:
            Database column name
        """
        mapping = {
            "created_date": "a.created_at",
            "created": "a.created_at",
            "modified_date": "a.modified_at",
            "modified": "a.modified_at",
            "quality_rating": "a.quality_rating",
            "file_size": "a.file_size",
            "filename": "a.file_path"
        }
        return mapping.get(field, "a.created_at")
    
    def _row_to_asset(self, row: Tuple) -> Dict[str, Any]:
        """Convert database row to asset dictionary.
        
        Args:
            row: Database row tuple
            
        Returns:
            Asset dictionary
        """
        # Column order from SELECT a.*, t.tags
        (content_hash, file_path, media_type, file_size, width, height,
         ai_source, quality_rating, created_at, modified_at, discovered_at,
         metadata_json, generation_params_json, prompt, description, tags) = row
        
        # Parse JSON fields
        metadata = json.loads(metadata_json) if metadata_json else {}
        generation_params = json.loads(generation_params_json) if generation_params_json else {}
        
        # Build asset dictionary
        asset = {
            "content_hash": content_hash,
            "file_path": file_path,
            "media_type": media_type,
            "file_size": file_size,
            "tags": tags or [],
            "ai_source": ai_source,
            "source_type": ai_source,  # For compatibility
            "quality_rating": quality_rating,
            "rating": quality_rating,  # For compatibility
            "created_at": created_at.isoformat() if created_at else None,
            "modified_at": modified_at.isoformat() if modified_at else None,
            "discovered_at": discovered_at.isoformat() if discovered_at else None,
            "first_seen": created_at,  # For compatibility
            "last_seen": modified_at,  # For compatibility
            "width": width,
            "height": height,
            "dimensions": {"width": width, "height": height} if width and height else None,
            "prompt": prompt,
            "description": description,
            "metadata": metadata,
            "generation_params": generation_params,
            "embedded_metadata": metadata,  # For compatibility
        }
        
        return asset
    
    def delete_asset(self, content_hash: str) -> bool:
        """Remove an asset from the index.
        
        Args:
            content_hash: Asset content hash
            
        Returns:
            True if deleted, False if not found
        """
        result = self.conn.execute(
            "DELETE FROM assets WHERE content_hash = ?",
            [content_hash]
        )
        return result.rowcount > 0
    
    def clear_index(self) -> None:
        """Clear the entire search index."""
        # Delete in order to respect foreign key constraints
        self.conn.execute("DELETE FROM perceptual_hashes")
        self.conn.execute("DELETE FROM asset_tags")
        self.conn.execute("DELETE FROM assets")
        logger.info("Search index cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get search index statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = {}
        
        # Total assets
        stats["total_assets"] = self.conn.execute(
            "SELECT COUNT(*) FROM assets"
        ).fetchone()[0]
        
        # Assets by media type
        media_stats = self.conn.execute("""
            SELECT media_type, COUNT(*) as count
            FROM assets
            GROUP BY media_type
        """).fetchall()
        stats["by_media_type"] = {mt: count for mt, count in media_stats}
        
        # Assets by AI source
        source_stats = self.conn.execute("""
            SELECT ai_source, COUNT(*) as count
            FROM assets
            WHERE ai_source IS NOT NULL
            GROUP BY ai_source
        """).fetchall()
        stats["by_ai_source"] = {src: count for src, count in source_stats}
        
        # Assets with tags
        stats["assets_with_tags"] = self.conn.execute(
            "SELECT COUNT(*) FROM asset_tags WHERE array_length(tags) > 0"
        ).fetchone()[0]
        
        # Total unique tags
        stats["unique_tags"] = self.conn.execute("""
            SELECT COUNT(DISTINCT tag) FROM (
                SELECT unnest(tags) as tag FROM asset_tags
            )
        """).fetchone()[0]
        
        # Database size (if using file-based storage)
        if self.db_path and self.db_path.exists():
            stats["storage_size_mb"] = self.db_path.stat().st_size / (1024 * 1024)
        else:
            stats["storage_size_mb"] = 0.0
        
        return stats
    
    def index_perceptual_hashes(
        self, 
        content_hash: str, 
        phash: str | None = None,
        dhash: str | None = None,
        ahash: str | None = None
    ) -> None:
        """Store perceptual hashes for an asset.
        
        Args:
            content_hash: Asset content hash
            phash: Perceptual hash (DCT-based)
            dhash: Difference hash
            ahash: Average hash
        """
        self.conn.execute("""
            INSERT INTO perceptual_hashes (content_hash, phash, dhash, ahash)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (content_hash) DO UPDATE SET
                phash = EXCLUDED.phash,
                dhash = EXCLUDED.dhash,
                ahash = EXCLUDED.ahash
        """, [content_hash, phash, dhash, ahash])
        
        logger.debug(f"Indexed perceptual hashes for: {content_hash}")
    
    def find_similar_by_phash(
        self, 
        target_hash: str, 
        threshold: int = 10,
        limit: int = 20
    ) -> List[Tuple[str, str, int]]:
        """Find similar images by perceptual hash.
        
        Uses a simple character-by-character comparison for now.
        For production, consider using Hamming distance UDF.
        
        Args:
            target_hash: Target perceptual hash
            threshold: Maximum difference threshold
            limit: Maximum results
            
        Returns:
            List of (content_hash, file_path, distance) tuples
        """
        # For now, use exact match as DuckDB doesn't have built-in Hamming distance
        # In production, you'd want to implement a UDF or use an extension
        results = self.conn.execute("""
            SELECT 
                p.content_hash,
                a.file_path,
                p.phash
            FROM perceptual_hashes p
            JOIN assets a ON p.content_hash = a.content_hash
            WHERE p.phash IS NOT NULL
            LIMIT ?
        """, [limit * 10]).fetchall()  # Get more to filter
        
        # Calculate distances in Python
        from ..assets.perceptual_hashing import hamming_distance
        
        similar = []
        for content_hash, file_path, phash in results:
            if phash and phash != target_hash:
                try:
                    distance = hamming_distance(target_hash, phash)
                    if distance <= threshold:
                        similar.append((content_hash, file_path, distance))
                except ValueError:
                    continue
        
        # Sort by distance and limit
        similar.sort(key=lambda x: x[2])
        return similar[:limit]
    
    def get_perceptual_hash(self, content_hash: str) -> Dict[str, str | None]:
        """Get perceptual hashes for an asset.
        
        Args:
            content_hash: Asset content hash
            
        Returns:
            Dict with phash, dhash, ahash keys
        """
        result = self.conn.execute("""
            SELECT phash, dhash, ahash
            FROM perceptual_hashes
            WHERE content_hash = ?
        """, [content_hash]).fetchone()
        
        if result:
            return {
                "phash": result[0],
                "dhash": result[1],
                "ahash": result[2]
            }
        
        return {"phash": None, "dhash": None, "ahash": None}
    
    def find_similar_to_multiple(
        self,
        content_hashes: List[str],
        threshold: int = 10,
        limit: int = 50,
        exclude_hashes: Optional[Set[str]] = None
    ) -> List[Dict[str, Any]]:
        """Find images similar to multiple source images.
        
        This method finds images similar to any of the provided source images,
        useful for finding more like a selection.
        
        Args:
            content_hashes: List of content hashes to find similar to
            threshold: Maximum Hamming distance for similarity
            limit: Maximum results to return
            exclude_hashes: Optional set of hashes to exclude from results
            
        Returns:
            List of result dicts with content_hash, file_path, min_distance,
            and similar_to (list of source hashes it's similar to)
        """
        if not content_hashes:
            return []
        
        exclude_hashes = exclude_hashes or set()
        # Always exclude the source hashes
        exclude_hashes.update(content_hashes)
        
        # Get perceptual hashes for all source images
        source_hashes = {}
        for content_hash in content_hashes:
            hashes = self.get_perceptual_hash(content_hash)
            if hashes.get("phash"):
                source_hashes[content_hash] = hashes["phash"]
        
        if not source_hashes:
            logger.warning("No perceptual hashes found for source images")
            return []
        
        # Get all candidates with perceptual hashes
        candidates = self.conn.execute("""
            SELECT 
                p.content_hash,
                a.file_path,
                p.phash,
                a.ai_source,
                a.quality_rating,
                a.created_at,
                t.tags
            FROM perceptual_hashes p
            JOIN assets a ON p.content_hash = a.content_hash
            LEFT JOIN asset_tags t ON a.content_hash = t.content_hash
            WHERE p.phash IS NOT NULL
            LIMIT ?
        """, [limit * 20]).fetchall()  # Get more candidates to filter
        
        # Calculate distances to all source images
        from ..assets.perceptual_hashing import hamming_distance
        
        results = {}
        for content_hash, file_path, phash, ai_source, quality_rating, created_at, tags in candidates:
            if content_hash in exclude_hashes or not phash:
                continue
            
            # Calculate minimum distance to any source image
            min_distance = float('inf')
            similar_to = []
            
            for source_hash, source_phash in source_hashes.items():
                try:
                    distance = hamming_distance(source_phash, phash)
                    if distance <= threshold:
                        similar_to.append(source_hash)
                        min_distance = min(min_distance, distance)
                except ValueError:
                    continue
            
            if similar_to:
                results[content_hash] = {
                    "content_hash": content_hash,
                    "file_path": file_path,
                    "min_distance": min_distance,
                    "similar_to": similar_to,
                    "ai_source": ai_source,
                    "quality_rating": quality_rating,
                    "created_at": created_at.isoformat() if created_at else None,
                    "tags": tags or [],
                }
        
        # Sort by minimum distance and return top results
        sorted_results = sorted(results.values(), key=lambda x: x["min_distance"])
        return sorted_results[:limit]
    
    def close(self):
        """Close the database connection."""
        self.conn.close()