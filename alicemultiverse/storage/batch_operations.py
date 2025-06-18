"""Batch operations for DuckDB storage to improve performance."""

import logging
from datetime import datetime
from typing import Any, Dict, List, Tuple

from ..monitoring.tracker import track_database_operation, PerformanceTracker

logger = logging.getLogger(__name__)


class BatchOperationsMixin:
    """Mixin for batch database operations."""
    
    @PerformanceTracker.track_db_method
    def batch_upsert_assets(self, assets: List[Dict[str, Any]]) -> int:
        """Batch upsert multiple assets for better performance.
        
        Args:
            assets: List of asset dictionaries with metadata
            
        Returns:
            Number of assets successfully upserted
        """
        if not assets:
            return 0
            
        # Prepare batch data
        asset_data = []
        tag_data = []
        understanding_data = []
        
        for asset in assets:
            content_hash = asset.get("content_hash")
            if not content_hash:
                continue
                
            # Prepare asset record
            asset_data.append((
                content_hash,
                asset.get("file_path", ""),
                asset.get("file_name", ""),
                asset.get("file_size", 0),
                asset.get("media_type", "image"),
                asset.get("width", 0),
                asset.get("height", 0),
                asset.get("duration"),
                asset.get("source_type", "unknown"),
                asset.get("ai_model", ""),
                asset.get("prompt", ""),
                asset.get("negative_prompt", ""),
                asset.get("date_taken", datetime.now()),
                asset.get("date_created", datetime.now()),
                asset.get("date_modified", datetime.now()),
                asset.get("project", ""),
                asset.get("asset_role", "primary"),
                asset.get("metadata", {}),
                datetime.now()  # added_at
            ))
            
            # Prepare tag records
            if "tags" in asset:
                if isinstance(asset["tags"], list):
                    for tag in asset["tags"]:
                        tag_data.append((content_hash, "general", tag, 1.0, "user"))
                elif isinstance(asset["tags"], dict):
                    for tag_type, tag_list in asset["tags"].items():
                        for tag in tag_list:
                            if isinstance(tag, dict):
                                tag_data.append((
                                    content_hash, tag_type, 
                                    tag["value"], tag.get("confidence", 1.0),
                                    tag.get("source", "ai")
                                ))
                            else:
                                tag_data.append((content_hash, tag_type, tag, 1.0, "ai"))
            
            # Prepare understanding records
            if "understanding" in asset:
                understanding = asset["understanding"]
                understanding_data.append((
                    content_hash,
                    understanding.get("provider", "unknown"),
                    understanding.get("model", ""),
                    understanding.get("analysis_date", datetime.now()),
                    understanding.get("description", ""),
                    understanding.get("cost", 0.0),
                    understanding.get("metadata", {})
                ))
        
        try:
            # Begin transaction for atomicity
            self.conn.execute("BEGIN TRANSACTION")
            
            # Batch insert assets
            if asset_data:
                self.conn.executemany("""
                    INSERT OR REPLACE INTO assets (
                        content_hash, file_path, file_name, file_size,
                        media_type, width, height, duration,
                        source_type, ai_model, prompt, negative_prompt,
                        date_taken, date_created, date_modified,
                        project, asset_role, metadata, added_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, asset_data)
            
            # Batch delete and insert tags
            if tag_data:
                # Delete existing tags for these assets
                content_hashes = list(set(t[0] for t in tag_data))
                placeholders = ','.join(['?'] * len(content_hashes))
                self.conn.execute(
                    f"DELETE FROM tags WHERE content_hash IN ({placeholders})",
                    content_hashes
                )
                
                # Insert new tags
                self.conn.executemany("""
                    INSERT INTO tags (content_hash, tag_type, tag_value, confidence, source)
                    VALUES (?, ?, ?, ?, ?)
                """, tag_data)
            
            # Batch insert understanding
            if understanding_data:
                self.conn.executemany("""
                    INSERT OR REPLACE INTO understanding (
                        content_hash, provider, model, analysis_date,
                        description, cost, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, understanding_data)
            
            # Commit transaction
            self.conn.execute("COMMIT")
            
            logger.info(f"Batch upserted {len(asset_data)} assets with {len(tag_data)} tags")
            return len(asset_data)
            
        except Exception as e:
            # Rollback on error
            self.conn.execute("ROLLBACK")
            logger.error(f"Batch upsert failed: {e}")
            raise
    
    def batch_update_tags(self, updates: List[Tuple[str, Dict[str, List[str]]]]) -> int:
        """Batch update tags for multiple assets.
        
        Args:
            updates: List of (content_hash, tags) tuples
            
        Returns:
            Number of assets updated
        """
        if not updates:
            return 0
            
        try:
            self.conn.execute("BEGIN TRANSACTION")
            
            # Prepare all tag data
            all_tag_data = []
            content_hashes = []
            
            for content_hash, tags in updates:
                content_hashes.append(content_hash)
                
                if isinstance(tags, dict):
                    for tag_type, tag_list in tags.items():
                        for tag in tag_list:
                            all_tag_data.append((content_hash, tag_type, tag, 1.0, "user"))
                elif isinstance(tags, list):
                    for tag in tags:
                        all_tag_data.append((content_hash, "general", tag, 1.0, "user"))
            
            # Delete existing tags
            if content_hashes:
                placeholders = ','.join(['?'] * len(content_hashes))
                self.conn.execute(
                    f"DELETE FROM tags WHERE content_hash IN ({placeholders})",
                    content_hashes
                )
            
            # Insert new tags
            if all_tag_data:
                self.conn.executemany("""
                    INSERT INTO tags (content_hash, tag_type, tag_value, confidence, source)
                    VALUES (?, ?, ?, ?, ?)
                """, all_tag_data)
            
            # Update modified timestamps
            self.conn.executemany("""
                UPDATE assets SET modified_at = ? WHERE content_hash = ?
            """, [(datetime.now(), ch) for ch in content_hashes])
            
            self.conn.execute("COMMIT")
            
            logger.info(f"Batch updated tags for {len(content_hashes)} assets")
            return len(content_hashes)
            
        except Exception as e:
            self.conn.execute("ROLLBACK")
            logger.error(f"Batch tag update failed: {e}")
            raise
    
    def batch_search_by_tags(
        self, 
        tag_queries: List[Dict[str, List[str]]], 
        mode: str = "any"
    ) -> Dict[str, List[Dict[str, Any]]]:
        """Batch search for assets by multiple tag queries.
        
        Args:
            tag_queries: List of tag query dictionaries
            mode: "any" or "all" for tag matching
            
        Returns:
            Dictionary mapping query index to results
        """
        results = {}
        
        # Build a single query with UNION for better performance
        query_parts = []
        params = []
        
        for idx, tags in enumerate(tag_queries):
            tag_conditions = []
            
            for tag_type, tag_values in tags.items():
                if tag_values:
                    placeholders = ','.join(['?'] * len(tag_values))
                    tag_conditions.append(
                        f"(tag_type = ? AND tag_value IN ({placeholders}))"
                    )
                    params.extend([tag_type] + tag_values)
            
            if tag_conditions:
                condition = " OR ".join(tag_conditions) if mode == "any" else " AND ".join(tag_conditions)
                
                query_part = f"""
                    SELECT {idx} as query_idx, a.*, 
                           GROUP_CONCAT(t.tag_type || ':' || t.tag_value) as all_tags
                    FROM assets a
                    JOIN tags t ON a.content_hash = t.content_hash
                    WHERE a.content_hash IN (
                        SELECT DISTINCT content_hash FROM tags WHERE {condition}
                    )
                    GROUP BY a.content_hash
                """
                query_parts.append(query_part)
        
        if query_parts:
            full_query = " UNION ALL ".join(query_parts)
            
            # Execute combined query
            rows = self.conn.execute(full_query, params).fetchall()
            
            # Group results by query index
            for row in rows:
                query_idx = row[0]
                if query_idx not in results:
                    results[query_idx] = []
                
                # Convert row to dict (skip query_idx)
                asset = dict(zip([d[0] for d in self.conn.description[1:]], row[1:]))
                results[query_idx].append(asset)
        
        return results