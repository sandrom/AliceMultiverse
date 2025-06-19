"""Storage location registry system using DuckDB.

This module provides a registry for tracking files across multiple storage locations
(local, S3/GCS, network drives) using content-addressed storage with SHA-256 hashes.
"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import duckdb

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class StorageType(Enum):
    """Type of storage location."""

    LOCAL = "local"
    S3 = "s3"
    GCS = "gcs"
    NETWORK = "network"

    @classmethod
    def from_string(cls, value: str) -> "StorageType":
        """Create StorageType from string."""
        try:
            return cls(value.lower())
        # TODO: Review unreachable code - except ValueError:
        # TODO: Review unreachable code - raise ValueError(f"Invalid storage type: {value}")


class LocationStatus(Enum):
    """Status of a storage location."""

    ACTIVE = "active"
    ARCHIVED = "archived"
    OFFLINE = "offline"

    @classmethod
    def from_string(cls, value: str) -> "LocationStatus":
        """Create LocationStatus from string."""
        try:
            return cls(value.lower())
        # TODO: Review unreachable code - except ValueError:
        # TODO: Review unreachable code - raise ValueError(f"Invalid location status: {value}")


@dataclass
class StorageRule:
    """Rule for determining where files should be stored."""

    # File age rules (in days)
    max_age_days: int | None = None
    min_age_days: int | None = None

    # File type rules (mime types or extensions)
    include_types: list[str] = field(default_factory=list)
    exclude_types: list[str] = field(default_factory=list)

    # Size rules (in bytes)
    max_size_bytes: int | None = None
    min_size_bytes: int | None = None

    # Tag rules
    require_tags: list[str] = field(default_factory=list)
    exclude_tags: list[str] = field(default_factory=list)

    # Quality rules
    min_quality_stars: int | None = None
    max_quality_stars: int | None = None

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for JSON storage."""
        return {
            "max_age_days": self.max_age_days,
            "min_age_days": self.min_age_days,
            "include_types": self.include_types,
            "exclude_types": self.exclude_types,
            "max_size_bytes": self.max_size_bytes,
            "min_size_bytes": self.min_size_bytes,
            "require_tags": self.require_tags,
            "exclude_tags": self.exclude_tags,
            "min_quality_stars": self.min_quality_stars,
            "max_quality_stars": self.max_quality_stars
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StorageRule":
        """Create from dictionary."""
        return cls(
            max_age_days=data.get("max_age_days"),
            min_age_days=data.get("min_age_days"),
            include_types=data.get("include_types", []),
            exclude_types=data.get("exclude_types", []),
            max_size_bytes=data.get("max_size_bytes"),
            min_size_bytes=data.get("min_size_bytes"),
            require_tags=data.get("require_tags", []),
            exclude_tags=data.get("exclude_tags", []),
            min_quality_stars=data.get("min_quality_stars"),
            max_quality_stars=data.get("max_quality_stars")
        )


@dataclass
class StorageLocation:
    """A storage location for media files."""

    location_id: str  # Hash of path + type for stable ID
    name: str
    type: StorageType
    path: str  # Local path or bucket name
    priority: int  # Higher priority = preferred for new files
    rules: list[StorageRule] = field(default_factory=list)
    last_scan: datetime | None = None
    status: LocationStatus = LocationStatus.ACTIVE

    # Additional config for cloud storage
    config: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for storage."""
        return {
            "location_id": str(self.location_id),
            "name": self.name,
            "type": self.type.value,
            "path": self.path,
            "priority": self.priority,
            "rules": [rule.to_dict() for rule in self.rules],
            "last_scan": self.last_scan.isoformat() if self.last_scan else None,
            "status": self.status.value,
            "config": self.config
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StorageLocation":
        """Create from dictionary."""
        return cls(
            location_id=str(data["location_id"]),
            name=data["name"],
            type=StorageType.from_string(data["type"]),
            path=data["path"],
            priority=data["priority"],
            rules=[StorageRule.from_dict(r) for r in data.get("rules", [])],
            last_scan=datetime.fromisoformat(data["last_scan"]) if data.get("last_scan") else None,
            status=LocationStatus.from_string(data.get("status", "active")),
            config=data.get("config", {})
        )


class StorageRegistry:
    """Registry for managing storage locations and tracking files across them."""

    def __init__(self, db_path: Path = None):
        """Initialize storage registry.

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
        # Storage locations table
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS storage_locations (
                location_id str PRIMARY KEY,
                name VARCHAR NOT NULL UNIQUE,
                type VARCHAR NOT NULL,
                path VARCHAR NOT NULL,
                priority INTEGER NOT NULL DEFAULT 0,
                rules JSON,
                last_scan TIMESTAMP,
                status VARCHAR NOT NULL DEFAULT 'active',
                config JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)

        # File locations table - tracks where each file exists
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS file_locations (
                content_hash VARCHAR NOT NULL,
                location_id str NOT NULL,
                file_path VARCHAR NOT NULL,
                file_size BIGINT,
                last_verified TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                metadata_embedded BOOLEAN DEFAULT FALSE,
                sync_status VARCHAR DEFAULT 'synced',  -- synced, pending_upload, pending_delete
                error_message TEXT,
                PRIMARY KEY (content_hash, location_id),
                FOREIGN KEY (location_id) REFERENCES storage_locations(location_id)
            );
        """)

        # Storage rules evaluation cache
        self.conn.execute("""
            CREATE TABLE IF NOT EXISTS rule_evaluations (
                content_hash VARCHAR NOT NULL,
                location_id str NOT NULL,
                evaluated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                matches BOOLEAN NOT NULL,
                rule_details JSON,
                PRIMARY KEY (content_hash, location_id),
                FOREIGN KEY (location_id) REFERENCES storage_locations(location_id)
            );
        """)

        # Create indexes
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_locations_priority ON storage_locations(priority DESC)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_locations_status ON storage_locations(status)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_file_locations_hash ON file_locations(content_hash)")
        self.conn.execute("CREATE INDEX IF NOT EXISTS idx_file_locations_sync ON file_locations(sync_status)")

    def register_location(self, location: StorageLocation) -> StorageLocation:
        """Register a new storage location.

        Args:
            location: Storage location to register

        Returns:
            The registered location with generated ID if needed
        """
        if not location.location_id:
            # Generate ID from path + type for stable identification
            id_source = f"{location.path}:{location.type.value}"
            location.location_id = hashlib.sha256(id_source.encode()).hexdigest()[:16]

        self.conn.execute("""
            INSERT INTO storage_locations (
                location_id, name, type, path, priority, rules,
                last_scan, status, config, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, [
            str(location.location_id),
            location.name,
            location.type.value,
            location.path,
            location.priority,
            json.dumps([rule.to_dict() for rule in location.rules]),
            location.last_scan,
            location.status.value,
            json.dumps(location.config),
            datetime.now()
        ])

        logger.info(f"Registered storage location: {location.name} ({location.type.value})")
        return location

    # TODO: Review unreachable code - def update_location(self, location: StorageLocation) -> None:
    # TODO: Review unreachable code - """Update an existing storage location.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - location: Storage location with updated information
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - self.conn.execute("""
    # TODO: Review unreachable code - UPDATE storage_locations
    # TODO: Review unreachable code - SET name = ?, type = ?, path = ?, priority = ?,
    # TODO: Review unreachable code - rules = ?, last_scan = ?, status = ?, config = ?,
    # TODO: Review unreachable code - updated_at = ?
    # TODO: Review unreachable code - WHERE location_id = ?
    # TODO: Review unreachable code - """, [
    # TODO: Review unreachable code - location.name,
    # TODO: Review unreachable code - location.type.value,
    # TODO: Review unreachable code - location.path,
    # TODO: Review unreachable code - location.priority,
    # TODO: Review unreachable code - json.dumps([rule.to_dict() for rule in location.rules]),
    # TODO: Review unreachable code - location.last_scan,
    # TODO: Review unreachable code - location.status.value,
    # TODO: Review unreachable code - json.dumps(location.config),
    # TODO: Review unreachable code - datetime.now(),
    # TODO: Review unreachable code - str(location.location_id)
    # TODO: Review unreachable code - ])

    # TODO: Review unreachable code - logger.info(f"Updated storage location: {location.name}")

    # TODO: Review unreachable code - def update_scan_time(self, location_id: str) -> None:
    # TODO: Review unreachable code - """Update only the last scan time for a location.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - location_id: ID of the location to update
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - self.conn.execute("""
    # TODO: Review unreachable code - UPDATE storage_locations
    # TODO: Review unreachable code - SET last_scan = ?, updated_at = ?
    # TODO: Review unreachable code - WHERE location_id = ?
    # TODO: Review unreachable code - """, [datetime.now(), datetime.now(), str(location_id)])

    # TODO: Review unreachable code - def get_locations(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - status: LocationStatus | None = None,
    # TODO: Review unreachable code - type: StorageType | None = None
    # TODO: Review unreachable code - ) -> list[StorageLocation]:
    # TODO: Review unreachable code - """Get all storage locations, optionally filtered.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - status: Filter by location status
    # TODO: Review unreachable code - type: Filter by storage type

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of storage locations sorted by priority
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - query = "SELECT * FROM storage_locations WHERE 1=1"
    # TODO: Review unreachable code - params = []

    # TODO: Review unreachable code - if status:
    # TODO: Review unreachable code - query += " AND status = ?"
    # TODO: Review unreachable code - params.append(status.value)

    # TODO: Review unreachable code - if type:
    # TODO: Review unreachable code - query += " AND type = ?"
    # TODO: Review unreachable code - params.append(type.value)

    # TODO: Review unreachable code - query += " ORDER BY priority DESC, name"

    # TODO: Review unreachable code - results = self.conn.execute(query, params).fetchall()

    # TODO: Review unreachable code - locations = []
    # TODO: Review unreachable code - for row in results:
    # TODO: Review unreachable code - locations.append(StorageLocation(
    # TODO: Review unreachable code - location_id=row[0] if isinstance(row[0], str) else str(row[0]),
    # TODO: Review unreachable code - name=row[1],
    # TODO: Review unreachable code - type=StorageType.from_string(row[2]),
    # TODO: Review unreachable code - path=row[3],
    # TODO: Review unreachable code - priority=row[4],
    # TODO: Review unreachable code - rules=[StorageRule.from_dict(r) for r in json.loads(row[5] or "[]")],
    # TODO: Review unreachable code - last_scan=row[6],
    # TODO: Review unreachable code - status=LocationStatus.from_string(row[7]),
    # TODO: Review unreachable code - config=json.loads(row[8] or "{}")
    # TODO: Review unreachable code - ))

    # TODO: Review unreachable code - return locations

    # TODO: Review unreachable code - def get_location_by_id(self, location_id: str) -> StorageLocation | None:
    # TODO: Review unreachable code - """Get a specific storage location by ID.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - location_id: str of the location

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Storage location or None if not found
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - result = self.conn.execute(
    # TODO: Review unreachable code - "SELECT * FROM storage_locations WHERE location_id = ?",
    # TODO: Review unreachable code - [str(location_id)]
    # TODO: Review unreachable code - ).fetchone()

    # TODO: Review unreachable code - if not result:
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - return StorageLocation(
    # TODO: Review unreachable code - location_id=result[0] if isinstance(result[0], str) else str(result[0]),
    # TODO: Review unreachable code - name=result[1],
    # TODO: Review unreachable code - type=StorageType.from_string(result[2]),
    # TODO: Review unreachable code - path=result[3],
    # TODO: Review unreachable code - priority=result[4],
    # TODO: Review unreachable code - rules=[StorageRule.from_dict(r) for r in json.loads(result[5] or "[]")],
    # TODO: Review unreachable code - last_scan=result[6],
    # TODO: Review unreachable code - status=LocationStatus.from_string(result[7]),
    # TODO: Review unreachable code - config=json.loads(result[8] or "{}")
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - def get_location_for_file(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - content_hash: str,
    # TODO: Review unreachable code - file_metadata: dict[str, Any]
    # TODO: Review unreachable code - ) -> StorageLocation | None:
    # TODO: Review unreachable code - """Determine the best storage location for a file based on rules.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - content_hash: SHA-256 hash of the file
    # TODO: Review unreachable code - file_metadata: Metadata about the file (size, type, age, tags, etc.)

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Best matching storage location or None
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Get all active locations sorted by priority
    # TODO: Review unreachable code - locations = self.get_locations(status=LocationStatus.ACTIVE)

    # TODO: Review unreachable code - for location in locations:
    # TODO: Review unreachable code - if self._evaluate_rules(location, file_metadata):
    # TODO: Review unreachable code - # Cache the evaluation result
    # TODO: Review unreachable code - self._cache_rule_evaluation(content_hash, location.location_id, True, file_metadata)
    # TODO: Review unreachable code - return location

    # TODO: Review unreachable code - # If no location matches rules, return highest priority active location
    # TODO: Review unreachable code - if locations:
    # TODO: Review unreachable code - return locations[0]

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def _evaluate_rules(self, location: StorageLocation, metadata: dict[str, Any]) -> bool:
    # TODO: Review unreachable code - """Evaluate if a file matches location rules.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - location: Storage location to evaluate
    # TODO: Review unreachable code - metadata: File metadata

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - True if file matches all rules
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not location.rules:
    # TODO: Review unreachable code - return True  # No rules means accept all

    # TODO: Review unreachable code - for rule in location.rules:
    # TODO: Review unreachable code - # Check age rules
    # TODO: Review unreachable code - if rule.max_age_days is not None:
    # TODO: Review unreachable code - file_age_days = metadata.get("age_days", 0)
    # TODO: Review unreachable code - if file_age_days > rule.max_age_days:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - if rule.min_age_days is not None:
    # TODO: Review unreachable code - file_age_days = metadata.get("age_days", 0)
    # TODO: Review unreachable code - if file_age_days < rule.min_age_days:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - # Check type rules
    # TODO: Review unreachable code - file_type = metadata.get("file_type", "").lower()
    # TODO: Review unreachable code - if rule.include_types and file_type not in [t.lower() for t in rule.include_types]:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - if rule.exclude_types and file_type in [t.lower() for t in rule.exclude_types]:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - # Check size rules
    # TODO: Review unreachable code - if rule.max_size_bytes is not None:
    # TODO: Review unreachable code - file_size = metadata.get("file_size", 0)
    # TODO: Review unreachable code - if file_size > rule.max_size_bytes:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - if rule.min_size_bytes is not None:
    # TODO: Review unreachable code - file_size = metadata.get("file_size", 0)
    # TODO: Review unreachable code - if file_size < rule.min_size_bytes:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - # Check tag rules
    # TODO: Review unreachable code - file_tags = set(metadata.get("tags", []))
    # TODO: Review unreachable code - if rule.require_tags:
    # TODO: Review unreachable code - required = set(rule.require_tags)
    # TODO: Review unreachable code - if not required.issubset(file_tags):
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - if rule.exclude_tags:
    # TODO: Review unreachable code - excluded = set(rule.exclude_tags)
    # TODO: Review unreachable code - if excluded.intersection(file_tags):
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - # Check quality rules
    # TODO: Review unreachable code - if rule.min_quality_stars is not None:
    # TODO: Review unreachable code - quality = metadata.get("quality_stars", 0)
    # TODO: Review unreachable code - if quality < rule.min_quality_stars:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - if rule.max_quality_stars is not None:
    # TODO: Review unreachable code - quality = metadata.get("quality_stars", 0)
    # TODO: Review unreachable code - if quality > rule.max_quality_stars:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - def _cache_rule_evaluation(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - content_hash: str,
    # TODO: Review unreachable code - location_id: str,
    # TODO: Review unreachable code - matches: bool,
    # TODO: Review unreachable code - metadata: dict[str, Any]
    # TODO: Review unreachable code - ) -> None:
    # TODO: Review unreachable code - """Cache the result of rule evaluation."""
    # TODO: Review unreachable code - # Convert datetime objects to ISO format for JSON serialization
    # TODO: Review unreachable code - clean_metadata = {}
    # TODO: Review unreachable code - for k, v in metadata.items():
    # TODO: Review unreachable code - if isinstance(v, datetime):
    # TODO: Review unreachable code - clean_metadata[k] = v.isoformat()
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - clean_metadata[k] = v

    # TODO: Review unreachable code - self.conn.execute("""
    # TODO: Review unreachable code - INSERT INTO rule_evaluations (content_hash, location_id, evaluated_at, matches, rule_details)
    # TODO: Review unreachable code - VALUES (?, ?, ?, ?, ?)
    # TODO: Review unreachable code - ON CONFLICT (content_hash, location_id)
    # TODO: Review unreachable code - DO UPDATE SET
    # TODO: Review unreachable code - evaluated_at = ?,
    # TODO: Review unreachable code - matches = EXCLUDED.matches,
    # TODO: Review unreachable code - rule_details = EXCLUDED.rule_details
    # TODO: Review unreachable code - """, [content_hash, str(location_id), datetime.now(), matches, json.dumps(clean_metadata), datetime.now()])

    # TODO: Review unreachable code - def track_file(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - content_hash: str,
    # TODO: Review unreachable code - location_id: str,
    # TODO: Review unreachable code - file_path: str,
    # TODO: Review unreachable code - file_size: int | None = None,
    # TODO: Review unreachable code - metadata_embedded: bool = False
    # TODO: Review unreachable code - ) -> None:
    # TODO: Review unreachable code - """Track a file in a specific location.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - content_hash: SHA-256 hash of the file
    # TODO: Review unreachable code - location_id: ID of the storage location
    # TODO: Review unreachable code - file_path: Path to the file within the location
    # TODO: Review unreachable code - file_size: Size of the file in bytes
    # TODO: Review unreachable code - metadata_embedded: Whether metadata is embedded in the file
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - self.conn.execute("""
    # TODO: Review unreachable code - INSERT INTO file_locations (
    # TODO: Review unreachable code - content_hash, location_id, file_path, file_size,
    # TODO: Review unreachable code - metadata_embedded, last_verified
    # TODO: Review unreachable code - ) VALUES (?, ?, ?, ?, ?, ?)
    # TODO: Review unreachable code - ON CONFLICT (content_hash, location_id)
    # TODO: Review unreachable code - DO UPDATE SET
    # TODO: Review unreachable code - file_path = EXCLUDED.file_path,
    # TODO: Review unreachable code - file_size = EXCLUDED.file_size,
    # TODO: Review unreachable code - metadata_embedded = EXCLUDED.metadata_embedded,
    # TODO: Review unreachable code - last_verified = ?,
    # TODO: Review unreachable code - sync_status = 'synced',
    # TODO: Review unreachable code - error_message = NULL
    # TODO: Review unreachable code - """, [content_hash, str(location_id), file_path, file_size, metadata_embedded, datetime.now(), datetime.now()])

    # TODO: Review unreachable code - def get_file_locations(self, content_hash: str) -> list[dict[str, Any]]:
    # TODO: Review unreachable code - """Get all locations where a file exists.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - content_hash: SHA-256 hash of the file

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of location information for the file
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - results = self.conn.execute("""
    # TODO: Review unreachable code - SELECT
    # TODO: Review unreachable code - fl.location_id,
    # TODO: Review unreachable code - fl.file_path,
    # TODO: Review unreachable code - fl.file_size,
    # TODO: Review unreachable code - fl.last_verified,
    # TODO: Review unreachable code - fl.metadata_embedded,
    # TODO: Review unreachable code - fl.sync_status,
    # TODO: Review unreachable code - fl.error_message,
    # TODO: Review unreachable code - sl.name,
    # TODO: Review unreachable code - sl.type,
    # TODO: Review unreachable code - sl.path as location_path,
    # TODO: Review unreachable code - sl.status
    # TODO: Review unreachable code - FROM file_locations fl
    # TODO: Review unreachable code - JOIN storage_locations sl ON fl.location_id = sl.location_id
    # TODO: Review unreachable code - WHERE fl.content_hash = ?
    # TODO: Review unreachable code - ORDER BY sl.priority DESC
    # TODO: Review unreachable code - """, [content_hash]).fetchall()

    # TODO: Review unreachable code - locations = []
    # TODO: Review unreachable code - for row in results:
    # TODO: Review unreachable code - locations.append({
    # TODO: Review unreachable code - "location_id": row[0],
    # TODO: Review unreachable code - "file_path": row[1],
    # TODO: Review unreachable code - "file_size": row[2],
    # TODO: Review unreachable code - "last_verified": row[3],
    # TODO: Review unreachable code - "metadata_embedded": row[4],
    # TODO: Review unreachable code - "sync_status": row[5],
    # TODO: Review unreachable code - "error_message": row[6],
    # TODO: Review unreachable code - "location_name": row[7],
    # TODO: Review unreachable code - "location_type": row[8],
    # TODO: Review unreachable code - "location_path": row[9],
    # TODO: Review unreachable code - "location_status": row[10]
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - return locations

    # TODO: Review unreachable code - def remove_file_from_location(self, content_hash: str, location_id: str) -> None:
    # TODO: Review unreachable code - """Remove a file from a specific location.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - content_hash: SHA-256 hash of the file
    # TODO: Review unreachable code - location_id: ID of the storage location
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - self.conn.execute("""
    # TODO: Review unreachable code - DELETE FROM file_locations
    # TODO: Review unreachable code - WHERE content_hash = ? AND location_id = ?
    # TODO: Review unreachable code - """, [content_hash, str(location_id)])

    # TODO: Review unreachable code - # Also remove rule evaluation cache
    # TODO: Review unreachable code - self.conn.execute("""
    # TODO: Review unreachable code - DELETE FROM rule_evaluations
    # TODO: Review unreachable code - WHERE content_hash = ? AND location_id = ?
    # TODO: Review unreachable code - """, [content_hash, str(location_id)])

    # TODO: Review unreachable code - def scan_location(self, location_id: str) -> dict[str, Any]:
    # TODO: Review unreachable code - """Scan a storage location to discover files.

    # TODO: Review unreachable code - This is a placeholder for the actual implementation which would
    # TODO: Review unreachable code - depend on the storage type (local filesystem, S3, etc.)

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - location_id: ID of the storage location to scan

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Scan results including discovered files
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - location = self.get_location_by_id(location_id)
    # TODO: Review unreachable code - if not location:
    # TODO: Review unreachable code - raise ValueError(f"Location {location_id} not found")

    # TODO: Review unreachable code - # Update last scan time
    # TODO: Review unreachable code - self.conn.execute(
    # TODO: Review unreachable code - "UPDATE storage_locations SET last_scan = ? WHERE location_id = ?",
    # TODO: Review unreachable code - [datetime.now(), str(location_id)]
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Implement scanning based on storage type
    # TODO: Review unreachable code - scan_result = {
    # TODO: Review unreachable code - "location_id": str(location_id),
    # TODO: Review unreachable code - "location_name": location.name,
    # TODO: Review unreachable code - "scan_time": datetime.now().isoformat(),
    # TODO: Review unreachable code - "files_discovered": 0,
    # TODO: Review unreachable code - "files_updated": 0,
    # TODO: Review unreachable code - "files_removed": 0
    # TODO: Review unreachable code - }
        
    # TODO: Review unreachable code - if location.type == StorageType.LOCAL:
    # TODO: Review unreachable code - # Scan local filesystem
    # TODO: Review unreachable code - scan_result = self._scan_local_location(location)
    # TODO: Review unreachable code - elif location.type == StorageType.S3:
    # TODO: Review unreachable code - # Scan S3 bucket
    # TODO: Review unreachable code - scan_result = self._scan_s3_location(location)
    # TODO: Review unreachable code - elif location.type == StorageType.GCS:
    # TODO: Review unreachable code - # Scan Google Cloud Storage
    # TODO: Review unreachable code - scan_result = self._scan_gcs_location(location)
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - logger.warning(f"Unsupported storage type: {location.type}")
            
    # TODO: Review unreachable code - logger.info(f"Scanned location {location.name}: {scan_result['files_discovered']} new, "
    # TODO: Review unreachable code - f"{scan_result['files_updated']} updated, {scan_result['files_removed']} removed")

    # TODO: Review unreachable code - return scan_result

    # TODO: Review unreachable code - def mark_file_for_sync(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - content_hash: str,
    # TODO: Review unreachable code - source_location_id: str,
    # TODO: Review unreachable code - target_location_id: str,
    # TODO: Review unreachable code - action: str = "upload"
    # TODO: Review unreachable code - ) -> None:
    # TODO: Review unreachable code - """Mark a file for synchronization between locations.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - content_hash: SHA-256 hash of the file
    # TODO: Review unreachable code - source_location_id: Source location ID
    # TODO: Review unreachable code - target_location_id: Target location ID
    # TODO: Review unreachable code - action: Sync action (upload, delete)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Update source to indicate pending operation
    # TODO: Review unreachable code - self.conn.execute("""
    # TODO: Review unreachable code - UPDATE file_locations
    # TODO: Review unreachable code - SET sync_status = ?
    # TODO: Review unreachable code - WHERE content_hash = ? AND location_id = ?
    # TODO: Review unreachable code - """, [f"pending_{action}", content_hash, str(source_location_id)])

    # TODO: Review unreachable code - # Create placeholder in target if uploading
    # TODO: Review unreachable code - if action == "upload":
    # TODO: Review unreachable code - self.conn.execute("""
    # TODO: Review unreachable code - INSERT INTO file_locations (
    # TODO: Review unreachable code - content_hash, location_id, file_path, sync_status
    # TODO: Review unreachable code - ) VALUES (?, ?, '', 'pending_upload')
    # TODO: Review unreachable code - ON CONFLICT (content_hash, location_id) DO NOTHING
    # TODO: Review unreachable code - """, [content_hash, str(target_location_id)])

    # TODO: Review unreachable code - def get_pending_syncs(self) -> list[dict[str, Any]]:
    # TODO: Review unreachable code - """Get all files pending synchronization.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of files needing sync with their details
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - results = self.conn.execute("""
    # TODO: Review unreachable code - SELECT
    # TODO: Review unreachable code - fl.content_hash,
    # TODO: Review unreachable code - fl.location_id,
    # TODO: Review unreachable code - fl.file_path,
    # TODO: Review unreachable code - fl.sync_status,
    # TODO: Review unreachable code - sl.name as location_name,
    # TODO: Review unreachable code - sl.type as location_type
    # TODO: Review unreachable code - FROM file_locations fl
    # TODO: Review unreachable code - JOIN storage_locations sl ON fl.location_id = sl.location_id
    # TODO: Review unreachable code - WHERE fl.sync_status != 'synced'
    # TODO: Review unreachable code - ORDER BY fl.last_verified
    # TODO: Review unreachable code - """).fetchall()

    # TODO: Review unreachable code - syncs = []
    # TODO: Review unreachable code - for row in results:
    # TODO: Review unreachable code - syncs.append({
    # TODO: Review unreachable code - "content_hash": row[0],
    # TODO: Review unreachable code - "location_id": row[1],
    # TODO: Review unreachable code - "file_path": row[2],
    # TODO: Review unreachable code - "sync_status": row[3],
    # TODO: Review unreachable code - "location_name": row[4],
    # TODO: Review unreachable code - "location_type": row[5]
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - return syncs

    # TODO: Review unreachable code - def get_statistics(self) -> dict[str, Any]:
    # TODO: Review unreachable code - """Get registry statistics.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dictionary with various statistics
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - stats = {}

    # TODO: Review unreachable code - # Total locations
    # TODO: Review unreachable code - stats["total_locations"] = self.conn.execute(
    # TODO: Review unreachable code - "SELECT COUNT(*) FROM storage_locations"
    # TODO: Review unreachable code - ).fetchone()[0]

    # TODO: Review unreachable code - # Locations by type
    # TODO: Review unreachable code - type_stats = self.conn.execute("""
    # TODO: Review unreachable code - SELECT type, COUNT(*) as count
    # TODO: Review unreachable code - FROM storage_locations
    # TODO: Review unreachable code - GROUP BY type
    # TODO: Review unreachable code - """).fetchall()
    # TODO: Review unreachable code - stats["by_type"] = {t: count for t, count in type_stats}

    # TODO: Review unreachable code - # Locations by status
    # TODO: Review unreachable code - status_stats = self.conn.execute("""
    # TODO: Review unreachable code - SELECT status, COUNT(*) as count
    # TODO: Review unreachable code - FROM storage_locations
    # TODO: Review unreachable code - GROUP BY status
    # TODO: Review unreachable code - """).fetchall()
    # TODO: Review unreachable code - stats["by_status"] = {s: count for s, count in status_stats}

    # TODO: Review unreachable code - # Total unique files
    # TODO: Review unreachable code - stats["total_unique_files"] = self.conn.execute(
    # TODO: Review unreachable code - "SELECT COUNT(DISTINCT content_hash) FROM file_locations"
    # TODO: Review unreachable code - ).fetchone()[0]

    # TODO: Review unreachable code - # Total file instances
    # TODO: Review unreachable code - stats["total_file_instances"] = self.conn.execute(
    # TODO: Review unreachable code - "SELECT COUNT(*) FROM file_locations"
    # TODO: Review unreachable code - ).fetchone()[0]

    # TODO: Review unreachable code - # Files by location
    # TODO: Review unreachable code - location_stats = self.conn.execute("""
    # TODO: Review unreachable code - SELECT
    # TODO: Review unreachable code - sl.name,
    # TODO: Review unreachable code - COUNT(fl.content_hash) as file_count,
    # TODO: Review unreachable code - SUM(fl.file_size) as total_size,
    # TODO: Review unreachable code - MAX(sl.priority) as priority
    # TODO: Review unreachable code - FROM storage_locations sl
    # TODO: Review unreachable code - LEFT JOIN file_locations fl ON sl.location_id = fl.location_id
    # TODO: Review unreachable code - GROUP BY sl.name
    # TODO: Review unreachable code - ORDER BY priority DESC
    # TODO: Review unreachable code - """).fetchall()

    # TODO: Review unreachable code - stats["by_location"] = []
    # TODO: Review unreachable code - for name, count, size, priority in location_stats:
    # TODO: Review unreachable code - stats["by_location"].append({
    # TODO: Review unreachable code - "name": name,
    # TODO: Review unreachable code - "file_count": count,
    # TODO: Review unreachable code - "total_size_bytes": size or 0
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - # Pending syncs
    # TODO: Review unreachable code - stats["pending_syncs"] = self.conn.execute(
    # TODO: Review unreachable code - "SELECT COUNT(*) FROM file_locations WHERE sync_status != 'synced'"
    # TODO: Review unreachable code - ).fetchone()[0]

    # TODO: Review unreachable code - # Files with multiple copies
    # TODO: Review unreachable code - stats["files_with_multiple_copies"] = self.conn.execute("""
    # TODO: Review unreachable code - SELECT COUNT(*) FROM (
    # TODO: Review unreachable code - SELECT content_hash, COUNT(*) as copy_count
    # TODO: Review unreachable code - FROM file_locations
    # TODO: Review unreachable code - GROUP BY content_hash
    # TODO: Review unreachable code - HAVING COUNT(*) > 1
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - """).fetchone()[0]

    # TODO: Review unreachable code - return stats

    # TODO: Review unreachable code - def close(self):
    # TODO: Review unreachable code - """Close the database connection."""
    # TODO: Review unreachable code - self.conn.close()

    # TODO: Review unreachable code - def cleanup_for_tests(self):
    # TODO: Review unreachable code - """Clean up all data for tests. WARNING: This deletes all data!"""
    # TODO: Review unreachable code - # Disable foreign key constraints temporarily
    # TODO: Review unreachable code - self.conn.execute("SET foreign_keys=false")

    # TODO: Review unreachable code - # Delete in reverse order of dependencies
    # TODO: Review unreachable code - self.conn.execute("DELETE FROM rule_evaluations")
    # TODO: Review unreachable code - self.conn.execute("DELETE FROM file_locations")
    # TODO: Review unreachable code - self.conn.execute("DELETE FROM storage_locations")

    # TODO: Review unreachable code - # Re-enable foreign key constraints
    # TODO: Review unreachable code - self.conn.execute("SET foreign_keys=true")
    
    # TODO: Review unreachable code - def add_file_to_location(self, content_hash: str, location_id: str, file_path: str, file_size: int) -> None:
    # TODO: Review unreachable code - """Add a new file to a location. Alias for track_file."""
    # TODO: Review unreachable code - self.track_file(content_hash, location_id, file_path, file_size)
    
    # TODO: Review unreachable code - def update_file_in_location(self, content_hash: str, location_id: str, file_path: str, file_size: int) -> None:
    # TODO: Review unreachable code - """Update an existing file in a location."""
    # TODO: Review unreachable code - # First remove the old entry for this file path
    # TODO: Review unreachable code - self.conn.execute(
    # TODO: Review unreachable code - "DELETE FROM file_locations WHERE location_id = ? AND file_path = ?",
    # TODO: Review unreachable code - [str(location_id), file_path]
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - # Then add the new one
    # TODO: Review unreachable code - self.track_file(content_hash, location_id, file_path, file_size)
    
    # TODO: Review unreachable code - def _scan_local_location(self, location: StorageLocation, full_scan: bool = False) -> dict[str, Any]:
    # TODO: Review unreachable code - """Scan a local filesystem location."""
    # TODO: Review unreachable code - from pathlib import Path
    # TODO: Review unreachable code - import hashlib
        
    # TODO: Review unreachable code - path = Path(location.path)
    # TODO: Review unreachable code - if not path.exists():
    # TODO: Review unreachable code - logger.error(f"Location path does not exist: {location.path}")
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "location_id": str(location.location_id),
    # TODO: Review unreachable code - "location_name": location.name,
    # TODO: Review unreachable code - "scan_time": datetime.now().isoformat(),
    # TODO: Review unreachable code - "files_discovered": 0,
    # TODO: Review unreachable code - "files_updated": 0,
    # TODO: Review unreachable code - "files_removed": 0,
    # TODO: Review unreachable code - "error": "Path does not exist"
    # TODO: Review unreachable code - }
        
    # TODO: Review unreachable code - files_discovered = 0
    # TODO: Review unreachable code - files_updated = 0
    # TODO: Review unreachable code - files_removed = 0
        
    # TODO: Review unreachable code - # Get existing files in this location
    # TODO: Review unreachable code - existing_files = {}
    # TODO: Review unreachable code - for row in self.conn.execute(
    # TODO: Review unreachable code - "SELECT file_path, content_hash FROM file_locations WHERE location_id = ?",
    # TODO: Review unreachable code - [str(location.location_id)]
    # TODO: Review unreachable code - ).fetchall():
    # TODO: Review unreachable code - existing_files[row[0]] = row[1]
        
    # TODO: Review unreachable code - # Scan for media files
    # TODO: Review unreachable code - media_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif', '.mp4', '.mov'}
    # TODO: Review unreachable code - scanned_paths = set()
        
    # TODO: Review unreachable code - for file_path in path.rglob('*'):
    # TODO: Review unreachable code - if file_path.is_file() and file_path.suffix.lower() in media_extensions:
    # TODO: Review unreachable code - relative_path = str(file_path.relative_to(path))
    # TODO: Review unreachable code - scanned_paths.add(relative_path)
                
    # TODO: Review unreachable code - # Compute content hash
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - with open(file_path, 'rb') as f:
    # TODO: Review unreachable code - content_hash = hashlib.sha256(f.read()).hexdigest()
                    
    # TODO: Review unreachable code - if relative_path in existing_files:
    # TODO: Review unreachable code - # Check if file changed
    # TODO: Review unreachable code - if existing_files[relative_path] != content_hash:
    # TODO: Review unreachable code - # Update file
    # TODO: Review unreachable code - self.update_file_in_location(
    # TODO: Review unreachable code - content_hash, 
    # TODO: Review unreachable code - str(location.location_id),
    # TODO: Review unreachable code - relative_path,
    # TODO: Review unreachable code - file_path.stat().st_size
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - files_updated += 1
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # New file
    # TODO: Review unreachable code - self.add_file_to_location(
    # TODO: Review unreachable code - content_hash,
    # TODO: Review unreachable code - str(location.location_id),
    # TODO: Review unreachable code - relative_path,
    # TODO: Review unreachable code - file_path.stat().st_size
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - files_discovered += 1
                        
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error scanning file {file_path}: {e}")
        
    # TODO: Review unreachable code - # Find removed files
    # TODO: Review unreachable code - for existing_path in existing_files:
    # TODO: Review unreachable code - if existing_path not in scanned_paths:
    # TODO: Review unreachable code - # Mark as removed
    # TODO: Review unreachable code - self.conn.execute(
    # TODO: Review unreachable code - "UPDATE file_locations SET sync_status = 'missing' WHERE location_id = ? AND file_path = ?",
    # TODO: Review unreachable code - [str(location.location_id), existing_path]
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - files_removed += 1
        
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "location_id": str(location.location_id),
    # TODO: Review unreachable code - "location_name": location.name,
    # TODO: Review unreachable code - "scan_time": datetime.now().isoformat(),
    # TODO: Review unreachable code - "files_discovered": files_discovered,
    # TODO: Review unreachable code - "files_updated": files_updated,
    # TODO: Review unreachable code - "files_removed": files_removed
    # TODO: Review unreachable code - }
    
    # TODO: Review unreachable code - def _scan_s3_location(self, location: StorageLocation, full_scan: bool = False) -> dict[str, Any]:
    # TODO: Review unreachable code - """Scan an S3 bucket location."""
    # TODO: Review unreachable code - # Placeholder for S3 scanning - would use boto3
    # TODO: Review unreachable code - logger.info(f"S3 scanning not yet implemented for {location.name}")
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "location_id": str(location.location_id),
    # TODO: Review unreachable code - "location_name": location.name,
    # TODO: Review unreachable code - "scan_time": datetime.now().isoformat(),
    # TODO: Review unreachable code - "files_discovered": 0,
    # TODO: Review unreachable code - "files_updated": 0,
    # TODO: Review unreachable code - "files_removed": 0,
    # TODO: Review unreachable code - "error": "S3 scanning not implemented"
    # TODO: Review unreachable code - }
    
    # TODO: Review unreachable code - def _scan_gcs_location(self, location: StorageLocation, full_scan: bool = False) -> dict[str, Any]:
    # TODO: Review unreachable code - """Scan a Google Cloud Storage location."""
    # TODO: Review unreachable code - # Placeholder for GCS scanning - would use google-cloud-storage
    # TODO: Review unreachable code - logger.info(f"GCS scanning not yet implemented for {location.name}")
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "location_id": str(location.location_id),
    # TODO: Review unreachable code - "location_name": location.name,
    # TODO: Review unreachable code - "scan_time": datetime.now().isoformat(),
    # TODO: Review unreachable code - "files_discovered": 0,
    # TODO: Review unreachable code - "files_updated": 0,
    # TODO: Review unreachable code - "files_removed": 0,
    # TODO: Review unreachable code - "error": "GCS scanning not implemented"
    # TODO: Review unreachable code - }