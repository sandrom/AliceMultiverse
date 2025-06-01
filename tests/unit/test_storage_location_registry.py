"""Unit tests for storage location registry."""

import json
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from uuid import uuid4

import pytest

from alicemultiverse.storage import (
    LocationStatus,
    StorageLocation,
    StorageRegistry,
    StorageRule,
    StorageType,
)


@pytest.fixture
def temp_db():
    """Create a temporary database file."""
    # Create a temporary directory for the test
    temp_dir = tempfile.mkdtemp()
    db_path = Path(temp_dir) / "test.duckdb"
    yield db_path
    # Cleanup
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)


@pytest.fixture
def registry(temp_db):
    """Create a test storage registry."""
    return StorageRegistry(db_path=temp_db)


@pytest.fixture
def sample_location():
    """Create a sample storage location."""
    return StorageLocation(
        location_id=uuid4(),
        name="Primary Local Storage",
        type=StorageType.LOCAL,
        path="/data/media/primary",
        priority=100,
        rules=[
            StorageRule(
                max_age_days=30,
                include_types=["image/jpeg", "image/png"],
                min_quality_stars=3
            )
        ],
        status=LocationStatus.ACTIVE
    )


@pytest.fixture
def sample_locations():
    """Create multiple sample storage locations."""
    return [
        StorageLocation(
            location_id=uuid4(),
            name="Hot Storage",
            type=StorageType.LOCAL,
            path="/data/media/hot",
            priority=100,
            rules=[
                StorageRule(max_age_days=7, min_quality_stars=4)
            ],
            status=LocationStatus.ACTIVE
        ),
        StorageLocation(
            location_id=uuid4(),
            name="Archive Storage",
            type=StorageType.S3,
            path="my-archive-bucket",
            priority=50,
            rules=[
                StorageRule(min_age_days=30, max_quality_stars=3)
            ],
            status=LocationStatus.ACTIVE,
            config={"region": "us-west-2", "storage_class": "GLACIER"}
        ),
        StorageLocation(
            location_id=uuid4(),
            name="Backup Storage",
            type=StorageType.GCS,
            path="my-backup-bucket",
            priority=25,
            rules=[],  # No rules - accepts everything
            status=LocationStatus.ACTIVE,
            config={"project": "my-project"}
        ),
        StorageLocation(
            location_id=uuid4(),
            name="Offline Storage",
            type=StorageType.NETWORK,
            path="//nas/media/offline",
            priority=10,
            status=LocationStatus.OFFLINE
        )
    ]


class TestStorageRule:
    """Test StorageRule functionality."""
    
    def test_rule_creation(self):
        """Test creating storage rules."""
        rule = StorageRule(
            max_age_days=30,
            min_age_days=7,
            include_types=["image/jpeg", "image/png"],
            exclude_types=["image/gif"],
            max_size_bytes=100_000_000,  # 100MB
            min_size_bytes=1000,  # 1KB
            require_tags=["production", "approved"],
            exclude_tags=["draft", "rejected"],
            min_quality_stars=3,
            max_quality_stars=5
        )
        
        assert rule.max_age_days == 30
        assert rule.min_age_days == 7
        assert "image/jpeg" in rule.include_types
        assert "image/gif" in rule.exclude_types
        assert rule.max_size_bytes == 100_000_000
        assert rule.min_size_bytes == 1000
        assert "production" in rule.require_tags
        assert "draft" in rule.exclude_tags
        assert rule.min_quality_stars == 3
        assert rule.max_quality_stars == 5
    
    def test_rule_serialization(self):
        """Test rule to/from dict conversion."""
        rule = StorageRule(
            max_age_days=30,
            include_types=["image/jpeg"],
            require_tags=["approved"]
        )
        
        # Convert to dict
        rule_dict = rule.to_dict()
        assert rule_dict["max_age_days"] == 30
        assert rule_dict["include_types"] == ["image/jpeg"]
        assert rule_dict["require_tags"] == ["approved"]
        
        # Convert back from dict
        rule2 = StorageRule.from_dict(rule_dict)
        assert rule2.max_age_days == rule.max_age_days
        assert rule2.include_types == rule.include_types
        assert rule2.require_tags == rule.require_tags


