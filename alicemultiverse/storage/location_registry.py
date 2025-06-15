"""Storage location registry system using DuckDB.

This module provides a registry for tracking files across multiple storage locations
(local, S3/GCS, network drives) using content-addressed storage with SHA-256 hashes.
"""

import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any
import hashlib

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
        except ValueError:
            raise ValueError(f"Invalid storage type: {value}")


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
        except ValueError:
            raise ValueError(f"Invalid location status: {value}")


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

    def update_location(self, location: StorageLocation) -> None:
        """Update an existing storage location.
        
        Args:
            location: Storage location with updated information
        """
        self.conn.execute("""
            UPDATE storage_locations 
            SET name = ?, type = ?, path = ?, priority = ?, 
                rules = ?, last_scan = ?, status = ?, config = ?,
                updated_at = ?
            WHERE location_id = ?
        """, [
            location.name,
            location.type.value,
            location.path,
            location.priority,
            json.dumps([rule.to_dict() for rule in location.rules]),
            location.last_scan,
            location.status.value,
            json.dumps(location.config),
            datetime.now(),
            str(location.location_id)
        ])

        logger.info(f"Updated storage location: {location.name}")

    def update_scan_time(self, location_id: str) -> None:
        """Update only the last scan time for a location.
        
        Args:
            location_id: ID of the location to update
        """
        self.conn.execute("""
            UPDATE storage_locations 
            SET last_scan = ?, updated_at = ?
            WHERE location_id = ?
        """, [datetime.now(), datetime.now(), str(location_id)])

    def get_locations(
        self,
        status: LocationStatus | None = None,
        type: StorageType | None = None
    ) -> list[StorageLocation]:
        """Get all storage locations, optionally filtered.
        
        Args:
            status: Filter by location status
            type: Filter by storage type
            
        Returns:
            List of storage locations sorted by priority
        """
        query = "SELECT * FROM storage_locations WHERE 1=1"
        params = []

        if status:
            query += " AND status = ?"
            params.append(status.value)

        if type:
            query += " AND type = ?"
            params.append(type.value)

        query += " ORDER BY priority DESC, name"

        results = self.conn.execute(query, params).fetchall()

        locations = []
        for row in results:
            locations.append(StorageLocation(
                location_id=row[0] if isinstance(row[0], str) else str(row[0]),
                name=row[1],
                type=StorageType.from_string(row[2]),
                path=row[3],
                priority=row[4],
                rules=[StorageRule.from_dict(r) for r in json.loads(row[5] or "[]")],
                last_scan=row[6],
                status=LocationStatus.from_string(row[7]),
                config=json.loads(row[8] or "{}")
            ))

        return locations

    def get_location_by_id(self, location_id: str) -> StorageLocation | None:
        """Get a specific storage location by ID.
        
        Args:
            location_id: str of the location
            
        Returns:
            Storage location or None if not found
        """
        result = self.conn.execute(
            "SELECT * FROM storage_locations WHERE location_id = ?",
            [str(location_id)]
        ).fetchone()

        if not result:
            return None

        return StorageLocation(
            location_id=result[0] if isinstance(result[0], str) else str(result[0]),
            name=result[1],
            type=StorageType.from_string(result[2]),
            path=result[3],
            priority=result[4],
            rules=[StorageRule.from_dict(r) for r in json.loads(result[5] or "[]")],
            last_scan=result[6],
            status=LocationStatus.from_string(result[7]),
            config=json.loads(result[8] or "{}")
        )

    def get_location_for_file(
        self,
        content_hash: str,
        file_metadata: dict[str, Any]
    ) -> StorageLocation | None:
        """Determine the best storage location for a file based on rules.
        
        Args:
            content_hash: SHA-256 hash of the file
            file_metadata: Metadata about the file (size, type, age, tags, etc.)
            
        Returns:
            Best matching storage location or None
        """
        # Get all active locations sorted by priority
        locations = self.get_locations(status=LocationStatus.ACTIVE)

        for location in locations:
            if self._evaluate_rules(location, file_metadata):
                # Cache the evaluation result
                self._cache_rule_evaluation(content_hash, location.location_id, True, file_metadata)
                return location

        # If no location matches rules, return highest priority active location
        if locations:
            return locations[0]

        return None

    def _evaluate_rules(self, location: StorageLocation, metadata: dict[str, Any]) -> bool:
        """Evaluate if a file matches location rules.
        
        Args:
            location: Storage location to evaluate
            metadata: File metadata
            
        Returns:
            True if file matches all rules
        """
        if not location.rules:
            return True  # No rules means accept all

        for rule in location.rules:
            # Check age rules
            if rule.max_age_days is not None:
                file_age_days = metadata.get("age_days", 0)
                if file_age_days > rule.max_age_days:
                    return False

            if rule.min_age_days is not None:
                file_age_days = metadata.get("age_days", 0)
                if file_age_days < rule.min_age_days:
                    return False

            # Check type rules
            file_type = metadata.get("file_type", "").lower()
            if rule.include_types and file_type not in [t.lower() for t in rule.include_types]:
                return False

            if rule.exclude_types and file_type in [t.lower() for t in rule.exclude_types]:
                return False

            # Check size rules
            if rule.max_size_bytes is not None:
                file_size = metadata.get("file_size", 0)
                if file_size > rule.max_size_bytes:
                    return False

            if rule.min_size_bytes is not None:
                file_size = metadata.get("file_size", 0)
                if file_size < rule.min_size_bytes:
                    return False

            # Check tag rules
            file_tags = set(metadata.get("tags", []))
            if rule.require_tags:
                required = set(rule.require_tags)
                if not required.issubset(file_tags):
                    return False

            if rule.exclude_tags:
                excluded = set(rule.exclude_tags)
                if excluded.intersection(file_tags):
                    return False

            # Check quality rules
            if rule.min_quality_stars is not None:
                quality = metadata.get("quality_stars", 0)
                if quality < rule.min_quality_stars:
                    return False

            if rule.max_quality_stars is not None:
                quality = metadata.get("quality_stars", 0)
                if quality > rule.max_quality_stars:
                    return False

        return True

    def _cache_rule_evaluation(
        self,
        content_hash: str,
        location_id: str,
        matches: bool,
        metadata: dict[str, Any]
    ) -> None:
        """Cache the result of rule evaluation."""
        # Convert datetime objects to ISO format for JSON serialization
        clean_metadata = {}
        for k, v in metadata.items():
            if isinstance(v, datetime):
                clean_metadata[k] = v.isoformat()
            else:
                clean_metadata[k] = v

        self.conn.execute("""
            INSERT INTO rule_evaluations (content_hash, location_id, evaluated_at, matches, rule_details)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (content_hash, location_id) 
            DO UPDATE SET 
                evaluated_at = ?,
                matches = EXCLUDED.matches,
                rule_details = EXCLUDED.rule_details
        """, [content_hash, str(location_id), datetime.now(), matches, json.dumps(clean_metadata), datetime.now()])

    def track_file(
        self,
        content_hash: str,
        location_id: str,
        file_path: str,
        file_size: int | None = None,
        metadata_embedded: bool = False
    ) -> None:
        """Track a file in a specific location.
        
        Args:
            content_hash: SHA-256 hash of the file
            location_id: ID of the storage location
            file_path: Path to the file within the location
            file_size: Size of the file in bytes
            metadata_embedded: Whether metadata is embedded in the file
        """
        self.conn.execute("""
            INSERT INTO file_locations (
                content_hash, location_id, file_path, file_size, 
                metadata_embedded, last_verified
            ) VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT (content_hash, location_id) 
            DO UPDATE SET 
                file_path = EXCLUDED.file_path,
                file_size = EXCLUDED.file_size,
                metadata_embedded = EXCLUDED.metadata_embedded,
                last_verified = ?,
                sync_status = 'synced',
                error_message = NULL
        """, [content_hash, str(location_id), file_path, file_size, metadata_embedded, datetime.now(), datetime.now()])

    def get_file_locations(self, content_hash: str) -> list[dict[str, Any]]:
        """Get all locations where a file exists.
        
        Args:
            content_hash: SHA-256 hash of the file
            
        Returns:
            List of location information for the file
        """
        results = self.conn.execute("""
            SELECT 
                fl.location_id,
                fl.file_path,
                fl.file_size,
                fl.last_verified,
                fl.metadata_embedded,
                fl.sync_status,
                fl.error_message,
                sl.name,
                sl.type,
                sl.path as location_path,
                sl.status
            FROM file_locations fl
            JOIN storage_locations sl ON fl.location_id = sl.location_id
            WHERE fl.content_hash = ?
            ORDER BY sl.priority DESC
        """, [content_hash]).fetchall()

        locations = []
        for row in results:
            locations.append({
                "location_id": row[0],
                "file_path": row[1],
                "file_size": row[2],
                "last_verified": row[3],
                "metadata_embedded": row[4],
                "sync_status": row[5],
                "error_message": row[6],
                "location_name": row[7],
                "location_type": row[8],
                "location_path": row[9],
                "location_status": row[10]
            })

        return locations

    def remove_file_from_location(self, content_hash: str, location_id: str) -> None:
        """Remove a file from a specific location.
        
        Args:
            content_hash: SHA-256 hash of the file
            location_id: ID of the storage location
        """
        self.conn.execute("""
            DELETE FROM file_locations 
            WHERE content_hash = ? AND location_id = ?
        """, [content_hash, str(location_id)])

        # Also remove rule evaluation cache
        self.conn.execute("""
            DELETE FROM rule_evaluations 
            WHERE content_hash = ? AND location_id = ?
        """, [content_hash, str(location_id)])

    def scan_location(self, location_id: str) -> dict[str, Any]:
        """Scan a storage location to discover files.
        
        This is a placeholder for the actual implementation which would
        depend on the storage type (local filesystem, S3, etc.)
        
        Args:
            location_id: ID of the storage location to scan
            
        Returns:
            Scan results including discovered files
        """
        location = self.get_location_by_id(location_id)
        if not location:
            raise ValueError(f"Location {location_id} not found")

        # Update last scan time
        self.conn.execute(
            "UPDATE storage_locations SET last_scan = ? WHERE location_id = ?",
            [datetime.now(), str(location_id)]
        )

        # TODO: Implement actual scanning based on storage type
        # This would involve:
        # 1. Listing files in the location
        # 2. Computing content hashes
        # 3. Tracking discovered files
        # 4. Identifying missing/deleted files

        logger.info(f"Scanned location {location.name} (placeholder implementation)")

        return {
            "location_id": str(location_id),
            "location_name": location.name,
            "scan_time": datetime.now().isoformat(),
            "files_discovered": 0,  # Placeholder
            "files_updated": 0,     # Placeholder
            "files_removed": 0      # Placeholder
        }

    def mark_file_for_sync(
        self,
        content_hash: str,
        source_location_id: str,
        target_location_id: str,
        action: str = "upload"
    ) -> None:
        """Mark a file for synchronization between locations.
        
        Args:
            content_hash: SHA-256 hash of the file
            source_location_id: Source location ID
            target_location_id: Target location ID
            action: Sync action (upload, delete)
        """
        # Update source to indicate pending operation
        self.conn.execute("""
            UPDATE file_locations 
            SET sync_status = ?
            WHERE content_hash = ? AND location_id = ?
        """, [f"pending_{action}", content_hash, str(source_location_id)])

        # Create placeholder in target if uploading
        if action == "upload":
            self.conn.execute("""
                INSERT INTO file_locations (
                    content_hash, location_id, file_path, sync_status
                ) VALUES (?, ?, '', 'pending_upload')
                ON CONFLICT (content_hash, location_id) DO NOTHING
            """, [content_hash, str(target_location_id)])

    def get_pending_syncs(self) -> list[dict[str, Any]]:
        """Get all files pending synchronization.
        
        Returns:
            List of files needing sync with their details
        """
        results = self.conn.execute("""
            SELECT 
                fl.content_hash,
                fl.location_id,
                fl.file_path,
                fl.sync_status,
                sl.name as location_name,
                sl.type as location_type
            FROM file_locations fl
            JOIN storage_locations sl ON fl.location_id = sl.location_id
            WHERE fl.sync_status != 'synced'
            ORDER BY fl.last_verified
        """).fetchall()

        syncs = []
        for row in results:
            syncs.append({
                "content_hash": row[0],
                "location_id": row[1],
                "file_path": row[2],
                "sync_status": row[3],
                "location_name": row[4],
                "location_type": row[5]
            })

        return syncs

    def get_statistics(self) -> dict[str, Any]:
        """Get registry statistics.
        
        Returns:
            Dictionary with various statistics
        """
        stats = {}

        # Total locations
        stats["total_locations"] = self.conn.execute(
            "SELECT COUNT(*) FROM storage_locations"
        ).fetchone()[0]

        # Locations by type
        type_stats = self.conn.execute("""
            SELECT type, COUNT(*) as count
            FROM storage_locations
            GROUP BY type
        """).fetchall()
        stats["by_type"] = {t: count for t, count in type_stats}

        # Locations by status
        status_stats = self.conn.execute("""
            SELECT status, COUNT(*) as count
            FROM storage_locations
            GROUP BY status
        """).fetchall()
        stats["by_status"] = {s: count for s, count in status_stats}

        # Total unique files
        stats["total_unique_files"] = self.conn.execute(
            "SELECT COUNT(DISTINCT content_hash) FROM file_locations"
        ).fetchone()[0]

        # Total file instances
        stats["total_file_instances"] = self.conn.execute(
            "SELECT COUNT(*) FROM file_locations"
        ).fetchone()[0]

        # Files by location
        location_stats = self.conn.execute("""
            SELECT 
                sl.name,
                COUNT(fl.content_hash) as file_count,
                SUM(fl.file_size) as total_size,
                MAX(sl.priority) as priority
            FROM storage_locations sl
            LEFT JOIN file_locations fl ON sl.location_id = fl.location_id
            GROUP BY sl.name
            ORDER BY priority DESC
        """).fetchall()

        stats["by_location"] = []
        for name, count, size, priority in location_stats:
            stats["by_location"].append({
                "name": name,
                "file_count": count,
                "total_size_bytes": size or 0
            })

        # Pending syncs
        stats["pending_syncs"] = self.conn.execute(
            "SELECT COUNT(*) FROM file_locations WHERE sync_status != 'synced'"
        ).fetchone()[0]

        # Files with multiple copies
        stats["files_with_multiple_copies"] = self.conn.execute("""
            SELECT COUNT(*) FROM (
                SELECT content_hash, COUNT(*) as copy_count
                FROM file_locations
                GROUP BY content_hash
                HAVING COUNT(*) > 1
            )
        """).fetchone()[0]

        return stats

    def close(self):
        """Close the database connection."""
        self.conn.close()

    def cleanup_for_tests(self):
        """Clean up all data for tests. WARNING: This deletes all data!"""
        # Disable foreign key constraints temporarily
        self.conn.execute("SET foreign_keys=false")

        # Delete in reverse order of dependencies
        self.conn.execute("DELETE FROM rule_evaluations")
        self.conn.execute("DELETE FROM file_locations")
        self.conn.execute("DELETE FROM storage_locations")

        # Re-enable foreign key constraints
        self.conn.execute("SET foreign_keys=true")
