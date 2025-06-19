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
                    if asset is not None:
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

    # TODO: Review unreachable code - def search_by_tags(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - tags: list[str],
    # TODO: Review unreachable code - tag_type: str | None = None,
    # TODO: Review unreachable code - match_all: bool = False,
    # TODO: Review unreachable code - limit: int = 100,
    # TODO: Review unreachable code - offset: int = 0,
    # TODO: Review unreachable code - ) -> tuple[list[dict[str, Any]], int]:
    # TODO: Review unreachable code - """Search assets by tags.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - tags: List of tags to search for
    # TODO: Review unreachable code - tag_type: Specific tag type to search in
    # TODO: Review unreachable code - match_all: Require all tags to match
    # TODO: Review unreachable code - limit: Maximum results
    # TODO: Review unreachable code - offset: Skip results

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Tuple of (results, total_count)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not tags:
    # TODO: Review unreachable code - return [], 0

    # TODO: Review unreachable code - # Build tag query
    # TODO: Review unreachable code - tag_conditions = []
    # TODO: Review unreachable code - params = []

    # TODO: Review unreachable code - for tag in tags:
    # TODO: Review unreachable code - condition = "tag_value = ?"
    # TODO: Review unreachable code - params.append(tag)

    # TODO: Review unreachable code - if tag_type:
    # TODO: Review unreachable code - condition += " AND tag_type = ?"
    # TODO: Review unreachable code - params.append(tag_type)

    # TODO: Review unreachable code - tag_conditions.append(f"({condition})")

    # TODO: Review unreachable code - if match_all:
    # TODO: Review unreachable code - # All tags must match
    # TODO: Review unreachable code - tag_query = f"""
    # TODO: Review unreachable code - SELECT content_hash
    # TODO: Review unreachable code - FROM tags
    # TODO: Review unreachable code - WHERE {" OR ".join(tag_conditions)}
    # TODO: Review unreachable code - GROUP BY content_hash
    # TODO: Review unreachable code - HAVING COUNT(DISTINCT tag_value) = {len(tags)}
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Any tag can match
    # TODO: Review unreachable code - tag_query = f"""
    # TODO: Review unreachable code - SELECT DISTINCT content_hash
    # TODO: Review unreachable code - FROM tags
    # TODO: Review unreachable code - WHERE {" OR ".join(tag_conditions)}
    # TODO: Review unreachable code - """

    # TODO: Review unreachable code - # Get count
    # TODO: Review unreachable code - count_query = f"SELECT COUNT(*) FROM ({tag_query}) t"
    # TODO: Review unreachable code - total_count = self.conn.execute(count_query, params).fetchone()[0]

    # TODO: Review unreachable code - # Get assets
    # TODO: Review unreachable code - asset_query = f"""
    # TODO: Review unreachable code - SELECT a.*
    # TODO: Review unreachable code - FROM assets a
    # TODO: Review unreachable code - INNER JOIN ({tag_query}) t ON a.content_hash = t.content_hash
    # TODO: Review unreachable code - ORDER BY a.created_at DESC
    # TODO: Review unreachable code - LIMIT {limit} OFFSET {offset}
    # TODO: Review unreachable code - """

    # TODO: Review unreachable code - results = self.conn.execute(asset_query, params).fetchall()
    # TODO: Review unreachable code - # Store column names before doing other queries
    # TODO: Review unreachable code - columns = [desc[0] for desc in self.conn.description]

    # TODO: Review unreachable code - # Convert to dictionaries
    # TODO: Review unreachable code - assets = []
    # TODO: Review unreachable code - for row in results:
    # TODO: Review unreachable code - asset = self._row_to_dict(row, columns)

    # TODO: Review unreachable code - # Add tags
    # TODO: Review unreachable code - content_hash = asset["content_hash"]
    # TODO: Review unreachable code - tags_result = self.conn.execute("""
    # TODO: Review unreachable code - SELECT tag_type, tag_value, confidence, source
    # TODO: Review unreachable code - FROM tags WHERE content_hash = ?
    # TODO: Review unreachable code - ORDER BY tag_type, confidence DESC
    # TODO: Review unreachable code - """, [content_hash]).fetchall()

    # TODO: Review unreachable code - if tags_result:
    # TODO: Review unreachable code - asset["tags"] = {}
    # TODO: Review unreachable code - for tag_type, tag_value, confidence, source in tags_result:
    # TODO: Review unreachable code - if tag_type not in asset["tags"]:
    # TODO: Review unreachable code - asset["tags"][tag_type] = []
    # TODO: Review unreachable code - asset["tags"][tag_type].append({
    # TODO: Review unreachable code - "value": tag_value,
    # TODO: Review unreachable code - "confidence": confidence,
    # TODO: Review unreachable code - "source": source
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - assets.append(asset)

    # TODO: Review unreachable code - return assets, total_count

    # TODO: Review unreachable code - def search_by_text(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - query: str,
    # TODO: Review unreachable code - search_fields: list[str] | None = None,
    # TODO: Review unreachable code - limit: int = 100,
    # TODO: Review unreachable code - offset: int = 0,
    # TODO: Review unreachable code - ) -> tuple[list[dict[str, Any]], int]:
    # TODO: Review unreachable code - """Full-text search across specified fields.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - query: Search query
    # TODO: Review unreachable code - search_fields: Fields to search in (default: prompt, description)
    # TODO: Review unreachable code - limit: Maximum results
    # TODO: Review unreachable code - offset: Skip results

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Tuple of (results, total_count)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not query:
    # TODO: Review unreachable code - return [], 0

    # TODO: Review unreachable code - if not search_fields:
    # TODO: Review unreachable code - search_fields = ["prompt", "description"]

    # TODO: Review unreachable code - # Build search conditions
    # TODO: Review unreachable code - conditions = []
    # TODO: Review unreachable code - params = []

    # TODO: Review unreachable code - for field in search_fields:
    # TODO: Review unreachable code - if field in ["prompt", "description"]:
    # TODO: Review unreachable code - # Use FTS if available
    # TODO: Review unreachable code - conditions.append(f"{field} MATCH ?")
    # TODO: Review unreachable code - params.append(query)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Use LIKE for other fields
    # TODO: Review unreachable code - conditions.append(f"{field} LIKE ?")
    # TODO: Review unreachable code - params.append(f"%{query}%")

    # TODO: Review unreachable code - where_clause = " OR ".join(conditions)

    # TODO: Review unreachable code - # Get count
    # TODO: Review unreachable code - count_query = f"SELECT COUNT(*) FROM assets WHERE {where_clause}"
    # TODO: Review unreachable code - total_count = self.conn.execute(count_query, params).fetchone()[0]

    # TODO: Review unreachable code - # Get results
    # TODO: Review unreachable code - search_query = f"""
    # TODO: Review unreachable code - SELECT * FROM assets
    # TODO: Review unreachable code - WHERE {where_clause}
    # TODO: Review unreachable code - ORDER BY created_at DESC
    # TODO: Review unreachable code - LIMIT {limit} OFFSET {offset}
    # TODO: Review unreachable code - """

    # TODO: Review unreachable code - results = self.conn.execute(search_query, params).fetchall()

    # TODO: Review unreachable code - # Convert to dictionaries
    # TODO: Review unreachable code - assets = [self._row_to_dict(row) for row in results]

    # TODO: Review unreachable code - return assets, total_count

    # TODO: Review unreachable code - def search_with_cache(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - filters: dict[str, Any] | None = None,
    # TODO: Review unreachable code - sort_by: str = "created_at",
    # TODO: Review unreachable code - sort_order: str = "desc",
    # TODO: Review unreachable code - limit: int = 100,
    # TODO: Review unreachable code - offset: int = 0,
    # TODO: Review unreachable code - cache_ttl: int = 300,  # 5 minutes
    # TODO: Review unreachable code - ) -> tuple[list[dict[str, Any]], int]:
    # TODO: Review unreachable code - """Search with query caching for performance.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - filters: Search filters
    # TODO: Review unreachable code - sort_by: Sort field
    # TODO: Review unreachable code - sort_order: Sort order
    # TODO: Review unreachable code - limit: Maximum results
    # TODO: Review unreachable code - offset: Skip results
    # TODO: Review unreachable code - cache_ttl: Cache time-to-live in seconds

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Tuple of (results, total_count)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Generate cache key
    # TODO: Review unreachable code - cache_data = {
    # TODO: Review unreachable code - "filters": filters or {},
    # TODO: Review unreachable code - "sort_by": sort_by,
    # TODO: Review unreachable code - "sort_order": sort_order,
    # TODO: Review unreachable code - "limit": limit,
    # TODO: Review unreachable code - "offset": offset
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - cache_key = hashlib.md5(json.dumps(cache_data, sort_keys=True).encode()).hexdigest()

    # TODO: Review unreachable code - # Check cache
    # TODO: Review unreachable code - cutoff_time = datetime.now() - timedelta(seconds=cache_ttl)
    # TODO: Review unreachable code - cached = self.conn.execute("""
    # TODO: Review unreachable code - SELECT results, total_count
    # TODO: Review unreachable code - FROM query_cache
    # TODO: Review unreachable code - WHERE cache_key = ? AND cached_at > ?
    # TODO: Review unreachable code - """, [cache_key, cutoff_time]).fetchone()

    # TODO: Review unreachable code - if cached:
    # TODO: Review unreachable code - results = json.loads(cached[0])
    # TODO: Review unreachable code - total_count = cached[1]
    # TODO: Review unreachable code - logger.debug(f"Cache hit for query {cache_key}")
    # TODO: Review unreachable code - return results, total_count

    # TODO: Review unreachable code - # Execute search
    # TODO: Review unreachable code - results, total_count = self.search(
    # TODO: Review unreachable code - filters, sort_by, sort_order, limit, offset, include_metadata=True
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Cache results
    # TODO: Review unreachable code - self.conn.execute("""
    # TODO: Review unreachable code - INSERT OR REPLACE INTO query_cache (cache_key, results, total_count, cached_at)
    # TODO: Review unreachable code - VALUES (?, ?, ?, ?)
    # TODO: Review unreachable code - """, [cache_key, json.dumps(results, default=str), total_count, datetime.now()])

    # TODO: Review unreachable code - # Clean old cache entries
    # TODO: Review unreachable code - self.conn.execute(
    # TODO: Review unreachable code - "DELETE FROM query_cache WHERE cached_at < ?",
    # TODO: Review unreachable code - [datetime.now() - timedelta(hours=1)]
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - return results, total_count

    # TODO: Review unreachable code - def _apply_search_filters(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - filters: dict[str, Any]
    # TODO: Review unreachable code - ) -> tuple[str, list[Any]]:
    # TODO: Review unreachable code - """Apply search filters to build WHERE clause.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - filters: Dictionary of filters

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Tuple of (where_clause, parameters)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - conditions = []
    # TODO: Review unreachable code - params = []

    # TODO: Review unreachable code - for key, value in filters.items():
    # TODO: Review unreachable code - if value is None:
    # TODO: Review unreachable code - continue

    # TODO: Review unreachable code - # Handle different filter types
    # TODO: Review unreachable code - if key == "content_hash":
    # TODO: Review unreachable code - conditions.append("content_hash = ?")
    # TODO: Review unreachable code - params.append(value)

    # TODO: Review unreachable code - elif key == "media_type":
    # TODO: Review unreachable code - conditions.append("media_type = ?")
    # TODO: Review unreachable code - params.append(value)

    # TODO: Review unreachable code - elif key == "ai_source":
    # TODO: Review unreachable code - if isinstance(value, list):
    # TODO: Review unreachable code - placeholders = ",".join("?" * len(value))
    # TODO: Review unreachable code - conditions.append(f"ai_source IN ({placeholders})")
    # TODO: Review unreachable code - params.extend(value)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - conditions.append("ai_source = ?")
    # TODO: Review unreachable code - params.append(value)

    # TODO: Review unreachable code - elif key == "quality_rating":
    # TODO: Review unreachable code - if isinstance(value, dict):
    # TODO: Review unreachable code - if value is not None and "min" in value:
    # TODO: Review unreachable code - conditions.append("quality_rating >= ?")
    # TODO: Review unreachable code - params.append(value["min"])
    # TODO: Review unreachable code - if value is not None and "max" in value:
    # TODO: Review unreachable code - conditions.append("quality_rating <= ?")
    # TODO: Review unreachable code - params.append(value["max"])
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - conditions.append("quality_rating = ?")
    # TODO: Review unreachable code - params.append(value)

    # TODO: Review unreachable code - elif key == "file_size":
    # TODO: Review unreachable code - if isinstance(value, dict):
    # TODO: Review unreachable code - if value is not None and "min" in value:
    # TODO: Review unreachable code - conditions.append("file_size >= ?")
    # TODO: Review unreachable code - params.append(value["min"])
    # TODO: Review unreachable code - if value is not None and "max" in value:
    # TODO: Review unreachable code - conditions.append("file_size <= ?")
    # TODO: Review unreachable code - params.append(value["max"])
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - conditions.append("file_size = ?")
    # TODO: Review unreachable code - params.append(value)

    # TODO: Review unreachable code - elif key == "created_after":
    # TODO: Review unreachable code - conditions.append("created_at >= ?")
    # TODO: Review unreachable code - params.append(self._parse_timestamp(value))

    # TODO: Review unreachable code - elif key == "created_before":
    # TODO: Review unreachable code - conditions.append("created_at <= ?")
    # TODO: Review unreachable code - params.append(self._parse_timestamp(value))

    # TODO: Review unreachable code - elif key == "project":
    # TODO: Review unreachable code - conditions.append("project = ?")
    # TODO: Review unreachable code - params.append(value)

    # TODO: Review unreachable code - elif key == "collection":
    # TODO: Review unreachable code - conditions.append("collection = ?")
    # TODO: Review unreachable code - params.append(value)

    # TODO: Review unreachable code - elif key == "asset_role":
    # TODO: Review unreachable code - if isinstance(value, list):
    # TODO: Review unreachable code - placeholders = ",".join("?" * len(value))
    # TODO: Review unreachable code - conditions.append(f"asset_role IN ({placeholders})")
    # TODO: Review unreachable code - params.extend(value)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - conditions.append("asset_role = ?")
    # TODO: Review unreachable code - params.append(value)

    # TODO: Review unreachable code - elif key == "has_prompt":
    # TODO: Review unreachable code - if value:
    # TODO: Review unreachable code - conditions.append("prompt IS NOT NULL AND prompt != ''")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - conditions.append("(prompt IS NULL OR prompt = '')")

    # TODO: Review unreachable code - elif key == "has_description":
    # TODO: Review unreachable code - if value:
    # TODO: Review unreachable code - conditions.append("description IS NOT NULL AND description != ''")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - conditions.append("(description IS NULL OR description = '')")

    # TODO: Review unreachable code - elif key == "tags":
    # TODO: Review unreachable code - # Handle tag filters
    # TODO: Review unreachable code - if isinstance(value, list):
    # TODO: Review unreachable code - # Search for assets with any of these tags
    # TODO: Review unreachable code - tag_query = """
    # TODO: Review unreachable code - EXISTS (
    # TODO: Review unreachable code - SELECT 1 FROM tags t
    # TODO: Review unreachable code - WHERE t.content_hash = assets.content_hash
    # TODO: Review unreachable code - AND t.tag_value IN ({})
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - """.format(",".join("?" * len(value)))
    # TODO: Review unreachable code - conditions.append(tag_query)
    # TODO: Review unreachable code - params.extend(value)
    # TODO: Review unreachable code - elif isinstance(value, dict):
    # TODO: Review unreachable code - # Search for specific tag types
    # TODO: Review unreachable code - for tag_type, tag_values in value.items():
    # TODO: Review unreachable code - if isinstance(tag_values, list):
    # TODO: Review unreachable code - tag_query = """
    # TODO: Review unreachable code - EXISTS (
    # TODO: Review unreachable code - SELECT 1 FROM tags t
    # TODO: Review unreachable code - WHERE t.content_hash = assets.content_hash
    # TODO: Review unreachable code - AND t.tag_type = ?
    # TODO: Review unreachable code - AND t.tag_value IN ({})
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - """.format(",".join("?" * len(tag_values)))
    # TODO: Review unreachable code - conditions.append(tag_query)
    # TODO: Review unreachable code - params.append(tag_type)
    # TODO: Review unreachable code - params.extend(tag_values)

    # TODO: Review unreachable code - where_clause = " AND ".join(conditions) if conditions else ""
    # TODO: Review unreachable code - return where_clause, params

    # TODO: Review unreachable code - def _map_sort_field(self, field: str) -> str:
    # TODO: Review unreachable code - """Map user-friendly sort field names to database columns."""
    # TODO: Review unreachable code - field_mapping = {
    # TODO: Review unreachable code - "created": "created_at",
    # TODO: Review unreachable code - "modified": "modified_at",
    # TODO: Review unreachable code - "discovered": "discovered_at",
    # TODO: Review unreachable code - "size": "file_size",
    # TODO: Review unreachable code - "quality": "quality_rating",
    # TODO: Review unreachable code - "score": "quality_score",
    # TODO: Review unreachable code - "type": "media_type",
    # TODO: Review unreachable code - "source": "ai_source",
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - return field_mapping.get(field, field) or 0
