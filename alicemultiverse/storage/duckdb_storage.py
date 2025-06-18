"""Core storage operations for DuckDB."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from ..core.structured_logging import get_logger
from .duckdb_base import DuckDBBase
from .batch_operations import BatchOperationsMixin

logger = get_logger(__name__)


class DuckDBStorage(DuckDBBase, BatchOperationsMixin):
    """Storage operations for assets in DuckDB."""

    def upsert_asset(
        self,
        content_hash: str,
        file_path: Path | str,
        metadata: dict[str, Any],
        storage_type: str = "local",
        storage_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Upsert asset with location tracking.

        Args:
            content_hash: Content hash of the asset
            file_path: Path to the file
            metadata: Asset metadata
            storage_type: Type of storage (local, s3, etc.)
            storage_metadata: Additional storage-specific metadata
        """
        file_path = Path(file_path)
        now = datetime.now()

        # Check if asset exists
        existing = self.conn.execute(
            "SELECT locations, metadata FROM assets WHERE content_hash = ?",
            [content_hash]
        ).fetchone()

        if existing:
            # Update existing asset
            locations, existing_metadata = existing
            locations = json.loads(locations) if locations else []
            existing_metadata = json.loads(existing_metadata) if existing_metadata else {}

            # Add new location if not already present
            self._add_file_location(
                content_hash, file_path, locations, storage_type, storage_metadata
            )

            # Merge metadata
            merged_metadata = {**existing_metadata, **metadata}

            # Update asset
            self.conn.execute("""
                UPDATE assets SET
                    locations = ?,
                    modified_at = ?,
                    metadata = ?
                WHERE content_hash = ?
            """, [
                json.dumps(locations),
                now,
                json.dumps(merged_metadata),
                content_hash
            ])

        else:
            # Insert new asset
            locations = [{
                "path": str(file_path),
                "storage_type": storage_type,
                "added_at": now.isoformat(),
                "metadata": storage_metadata or {}
            }]

            # Extract fields from metadata
            media_type = metadata.get("media_type", "unknown")
            file_size = metadata.get("file_size", 0)
            ai_source = metadata.get("ai_source", "unknown")
            quality_rating = metadata.get("quality_rating")
            quality_score = metadata.get("quality_score")
            description = metadata.get("description", "")
            prompt = metadata.get("prompt", "")
            project = metadata.get("project", "default")
            collection = metadata.get("collection", "")

            # Handle timestamps
            created_at = self._parse_timestamp(metadata.get("created_at", now))
            modified_at = self._parse_timestamp(metadata.get("modified_at", now))
            discovered_at = self._parse_timestamp(metadata.get("discovered_at", now))

            self.conn.execute("""
                INSERT INTO assets (
                    content_hash, locations, media_type, file_size,
                    ai_source, quality_rating, quality_score,
                    description, prompt, created_at, modified_at,
                    discovered_at, project, collection, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                content_hash, json.dumps(locations), media_type, file_size,
                ai_source, quality_rating, quality_score,
                description, prompt, created_at, modified_at,
                discovered_at, project, collection, json.dumps(metadata)
            ])

        # Update tags if present
        if "tags" in metadata:
            self._upsert_tags(content_hash, metadata["tags"])

        # Update understanding if present
        if "understanding" in metadata:
            self._upsert_understanding(content_hash, metadata["understanding"])

        # Update generation metadata if present
        if any(key in metadata for key in ["provider", "model", "negative_prompt", "parameters"]):
            self._upsert_generation(content_hash, metadata)

        logger.debug(f"Upserted asset {content_hash} at {file_path}")

    def _add_file_location(
        self,
        content_hash: str,
        file_path: Path,
        locations: list[dict[str, Any]],
        storage_type: str = "local",
        storage_metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a file location to the locations list if not already present."""
        path_str = str(file_path)

        # Check if location already exists
        for loc in locations:
            if loc["path"] == path_str:
                # Update metadata if provided
                if storage_metadata:
                    loc["metadata"] = storage_metadata
                loc["last_verified"] = datetime.now().isoformat()
                return

        # Add new location
        locations.append({
            "path": path_str,
            "storage_type": storage_type,
            "added_at": datetime.now().isoformat(),
            "metadata": storage_metadata or {}
        })

    def _upsert_tags(self, content_hash: str, tags: list[str] | dict[str, list[str]]) -> None:
        """Upsert tags for an asset."""
        # Delete existing tags
        self.conn.execute("DELETE FROM tags WHERE content_hash = ?", [content_hash])

        # Insert new tags
        if isinstance(tags, list):
            # Simple tag list
            for tag in tags:
                self.conn.execute("""
                    INSERT INTO tags (content_hash, tag_type, tag_value, source)
                    VALUES (?, ?, ?, ?)
                """, [content_hash, "general", tag, "user"])

        elif isinstance(tags, dict):
            # Categorized tags
            for tag_type, tag_list in tags.items():
                for tag in tag_list:
                    # Handle tags with confidence scores
                    if isinstance(tag, dict) and "value" in tag:
                        self.conn.execute("""
                            INSERT INTO tags (content_hash, tag_type, tag_value, confidence, source)
                            VALUES (?, ?, ?, ?, ?)
                        """, [
                            content_hash, tag_type, tag["value"],
                            tag.get("confidence", 1.0), tag.get("source", "ai")
                        ])
                    else:
                        self.conn.execute("""
                            INSERT INTO tags (content_hash, tag_type, tag_value, source)
                            VALUES (?, ?, ?, ?)
                        """, [content_hash, tag_type, tag, "ai"])

    def _upsert_understanding(self, content_hash: str, understanding: dict[str, Any]) -> None:
        """Upsert understanding analysis results."""
        provider = understanding.get("provider", "unknown")
        model = understanding.get("model", "")
        description = understanding.get("description", "")
        cost = understanding.get("cost", 0.0)
        analysis_date = self._parse_timestamp(understanding.get("analysis_date", datetime.now()))

        # Remove fields that are stored separately
        metadata = {k: v for k, v in understanding.items()
                   if k not in ["provider", "model", "description", "cost", "analysis_date"]}

        self.conn.execute("""
            INSERT OR REPLACE INTO understanding (
                content_hash, provider, model, analysis_date,
                description, cost, metadata
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            content_hash, provider, model, analysis_date,
            description, cost, json.dumps(metadata)
        ])

    def _upsert_generation(self, content_hash: str, generation: dict[str, Any]) -> None:
        """Upsert generation metadata."""
        self.conn.execute("""
            INSERT OR REPLACE INTO generation_metadata (
                content_hash, provider, model, prompt,
                negative_prompt, parameters, generation_date
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            content_hash,
            generation.get("provider"),
            generation.get("model"),
            generation.get("prompt"),
            generation.get("negative_prompt"),
            json.dumps(generation.get("parameters", {})),
            self._parse_timestamp(generation.get("generation_date", datetime.now()))
        ])

    def get_asset_by_hash(self, content_hash: str) -> dict[str, Any] | None:
        """Get asset by content hash."""
        result = self.conn.execute("""
            SELECT * FROM assets WHERE content_hash = ?
        """, [content_hash]).fetchone()

        if not result:
            return None

        asset = self._row_to_dict(result)

        # Get tags
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

        return asset

    def get_all_locations(self, content_hash: str) -> list[dict[str, Any]]:
        """Get all locations where an asset exists."""
        result = self.conn.execute(
            "SELECT locations FROM assets WHERE content_hash = ?",
            [content_hash]
        ).fetchone()

        if not result or not result[0]:
            return []

        locations = json.loads(result[0])
        return locations if isinstance(locations, list) else []

    def remove_location(self, content_hash: str, file_path: Path) -> None:
        """Remove a specific location for an asset."""
        result = self.conn.execute(
            "SELECT locations FROM assets WHERE content_hash = ?",
            [content_hash]
        ).fetchone()

        if not result or not result[0]:
            return

        locations = json.loads(result[0])
        path_str = str(file_path)

        # Filter out the location
        new_locations = [loc for loc in locations if loc["path"] != path_str]

        if new_locations:
            # Update with remaining locations
            self.conn.execute(
                "UPDATE assets SET locations = ? WHERE content_hash = ?",
                [json.dumps(new_locations), content_hash]
            )
        else:
            # No locations left, delete the asset
            self.delete_asset(content_hash)

    def delete_asset(self, content_hash: str) -> None:
        """Delete an asset and all related data."""
        # Delete from all tables
        self.conn.execute("DELETE FROM assets WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM tags WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM understanding WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM generation_metadata WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM perceptual_hashes WHERE content_hash = ?", [content_hash])

        logger.info(f"Deleted asset {content_hash}")

    def upsert_assets_batch(
        self,
        assets: list[tuple[str, Path | str, dict[str, Any]]],
        storage_type: str = "local",
        batch_size: int = 100,
    ) -> dict[str, Any]:
        """Batch upsert multiple assets for performance.

        Args:
            assets: List of (content_hash, file_path, metadata) tuples
            storage_type: Type of storage for all assets
            batch_size: Number of assets to process at once

        Returns:
            Summary of the operation
        """
        total = len(assets)
        processed = 0
        errors = []

        for i in range(0, total, batch_size):
            batch = assets[i:i + batch_size]

            try:
                # Start transaction for batch
                self.conn.execute("BEGIN TRANSACTION")

                for content_hash, file_path, metadata in batch:
                    try:
                        self.upsert_asset(
                            content_hash, file_path, metadata, storage_type
                        )
                        processed += 1
                    except Exception as e:
                        errors.append({
                            "content_hash": content_hash,
                            "file_path": str(file_path),
                            "error": str(e)
                        })

                # Commit batch
                self.conn.execute("COMMIT")

            except Exception as e:
                # Rollback on batch error
                self.conn.execute("ROLLBACK")
                logger.error(f"Batch upsert failed: {e}")
                errors.extend([{
                    "content_hash": item[0],
                    "file_path": str(item[1]),
                    "error": f"Batch error: {e}"
                } for item in batch])

        return {
            "total": total,
            "processed": processed,
            "errors": errors,
            "success_rate": processed / total if total > 0 else 0
        }

    def set_asset_role(self, content_hash: str, role: str) -> bool:
        """Set the role of an asset.

        Args:
            content_hash: Content hash of the asset
            role: Role to set (e.g., 'primary', 'b-roll', 'reference')

        Returns:
            True if successful, False otherwise
        """
        try:
            self.conn.execute("""
                UPDATE assets
                SET asset_role = ?, modified_at = ?
                WHERE content_hash = ?
            """, [role, datetime.now(), content_hash])

            # Check if the update was successful by verifying the role
            check_result = self.conn.execute(
                "SELECT asset_role FROM assets WHERE content_hash = ?",
                [content_hash]
            ).fetchone()

            return check_result is not None and check_result[0] == role

        except Exception as e:
            logger.error(f"Failed to set asset role: {e}")
            return False

    def get_assets_by_role(self, role: str, limit: int = 100) -> list[dict[str, Any]]:
        """Get all assets with a specific role.

        Args:
            role: Role to filter by
            limit: Maximum number of results

        Returns:
            List of assets with the specified role
        """
        results = self.conn.execute("""
            SELECT * FROM assets
            WHERE asset_role = ?
            ORDER BY modified_at DESC
            LIMIT ?
        """, [role, limit]).fetchall()

        return [self._row_to_dict(row) for row in results]