class TestStorageLocation:
    """Test StorageLocation functionality."""
    
    def test_location_creation(self):
        """Test creating storage locations."""
        location = StorageLocation(
            location_id=uuid4(),
            name="Test Storage",
            type=StorageType.S3,
            path="test-bucket",
            priority=50,
            rules=[StorageRule(max_age_days=30)],
            status=LocationStatus.ACTIVE,
            config={"region": "us-east-1"}
        )
        
        assert location.name == "Test Storage"
        assert location.type == StorageType.S3
        assert location.path == "test-bucket"
        assert location.priority == 50
        assert len(location.rules) == 1
        assert location.status == LocationStatus.ACTIVE
        assert location.config["region"] == "us-east-1"
    
    def test_location_serialization(self):
        """Test location to/from dict conversion."""
        location = StorageLocation(
            location_id=uuid4(),
            name="Test Storage",
            type=StorageType.LOCAL,
            path="/data/test",
            priority=100,
            rules=[StorageRule(max_age_days=30)],
            last_scan=datetime.now(),
            status=LocationStatus.ACTIVE
        )
        
        # Convert to dict
        loc_dict = location.to_dict()
        assert loc_dict["name"] == "Test Storage"
        assert loc_dict["type"] == "local"
        assert loc_dict["path"] == "/data/test"
        assert loc_dict["priority"] == 100
        assert len(loc_dict["rules"]) == 1
        assert loc_dict["last_scan"] is not None
        assert loc_dict["status"] == "active"
        
        # Convert back from dict
        location2 = StorageLocation.from_dict(loc_dict)
        assert location2.name == location.name
        assert location2.type == location.type
        assert location2.path == location.path
        assert location2.priority == location.priority
        assert len(location2.rules) == len(location.rules)
        assert location2.status == location.status
    
    def test_storage_type_from_string(self):
        """Test StorageType enum conversion from string."""
        assert StorageType.from_string("local") == StorageType.LOCAL
        assert StorageType.from_string("s3") == StorageType.S3
        assert StorageType.from_string("gcs") == StorageType.GCS
        assert StorageType.from_string("network") == StorageType.NETWORK
        
        with pytest.raises(ValueError):
            StorageType.from_string("invalid")
    
    def test_location_status_from_string(self):
        """Test LocationStatus enum conversion from string."""
        assert LocationStatus.from_string("active") == LocationStatus.ACTIVE
        assert LocationStatus.from_string("archived") == LocationStatus.ARCHIVED
        assert LocationStatus.from_string("offline") == LocationStatus.OFFLINE
        
        with pytest.raises(ValueError):
            LocationStatus.from_string("invalid")


