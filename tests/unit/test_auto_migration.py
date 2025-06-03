"""Tests for auto-migration service."""

import asyncio
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from PIL import Image

from alicemultiverse.storage.auto_migration import AutoMigrationService, MigrationScheduler
from alicemultiverse.storage.duckdb_cache import DuckDBSearchCache
from alicemultiverse.storage.location_registry import (
    StorageLocation,
    StorageRegistry,
    StorageRule,
    StorageType,
)
from alicemultiverse.storage.multi_path_scanner import MultiPathScanner


def create_test_image(path: Path, age_days: int = 0, quality: int = 3):
    """Create a test image with metadata."""
    img = Image.new('RGB', (10, 10), color='red')
    img.save(path, 'PNG')
    
    # Set file modification time
    if age_days > 0:
        file_date = datetime.now() - timedelta(days=age_days)
        import os
        timestamp = file_date.timestamp()
        os.utime(path, (timestamp, timestamp))


class TestAutoMigrationService:
    """Test auto-migration functionality."""
    
    @pytest.mark.asyncio
    async def test_analyze_migrations(self, tmp_path):
        """Test migration analysis."""
        # Setup test directories
        source_dir = tmp_path / "source"
        archive_dir = tmp_path / "archive"
        source_dir.mkdir()
        archive_dir.mkdir()
        
        # Create test files
        old_file = source_dir / "old_file.png"
        new_file = source_dir / "new_file.png"
        create_test_image(old_file, age_days=60)
        create_test_image(new_file, age_days=5)
        
        # Setup storage system
        cache = DuckDBSearchCache(tmp_path / "cache.db")
        registry = StorageRegistry(tmp_path / "registry.db")
        
        # Register locations with rules
        source_location = StorageLocation(
            location_id=None,
            name="Source",
            type=StorageType.LOCAL,
            path=str(source_dir),
            priority=100,
            rules=[StorageRule(max_age_days=30)]  # Keep files < 30 days
        )
        
        archive_location = StorageLocation(
            location_id=None,
            name="Archive",
            type=StorageType.LOCAL,
            path=str(archive_dir),
            priority=50,
            rules=[StorageRule(min_age_days=31)]  # Files > 30 days
        )
        
        source_loc = registry.register_location(source_location)
        archive_loc = registry.register_location(archive_location)
        
        # Directly add files to cache for testing
        scanner = MultiPathScanner(cache, registry)
        
        # Add old file to cache
        old_hash = "old_file_hash_12345"
        cache.upsert_asset(
            content_hash=old_hash,
            file_path=old_file,
            file_size=old_file.stat().st_size,
            metadata={'media_type': 'image'},
            storage_type='local'
        )
        
        # Add new file to cache
        new_hash = "new_file_hash_67890"
        cache.upsert_asset(
            content_hash=new_hash,
            file_path=new_file,
            file_size=new_file.stat().st_size,
            metadata={'media_type': 'image'},
            storage_type='local'
        )
        
        # Track files in registry
        registry.track_file(
            old_hash,
            source_loc.location_id,
            str(old_file),
            old_file.stat().st_size
        )
        
        registry.track_file(
            new_hash,
            source_loc.location_id,
            str(new_file),
            new_file.stat().st_size
        )
        
        # Create migration service
        service = AutoMigrationService(cache, registry, scanner)
        
        # Analyze migrations
        migrations = await service.analyze_migrations(dry_run=True, show_progress=False)
        
        # Old file should be marked for migration
        assert len(migrations) >= 1
        
        # Check migration details
        migration_found = False
        for content_hash, plans in migrations.items():
            for plan in plans:
                file_path = plan['file_info'].get('path', '')
                print(f"Found migration for: {file_path}")
                if "old_file" in file_path:
                    migration_found = True
                    assert plan['target_location'].name == "Archive"
                    assert "exceeds minimum" in plan['reason'] or "File age" in plan['reason']
        
        assert migration_found, f"Old file should be marked for migration. Found migrations: {list(migrations.keys())}"
        
        cache.close()
        registry.close()
    
    @pytest.mark.asyncio
    async def test_execute_migrations(self, tmp_path):
        """Test executing migrations."""
        # Setup test directories
        source_dir = tmp_path / "source"
        archive_dir = tmp_path / "archive"
        source_dir.mkdir()
        archive_dir.mkdir()
        
        # Create test file
        test_file = source_dir / "migrate_me.png"
        create_test_image(test_file, age_days=45)
        
        # Setup storage system
        cache = DuckDBSearchCache(tmp_path / "cache.db")
        registry = StorageRegistry(tmp_path / "registry.db")
        
        # Register locations
        source_location = StorageLocation(
            location_id=None,
            name="Source",
            type=StorageType.LOCAL,
            path=str(source_dir),
            priority=100,
            rules=[StorageRule(max_age_days=30)]
        )
        
        archive_location = StorageLocation(
            location_id=None,
            name="Archive",
            type=StorageType.LOCAL,
            path=str(archive_dir),
            priority=50,
            rules=[StorageRule(min_age_days=31)]
        )
        
        source_loc = registry.register_location(source_location)
        archive_loc = registry.register_location(archive_location)
        
        # Scan and create service
        scanner = MultiPathScanner(cache, registry)
        await scanner._scan_local_location(source_loc, show_progress=False)
        
        service = AutoMigrationService(cache, registry, scanner)
        
        # Run full migration (copy mode)
        results = await service.run_auto_migration(
            dry_run=False,
            move_files=False,
            show_progress=False
        )
        
        # Check results
        assert results['analysis']['files_to_migrate'] >= 1
        assert results['execution'] is not None
        assert results['execution']['files_migrated'] >= 1
        
        # Verify file was copied (not moved)
        assert test_file.exists()  # Original still exists
        assert (archive_dir / "migrate_me.png").exists()  # Copy exists
        
        cache.close()
        registry.close()
    
    @pytest.mark.asyncio
    async def test_move_files(self, tmp_path):
        """Test moving files instead of copying."""
        # Setup test directories
        source_dir = tmp_path / "source"
        archive_dir = tmp_path / "archive"
        source_dir.mkdir()
        archive_dir.mkdir()
        
        # Create test file
        test_file = source_dir / "move_me.png"
        create_test_image(test_file, age_days=45)
        
        # Setup storage system
        cache = DuckDBSearchCache(tmp_path / "cache.db")
        registry = StorageRegistry(tmp_path / "registry.db")
        
        # Register locations
        source_location = StorageLocation(
            location_id=None,
            name="Source",
            type=StorageType.LOCAL,
            path=str(source_dir),
            priority=100,
            rules=[StorageRule(max_age_days=30)]
        )
        
        archive_location = StorageLocation(
            location_id=None,
            name="Archive",
            type=StorageType.LOCAL,
            path=str(archive_dir),
            priority=50,
            rules=[StorageRule(min_age_days=31)]
        )
        
        source_loc = registry.register_location(source_location)
        archive_loc = registry.register_location(archive_location)
        
        # Scan and create service
        scanner = MultiPathScanner(cache, registry)
        await scanner._scan_local_location(source_loc, show_progress=False)
        
        service = AutoMigrationService(cache, registry, scanner)
        
        # Run migration with move=True
        results = await service.run_auto_migration(
            dry_run=False,
            move_files=True,
            show_progress=False
        )
        
        # Verify file was moved
        assert not test_file.exists()  # Original gone
        assert (archive_dir / "move_me.png").exists()  # Moved to archive
        
        cache.close()
        registry.close()


class TestMigrationScheduler:
    """Test migration scheduler."""
    
    @pytest.mark.asyncio
    async def test_scheduler_start_stop(self, tmp_path):
        """Test starting and stopping scheduler."""
        # Minimal setup
        cache = DuckDBSearchCache(tmp_path / "cache.db")
        registry = StorageRegistry(tmp_path / "registry.db")
        
        service = AutoMigrationService(cache, registry)
        scheduler = MigrationScheduler(service)
        
        # Start scheduler
        await scheduler.start(interval_hours=24)
        assert scheduler._running
        assert scheduler._task is not None
        
        # Stop scheduler
        await scheduler.stop()
        assert not scheduler._running
        
        cache.close()
        registry.close()