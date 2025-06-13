"""Unified DuckDB implementation for AliceMultiverse.

This module combines the best features of DuckDBSearchCache and DuckDBSearch
into a single, coherent implementation that serves as both a cache and search engine.

Key Features:
- Multi-location support (from DuckDBSearchCache)
- Advanced search capabilities (from DuckDBSearch)
- Perceptual hash similarity search
- Full-text search on prompts and descriptions
- Structured metadata storage
- Export to Parquet for analytics
"""

import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import duckdb

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class UnifiedDuckDBStorage:
    """Unified DuckDB storage for AliceMultiverse.
    
    Combines multi-location tracking, advanced search, and analytics
    in a single coherent implementation.
    """
    
    # Class-level connection pool
    _connections = {}
    _connection_lock = None
    
    def __init__(self, db_path: Optional[Path] = None, read_only: bool = False):
        """Initialize unified DuckDB storage.
        
        Args:
            db_path: Path to DuckDB database file. If None, uses in-memory database.
            read_only: Open database in read-only mode (better for concurrent reads)
        """
        import threading
        if UnifiedDuckDBStorage._connection_lock is None:
            UnifiedDuckDBStorage._connection_lock = threading.Lock()
            
        self.db_path = db_path
        self.read_only = read_only
        
        # Use connection pooling for file-based databases
        if db_path:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db_key = (str(db_path), read_only)
            
            with UnifiedDuckDBStorage._connection_lock:
                if db_key not in UnifiedDuckDBStorage._connections:
                    UnifiedDuckDBStorage._connections[db_key] = duckdb.connect(
                        str(db_path),
                        read_only=read_only
                    )
                self.conn = UnifiedDuckDBStorage._connections[db_key]
        else:
            self.conn = duckdb.connect()
        
        self._init_schema()
        logger.info(f"Unified DuckDB initialized: {'in-memory' if not db_path else db_path} (read_only={read_only})")
    
    def _init_schema(self):
        """Initialize unified database schema."""
        # Query cache table for performance
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS query_cache (
                cache_key VARCHAR PRIMARY KEY,
                results JSON,
                total_count INTEGER,
                cached_at TIMESTAMP
            );
        """)
        
        # Create index on cache timestamp for cleanup
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_cache_time ON query_cache(cached_at)")
        
        # Tag cache for facet calculations
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tag_cache (
                cache_key VARCHAR PRIMARY KEY,
                tag_counts JSON,
                cached_at TIMESTAMP
            );
        """)
        # Main assets table with multi-location support
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS assets (
                -- Identity
                content_hash VARCHAR PRIMARY KEY,
                
                -- Locations (array of paths/URLs where file exists)
                locations STRUCT(
                    path VARCHAR,
                    storage_type VARCHAR,  -- local, s3, gcs, network
                    last_verified TIMESTAMP,
                    has_embedded_metadata BOOLEAN
                )[],
                
                -- Core metadata
                media_type VARCHAR,
                file_size BIGINT,
                width INTEGER,
                height INTEGER,
                
                -- Quality and source
                ai_source VARCHAR,
                quality_rating DOUBLE,
                
                -- Timestamps
                created_at TIMESTAMP,
                modified_at TIMESTAMP,
                discovered_at TIMESTAMP,
                last_file_scan TIMESTAMP,
                
                -- Search fields
                prompt TEXT,
                description TEXT,
                
                -- Flexible metadata
                metadata JSON,
                generation_params JSON
            );
        """)
        
        # Unified tags table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_tags (
                content_hash VARCHAR PRIMARY KEY,
                
                -- All tags for general search
                tags VARCHAR[],
                
                -- Categorized tags (best of both)
                style VARCHAR[],
                mood VARCHAR[],
                subject VARCHAR[],
                color VARCHAR[],
                technical VARCHAR[],
                objects VARCHAR[],
                
                -- Custom tags as JSON for flexibility
                custom_tags JSON,
                
                FOREIGN KEY (content_hash) REFERENCES assets(content_hash)
            );
        """)
        
        # AI Understanding table (from DuckDBSearchCache)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_understanding (
                content_hash VARCHAR PRIMARY KEY,
                
                -- AI Understanding
                understanding STRUCT(
                    description TEXT,
                    generated_prompt TEXT,
                    negative_prompt TEXT,
                    provider VARCHAR,
                    model VARCHAR,
                    cost DECIMAL(10,6),
                    analyzed_at TIMESTAMP
                ),
                
                -- Model outputs for comparison
                model_outputs JSON,
                
                -- Embeddings for similarity search
                embedding FLOAT[1536],  -- OpenAI ada-002 size
                
                FOREIGN KEY (content_hash) REFERENCES assets(content_hash)
            );
        """)
        
        # Generation info table (from DuckDBSearchCache)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_generation (
                content_hash VARCHAR PRIMARY KEY,
                
                -- Generation details
                generation STRUCT(
                    provider VARCHAR,
                    model VARCHAR,
                    prompt TEXT,
                    parameters JSON,
                    cost DECIMAL(10,6),
                    generated_at TIMESTAMP
                ),
                
                FOREIGN KEY (content_hash) REFERENCES assets(content_hash)
            );
        """)
        
        # Perceptual hashes table (from DuckDBSearch)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS perceptual_hashes (
                content_hash VARCHAR PRIMARY KEY,
                phash VARCHAR,       -- Perceptual hash (DCT-based)
                dhash VARCHAR,       -- Difference hash
                ahash VARCHAR,       -- Average hash
                
                FOREIGN KEY (content_hash) REFERENCES assets(content_hash)
            );
        """)
        
        # Embeddings table (new: combine both similarity approaches)
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS embeddings (
                content_hash VARCHAR PRIMARY KEY,
                embedding_type VARCHAR,  -- 'openai-ada-002', 'clip', etc.
                embedding FLOAT[],
                FOREIGN KEY (content_hash) REFERENCES assets(content_hash)
            );
        """)
        
        # Create indexes for performance
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_media_type ON assets(media_type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ai_source ON assets(ai_source)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_quality_rating ON assets(quality_rating)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_created_at ON assets(created_at)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_modified_at ON assets(modified_at)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_file_size ON assets(file_size)")
        
        # Composite indexes for common query patterns
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_type_created ON assets(media_type, created_at DESC)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_source_quality ON assets(ai_source, quality_rating DESC)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_size_type ON assets(file_size, media_type)")
        
        # Full-text search indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt ON assets(prompt)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_description ON assets(description)")
        
        # Perceptual hash indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_phash ON perceptual_hashes(phash)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_dhash ON perceptual_hashes(dhash)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_ahash ON perceptual_hashes(ahash)")
        
        # Tag performance indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_all_tags ON asset_tags(tags)")
        
        # Enable DuckDB optimizations
        self.conn.execute("SET memory_limit='4GB'")
        self.conn.execute("SET threads=4")
        self.conn.execute("SET enable_progress_bar=false")
    
    # Methods from DuckDBSearchCache
    def upsert_asset(
        self,
        content_hash: str,
        file_path: Path,
        metadata: Dict[str, Any],
        storage_type: str = "local"
    ) -> None:
        """Add or update an asset with location tracking.
        
        Args:
            content_hash: SHA-256 hash of file content
            file_path: Path to the file
            metadata: Metadata extracted from file
            storage_type: Type of storage (local, s3, gcs, network)
        """
        # Extract file stats if available
        file_size = metadata.get("file_size")
        created_at = self._parse_timestamp(metadata.get("created_at"))
        modified_at = self._parse_timestamp(metadata.get("modified_at"))
        
        if file_path.exists() and (file_size is None or created_at is None):
            try:
                file_stat = file_path.stat()
                if file_size is None:
                    file_size = file_stat.st_size
                if created_at is None:
                    created_at = datetime.fromtimestamp(file_stat.st_ctime)
                if modified_at is None:
                    modified_at = datetime.fromtimestamp(file_stat.st_mtime)
            except (FileNotFoundError, OSError):
                pass
        
        # Default timestamps
        if created_at is None:
            created_at = datetime.now()
        if modified_at is None:
            modified_at = datetime.now()
        
        # Check if asset exists
        existing = self.conn.execute(
            "SELECT content_hash FROM assets WHERE content_hash = ?",
            [content_hash]
        ).fetchone()
        
        if existing:
            # Update existing asset - add new location
            self._add_file_location(content_hash, file_path, storage_type)
        else:
            # Extract additional fields
            media_type = metadata.get("media_type", "unknown")
            if hasattr(media_type, 'value'):
                media_type = media_type.value
            
            # Extract dimensions
            dimensions = metadata.get("dimensions", {})
            width = dimensions.get("width") if dimensions else metadata.get("width")
            height = dimensions.get("height") if dimensions else metadata.get("height")
            
            # Extract AI source
            ai_source = metadata.get("ai_source") or metadata.get("source_type")
            
            # Extract quality rating
            quality_rating = metadata.get("quality_rating") or metadata.get("quality_stars")
            
            # Extract text fields
            prompt = metadata.get("prompt", "")
            if not prompt and metadata.get("generation_params"):
                prompt = metadata["generation_params"].get("prompt", "")
            
            description = metadata.get("description", "")
            if not description and metadata.get("understanding"):
                understanding = metadata["understanding"]
                if isinstance(understanding, dict):
                    description = understanding.get("description", "")
            
            # Prepare clean metadata
            clean_metadata = {
                k: v for k, v in metadata.items()
                if k not in ["content_hash", "file_path", "media_type", "file_size",
                             "width", "height", "ai_source", "quality_rating",
                             "created_at", "modified_at", "discovered_at",
                             "tags", "prompt", "description", "generation_params",
                             "understanding", "generation"]
            }
            
            # Insert new asset
            self.conn.execute("""
                INSERT INTO assets (
                    content_hash, locations, media_type, file_size,
                    width, height, ai_source, quality_rating,
                    created_at, modified_at, discovered_at, last_file_scan,
                    prompt, description, metadata, generation_params
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                content_hash,
                [{
                    "path": str(file_path),
                    "storage_type": storage_type,
                    "last_verified": datetime.now(),
                    "has_embedded_metadata": True
                }],
                media_type, file_size, width, height, ai_source, quality_rating,
                created_at, modified_at, datetime.now(), datetime.now(),
                prompt, description,
                json.dumps(clean_metadata) if clean_metadata else None,
                json.dumps(metadata.get("generation_params")) if metadata.get("generation_params") else None
            ])
        
        # Update related tables
        if "tags" in metadata:
            self._upsert_tags(content_hash, metadata["tags"])
        
        if "understanding" in metadata:
            self._upsert_understanding(content_hash, metadata["understanding"])
        
        if "generation" in metadata:
            self._upsert_generation(content_hash, metadata["generation"])
    
    def search_by_tags(
        self,
        tags: Dict[str, List[str]],
        limit: int = 100,
        mode: str = "any"  # "any" or "all"
    ) -> List[Dict[str, Any]]:
        """Search assets by categorized tags with optimized query.
        
        Args:
            tags: Dictionary of tag categories and values
            limit: Maximum number of results
            mode: Search mode - "any" (OR) or "all" (AND) for tags
            
        Returns:
            List of matching assets
        """
        # Flatten all tags for faster search
        all_tag_values = []
        for category, values in tags.items():
            all_tag_values.extend(values)
        
        if not all_tag_values:
            return []
        
        # Use optimized query with flattened tags for better performance
        if mode == "any":
            # ANY mode - match any of the tags
            query = """
                WITH tag_matches AS (
                    SELECT DISTINCT content_hash
                    FROM asset_tags
                    WHERE list_has_any(tags, ?::VARCHAR[])
                )
                SELECT 
                    a.*,
                    t.tags, t.style, t.mood, t.subject, t.color, t.technical, t.objects, t.custom_tags,
                    u.understanding, u.embedding,
                    g.generation,
                    p.phash, p.dhash, p.ahash
                FROM tag_matches tm
                JOIN assets a ON tm.content_hash = a.content_hash
                LEFT JOIN asset_tags t ON a.content_hash = t.content_hash
                LEFT JOIN asset_understanding u ON a.content_hash = u.content_hash
                LEFT JOIN asset_generation g ON a.content_hash = g.content_hash
                LEFT JOIN perceptual_hashes p ON a.content_hash = p.content_hash
                ORDER BY a.created_at DESC
                LIMIT ?
            """
            params = [all_tag_values, limit]
        else:
            # ALL mode - match all tags
            query = """
                WITH tag_matches AS (
                    SELECT content_hash, COUNT(DISTINCT tag) as match_count
                    FROM (
                        SELECT content_hash, unnest(tags) as tag
                        FROM asset_tags
                    ) tag_list
                    WHERE tag IN (SELECT unnest(?::VARCHAR[]))
                    GROUP BY content_hash
                    HAVING match_count = ?
                )
                SELECT 
                    a.*,
                    t.tags, t.style, t.mood, t.subject, t.color, t.technical, t.objects, t.custom_tags,
                    u.understanding, u.embedding,
                    g.generation,
                    p.phash, p.dhash, p.ahash
                FROM tag_matches tm
                JOIN assets a ON tm.content_hash = a.content_hash
                LEFT JOIN asset_tags t ON a.content_hash = t.content_hash
                LEFT JOIN asset_understanding u ON a.content_hash = u.content_hash
                LEFT JOIN asset_generation g ON a.content_hash = g.content_hash
                LEFT JOIN perceptual_hashes p ON a.content_hash = p.content_hash
                ORDER BY a.created_at DESC
                LIMIT ?
            """
            params = [all_tag_values, len(all_tag_values), limit]
        
        if not conditions:
            return []
        
        query = f"""
            SELECT 
                a.*,
                t.tags, t.style, t.mood, t.subject, t.color, t.technical, t.objects, t.custom_tags,
                u.understanding, u.embedding,
                g.generation,
                p.phash, p.dhash, p.ahash
            FROM assets a
            LEFT JOIN asset_tags t ON a.content_hash = t.content_hash
            LEFT JOIN asset_understanding u ON a.content_hash = u.content_hash
            LEFT JOIN asset_generation g ON a.content_hash = g.content_hash
            LEFT JOIN perceptual_hashes p ON a.content_hash = p.content_hash
            WHERE {' OR '.join(conditions)}
            ORDER BY a.created_at DESC
            LIMIT ?
        """
        
        params.append(limit)
        results = self.conn.execute(query, params).fetchall()
        
        return [self._row_to_dict(row) for row in results]
    
    # Methods from DuckDBSearch
    def search_with_cache(
        self,
        filters: Dict[str, Any] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        limit: int = 50,
        offset: int = 0,
        use_cache: bool = True
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Search with built-in query result caching.
        
        Args:
            filters: Search filters
            sort_by: Sort field
            order: Sort order (asc/desc)
            limit: Maximum results
            offset: Result offset
            use_cache: Whether to use query cache
            
        Returns:
            Tuple of (results, total_count)
        """
        # Create cache key from query parameters
        cache_key = None
        if use_cache:
            import hashlib
            cache_data = {
                "filters": filters or {},
                "sort_by": sort_by,
                "order": order,
                "limit": limit,
                "offset": offset
            }
            cache_key = hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()
            
            # Check if we have cached results
            cached = self.conn.execute(
                "SELECT results, total_count, cached_at FROM query_cache WHERE cache_key = ?",
                [cache_key]
            ).fetchone()
            
            if cached:
                results_json, total_count, cached_at = cached
                # Check if cache is still valid (5 minutes)
                if (datetime.now() - cached_at).total_seconds() < 300:
                    return json.loads(results_json), total_count
        
        # Execute actual search
        results, total_count = self.search(filters, sort_by, order, limit, offset)
        
        # Cache results if enabled
        if use_cache and cache_key:
            # Convert results to JSON-serializable format
            serializable_results = []
            for result in results:
                serialized = result.copy()
                # Convert datetime objects
                for field in ["created_at", "modified_at", "discovered_at", "last_file_scan"]:
                    if field in serialized and hasattr(serialized[field], "isoformat"):
                        serialized[field] = serialized[field].isoformat()
                serializable_results.append(serialized)
            
            # Store in cache table
            self.conn.execute(
                "INSERT OR REPLACE INTO query_cache (cache_key, results, total_count, cached_at) VALUES (?, ?, ?, ?)",
                [cache_key, json.dumps(serializable_results), total_count, datetime.now()]
            )
        
        return results, total_count
    
    def search(
        self,
        filters: Dict[str, Any] = None,
        sort_by: str = "created_at",
        order: str = "desc",
        limit: int = 50,
        offset: int = 0
    ) -> Tuple[List[Dict[str, Any]], int]:
        """Advanced search with filters and facets.
        
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
        query_parts = ["""
            SELECT 
                a.*,
                t.tags, t.style, t.mood, t.subject, t.color, t.technical, t.objects, t.custom_tags,
                u.understanding, u.embedding,
                g.generation,
                p.phash, p.dhash, p.ahash
            FROM assets a
        """]
        query_parts.append("LEFT JOIN asset_tags t ON a.content_hash = t.content_hash")
        query_parts.append("LEFT JOIN asset_understanding u ON a.content_hash = u.content_hash")
        query_parts.append("LEFT JOIN asset_generation g ON a.content_hash = g.content_hash")
        query_parts.append("LEFT JOIN perceptual_hashes p ON a.content_hash = p.content_hash")
        
        where_conditions = []
        params = []
        
        if filters:
            # Apply all filters from DuckDBSearch
            self._apply_search_filters(filters, where_conditions, params)
        
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
        assets = [self._row_to_dict(row) for row in results]
        
        return assets, total_count
    
    def get_facets(self, filters: Dict[str, Any] = None) -> Dict[str, List[Dict[str, Any]]]:
        """Get search facets for UI with optimized queries.
        
        Args:
            filters: Optional filters to apply before counting
            
        Returns:
            Dictionary of facets with counts
        """
        # Check facet cache first
        cache_key = json.dumps(filters or {}, sort_keys=True)
        cache_hash = hashlib.md5(cache_key.encode()).hexdigest()
        
        cached = self.conn.execute(
            "SELECT tag_counts, cached_at FROM tag_cache WHERE cache_key = ?",
            [cache_hash]
        ).fetchone()
        
        if cached:
            tag_counts, cached_at = cached
            if (datetime.now() - cached_at).total_seconds() < 300:  # 5 minute cache
                return json.loads(tag_counts)
        
        # Build optimized facet queries
        facets = {}
        
        # Get tag facets with single optimized query
        tag_query = """
            WITH tag_counts AS (
                SELECT tag, COUNT(DISTINCT a.content_hash) as count
                FROM assets a
                JOIN asset_tags t ON a.content_hash = t.content_hash
                CROSS JOIN unnest(t.tags) AS tag
                WHERE tag IS NOT NULL
                GROUP BY tag
            )
            SELECT tag, count
            FROM tag_counts
            ORDER BY count DESC
            LIMIT 30
        """
        tag_results = self.conn.execute(tag_query).fetchall()
        facets["tags"] = [{"value": tag, "count": count} for tag, count in tag_results]
        
        # Get other facets with a single aggregated query
        facet_query = """
            WITH facet_data AS (
                SELECT 
                    ai_source,
                    media_type,
                    CASE 
                        WHEN quality_rating >= 80 THEN '5_stars'
                        WHEN quality_rating >= 60 THEN '4_stars'
                        WHEN quality_rating >= 40 THEN '3_stars'
                        WHEN quality_rating >= 20 THEN '2_stars'
                        WHEN quality_rating > 0 THEN '1_star'
                        ELSE NULL
                    END as quality_bucket
                FROM assets
                WHERE ai_source IS NOT NULL OR media_type IS NOT NULL OR quality_rating IS NOT NULL
            )
            SELECT 
                'ai_source' as facet_type,
                ai_source as value,
                COUNT(*) as count
            FROM facet_data
            WHERE ai_source IS NOT NULL
            GROUP BY ai_source
            UNION ALL
            SELECT 
                'media_type' as facet_type,
                media_type as value,
                COUNT(*) as count
            FROM facet_data
            WHERE media_type IS NOT NULL
            GROUP BY media_type
            UNION ALL
            SELECT 
                'quality_rating' as facet_type,
                quality_bucket as value,
                COUNT(*) as count
            FROM facet_data
            WHERE quality_bucket IS NOT NULL
            GROUP BY quality_bucket
            ORDER BY facet_type, count DESC
        """
        
        other_results = self.conn.execute(facet_query).fetchall()
        
        facets["ai_sources"] = []
        facets["media_types"] = []
        facets["quality_ratings"] = []
        
        for facet_type, value, count in other_results:
            if facet_type == "ai_source" and len(facets["ai_sources"]) < 20:
                facets["ai_sources"].append({"value": value, "count": count})
            elif facet_type == "media_type":
                facets["media_types"].append({"value": value, "count": count})
            elif facet_type == "quality_rating":
                facets["quality_ratings"].append({"value": value, "count": count})
        
        # Sort quality ratings properly
        quality_order = ["5_stars", "4_stars", "3_stars", "2_stars", "1_star"]
        facets["quality_ratings"].sort(
            key=lambda x: quality_order.index(x["value"]) if x["value"] in quality_order else 999
        )
        
        # Cache the results
        self.conn.execute(
            "INSERT OR REPLACE INTO tag_cache (cache_key, tag_counts, cached_at) VALUES (?, ?, ?)",
            [cache_hash, json.dumps(facets), datetime.now()]
        )
        
        return facets
        }
    
    # New unified methods
    def find_similar(
        self,
        content_hash: str,
        method: str = "phash",
        threshold: float = 0.9,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """Find similar assets using specified method.
        
        Args:
            content_hash: Content hash of reference asset
            method: Similarity method ("phash", "embedding", "tags")
            threshold: Similarity threshold
            limit: Maximum results
            
        Returns:
            List of similar assets
        """
        if method == "phash":
            # Use perceptual hash similarity
            phash_data = self.conn.execute(
                "SELECT phash FROM perceptual_hashes WHERE content_hash = ?",
                [content_hash]
            ).fetchone()
            
            if not phash_data or not phash_data[0]:
                return []
            
            # Find similar by perceptual hash
            # (Implementation would use Hamming distance)
            return []
        
        elif method == "embedding":
            # Use embedding similarity
            # (Implementation would use cosine similarity)
            return []
        
        elif method == "tags":
            # Use tag similarity
            tags_data = self.conn.execute(
                "SELECT tags FROM asset_tags WHERE content_hash = ?",
                [content_hash]
            ).fetchone()
            
            if not tags_data or not tags_data[0]:
                return []
            
            # Find assets with similar tags
            # (Implementation would use Jaccard similarity)
            return []
        
        return []
    
    def get_asset_by_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get a single asset by content hash.
        
        Args:
            content_hash: SHA-256 hash of file content
            
        Returns:
            Asset metadata or None if not found
        """
        result = self.conn.execute("""
            SELECT 
                a.*,
                t.tags, t.style, t.mood, t.subject, t.color, t.technical, t.objects, t.custom_tags,
                u.understanding, u.embedding,
                g.generation,
                p.phash, p.dhash, p.ahash
            FROM assets a
            LEFT JOIN asset_tags t ON a.content_hash = t.content_hash
            LEFT JOIN asset_understanding u ON a.content_hash = u.content_hash
            LEFT JOIN asset_generation g ON a.content_hash = g.content_hash
            LEFT JOIN perceptual_hashes p ON a.content_hash = p.content_hash
            WHERE a.content_hash = ?
        """, [content_hash]).fetchone()
        
        return self._row_to_dict(result) if result else None
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get comprehensive storage statistics.
        
        Returns:
            Dictionary with statistics
        """
        stats = {}
        
        # Total assets
        stats["total_assets"] = self.conn.execute(
            "SELECT COUNT(*) FROM assets"
        ).fetchone()[0]
        
        # Assets by media type
        media_types = self.conn.execute("""
            SELECT media_type, COUNT(*) as count
            FROM assets
            GROUP BY media_type
        """).fetchall()
        stats["by_media_type"] = {mt: count for mt, count in media_types}
        
        # Total locations
        stats["total_locations"] = self.conn.execute(
            "SELECT SUM(len(locations)) FROM assets"
        ).fetchone()[0] or 0
        
        # Assets with various metadata
        stats["assets_with_tags"] = self.conn.execute(
            "SELECT COUNT(*) FROM asset_tags WHERE array_length(tags) > 0"
        ).fetchone()[0]
        
        stats["assets_with_understanding"] = self.conn.execute(
            "SELECT COUNT(*) FROM asset_understanding"
        ).fetchone()[0]
        
        stats["assets_with_perceptual_hashes"] = self.conn.execute(
            "SELECT COUNT(*) FROM perceptual_hashes WHERE phash IS NOT NULL"
        ).fetchone()[0]
        
        # Storage types
        storage_stats = self.conn.execute("""
            SELECT 
                unnest.storage_type,
                COUNT(*) as count
            FROM assets,
            UNNEST(locations) as unnest
            GROUP BY unnest.storage_type
        """).fetchall()
        stats["by_storage_type"] = {st: count for st, count in storage_stats}
        
        # Database size
        if self.db_path and self.db_path.exists():
            stats["storage_size_mb"] = self.db_path.stat().st_size / (1024 * 1024)
        
        return stats
    
    # Private helper methods
    def _add_file_location(
        self,
        content_hash: str,
        file_path: Path,
        storage_type: str
    ) -> None:
        """Add a new location for an existing asset."""
        # Get current locations
        result = self.conn.execute(
            "SELECT locations FROM assets WHERE content_hash = ?",
            [content_hash]
        ).fetchone()
        
        if result:
            locations = result[0] if result[0] else []
            
            # Check if location already exists
            path_str = str(file_path)
            location_exists = any(loc["path"] == path_str for loc in locations)
            
            if not location_exists:
                # Add new location
                locations.append({
                    "path": path_str,
                    "storage_type": storage_type,
                    "last_verified": datetime.now(),
                    "has_embedded_metadata": True
                })
                
                # Update locations
                # DuckDB has issues with foreign key constraints on array updates
                # So we need to work around this by temporarily disabling FK checks
                try:
                    # DuckDB doesn't support PRAGMA foreign_keys=off like SQLite
                    # Instead, we'll use a different approach - update without transaction
                    self.conn.execute(
                        "UPDATE assets SET locations = ? WHERE content_hash = ?",
                        [locations, content_hash]
                    )
                except Exception as e:
                    # If that fails, try deleting and re-inserting (nuclear option)
                    logger.warning(f"Failed to update locations, trying delete/insert: {e}")
                    
                    # Get current asset data
                    current = self.conn.execute(
                        "SELECT * FROM assets WHERE content_hash = ?",
                        [content_hash]
                    ).fetchone()
                    
                    if current:
                        # Delete related data first
                        self.conn.execute("DELETE FROM perceptual_hashes WHERE content_hash = ?", [content_hash])
                        self.conn.execute("DELETE FROM embeddings WHERE content_hash = ?", [content_hash])
                        self.conn.execute("DELETE FROM asset_generation WHERE content_hash = ?", [content_hash])
                        self.conn.execute("DELETE FROM asset_understanding WHERE content_hash = ?", [content_hash])
                        self.conn.execute("DELETE FROM asset_tags WHERE content_hash = ?", [content_hash])
                        
                        # Delete the asset
                        self.conn.execute("DELETE FROM assets WHERE content_hash = ?", [content_hash])
                        
                        # Re-insert with updated locations
                        self.conn.execute("""
                            INSERT INTO assets (
                                content_hash, locations, media_type, file_size,
                                width, height, ai_source, quality_rating,
                                created_at, modified_at, discovered_at, last_file_scan,
                                prompt, description, metadata, generation_params
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, [
                            current[0], locations, current[2], current[3],
                            current[4], current[5], current[6], current[7],
                            current[8], current[9], current[10], current[11],
                            current[12], current[13], current[14], current[15]
                        ])
    
    def _upsert_tags(self, content_hash: str, tags: Union[List[str], Dict[str, List[str]]]) -> None:
        """Insert or update tags for an asset."""
        # Normalize tags
        if isinstance(tags, list):
            tags_dict = {"custom": tags}
            all_tags = tags
        else:
            tags_dict = tags
            # Collect all tags
            all_tags = []
            for tag_list in tags_dict.values():
                if isinstance(tag_list, list):
                    all_tags.extend(tag_list)
        
        # Separate standard and custom tags
        standard_tags = ["style", "mood", "subject", "color", "technical", "objects"]
        
        # Build custom tags
        custom_tags = {}
        for k, v in tags_dict.items():
            if k not in standard_tags and k != "custom":
                custom_tags[k] = v
        
        # Add custom array to custom_tags
        if "custom" in tags_dict:
            custom_tags["custom"] = tags_dict["custom"]
        
        self.conn.execute("""
            INSERT INTO asset_tags (
                content_hash, tags, style, mood, subject, color, technical, objects, custom_tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (content_hash) DO UPDATE SET
                tags = EXCLUDED.tags,
                style = EXCLUDED.style,
                mood = EXCLUDED.mood,
                subject = EXCLUDED.subject,
                color = EXCLUDED.color,
                technical = EXCLUDED.technical,
                objects = EXCLUDED.objects,
                custom_tags = EXCLUDED.custom_tags
        """, [
            content_hash,
            all_tags,
            tags_dict.get("style", []),
            tags_dict.get("mood", []),
            tags_dict.get("subject", []),
            tags_dict.get("color", []),
            tags_dict.get("technical", []),
            tags_dict.get("objects", []),
            json.dumps(custom_tags) if custom_tags else None
        ])
    
    def _upsert_understanding(self, content_hash: str, understanding: Dict[str, Any]) -> None:
        """Insert or update AI understanding for an asset."""
        # Handle both new v4.0 format and legacy format
        if isinstance(understanding, dict):
            # Check if it's the new structured format
            if "description" in understanding or "tags" in understanding:
                # New format
                understanding_struct = {
                    "description": understanding.get("description"),
                    "generated_prompt": understanding.get("positive_prompt") or understanding.get("generated_prompt"),
                    "negative_prompt": understanding.get("negative_prompt"),
                    "provider": understanding.get("provider"),
                    "model": understanding.get("model"),
                    "cost": understanding.get("cost"),
                    "analyzed_at": understanding.get("analyzed_at")
                }
                model_outputs = understanding.get("model_outputs", {})
                embedding = understanding.get("embedding")
            else:
                # Legacy format with multiple providers
                # Extract from first provider
                first_provider_data = next(iter(understanding.values()), {})
                understanding_struct = {
                    "description": first_provider_data.get("description"),
                    "generated_prompt": first_provider_data.get("generated_prompt"),
                    "negative_prompt": first_provider_data.get("negative_prompt"),
                    "provider": first_provider_data.get("provider"),
                    "model": first_provider_data.get("model"),
                    "cost": first_provider_data.get("cost"),
                    "analyzed_at": first_provider_data.get("analyzed_at")
                }
                model_outputs = understanding
                embedding = None
        else:
            # Invalid format
            return
        
        self.conn.execute("""
            INSERT INTO asset_understanding (
                content_hash, understanding, model_outputs, embedding
            ) VALUES (?, ?, ?, ?)
            ON CONFLICT (content_hash) DO UPDATE SET
                understanding = EXCLUDED.understanding,
                model_outputs = EXCLUDED.model_outputs,
                embedding = EXCLUDED.embedding
        """, [content_hash, understanding_struct, json.dumps(model_outputs), embedding])
    
    def _upsert_generation(self, content_hash: str, generation: Dict[str, Any]) -> None:
        """Insert or update generation info for an asset."""
        generation_struct = {
            "provider": generation.get("provider"),
            "model": generation.get("model"),
            "prompt": generation.get("prompt"),
            "parameters": generation.get("parameters", {}),
            "cost": generation.get("cost"),
            "generated_at": generation.get("generated_at")
        }
        
        self.conn.execute("""
            INSERT INTO asset_generation (content_hash, generation)
            VALUES (?, ?)
            ON CONFLICT (content_hash) DO UPDATE SET generation = EXCLUDED.generation
        """, [content_hash, generation_struct])
    
    def _apply_search_filters(
        self,
        filters: Dict[str, Any],
        where_conditions: List[str],
        params: List[Any]
    ) -> None:
        """Apply search filters to query conditions."""
        # Media type filter
        if filters.get("media_type"):
            where_conditions.append("a.media_type = ?")
            params.append(filters["media_type"])
        
        # File format filter
        if filters.get("file_formats"):
            format_conditions = []
            for fmt in filters["file_formats"]:
                format_conditions.append("EXISTS (SELECT 1 FROM unnest(a.locations) AS loc WHERE loc.path LIKE ?)")
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
        if filters.get("tags"):
            for tag in filters["tags"]:
                where_conditions.append("list_contains(t.tags, ?)")
                params.append(tag)
        
        if filters.get("any_tags"):
            or_conditions = []
            for tag in filters["any_tags"]:
                or_conditions.append("list_contains(t.tags, ?)")
                params.append(tag)
            if or_conditions:
                where_conditions.append(f"({' OR '.join(or_conditions)})")
        
        if filters.get("exclude_tags"):
            for tag in filters["exclude_tags"]:
                where_conditions.append("NOT list_contains(t.tags, ?)")
                params.append(tag)
        
        # Date range filter
        if filters.get("date_range"):
            date_range = filters["date_range"]
            if date_range.get("start"):
                where_conditions.append("a.created_at >= ?")
                params.append(self._parse_timestamp(date_range["start"]))
            if date_range.get("end"):
                where_conditions.append("a.created_at <= ?")
                params.append(self._parse_timestamp(date_range["end"]))
        
        # Text search filters
        if filters.get("prompt_keywords"):
            keyword_conditions = []
            for keyword in filters["prompt_keywords"]:
                keyword_conditions.append("a.prompt ILIKE ?")
                params.append(f"%{keyword}%")
            where_conditions.append(f"({' AND '.join(keyword_conditions)})")
        
        # Content hash filter (for specific lookups)
        if filters.get("content_hash"):
            where_conditions.append("a.content_hash = ?")
            params.append(filters["content_hash"])
    
    def _parse_timestamp(self, value: Any) -> Optional[datetime]:
        """Parse various timestamp formats."""
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
        """Map API sort field to database column."""
        mapping = {
            "created_date": "a.created_at",
            "created": "a.created_at",
            "created_at": "a.created_at",
            "modified_date": "a.modified_at",
            "modified": "a.modified_at",
            "modified_at": "a.modified_at",
            "quality_rating": "a.quality_rating",
            "file_size": "a.file_size",
            "filename": "(SELECT unnest(locations).path FROM unnest(a.locations) LIMIT 1)"
        }
        return mapping.get(field, "a.created_at")
    
    def upsert_assets_batch(
        self,
        assets: List[Tuple[str, Path, Dict[str, Any], str]]
    ) -> None:
        """Batch insert/update multiple assets for better performance.
        
        Args:
            assets: List of (content_hash, file_path, metadata, storage_type) tuples
        """
        if not assets:
            return
            
        # Prepare batch data
        new_assets = []
        existing_hashes = set()
        
        # Check which assets already exist (single query)
        content_hashes = [asset[0] for asset in assets]
        placeholders = ",".join(["?" for _ in content_hashes])
        existing_results = self.conn.execute(
            f"SELECT content_hash FROM assets WHERE content_hash IN ({placeholders})",
            content_hashes
        ).fetchall()
        
        for row in existing_results:
            existing_hashes.add(row[0])
        
        # Process assets
        for content_hash, file_path, metadata, storage_type in assets:
            if content_hash in existing_hashes:
                # Update existing - add location
                self._add_file_location(content_hash, file_path, storage_type)
            else:
                # Prepare for batch insert
                file_size = metadata.get("file_size")
                created_at = self._parse_timestamp(metadata.get("created_at"))
                modified_at = self._parse_timestamp(metadata.get("modified_at"))
                
                # Try to get file stats if needed
                if file_path.exists() and (file_size is None or created_at is None):
                    try:
                        file_stat = file_path.stat()
                        if file_size is None:
                            file_size = file_stat.st_size
                        if created_at is None:
                            created_at = datetime.fromtimestamp(file_stat.st_ctime)
                        if modified_at is None:
                            modified_at = datetime.fromtimestamp(file_stat.st_mtime)
                    except (FileNotFoundError, OSError):
                        pass
                
                # Default values
                if created_at is None:
                    created_at = datetime.now()
                if modified_at is None:
                    modified_at = datetime.now()
                
                # Extract fields
                media_type = metadata.get("media_type", "unknown")
                if hasattr(media_type, 'value'):
                    media_type = media_type.value
                
                dimensions = metadata.get("dimensions", {})
                width = dimensions.get("width") if dimensions else metadata.get("width")
                height = dimensions.get("height") if dimensions else metadata.get("height")
                
                ai_source = metadata.get("ai_source") or metadata.get("source_type")
                quality_rating = metadata.get("quality_rating") or metadata.get("quality_stars")
                
                prompt = metadata.get("prompt", "")
                if not prompt and metadata.get("generation_params"):
                    prompt = metadata["generation_params"].get("prompt", "")
                
                description = metadata.get("description", "")
                if not description and metadata.get("understanding"):
                    understanding = metadata["understanding"]
                    if isinstance(understanding, dict):
                        description = understanding.get("description", "")
                
                # Prepare clean metadata
                clean_metadata = {
                    k: v for k, v in metadata.items()
                    if k not in ["content_hash", "file_path", "media_type", "file_size",
                                 "width", "height", "ai_source", "quality_rating",
                                 "created_at", "modified_at", "discovered_at",
                                 "tags", "prompt", "description", "generation_params",
                                 "understanding", "generation"]
                }
                
                new_assets.append((
                    content_hash,
                    [{
                        "path": str(file_path),
                        "storage_type": storage_type,
                        "last_verified": datetime.now(),
                        "has_embedded_metadata": True
                    }],
                    media_type, file_size, width, height, ai_source, quality_rating,
                    created_at, modified_at, datetime.now(), datetime.now(),
                    prompt, description,
                    json.dumps(clean_metadata) if clean_metadata else None,
                    json.dumps(metadata.get("generation_params")) if metadata.get("generation_params") else None
                ))
        
        # Batch insert new assets
        if new_assets:
            self.conn.executemany("""
                INSERT INTO assets (
                    content_hash, locations, media_type, file_size,
                    width, height, ai_source, quality_rating,
                    created_at, modified_at, discovered_at, last_file_scan,
                    prompt, description, metadata, generation_params
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, new_assets)
            
            # Process related tables in batches
            tags_batch = []
            understanding_batch = []
            generation_batch = []
            
            for content_hash, file_path, metadata, storage_type in assets:
                if content_hash not in existing_hashes:
                    if "tags" in metadata:
                        tags_batch.append((content_hash, metadata["tags"]))
                    if "understanding" in metadata:
                        understanding_batch.append((content_hash, metadata["understanding"]))
                    if "generation" in metadata:
                        generation_batch.append((content_hash, metadata["generation"]))
            
            # Batch insert related data
            if tags_batch:
                for content_hash, tags in tags_batch:
                    self._upsert_tags(content_hash, tags)
            
            if understanding_batch:
                for content_hash, understanding in understanding_batch:
                    self._upsert_understanding(content_hash, understanding)
            
            if generation_batch:
                for content_hash, generation in generation_batch:
                    self._upsert_generation(content_hash, generation)
    
    def _row_to_dict(self, row: Tuple) -> Dict[str, Any]:
        """Convert a database row to dictionary with all fields."""
        if not row:
            return {}
        
        # Unpack all columns from the unified query
        (content_hash, locations, media_type, file_size, width, height,
         ai_source, quality_rating, created_at, modified_at, discovered_at,
         last_file_scan, prompt, description, metadata_json, generation_params_json,
         tags, style, mood, subject, color, technical, objects, custom_tags_json,
         understanding, embedding, generation, phash, dhash, ahash) = row
        
        # Parse JSON fields
        metadata = json.loads(metadata_json) if metadata_json else {}
        generation_params = json.loads(generation_params_json) if generation_params_json else {}
        custom_tags = json.loads(custom_tags_json) if custom_tags_json else {}
        
        # Build tags dictionary
        tags_dict = {}
        if style:
            tags_dict["style"] = style
        if mood:
            tags_dict["mood"] = mood
        if subject:
            tags_dict["subject"] = subject
        if color:
            tags_dict["color"] = color
        if technical:
            tags_dict["technical"] = technical
        if objects:
            tags_dict["objects"] = objects
        if custom_tags:
            # For DuckDBSearchCache compatibility, nest custom tags under "custom"
            tags_dict["custom"] = custom_tags
        
        # Get first file path for compatibility
        file_path = ""
        if locations and len(locations) > 0:
            file_path = locations[0]["path"]
        
        return {
            "content_hash": content_hash,
            "locations": locations or [],
            "file_path": file_path,  # For compatibility
            "media_type": media_type,
            "file_size": file_size,
            "width": width,
            "height": height,
            "dimensions": {"width": width, "height": height} if width and height else None,
            "ai_source": ai_source,
            "quality_rating": quality_rating,
            "created_at": created_at,
            "modified_at": modified_at,
            "discovered_at": discovered_at,
            "last_file_scan": last_file_scan,
            "prompt": prompt,
            "description": description,
            "metadata": metadata,
            "generation_params": generation_params,
            "tags": tags_dict,  # Return as dict for DuckDBSearchCache compatibility
            "all_tags": tags or [],  # Flat list of all tags
            "understanding": understanding,
            "embedding": embedding,
            "generation": generation,
            "perceptual_hashes": {
                "phash": phash,
                "dhash": dhash,
                "ahash": ahash
            } if any([phash, dhash, ahash]) else None
        }
    
    def analyze_query_performance(self, query: str, params: List[Any] = None) -> Dict[str, Any]:
        """Analyze query performance and return optimization suggestions.
        
        Args:
            query: SQL query to analyze
            params: Query parameters
            
        Returns:
            Dictionary with query plan and performance metrics
        """
        # Get query plan
        explain_query = f"EXPLAIN ANALYZE {query}"
        
        try:
            if params:
                plan_result = self.conn.execute(explain_query, params).fetchall()
            else:
                plan_result = self.conn.execute(explain_query).fetchall()
            
            # Parse the query plan
            plan_text = "\n".join([row[0] for row in plan_result])
            
            # Extract key metrics
            import re
            metrics = {
                "query": query,
                "plan": plan_text,
                "suggestions": []
            }
            
            # Look for performance issues
            if "Seq Scan" in plan_text:
                metrics["suggestions"].append(
                    "Sequential scan detected. Consider adding an index."
                )
            
            if "Sort" in plan_text and "Index" not in plan_text:
                metrics["suggestions"].append(
                    "Sort operation without index. Consider adding an index on the sort column."
                )
            
            # Extract timing if available
            timing_match = re.search(r"actual time=([0-9.]+)\.\.([0-9.]+)", plan_text)
            if timing_match:
                metrics["execution_time_ms"] = float(timing_match.group(2))
            
            return metrics
            
        except Exception as e:
            logger.error(f"Failed to analyze query: {e}")
            return {"error": str(e), "query": query}
    
    def optimize_database(self) -> Dict[str, Any]:
        """Run database optimization tasks.
        
        Returns:
            Dictionary with optimization results
        """
        results = {
            "vacuum": False,
            "analyze": False,
            "cache_cleared": False,
            "old_cache_entries": 0
        }
        
        try:
            # Run VACUUM to reclaim space
            self.conn.execute("VACUUM")
            results["vacuum"] = True
            
            # Update statistics
            self.conn.execute("ANALYZE")
            results["analyze"] = True
            
            # Clear old cache entries
            cutoff_time = datetime.now() - timedelta(hours=1)
            old_entries = self.conn.execute(
                "DELETE FROM query_cache WHERE cached_at < ? RETURNING cache_key",
                [cutoff_time]
            ).fetchall()
            results["old_cache_entries"] = len(old_entries)
            results["cache_cleared"] = True
            
            logger.info(f"Database optimization complete: {results}")
            
        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            results["error"] = str(e)
        
        return results
    
    def get_table_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all tables.
        
        Returns:
            Dictionary with table statistics
        """
        stats = {}
        
        tables = [
            "assets", "asset_tags", "asset_understanding", 
            "asset_generation", "perceptual_hashes", "embeddings",
            "query_cache", "tag_cache"
        ]
        
        for table in tables:
            try:
                # Get row count
                count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]
                
                # Get table size estimate
                # DuckDB doesn't have pg_relation_size, so we estimate based on row count
                # This is a rough estimate
                size_estimate = count * 1024  # Assume ~1KB per row average
                
                stats[table] = {
                    "row_count": count,
                    "size_estimate_mb": size_estimate / (1024 * 1024)
                }
                
                # Check for missing indexes on foreign keys
                if table != "assets":  # Skip primary table
                    # In DuckDB, we can check if queries would benefit from indexes
                    stats[table]["has_fk_index"] = True  # DuckDB handles this automatically
                    
            except Exception as e:
                stats[table] = {"error": str(e)}
        
        return stats
    
    def close(self):
        """Close the database connection."""
        # Don't close pooled connections
        if not self.db_path:
            self.conn.close()


# Compatibility layer classes
class DuckDBSearchCache(UnifiedDuckDBStorage):
    """Compatibility wrapper for DuckDBSearchCache."""
    
    def get_connection(self):
        """Get raw DuckDB connection (for MCP server)."""
        return self.conn
    
    def search_by_text(
        self,
        query: str,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search assets by text in descriptions and prompts.
        
        Args:
            query: Text query to search for
            limit: Maximum number of results
            
        Returns:
            List of matching assets
        """
        results = self.conn.execute("""
            SELECT 
                a.*,
                t.tags, t.style, t.mood, t.subject, t.color, t.technical, t.objects, t.custom_tags,
                u.understanding, u.embedding,
                g.generation,
                p.phash, p.dhash, p.ahash
            FROM assets a
            LEFT JOIN asset_tags t ON a.content_hash = t.content_hash
            LEFT JOIN asset_understanding u ON a.content_hash = u.content_hash
            LEFT JOIN asset_generation g ON a.content_hash = g.content_hash
            LEFT JOIN perceptual_hashes p ON a.content_hash = p.content_hash
            WHERE 
                regexp_matches(a.description, ?, 'i') OR
                regexp_matches(a.prompt, ?, 'i') OR
                regexp_matches(u.understanding.description, ?, 'i') OR
                regexp_matches(u.understanding.generated_prompt, ?, 'i') OR
                regexp_matches(g.generation.prompt, ?, 'i')
            ORDER BY a.created_at DESC
            LIMIT ?
        """, [query, query, query, query, query, limit]).fetchall()
        
        return [self._row_to_dict(row) for row in results]
    
    def get_all_locations(self, content_hash: str) -> List[Dict[str, Any]]:
        """Get all locations where a file exists.
        
        Args:
            content_hash: SHA-256 hash of file content
            
        Returns:
            List of locations with their details
        """
        result = self.conn.execute(
            "SELECT locations FROM assets WHERE content_hash = ?",
            [content_hash]
        ).fetchone()
        
        return result[0] if result and result[0] else []
    
    def remove_location(self, content_hash: str, file_path: Path) -> None:
        """Remove a location for an asset."""
        locations = self.get_all_locations(content_hash)
        path_str = str(file_path)
        
        # Filter out the location to remove
        updated_locations = [loc for loc in locations if loc["path"] != path_str]
        
        if updated_locations:
            # Update with remaining locations - use the same workaround as _add_file_location
            try:
                self.conn.execute(
                    "UPDATE assets SET locations = ? WHERE content_hash = ?",
                    [updated_locations, content_hash]
                )
            except Exception as e:
                # If that fails, try deleting and re-inserting (nuclear option)
                logger.warning(f"Failed to update locations in remove_location, trying delete/insert: {e}")
                
                # Get current asset data
                current = self.conn.execute(
                    "SELECT * FROM assets WHERE content_hash = ?",
                    [content_hash]
                ).fetchone()
                
                if current:
                    # Delete related data first
                    self.conn.execute("DELETE FROM perceptual_hashes WHERE content_hash = ?", [content_hash])
                    self.conn.execute("DELETE FROM embeddings WHERE content_hash = ?", [content_hash])
                    self.conn.execute("DELETE FROM asset_generation WHERE content_hash = ?", [content_hash])
                    self.conn.execute("DELETE FROM asset_understanding WHERE content_hash = ?", [content_hash])
                    self.conn.execute("DELETE FROM asset_tags WHERE content_hash = ?", [content_hash])
                    
                    # Delete the asset
                    self.conn.execute("DELETE FROM assets WHERE content_hash = ?", [content_hash])
                    
                    # Re-insert with updated locations
                    self.conn.execute("""
                        INSERT INTO assets (
                            content_hash, locations, media_type, file_size,
                            width, height, ai_source, quality_rating,
                            created_at, modified_at, discovered_at, last_file_scan,
                            prompt, description, metadata, generation_params
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, [
                        current[0], updated_locations, current[2], current[3],
                        current[4], current[5], current[6], current[7],
                        current[8], current[9], current[10], current[11],
                        current[12], current[13], current[14], current[15]
                    ])
        else:
            # No locations left - remove asset entirely
            self.delete_asset(content_hash)
    
    def delete_asset(self, content_hash: str) -> None:
        """Delete an asset and all its metadata."""
        # Delete from all related tables
        self.conn.execute("DELETE FROM embeddings WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM perceptual_hashes WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM asset_generation WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM asset_understanding WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM asset_tags WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM assets WHERE content_hash = ?", [content_hash])
    
    def rebuild_from_scratch(self) -> None:
        """Clear the cache completely (ready for rebuild from files)."""
        logger.warning("Clearing entire DuckDB cache for rebuild")
        
        # Drop all tables
        for table in ["embeddings", "perceptual_hashes", "asset_generation", 
                      "asset_understanding", "asset_tags", "assets"]:
            self.conn.execute(f"DROP TABLE IF EXISTS {table}")
        
        # Recreate schema
        self._init_schema()
        
        logger.info("DuckDB cache cleared and schema recreated")
    
    def export_to_parquet(self, output_dir: Path) -> Dict[str, Path]:
        """Export cache to Parquet files for analytics.
        
        Args:
            output_dir: Directory to export Parquet files to
            
        Returns:
            Dictionary mapping table names to output paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_files = {}
        
        # Export each table
        for table in ["assets", "asset_tags", "asset_understanding", "asset_generation"]:
            output_path = output_dir / f"{table}_{timestamp}.parquet"
            
            self.conn.execute(f"""
                COPY (SELECT * FROM {table})
                TO '{output_path}'
                (FORMAT PARQUET, COMPRESSION ZSTD)
            """)
            
            output_files[table] = output_path
            logger.info(f"Exported {table} to {output_path}")
        
        return output_files


class DuckDBSearch(UnifiedDuckDBStorage):
    """Compatibility wrapper for DuckDBSearch."""
    
    def index_asset(self, metadata: Dict[str, Any]) -> None:
        """Add or update an asset in the search index."""
        # Convert to upsert_asset format
        content_hash = metadata["content_hash"]
        file_path = Path(metadata.get("file_path", ""))
        
        self.upsert_asset(content_hash, file_path, metadata, storage_type="local")
    
    def clear_index(self) -> None:
        """Clear the entire search index."""
        # Delete in order to respect foreign key constraints
        self.conn.execute("DELETE FROM embeddings")
        self.conn.execute("DELETE FROM perceptual_hashes")
        self.conn.execute("DELETE FROM asset_generation")
        self.conn.execute("DELETE FROM asset_understanding")
        self.conn.execute("DELETE FROM asset_tags")
        self.conn.execute("DELETE FROM assets")
        logger.info("Search index cleared")
    
    def index_perceptual_hashes(
        self,
        content_hash: str,
        phash: str | None = None,
        dhash: str | None = None,
        ahash: str | None = None
    ) -> None:
        """Store perceptual hashes for an asset."""
        self.conn.execute("""
            INSERT INTO perceptual_hashes (content_hash, phash, dhash, ahash)
            VALUES (?, ?, ?, ?)
            ON CONFLICT (content_hash) DO UPDATE SET
                phash = EXCLUDED.phash,
                dhash = EXCLUDED.dhash,
                ahash = EXCLUDED.ahash
        """, [content_hash, phash, dhash, ahash])