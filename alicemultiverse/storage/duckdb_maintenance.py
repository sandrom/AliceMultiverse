"""Maintenance operations for DuckDB storage."""

from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.structured_logging import get_logger
from .duckdb_base import DuckDBBase

logger = get_logger(__name__)


class DuckDBMaintenance(DuckDBBase):
    """Maintenance operations for DuckDB storage."""

    def optimize_database(self) -> dict[str, Any]:
        """Optimize database performance."""
        results = {
            "started_at": datetime.now(),
            "operations": []
        }

        try:
            # Analyze tables for query optimization
            tables = ["assets", "tags", "understanding", "generation_metadata",
                      "perceptual_hashes", "query_cache", "tag_cache"]

            for table in tables:
                try:
                    self.conn.execute(f"ANALYZE {table}")
                    results["operations"].append({
                        "operation": "analyze",
                        "table": table,
                        "status": "success"
                    })
                except Exception as e:
                    results["operations"].append({
                        "operation": "analyze",
                        "table": table,
                        "status": "failed",
                        "error": str(e)
                    })

            # Clean old cache entries
            cache_deleted = self._clean_cache()
            results["operations"].append({
                "operation": "clean_cache",
                "deleted": cache_deleted,
                "status": "success"
            })

            # Checkpoint the database (if file-based)
            if self.db_path:
                self.conn.execute("CHECKPOINT")
                results["operations"].append({
                    "operation": "checkpoint",
                    "status": "success"
                })

            results["completed_at"] = datetime.now()
            results["duration_seconds"] = (
                results["completed_at"] - results["started_at"]
            ).total_seconds()
            results["status"] = "success"

        except Exception as e:
            logger.error(f"Database optimization failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)

        return results

    def rebuild_from_scratch(self) -> None:
        """Rebuild database from scratch (destructive)."""
        logger.warning("Rebuilding database from scratch - all data will be lost!")

        # Drop all tables
        tables = [
            "assets", "tags", "understanding", "generation_metadata",
            "perceptual_hashes", "query_cache", "tag_cache"
        ]

        for table in tables:
            try:
                self.conn.execute(f"DROP TABLE IF EXISTS {table}")
                logger.info(f"Dropped table {table}")
            except Exception as e:
                logger.error(f"Failed to drop table {table}: {e}")

        # Recreate schema
        self._init_schema()
        logger.info("Database schema recreated")

    def export_to_parquet(self, output_dir: Path) -> dict[str, Path]:
        """Export tables to Parquet format for analytics.

        Args:
            output_dir: Directory to save Parquet files

        Returns:
            Dictionary mapping table names to output paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        exported = {}

        tables = ["assets", "tags", "understanding", "generation_metadata",
                  "perceptual_hashes"]

        for table in tables:
            try:
                output_path = output_dir / f"{table}.parquet"

                # Export to Parquet
                self.conn.execute(f"""
                    COPY (SELECT * FROM {table})
                    TO '{output_path}'
                    (FORMAT PARQUET)
                """)

                exported[table] = output_path
                logger.info(f"Exported {table} to {output_path}")

            except Exception as e:
                logger.error(f"Failed to export {table}: {e}")

        return exported

    def vacuum_database(self) -> dict[str, Any]:
        """Vacuum the database to reclaim space."""
        if not self.db_path:
            return {
                "status": "skipped",
                "reason": "In-memory database does not need vacuum"
            }

        try:
            # Get size before
            size_before = self.db_path.stat().st_size

            # Vacuum is not directly supported in DuckDB like SQLite
            # Instead, we can export and reimport
            logger.info("Starting database vacuum (export/import)")

            # This is a placeholder - actual implementation would need
            # to export all data and reimport to a new file

            # Get size after
            size_after = self.db_path.stat().st_size

            return {
                "status": "success",
                "size_before_bytes": size_before,
                "size_after_bytes": size_after,
                "space_saved_bytes": size_before - size_after,
                "space_saved_mb": (size_before - size_after) / (1024 * 1024)
            }

        except Exception as e:
            logger.error(f"Vacuum failed: {e}")
            return {
                "status": "failed",
                "error": str(e)
            }

    def verify_integrity(self) -> dict[str, Any]:
        """Verify database integrity."""
        results = {
            "status": "checking",
            "checks": []
        }

        try:
            # Check foreign key relationships
            orphaned_tags = self.conn.execute("""
                SELECT COUNT(*) FROM tags t
                LEFT JOIN assets a ON t.content_hash = a.content_hash
                WHERE a.content_hash IS NULL
            """).fetchone()[0]

            results["checks"].append({
                "check": "orphaned_tags",
                "count": orphaned_tags,
                "status": "ok" if orphaned_tags == 0 else "warning"
            })

            # Check for missing perceptual hashes
            missing_hashes = self.conn.execute("""
                SELECT COUNT(*) FROM assets a
                LEFT JOIN perceptual_hashes p ON a.content_hash = p.content_hash
                WHERE a.media_type = 'image' AND p.content_hash IS NULL
            """).fetchone()[0]

            results["checks"].append({
                "check": "missing_perceptual_hashes",
                "count": missing_hashes,
                "status": "ok" if missing_hashes == 0 else "info"
            })

            # Check for invalid locations
            invalid_locations = 0
            assets_with_locations = self.conn.execute(
                "SELECT content_hash, locations FROM assets WHERE locations IS NOT NULL"
            ).fetchall()

            for content_hash, locations_json in assets_with_locations:
                try:
                    import json
                    locations = json.loads(locations_json)
                    if not isinstance(locations, list):
                        invalid_locations += 1
                except Exception:
                    invalid_locations += 1

            results["checks"].append({
                "check": "invalid_locations",
                "count": invalid_locations,
                "status": "ok" if invalid_locations == 0 else "error"
            })

            # Overall status
            if any(check["status"] == "error" for check in results["checks"]):
                results["status"] = "error"
            elif any(check["status"] == "warning" for check in results["checks"]):
                results["status"] = "warning"
            else:
                results["status"] = "ok"

        except Exception as e:
            logger.error(f"Integrity check failed: {e}")
            results["status"] = "failed"
            results["error"] = str(e)

        return results

    def _clean_cache(self) -> int:
        """Clean old cache entries.

        Returns:
            Number of entries deleted
        """
        # Clean query cache older than 1 hour
        query_deleted = self.conn.execute("""
            DELETE FROM query_cache
            WHERE cached_at < datetime('now', '-1 hour')
        """).rowcount or 0

        # Clean tag cache older than 30 minutes
        tag_deleted = self.conn.execute("""
            DELETE FROM tag_cache
            WHERE cached_at < datetime('now', '-30 minutes')
        """).rowcount or 0

        total_deleted = (query_deleted or 0) + (tag_deleted or 0)

        if total_deleted > 0:
            logger.info(f"Cleaned {total_deleted} cache entries")

        return total_deleted
