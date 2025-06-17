"""Analytics and statistics functionality for DuckDB storage."""

import json
from datetime import datetime, timedelta
from typing import Any

from ..core.structured_logging import get_logger
from .duckdb_base import DuckDBBase

logger = get_logger(__name__)


class DuckDBAnalytics(DuckDBBase):
    """Analytics operations for assets in DuckDB."""

    def get_statistics(self) -> dict[str, Any]:
        """Get overall statistics about stored assets."""
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
            ORDER BY count DESC
        """).fetchall()
        stats["by_media_type"] = {mt: count for mt, count in media_types}

        # Assets by AI source
        ai_sources = self.conn.execute("""
            SELECT ai_source, COUNT(*) as count
            FROM assets
            GROUP BY ai_source
            ORDER BY count DESC
        """).fetchall()
        stats["by_ai_source"] = {source: count for source, count in ai_sources}

        # Quality distribution
        quality_dist = self.conn.execute("""
            SELECT quality_rating, COUNT(*) as count
            FROM assets
            WHERE quality_rating IS NOT NULL
            GROUP BY quality_rating
            ORDER BY quality_rating DESC
        """).fetchall()
        stats["quality_distribution"] = {rating: count for rating, count in quality_dist}

        # Storage statistics
        storage_stats = self.conn.execute("""
            SELECT 
                COUNT(*) as total_files,
                SUM(file_size) as total_size,
                AVG(file_size) as avg_size,
                MIN(file_size) as min_size,
                MAX(file_size) as max_size
            FROM assets
        """).fetchone()

        stats["storage"] = {
            "total_files": storage_stats[0],
            "total_size_bytes": storage_stats[1] or 0,
            "total_size_mb": (storage_stats[1] or 0) / (1024 * 1024),
            "total_size_gb": (storage_stats[1] or 0) / (1024 * 1024 * 1024),
            "average_size_mb": (storage_stats[2] or 0) / (1024 * 1024),
            "min_size_bytes": storage_stats[3] or 0,
            "max_size_bytes": storage_stats[4] or 0,
        }

        # Recent activity
        recent_stats = self.conn.execute("""
            SELECT 
                COUNT(CASE WHEN discovered_at > ? THEN 1 END) as added_24h,
                COUNT(CASE WHEN discovered_at > ? THEN 1 END) as added_7d,
                COUNT(CASE WHEN discovered_at > ? THEN 1 END) as added_30d
            FROM assets
        """, [
            datetime.now() - timedelta(days=1),
            datetime.now() - timedelta(days=7),
            datetime.now() - timedelta(days=30),
        ]).fetchone()

        stats["recent_activity"] = {
            "added_24h": recent_stats[0],
            "added_7d": recent_stats[1],
            "added_30d": recent_stats[2],
        }

        # Tag statistics
        tag_stats = self.conn.execute("""
            SELECT 
                COUNT(DISTINCT content_hash) as tagged_assets,
                COUNT(*) as total_tags,
                COUNT(DISTINCT tag_value) as unique_tags
            FROM tags
        """).fetchone()

        stats["tags"] = {
            "tagged_assets": tag_stats[0],
            "total_tags": tag_stats[1],
            "unique_tags": tag_stats[2],
        }

        # Top tags
        top_tags = self.conn.execute("""
            SELECT tag_value, COUNT(*) as count
            FROM tags
            GROUP BY tag_value
            ORDER BY count DESC
            LIMIT 20
        """).fetchall()
        stats["top_tags"] = [{"tag": tag, "count": count} for tag, count in top_tags]

        # Understanding statistics
        understanding_stats = self.conn.execute("""
            SELECT 
                provider,
                COUNT(*) as count,
                SUM(cost) as total_cost,
                AVG(cost) as avg_cost
            FROM understanding
            GROUP BY provider
        """).fetchall()

        stats["understanding"] = {}
        for provider, count, total_cost, avg_cost in understanding_stats:
            stats["understanding"][provider] = {
                "analyses": count,
                "total_cost": total_cost or 0,
                "average_cost": avg_cost or 0,
            }

        return stats

    def get_facets(self, filters: dict[str, Any] | None = None) -> dict[str, list[dict[str, Any]]]:
        """Get faceted counts for filtering."""
        facets = {}

        # Build base WHERE clause from filters
        where_conditions = []
        params = []

        if filters:
            for key, value in filters.items():
                if key == "media_type" and value:
                    where_conditions.append("media_type = ?")
                    params.append(value)
                elif key == "ai_source" and value:
                    where_conditions.append("ai_source = ?")
                    params.append(value)
                elif key == "project" and value:
                    where_conditions.append("project = ?")
                    params.append(value)

        where_clause = " WHERE " + " AND ".join(where_conditions) if where_conditions else ""

        # Media type facets
        query = f"""
            SELECT media_type, COUNT(*) as count
            FROM assets
            {where_clause}
            GROUP BY media_type
            ORDER BY count DESC
        """
        media_types = self.conn.execute(query, params).fetchall()
        facets["media_types"] = [
            {"value": mt, "count": count} for mt, count in media_types if mt
        ]

        # AI source facets
        query = f"""
            SELECT ai_source, COUNT(*) as count
            FROM assets
            {where_clause}
            GROUP BY ai_source
            ORDER BY count DESC
        """
        ai_sources = self.conn.execute(query, params).fetchall()
        facets["ai_sources"] = [
            {"value": source, "count": count} for source, count in ai_sources if source
        ]

        # Project facets
        query = f"""
            SELECT project, COUNT(*) as count
            FROM assets
            {where_clause}
            GROUP BY project
            ORDER BY count DESC
            LIMIT 20
        """
        projects = self.conn.execute(query, params).fetchall()
        facets["projects"] = [
            {"value": proj, "count": count} for proj, count in projects if proj
        ]

        # Quality rating facets
        quality_where = "WHERE quality_rating IS NOT NULL"
        if where_clause:
            quality_where = where_clause + " AND quality_rating IS NOT NULL"

        query = f"""
            SELECT quality_rating, COUNT(*) as count
            FROM assets
            {quality_where}
            GROUP BY quality_rating
            ORDER BY quality_rating DESC
        """
        quality_ratings = self.conn.execute(query, params).fetchall()
        facets["quality_ratings"] = [
            {"value": rating, "count": count} for rating, count in quality_ratings
        ]

        # Tag facets - check cache first
        cache_key = f"tags_{where_clause}_{json.dumps(params)}"
        cached = self.conn.execute("""
            SELECT tag_counts, cached_at
            FROM tag_cache
            WHERE cache_key = ?
            AND cached_at > ?
        """, [cache_key, datetime.now() - timedelta(minutes=5)]).fetchone()

        if cached:
            facets["tags"] = json.loads(cached[0])
        else:
            # Calculate tag facets
            if where_clause:
                # Need to join with assets table
                tag_query = f"""
                    SELECT t.tag_type, t.tag_value, COUNT(DISTINCT t.content_hash) as count
                    FROM tags t
                    INNER JOIN assets a ON t.content_hash = a.content_hash
                    {where_clause}
                    GROUP BY t.tag_type, t.tag_value
                    ORDER BY count DESC
                    LIMIT 100
                """
                tags = self.conn.execute(tag_query, params).fetchall()
            else:
                # Simple query without filters
                tags = self.conn.execute("""
                    SELECT tag_type, tag_value, COUNT(DISTINCT content_hash) as count
                    FROM tags
                    GROUP BY tag_type, tag_value
                    ORDER BY count DESC
                    LIMIT 100
                """).fetchall()

            # Group tags by type
            tag_groups = {}
            for tag_type, tag_value, count in tags:
                if tag_type not in tag_groups:
                    tag_groups[tag_type] = []
                tag_groups[tag_type].append({"value": tag_value, "count": count})

            facets["tags"] = tag_groups

            # Cache the result
            self.conn.execute("""
                INSERT OR REPLACE INTO tag_cache (cache_key, tag_counts, cached_at)
                VALUES (?, ?, ?)
            """, [cache_key, json.dumps(tag_groups), datetime.now()])

        return facets

    def get_table_stats(self) -> dict[str, dict[str, Any]]:
        """Get statistics about database tables."""
        tables = ["assets", "tags", "understanding", "generation_metadata",
                  "perceptual_hashes", "query_cache", "tag_cache"]

        stats = {}
        for table in tables:
            # Get row count
            count = self.conn.execute(f"SELECT COUNT(*) FROM {table}").fetchone()[0]

            # Get table size (approximate)
            # DuckDB doesn't have direct table size info like SQLite's page_count
            # So we estimate based on data
            size_query = f"""
                SELECT 
                    COUNT(*) * 1000 as estimated_size
                FROM {table}
            """
            size = self.conn.execute(size_query).fetchone()[0]

            stats[table] = {
                "row_count": count,
                "estimated_size_bytes": size,
                "estimated_size_mb": size / (1024 * 1024)
            }

        # Get total database size
        if self.db_path:
            try:
                stats["total_size_bytes"] = self.db_path.stat().st_size
                stats["total_size_mb"] = stats["total_size_bytes"] / (1024 * 1024)
            except Exception:
                pass

        return stats

    def analyze_query_performance(self, query: str, params: list[Any] | None = None) -> dict[str, Any]:
        """Analyze query performance using EXPLAIN."""
        try:
            # Get query plan
            explain_query = f"EXPLAIN {query}"
            if params:
                plan = self.conn.execute(explain_query, params).fetchall()
            else:
                plan = self.conn.execute(explain_query).fetchall()

            # Get query profile if available
            profile_query = f"EXPLAIN ANALYZE {query}"
            try:
                if params:
                    profile = self.conn.execute(profile_query, params).fetchall()
                else:
                    profile = self.conn.execute(profile_query).fetchall()
            except Exception:
                profile = None

            return {
                "query": query,
                "plan": [str(row) for row in plan],
                "profile": [str(row) for row in profile] if profile else None,
                "status": "analyzed"
            }

        except Exception as e:
            logger.error(f"Query analysis failed: {e}")
            return {
                "query": query,
                "error": str(e),
                "status": "failed"
            }
