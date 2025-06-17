"""Search functionality for DuckDB storage."""

import hashlib
import json
from datetime import datetime, timedelta
from typing import Any

from ..core.structured_logging import get_logger
from .duckdb_base import DuckDBBase

logger = get_logger(__name__)


class DuckDBSearch(DuckDBBase):
    """Search operations for assets in DuckDB."""

    def search(
        self,
        filters: dict[str, Any] | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 100,
        offset: int = 0,
        include_metadata: bool = True,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search assets with filters and pagination.
        
        Args:
            filters: Search filters
            sort_by: Field to sort by
            sort_order: Sort order (asc/desc)
            limit: Maximum results to return
            offset: Number of results to skip
            include_metadata: Include full metadata in results
            
        Returns:
            Tuple of (results, total_count)
        """
        # Build query
        base_query = "SELECT * FROM assets"
        count_query = "SELECT COUNT(*) FROM assets"

        where_clause, params = self._apply_search_filters(filters or {})

        if where_clause:
            base_query += f" WHERE {where_clause}"
            count_query += f" WHERE {where_clause}"

        # Get total count
        total_count = self.conn.execute(count_query, params).fetchone()[0]

        # Add sorting and pagination
        sort_field = self._map_sort_field(sort_by)
        base_query += f" ORDER BY {sort_field} {sort_order.upper()}"
        base_query += f" LIMIT {limit} OFFSET {offset}"

        # Execute search
        results = self.conn.execute(base_query, params).fetchall()
        # Store column names before doing other queries
        columns = [desc[0] for desc in self.conn.description]

        # Convert to dictionaries
        assets = []
        for row in results:
            asset = self._row_to_dict(row, columns)

            if include_metadata:
                # Add tags
                content_hash = asset["content_hash"]
                tags_result = self.conn.execute("""
                    SELECT tag_type, tag_value, confidence, source
                    FROM tags WHERE content_hash = ?
                    ORDER BY tag_type, confidence DESC
                """, [content_hash]).fetchall()

                if tags_result:
                    asset["tags"] = {}
                    for tag_type, tag_value, confidence, source in tags_result:
                        if tag_type not in asset["tags"]:
                            asset["tags"][tag_type] = []
                        asset["tags"][tag_type].append({
                            "value": tag_value,
                            "confidence": confidence,
                            "source": source
                        })

            assets.append(asset)

        return assets, total_count

    def search_by_tags(
        self,
        tags: list[str],
        tag_type: str | None = None,
        match_all: bool = False,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Search assets by tags.
        
        Args:
            tags: List of tags to search for
            tag_type: Specific tag type to search in
            match_all: Require all tags to match
            limit: Maximum results
            offset: Skip results
            
        Returns:
            Tuple of (results, total_count)
        """
        if not tags:
            return [], 0

        # Build tag query
        tag_conditions = []
        params = []

        for tag in tags:
            condition = "tag_value = ?"
            params.append(tag)

            if tag_type:
                condition += " AND tag_type = ?"
                params.append(tag_type)

            tag_conditions.append(f"({condition})")

        if match_all:
            # All tags must match
            tag_query = f"""
                SELECT content_hash 
                FROM tags 
                WHERE {" OR ".join(tag_conditions)}
                GROUP BY content_hash
                HAVING COUNT(DISTINCT tag_value) = {len(tags)}
            """
        else:
            # Any tag can match
            tag_query = f"""
                SELECT DISTINCT content_hash 
                FROM tags 
                WHERE {" OR ".join(tag_conditions)}
            """

        # Get count
        count_query = f"SELECT COUNT(*) FROM ({tag_query}) t"
        total_count = self.conn.execute(count_query, params).fetchone()[0]

        # Get assets
        asset_query = f"""
            SELECT a.* 
            FROM assets a
            INNER JOIN ({tag_query}) t ON a.content_hash = t.content_hash
            ORDER BY a.created_at DESC
            LIMIT {limit} OFFSET {offset}
        """

        results = self.conn.execute(asset_query, params).fetchall()
        # Store column names before doing other queries
        columns = [desc[0] for desc in self.conn.description]

        # Convert to dictionaries
        assets = []
        for row in results:
            asset = self._row_to_dict(row, columns)

            # Add tags
            content_hash = asset["content_hash"]
            tags_result = self.conn.execute("""
                SELECT tag_type, tag_value, confidence, source
                FROM tags WHERE content_hash = ?
                ORDER BY tag_type, confidence DESC
            """, [content_hash]).fetchall()

            if tags_result:
                asset["tags"] = {}
                for tag_type, tag_value, confidence, source in tags_result:
                    if tag_type not in asset["tags"]:
                        asset["tags"][tag_type] = []
                    asset["tags"][tag_type].append({
                        "value": tag_value,
                        "confidence": confidence,
                        "source": source
                    })

            assets.append(asset)

        return assets, total_count

    def search_by_text(
        self,
        query: str,
        search_fields: list[str] | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> tuple[list[dict[str, Any]], int]:
        """Full-text search across specified fields.
        
        Args:
            query: Search query
            search_fields: Fields to search in (default: prompt, description)
            limit: Maximum results
            offset: Skip results
            
        Returns:
            Tuple of (results, total_count)
        """
        if not query:
            return [], 0

        if not search_fields:
            search_fields = ["prompt", "description"]

        # Build search conditions
        conditions = []
        params = []

        for field in search_fields:
            if field in ["prompt", "description"]:
                # Use FTS if available
                conditions.append(f"{field} MATCH ?")
                params.append(query)
            else:
                # Use LIKE for other fields
                conditions.append(f"{field} LIKE ?")
                params.append(f"%{query}%")

        where_clause = " OR ".join(conditions)

        # Get count
        count_query = f"SELECT COUNT(*) FROM assets WHERE {where_clause}"
        total_count = self.conn.execute(count_query, params).fetchone()[0]

        # Get results
        search_query = f"""
            SELECT * FROM assets 
            WHERE {where_clause}
            ORDER BY created_at DESC
            LIMIT {limit} OFFSET {offset}
        """

        results = self.conn.execute(search_query, params).fetchall()

        # Convert to dictionaries
        assets = [self._row_to_dict(row) for row in results]

        return assets, total_count

    def search_with_cache(
        self,
        filters: dict[str, Any] | None = None,
        sort_by: str = "created_at",
        sort_order: str = "desc",
        limit: int = 100,
        offset: int = 0,
        cache_ttl: int = 300,  # 5 minutes
    ) -> tuple[list[dict[str, Any]], int]:
        """Search with query caching for performance.
        
        Args:
            filters: Search filters
            sort_by: Sort field
            sort_order: Sort order
            limit: Maximum results
            offset: Skip results
            cache_ttl: Cache time-to-live in seconds
            
        Returns:
            Tuple of (results, total_count)
        """
        # Generate cache key
        cache_data = {
            "filters": filters or {},
            "sort_by": sort_by,
            "sort_order": sort_order,
            "limit": limit,
            "offset": offset
        }
        cache_key = hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

        # Check cache
        cutoff_time = datetime.now() - timedelta(seconds=cache_ttl)
        cached = self.conn.execute("""
            SELECT results, total_count 
            FROM query_cache 
            WHERE cache_key = ? AND cached_at > ?
        """, [cache_key, cutoff_time]).fetchone()

        if cached:
            results = json.loads(cached[0])
            total_count = cached[1]
            logger.debug(f"Cache hit for query {cache_key}")
            return results, total_count

        # Execute search
        results, total_count = self.search(
            filters, sort_by, sort_order, limit, offset, include_metadata=True
        )

        # Cache results
        self.conn.execute("""
            INSERT OR REPLACE INTO query_cache (cache_key, results, total_count, cached_at)
            VALUES (?, ?, ?, ?)
        """, [cache_key, json.dumps(results, default=str), total_count, datetime.now()])

        # Clean old cache entries
        self.conn.execute(
            "DELETE FROM query_cache WHERE cached_at < ?",
            [datetime.now() - timedelta(hours=1)]
        )

        return results, total_count

    def _apply_search_filters(
        self,
        filters: dict[str, Any]
    ) -> tuple[str, list[Any]]:
        """Apply search filters to build WHERE clause.
        
        Args:
            filters: Dictionary of filters
            
        Returns:
            Tuple of (where_clause, parameters)
        """
        conditions = []
        params = []

        for key, value in filters.items():
            if value is None:
                continue

            # Handle different filter types
            if key == "content_hash":
                conditions.append("content_hash = ?")
                params.append(value)

            elif key == "media_type":
                conditions.append("media_type = ?")
                params.append(value)

            elif key == "ai_source":
                if isinstance(value, list):
                    placeholders = ",".join("?" * len(value))
                    conditions.append(f"ai_source IN ({placeholders})")
                    params.extend(value)
                else:
                    conditions.append("ai_source = ?")
                    params.append(value)

            elif key == "quality_rating":
                if isinstance(value, dict):
                    if "min" in value:
                        conditions.append("quality_rating >= ?")
                        params.append(value["min"])
                    if "max" in value:
                        conditions.append("quality_rating <= ?")
                        params.append(value["max"])
                else:
                    conditions.append("quality_rating = ?")
                    params.append(value)

            elif key == "file_size":
                if isinstance(value, dict):
                    if "min" in value:
                        conditions.append("file_size >= ?")
                        params.append(value["min"])
                    if "max" in value:
                        conditions.append("file_size <= ?")
                        params.append(value["max"])
                else:
                    conditions.append("file_size = ?")
                    params.append(value)

            elif key == "created_after":
                conditions.append("created_at >= ?")
                params.append(self._parse_timestamp(value))

            elif key == "created_before":
                conditions.append("created_at <= ?")
                params.append(self._parse_timestamp(value))

            elif key == "project":
                conditions.append("project = ?")
                params.append(value)

            elif key == "collection":
                conditions.append("collection = ?")
                params.append(value)

            elif key == "asset_role":
                if isinstance(value, list):
                    placeholders = ",".join("?" * len(value))
                    conditions.append(f"asset_role IN ({placeholders})")
                    params.extend(value)
                else:
                    conditions.append("asset_role = ?")
                    params.append(value)

            elif key == "has_prompt":
                if value:
                    conditions.append("prompt IS NOT NULL AND prompt != ''")
                else:
                    conditions.append("(prompt IS NULL OR prompt = '')")

            elif key == "has_description":
                if value:
                    conditions.append("description IS NOT NULL AND description != ''")
                else:
                    conditions.append("(description IS NULL OR description = '')")

            elif key == "tags":
                # Handle tag filters
                if isinstance(value, list):
                    # Search for assets with any of these tags
                    tag_query = """
                        EXISTS (
                            SELECT 1 FROM tags t 
                            WHERE t.content_hash = assets.content_hash 
                            AND t.tag_value IN ({})
                        )
                    """.format(",".join("?" * len(value)))
                    conditions.append(tag_query)
                    params.extend(value)
                elif isinstance(value, dict):
                    # Search for specific tag types
                    for tag_type, tag_values in value.items():
                        if isinstance(tag_values, list):
                            tag_query = """
                                EXISTS (
                                    SELECT 1 FROM tags t 
                                    WHERE t.content_hash = assets.content_hash 
                                    AND t.tag_type = ? 
                                    AND t.tag_value IN ({})
                                )
                            """.format(",".join("?" * len(tag_values)))
                            conditions.append(tag_query)
                            params.append(tag_type)
                            params.extend(tag_values)

        where_clause = " AND ".join(conditions) if conditions else ""
        return where_clause, params

    def _map_sort_field(self, field: str) -> str:
        """Map user-friendly sort field names to database columns."""
        field_mapping = {
            "created": "created_at",
            "modified": "modified_at",
            "discovered": "discovered_at",
            "size": "file_size",
            "quality": "quality_rating",
            "score": "quality_score",
            "type": "media_type",
            "source": "ai_source",
        }

        return field_mapping.get(field, field)
