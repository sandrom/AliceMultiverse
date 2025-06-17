"""Base DuckDB connection and schema management for AliceMultiverse."""

import json
import threading
from datetime import datetime
from pathlib import Path
from typing import Any

import duckdb

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class DuckDBBase:
    """Base class for DuckDB operations with connection pooling and schema management."""

    # Class-level connection pool
    _connections = {}
    _connection_lock = threading.Lock()

    def __init__(self, db_path: Path | None = None, read_only: bool = False):
        """Initialize DuckDB connection.
        
        Args:
            db_path: Path to DuckDB database file. If None, uses in-memory database.
            read_only: Open database in read-only mode (better for concurrent reads)
        """
        self.db_path = db_path
        self.read_only = read_only

        # Use connection pooling for file-based databases
        if db_path:
            db_path.parent.mkdir(parents=True, exist_ok=True)
            db_key = (str(db_path), read_only)

            with DuckDBBase._connection_lock:
                if db_key not in DuckDBBase._connections:
                    DuckDBBase._connections[db_key] = duckdb.connect(
                        str(db_path),
                        read_only=read_only
                    )
                self.conn = DuckDBBase._connections[db_key]
        else:
            self.conn = duckdb.connect()

        self._init_schema()
        logger.info(f"DuckDB initialized: {'in-memory' if not db_path else db_path} (read_only={read_only})")

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
                locations JSON,
                
                -- Basic metadata
                media_type VARCHAR,
                file_size BIGINT,
                ai_source VARCHAR,
                
                -- Quality metrics
                quality_rating INTEGER,
                quality_score DOUBLE,
                
                -- Content analysis
                description TEXT,
                prompt TEXT,
                
                -- Temporal
                created_at TIMESTAMP,
                modified_at TIMESTAMP,
                discovered_at TIMESTAMP,
                
                -- Organization
                project VARCHAR,
                collection VARCHAR,
                
                -- Metadata blob for flexibility
                metadata JSON
            );
        """)

        # Create indexes for common queries
        indexes = [
            ("idx_media_type", "media_type"),
            ("idx_ai_source", "ai_source"),
            ("idx_quality", "quality_rating"),
            ("idx_created", "created_at"),
            ("idx_project", "project"),
            ("idx_discovered", "discovered_at"),
        ]

        for idx_name, column in indexes:
            self.conn.execute(f"CREATE INDEX IF NOT EXISTS {idx_name} ON assets({column})")

        # Note: DuckDB FTS syntax is different from SQLite
        # For now, we'll use regular indexes and LIKE queries
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_prompt_text ON assets(prompt)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_description_text ON assets(description)")

        # Normalized tags table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS tags (
                content_hash VARCHAR,
                tag_type VARCHAR,
                tag_value VARCHAR,
                confidence DOUBLE DEFAULT 1.0,
                source VARCHAR,
                PRIMARY KEY (content_hash, tag_type, tag_value)
            );
        """)

        # Tag indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_tag_hash ON tags(content_hash)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_tag_type ON tags(tag_type)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_tag_value ON tags(tag_value)")

        # Understanding results table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS understanding (
                content_hash VARCHAR,
                provider VARCHAR,
                model VARCHAR,
                analysis_date TIMESTAMP,
                description TEXT,
                cost DOUBLE,
                metadata JSON,
                PRIMARY KEY (content_hash, provider)
            );
        """)

        # Generation metadata table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS generation_metadata (
                content_hash VARCHAR PRIMARY KEY,
                provider VARCHAR,
                model VARCHAR,
                prompt TEXT,
                negative_prompt TEXT,
                parameters JSON,
                generation_date TIMESTAMP
            );
        """)

        # Perceptual hashes for similarity search
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS perceptual_hashes (
                content_hash VARCHAR PRIMARY KEY,
                phash VARCHAR,
                dhash VARCHAR,
                ahash VARCHAR,
                whash VARCHAR,
                colorhash VARCHAR
            );
        """)

        # Create indexes for hash lookups
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_phash ON perceptual_hashes(phash)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_dhash ON perceptual_hashes(dhash)")

    def close(self):
        """Close database connection (no-op for pooled connections)."""
        if not self.db_path:
            # Only close in-memory connections
            self.conn.close()

    def _parse_timestamp(self, value: Any) -> datetime | None:
        """Parse various timestamp formats."""
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            # Try common formats
            formats = [
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%S.%f",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%dT%H:%M:%S.%fZ",
            ]

            for fmt in formats:
                try:
                    return datetime.strptime(value, fmt)
                except ValueError:
                    continue

        return None

    def _row_to_dict(self, row: tuple) -> dict[str, Any]:
        """Convert database row to dictionary."""
        if not row:
            return {}

        # Get column names from the last query
        columns = [desc[0] for desc in self.conn.description]

        result = {}
        for i, col in enumerate(columns):
            value = row[i]

            # Parse JSON columns
            if col in ["locations", "metadata", "parameters"] and value:
                try:
                    value = json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    pass

            # Parse timestamps
            elif col.endswith("_at") or col.endswith("_date"):
                value = self._parse_timestamp(value)

            result[col] = value

        return result