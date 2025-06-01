"""DuckDB search cache implementation.

This is a cache that can be rebuilt from files at any time.
All metadata is embedded in files - this just provides fast search.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import duckdb

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class DuckDBSearchCache:
    """Search cache using DuckDB for fast analytical queries.
    
    This is NOT the source of truth - files are! This cache can be
    completely rebuilt by scanning files and extracting their metadata.
    """
    
    def __init__(self, db_path: Path = None):
        """Initialize DuckDB search cache.
        
        Args:
            db_path: Path to DuckDB database file. If None, uses in-memory database.
        """
        self.db_path = db_path
        if db_path:
            self.conn = duckdb.connect(str(db_path))
        else:
            self.conn = duckdb.connect()
        
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        # Main assets table
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
                
                -- Core metadata (extracted from files)
                media_type VARCHAR,
                file_size BIGINT,
                created_at TIMESTAMP,
                modified_at TIMESTAMP,
                
                -- When we last extracted metadata from file
                last_file_scan TIMESTAMP,
                metadata_version VARCHAR
            );
        """)
        
        # Tags table with nested structure
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_tags (
                content_hash VARCHAR PRIMARY KEY,
                
                -- Standard tags as arrays
                style VARCHAR[],
                mood VARCHAR[],
                subject VARCHAR[],
                color VARCHAR[],
                technical VARCHAR[],
                objects VARCHAR[],
                
                -- Custom tags as JSON for flexibility
                custom_tags JSON
            );
        """)
        
        # AI Understanding table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_understanding (
                content_hash VARCHAR PRIMARY KEY,
                
                -- AI Understanding (from file metadata)
                understanding STRUCT(
                    description TEXT,
                    generated_prompt TEXT,
                    negative_prompt TEXT,
                    provider VARCHAR,
                    model VARCHAR,
                    cost DECIMAL(10,6),
                    analyzed_at TIMESTAMP
                ),
                
                -- Model outputs (for comparison)
                model_outputs JSON,
                
                -- Embeddings for similarity search
                embedding FLOAT[1536]  -- OpenAI ada-002 size
            );
        """)
        
        # Generation info table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS asset_generation (
                content_hash VARCHAR PRIMARY KEY,
                
                -- Generation details (from file metadata)
                generation STRUCT(
                    provider VARCHAR,
                    model VARCHAR,
                    prompt TEXT,
                    parameters JSON,
                    cost DECIMAL(10,6),
                    generated_at TIMESTAMP
                )
            );
        """)
        
        # Create indexes for fast search
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_media_type ON assets(media_type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_created ON assets(created_at)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_modified ON assets(modified_at)")
    
    def upsert_asset(
        self,
        content_hash: str,
        file_path: Path,
        metadata: Dict[str, Any],
        storage_type: str = "local",
        file_size: Optional[int] = None,
        created_at: Optional[datetime] = None,
        modified_at: Optional[datetime] = None
    ) -> None:
        """Insert or update an asset in the cache.
        
        Args:
            content_hash: SHA-256 hash of file content
            file_path: Path to the file
            metadata: Metadata extracted from file
            storage_type: Type of storage (local, s3, gcs, network)
            file_size: File size in bytes (optional, will stat file if not provided)
            created_at: Creation time (optional, will stat file if not provided)
            modified_at: Modification time (optional, will stat file if not provided)
        """
        # Extract file stats if not provided
        if file_size is None or created_at is None or modified_at is None:
            try:
                file_stat = file_path.stat()
                if file_size is None:
                    file_size = file_stat.st_size
                if created_at is None:
                    created_at = datetime.fromtimestamp(file_stat.st_ctime)
                if modified_at is None:
                    modified_at = datetime.fromtimestamp(file_stat.st_mtime)
            except (FileNotFoundError, OSError):
                # File might not exist locally (e.g., S3)
                if file_size is None:
                    file_size = 0
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
            # Insert new asset
            self.conn.execute("""
                INSERT INTO assets (
                    content_hash, 
                    locations,
                    media_type,
                    file_size,
                    created_at,
                    modified_at,
                    last_file_scan,
                    metadata_version
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, [
                content_hash,
                [{
                    "path": str(file_path),
                    "storage_type": storage_type,
                    "last_verified": datetime.now(),
                    "has_embedded_metadata": True
                }],
                metadata.get("media_type", "unknown"),
                file_size,
                created_at,
                modified_at,
                datetime.now(),
                metadata.get("metadata_version", "1.0")
            ])
        
        # Update tags if present
        if "tags" in metadata:
            self._upsert_tags(content_hash, metadata["tags"])
        
        # Update understanding if present
        if "understanding" in metadata:
            self._upsert_understanding(content_hash, metadata["understanding"])
        
        # Update generation info if present
        if "generation" in metadata:
            self._upsert_generation(content_hash, metadata["generation"])
    
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
                
                # Update locations (DuckDB has strict foreign key enforcement)
                # Temporarily disable foreign key checks isn't supported in DuckDB
                # So we need to use a transaction
                try:
                    self.conn.execute(
                        "UPDATE assets SET locations = ? WHERE content_hash = ?",
                        [locations, content_hash]
                    )
                except Exception as e:
                    # Log and re-raise
                    logger.error(f"Failed to update locations for {content_hash}: {e}")
                    raise
    
    def _upsert_tags(self, content_hash: str, tags: Dict[str, List[str]]) -> None:
        """Insert or update tags for an asset."""
        # Separate standard and custom tags
        standard_tags = ["style", "mood", "subject", "color", "technical", "objects"]
        
        # Build custom tags
        custom_tags = {}
        for k, v in tags.items():
            if k not in standard_tags:
                custom_tags[k] = v
        
        self.conn.execute("""
            INSERT INTO asset_tags (
                content_hash, style, mood, subject, color, technical, objects, custom_tags
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT (content_hash) DO UPDATE SET
                style = EXCLUDED.style,
                mood = EXCLUDED.mood,
                subject = EXCLUDED.subject,
                color = EXCLUDED.color,
                technical = EXCLUDED.technical,
                objects = EXCLUDED.objects,
                custom_tags = EXCLUDED.custom_tags
        """, [
            content_hash,
            tags.get("style", []),
            tags.get("mood", []),
            tags.get("subject", []),
            tags.get("color", []),
            tags.get("technical", []),
            tags.get("objects", []),
            json.dumps(custom_tags) if custom_tags else None
        ])
    
    def _upsert_understanding(self, content_hash: str, understanding: Dict[str, Any]) -> None:
        """Insert or update AI understanding for an asset."""
        # Extract understanding data
        understanding_struct = {
            "description": understanding.get("description"),
            "generated_prompt": understanding.get("generated_prompt"),
            "negative_prompt": understanding.get("negative_prompt"),
            "provider": understanding.get("provider"),
            "model": understanding.get("model"),
            "cost": understanding.get("cost"),
            "analyzed_at": understanding.get("analyzed_at")
        }
        
        # Model outputs for comparison
        model_outputs = understanding.get("model_outputs", {})
        
        # Embedding if available
        embedding = understanding.get("embedding")
        
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
    
    def search_by_tags(
        self,
        tags: Dict[str, List[str]],
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Search assets by tags.
        
        Args:
            tags: Dictionary of tag categories and values to search for
            limit: Maximum number of results
            
        Returns:
            List of matching assets with their metadata
        """
        conditions = []
        params = []
        
        # Build conditions for each tag category
        for category, values in tags.items():
            if category in ["style", "mood", "subject", "color", "technical", "objects"]:
                # Use DuckDB's list_has_any for array search
                conditions.append(f"list_has_any(t.{category}, ?::VARCHAR[])")
                params.append(values)
            else:
                # Search in custom tags JSON
                for value in values:
                    conditions.append(f"json_extract_string(t.custom_tags, '$.{category}') IS NOT NULL")
                    # No param needed for JSON path
        
        if not conditions:
            return []
        
        query = f"""
            SELECT 
                a.content_hash,
                a.locations,
                a.media_type,
                a.file_size,
                a.created_at,
                t.style,
                t.mood,
                t.subject,
                t.color,
                t.technical,
                t.objects,
                t.custom_tags,
                u.understanding,
                g.generation
            FROM assets a
            LEFT JOIN asset_tags t ON a.content_hash = t.content_hash
            LEFT JOIN asset_understanding u ON a.content_hash = u.content_hash
            LEFT JOIN asset_generation g ON a.content_hash = g.content_hash
            WHERE {' OR '.join(conditions)}
            ORDER BY a.created_at DESC
            LIMIT ?
        """
        
        params.append(limit)
        results = self.conn.execute(query, params).fetchall()
        
        # Convert to dictionaries
        return [self._row_to_dict(row) for row in results]
    
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
                a.content_hash,
                a.locations,
                a.media_type,
                a.file_size,
                a.created_at,
                t.style,
                t.mood,
                t.subject,
                t.color,
                t.technical,
                t.objects,
                t.custom_tags,
                u.understanding,
                g.generation
            FROM assets a
            LEFT JOIN asset_tags t ON a.content_hash = t.content_hash
            LEFT JOIN asset_understanding u ON a.content_hash = u.content_hash
            LEFT JOIN asset_generation g ON a.content_hash = g.content_hash
            WHERE 
                regexp_matches(u.understanding.description, ?, 'i') OR
                regexp_matches(u.understanding.generated_prompt, ?, 'i') OR
                regexp_matches(g.generation.prompt, ?, 'i')
            ORDER BY a.created_at DESC
            LIMIT ?
        """, [query, query, query, limit]).fetchall()
        
        return [self._row_to_dict(row) for row in results]
    
    def get_asset_by_hash(self, content_hash: str) -> Optional[Dict[str, Any]]:
        """Get a single asset by content hash.
        
        Args:
            content_hash: SHA-256 hash of file content
            
        Returns:
            Asset metadata or None if not found
        """
        result = self.conn.execute("""
            SELECT 
                a.content_hash,
                a.locations,
                a.media_type,
                a.file_size,
                a.created_at,
                t.style,
                t.mood,
                t.subject,
                t.color,
                t.technical,
                t.objects,
                t.custom_tags,
                u.understanding,
                g.generation
            FROM assets a
            LEFT JOIN asset_tags t ON a.content_hash = t.content_hash
            LEFT JOIN asset_understanding u ON a.content_hash = u.content_hash
            LEFT JOIN asset_generation g ON a.content_hash = g.content_hash
            WHERE a.content_hash = ?
        """, [content_hash]).fetchone()
        
        return self._row_to_dict(result) if result else None
    
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
        """Remove a location for an asset.
        
        Args:
            content_hash: SHA-256 hash of file content
            file_path: Path to remove
        """
        locations = self.get_all_locations(content_hash)
        path_str = str(file_path)
        
        # Filter out the location to remove
        updated_locations = [loc for loc in locations if loc["path"] != path_str]
        
        if updated_locations:
            # Update with remaining locations
            self.conn.execute(
                "UPDATE assets SET locations = ? WHERE content_hash = ?",
                [updated_locations, content_hash]
            )
        else:
            # No locations left - remove asset entirely
            self.delete_asset(content_hash)
    
    def delete_asset(self, content_hash: str) -> None:
        """Delete an asset and all its metadata.
        
        Args:
            content_hash: SHA-256 hash of file content
        """
        # Delete from all related tables
        self.conn.execute("DELETE FROM asset_generation WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM asset_understanding WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM asset_tags WHERE content_hash = ?", [content_hash])
        self.conn.execute("DELETE FROM assets WHERE content_hash = ?", [content_hash])
    
    def rebuild_from_scratch(self) -> None:
        """Clear the cache completely (ready for rebuild from files)."""
        logger.warning("Clearing entire DuckDB cache for rebuild")
        
        # Drop all tables
        for table in ["asset_generation", "asset_understanding", "asset_tags", "assets"]:
            self.conn.execute(f"DROP TABLE IF EXISTS {table}")
        
        # Recreate schema
        self._init_schema()
        
        logger.info("DuckDB cache cleared and schema recreated")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
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
        
        # Assets with tags
        stats["assets_with_tags"] = self.conn.execute(
            "SELECT COUNT(*) FROM asset_tags"
        ).fetchone()[0]
        
        # Assets with understanding
        stats["assets_with_understanding"] = self.conn.execute(
            "SELECT COUNT(*) FROM asset_understanding"
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
        
        return stats
    
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
    
    def _row_to_dict(self, row: Tuple) -> Dict[str, Any]:
        """Convert a database row to dictionary."""
        if not row:
            return {}
        
        # Build tags dictionary from separate columns
        tags = {}
        if len(row) > 5:
            # Standard tags (columns 5-10)
            if row[5]:  # style
                tags["style"] = row[5]
            if row[6]:  # mood
                tags["mood"] = row[6]
            if row[7]:  # subject
                tags["subject"] = row[7]
            if row[8]:  # color
                tags["color"] = row[8]
            if row[9]:  # technical
                tags["technical"] = row[9]
            if row[10]:  # objects
                tags["objects"] = row[10]
            
            # Custom tags from JSON (column 11)
            if len(row) > 11 and row[11]:
                try:
                    custom = json.loads(row[11])
                    tags["custom"] = custom
                except:
                    pass
        
        return {
            "content_hash": row[0],
            "locations": row[1] or [],
            "media_type": row[2],
            "file_size": row[3],
            "created_at": row[4],
            "tags": tags,
            "understanding": row[12] if len(row) > 12 else {},
            "generation": row[13] if len(row) > 13 else {}
        }
    
    def close(self):
        """Close the database connection."""
        self.conn.close()