class TestStorageRegistry:
    """Test StorageRegistry functionality."""
    
    def test_register_location(self, registry, sample_location):
        """Test registering a new storage location."""
        # Register location
        registered = registry.register_location(sample_location)
        
        assert registered.location_id is not None
        assert registered.name == sample_location.name
        
        # Verify it was saved
        locations = registry.get_locations()
        assert len(locations) == 1
        assert locations[0].name == sample_location.name
    
    def test_update_location(self, registry, sample_location):
        """Test updating an existing location."""
        # Register location
        registered = registry.register_location(sample_location)
        
        # Update it
        registered.priority = 200
        registered.status = LocationStatus.ARCHIVED
        registry.update_location(registered)
        
        # Verify update
        updated = registry.get_location_by_id(registered.location_id)
        assert updated.priority == 200
        assert updated.status == LocationStatus.ARCHIVED
    
    def test_get_locations_filtered(self, registry, sample_locations):
        """Test getting locations with filters."""
        # Register all locations
        for loc in sample_locations:
            registry.register_location(loc)
        
        # Get all locations
        all_locations = registry.get_locations()
        assert len(all_locations) == 4
        
        # Filter by status
        active_locations = registry.get_locations(status=LocationStatus.ACTIVE)
        assert len(active_locations) == 3
        
        offline_locations = registry.get_locations(status=LocationStatus.OFFLINE)
        assert len(offline_locations) == 1
        assert offline_locations[0].name == "Offline Storage"
        
        # Filter by type
        s3_locations = registry.get_locations(type=StorageType.S3)
        assert len(s3_locations) == 1
        assert s3_locations[0].name == "Archive Storage"
        
        # Filter by both
        active_local = registry.get_locations(
            status=LocationStatus.ACTIVE,
            type=StorageType.LOCAL
        )
        assert len(active_local) == 1
        assert active_local[0].name == "Hot Storage"
    
    def test_get_location_by_id(self, registry, sample_location):
        """Test getting a specific location by ID."""
        # Register location
        registered = registry.register_location(sample_location)
        
        # Get by ID
        retrieved = registry.get_location_by_id(registered.location_id)
        assert retrieved is not None
        assert retrieved.name == registered.name
        assert retrieved.location_id == registered.location_id
        
        # Try non-existent ID
        missing = registry.get_location_by_id(uuid4())
        assert missing is None
    
    def test_track_file(self, registry, sample_location):
        """Test tracking files in locations."""
        # Register location
        location = registry.register_location(sample_location)
        
        # Track a file
        content_hash = "abc123def456"
        registry.track_file(
            content_hash=content_hash,
            location_id=location.location_id,
            file_path="/data/media/primary/image.jpg",
            file_size=1024000,
            metadata_embedded=True
        )
        
        # Get file locations
        locations = registry.get_file_locations(content_hash)
        assert len(locations) == 1
        assert locations[0]["file_path"] == "/data/media/primary/image.jpg"
        assert locations[0]["file_size"] == 1024000
        assert locations[0]["metadata_embedded"] is True
        assert locations[0]["location_name"] == "Primary Local Storage"
    
    def test_track_file_multiple_locations(self, registry, sample_locations):
        """Test tracking the same file in multiple locations."""
        # Register locations
        hot = registry.register_location(sample_locations[0])
        archive = registry.register_location(sample_locations[1])
        
        content_hash = "abc123def456"
        
        # Track in hot storage
        registry.track_file(
            content_hash=content_hash,
            location_id=hot.location_id,
            file_path="/data/media/hot/image.jpg",
            file_size=1024000
        )
        
        # Track in archive storage
        registry.track_file(
            content_hash=content_hash,
            location_id=archive.location_id,
            file_path="archive/2024/image.jpg",
            file_size=1024000
        )
        
        # Get all locations
        locations = registry.get_file_locations(content_hash)
        assert len(locations) == 2
        
        # Should be sorted by priority
        assert locations[0]["location_name"] == "Hot Storage"
        assert locations[1]["location_name"] == "Archive Storage"
    
    def test_remove_file_from_location(self, registry, sample_location):
        """Test removing a file from a location."""
        # Register and track file
        location = registry.register_location(sample_location)
        content_hash = "abc123def456"
        
        registry.track_file(
            content_hash=content_hash,
            location_id=location.location_id,
            file_path="/data/media/primary/image.jpg"
        )
        
        # Verify it exists
        locations = registry.get_file_locations(content_hash)
        assert len(locations) == 1
        
        # Remove it
        registry.remove_file_from_location(content_hash, location.location_id)
        
        # Verify it's gone
        locations = registry.get_file_locations(content_hash)
        assert len(locations) == 0
    
    def test_evaluate_rules_age(self, registry, sample_locations):
        """Test rule evaluation based on file age."""
        # Register locations
        hot = registry.register_location(sample_locations[0])  # max_age_days=7
        archive = registry.register_location(sample_locations[1])  # min_age_days=30
        
        # Test new file (0 days old)
        new_file_metadata = {
            "age_days": 0,
            "file_type": "image/jpeg",
            "quality_stars": 5
        }
        
        location = registry.get_location_for_file("hash1", new_file_metadata)
        assert location.name == "Hot Storage"
        
        # Test old file (45 days old)
        old_file_metadata = {
            "age_days": 45,
            "file_type": "image/jpeg",
            "quality_stars": 2
        }
        
        location = registry.get_location_for_file("hash2", old_file_metadata)
        assert location.name == "Archive Storage"
    
    def test_evaluate_rules_quality(self, registry):
        """Test rule evaluation based on quality."""
        # Create locations with quality rules
        high_quality = StorageLocation(
            location_id=uuid4(),
            name="Premium Storage",
            type=StorageType.LOCAL,
            path="/data/premium",
            priority=100,
            rules=[StorageRule(min_quality_stars=4)],
            status=LocationStatus.ACTIVE
        )
        
        low_quality = StorageLocation(
            location_id=uuid4(),
            name="Budget Storage",
            type=StorageType.LOCAL,
            path="/data/budget",
            priority=50,
            rules=[StorageRule(max_quality_stars=2)],
            status=LocationStatus.ACTIVE
        )
        
        registry.register_location(high_quality)
        registry.register_location(low_quality)
        
        # Test high quality file
        high_q_metadata = {"quality_stars": 5}
        location = registry.get_location_for_file("hash1", high_q_metadata)
        assert location.name == "Premium Storage"
        
        # Test low quality file
        low_q_metadata = {"quality_stars": 1}
        location = registry.get_location_for_file("hash2", low_q_metadata)
        assert location.name == "Budget Storage"
    
    def test_evaluate_rules_file_type(self, registry):
        """Test rule evaluation based on file type."""
        # Create location that only accepts images
        image_storage = StorageLocation(
            location_id=uuid4(),
            name="Image Storage",
            type=StorageType.LOCAL,
            path="/data/images",
            priority=100,
            rules=[StorageRule(include_types=["image/jpeg", "image/png"])],
            status=LocationStatus.ACTIVE
        )
        
        # Create location that excludes videos
        no_video_storage = StorageLocation(
            location_id=uuid4(),
            name="No Video Storage",
            type=StorageType.LOCAL,
            path="/data/no-video",
            priority=50,
            rules=[StorageRule(exclude_types=["video/mp4", "video/avi"])],
            status=LocationStatus.ACTIVE
        )
        
        registry.register_location(image_storage)
        registry.register_location(no_video_storage)
        
        # Test image file
        image_metadata = {"file_type": "image/jpeg"}
        location = registry.get_location_for_file("hash1", image_metadata)
        assert location.name == "Image Storage"
        
        # Test video file - should NOT match Image Storage (wrong type) so falls back to highest priority
        video_metadata = {"file_type": "video/mp4"}
        location = registry.get_location_for_file("hash2", video_metadata)
        # Since video doesn't match Image Storage's include_types, it falls back to highest priority
        assert location.name == "Image Storage"  # Highest priority location
    
    def test_evaluate_rules_tags(self, registry):
        """Test rule evaluation based on tags."""
        # Create location requiring specific tags
        production_storage = StorageLocation(
            location_id=uuid4(),
            name="Production Storage",
            type=StorageType.LOCAL,
            path="/data/production",
            priority=100,
            rules=[StorageRule(require_tags=["approved", "production"])],
            status=LocationStatus.ACTIVE
        )
        
        # Create location excluding certain tags
        clean_storage = StorageLocation(
            location_id=uuid4(),
            name="Clean Storage",
            type=StorageType.LOCAL,
            path="/data/clean",
            priority=50,
            rules=[StorageRule(exclude_tags=["nsfw", "adult"])],
            status=LocationStatus.ACTIVE
        )
        
        registry.register_location(production_storage)
        registry.register_location(clean_storage)
        
        # Test file with required tags
        prod_metadata = {"tags": ["approved", "production", "hero"]}
        location = registry.get_location_for_file("hash1", prod_metadata)
        assert location.name == "Production Storage"
        
        # Test file without required tags
        draft_metadata = {"tags": ["draft", "review"]}
        location = registry.get_location_for_file("hash2", draft_metadata)
        assert location.name == "Clean Storage"
        
        # Test file with excluded tags
        adult_metadata = {"tags": ["nsfw", "adult"]}
        location = registry.get_location_for_file("hash3", adult_metadata)
        # Should not match any location with rules, falls back to highest priority
        assert location.name == "Production Storage"
    
    def test_mark_file_for_sync(self, registry, sample_locations):
        """Test marking files for synchronization."""
        # Register locations
        source = registry.register_location(sample_locations[0])
        target = registry.register_location(sample_locations[1])
        
        content_hash = "abc123def456"
        
        # Track file in source
        registry.track_file(
            content_hash=content_hash,
            location_id=source.location_id,
            file_path="/data/media/hot/image.jpg"
        )
        
        # Mark for sync to target
        registry.mark_file_for_sync(
            content_hash=content_hash,
            source_location_id=source.location_id,
            target_location_id=target.location_id,
            action="upload"
        )
        
        # Check pending syncs
        pending = registry.get_pending_syncs()
        assert len(pending) >= 1
        
        # Find our sync
        our_syncs = [s for s in pending if s["content_hash"] == content_hash]
        assert len(our_syncs) >= 1
        assert any(s["sync_status"] == "pending_upload" for s in our_syncs)
    
    def test_scan_location_placeholder(self, registry, sample_location):
        """Test the scan_location placeholder method."""
        # Register location
        location = registry.register_location(sample_location)
        
        # Scan it
        results = registry.scan_location(location.location_id)
        
        assert results["location_id"] == str(location.location_id)
        assert results["location_name"] == location.name
        assert "scan_time" in results
        assert results["files_discovered"] == 0  # Placeholder
        
        # Verify last_scan was updated
        updated = registry.get_location_by_id(location.location_id)
        assert updated.last_scan is not None
    
    def test_get_statistics(self, registry, sample_locations):
        """Test getting registry statistics."""
        # Register locations
        for loc in sample_locations:
            registry.register_location(loc)
        
        # Track some files
        content_hashes = ["hash1", "hash2", "hash3"]
        for i, hash in enumerate(content_hashes):
            # Track in multiple locations
            for j in range(min(i + 1, len(sample_locations))):
                registry.track_file(
                    content_hash=hash,
                    location_id=sample_locations[j].location_id,
                    file_path=f"/path/to/file{i}.jpg",
                    file_size=1024 * (i + 1)
                )
        
        # Get statistics
        stats = registry.get_statistics()
        
        assert stats["total_locations"] == 4
        assert stats["by_type"]["local"] == 1
        assert stats["by_type"]["s3"] == 1
        assert stats["by_type"]["gcs"] == 1
        assert stats["by_type"]["network"] == 1
        assert stats["by_status"]["active"] == 3
        assert stats["by_status"]["offline"] == 1
        assert stats["total_unique_files"] == 3
        assert stats["total_file_instances"] >= 3
        assert stats["files_with_multiple_copies"] >= 1
        
        # Check location stats
        location_names = [loc["name"] for loc in stats["by_location"]]
        assert "Hot Storage" in location_names
        assert "Archive Storage" in location_names
    
    def test_close_connection(self, registry):
        """Test closing the database connection."""
        # Register a location
        location = StorageLocation(
            location_id=uuid4(),
            name="Test",
            type=StorageType.LOCAL,
            path="/test",
            priority=1
        )
        registry.register_location(location)
        
        # Close connection
        registry.close()
        
        # Attempting to use should fail
        with pytest.raises(Exception):
            registry.get_locations()


class TestIntegration:
    """Integration tests for the storage registry system."""
    
    def test_complete_workflow(self, registry):
        """Test a complete workflow of managing storage locations and files."""
        # 1. Set up storage locations
        hot_storage = StorageLocation(
            location_id=uuid4(),
            name="Hot Storage",
            type=StorageType.LOCAL,
            path="/data/hot",
            priority=100,
            rules=[
                StorageRule(
                    max_age_days=7,
                    min_quality_stars=4,
                    include_types=["image/jpeg", "image/png"]
                )
            ],
            status=LocationStatus.ACTIVE
        )
        
        cold_storage = StorageLocation(
            location_id=uuid4(),
            name="Cold Storage",
            type=StorageType.S3,
            path="cold-bucket",
            priority=50,
            rules=[
                StorageRule(
                    min_age_days=7,
                    max_quality_stars=3
                )
            ],
            status=LocationStatus.ACTIVE,
            config={"region": "us-west-2", "storage_class": "GLACIER"}
        )
        
        backup_storage = StorageLocation(
            location_id=uuid4(),
            name="Backup",
            type=StorageType.GCS,
            path="backup-bucket",
            priority=25,
            rules=[],  # Accepts everything
            status=LocationStatus.ACTIVE
        )
        
        # Register all locations
        for loc in [hot_storage, cold_storage, backup_storage]:
            registry.register_location(loc)
        
        # 2. Process different types of files
        test_files = [
            {
                "hash": "high_quality_new",
                "metadata": {
                    "age_days": 1,
                    "quality_stars": 5,
                    "file_type": "image/jpeg",
                    "file_size": 2_000_000,
                    "tags": ["hero", "approved"]
                },
                "expected_location": "Hot Storage"
            },
            {
                "hash": "low_quality_old",
                "metadata": {
                    "age_days": 30,
                    "quality_stars": 2,
                    "file_type": "image/png",
                    "file_size": 500_000,
                    "tags": ["b_roll"]
                },
                "expected_location": "Cold Storage"
            },
            {
                "hash": "medium_quality_video",
                "metadata": {
                    "age_days": 3,
                    "quality_stars": 3,
                    "file_type": "video/mp4",
                    "file_size": 50_000_000,
                    "tags": ["draft"]
                },
                "expected_location": "Backup"  # Doesn't match hot (wrong type) or cold (too new)
            }
        ]
        
        # 3. Determine locations and track files
        for test_file in test_files:
            location = registry.get_location_for_file(
                test_file["hash"],
                test_file["metadata"]
            )
            assert location.name == test_file["expected_location"]
            
            # Track the file
            registry.track_file(
                content_hash=test_file["hash"],
                location_id=location.location_id,
                file_path=f"{location.path}/{test_file['hash']}.jpg",
                file_size=test_file["metadata"]["file_size"],
                metadata_embedded=True
            )
        
        # 4. Verify file locations
        for test_file in test_files:
            locations = registry.get_file_locations(test_file["hash"])
            assert len(locations) == 1
            assert locations[0]["location_name"] == test_file["expected_location"]
        
        # 5. Simulate file aging and migration
        # Mark high quality file for archive after it ages
        registry.mark_file_for_sync(
            content_hash="high_quality_new",
            source_location_id=hot_storage.location_id,
            target_location_id=cold_storage.location_id,
            action="upload"
        )
        
        # 6. Check statistics
        stats = registry.get_statistics()
        assert stats["total_unique_files"] == 3
        assert stats["pending_syncs"] >= 1
        
        # 7. Clean up
        registry.close()