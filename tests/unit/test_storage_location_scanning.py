"""Tests for storage location scanning functionality."""

import hashlib
import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from alicemultiverse.storage.location_registry import (
    LocationStatus,
    StorageLocation,
    StorageRegistry,
    StorageRule,
    StorageType,
)


class TestStorageLocationScanning:
    """Test storage location scanning functionality."""
    
    @pytest.fixture
    def registry(self, tmp_path):
        """Create a test registry with in-memory database."""
        return StorageRegistry()
    
    @pytest.fixture
    def local_location(self, tmp_path):
        """Create a local storage location."""
        location_path = tmp_path / "test_storage"
        location_path.mkdir()
        
        return StorageLocation(
            location_id="test_local",
            name="Test Local Storage",
            type=StorageType.LOCAL,
            path=str(location_path),
            priority=10,
            status=LocationStatus.ACTIVE
        )
    
    @pytest.fixture
    def sample_media_files(self, local_location):
        """Create sample media files in the location."""
        location_path = Path(local_location.path)
        
        # Create some test files
        files = []
        for i in range(3):
            file_path = location_path / f"image{i}.jpg"
            content = f"fake image data {i}".encode()
            file_path.write_bytes(content)
            files.append({
                "path": file_path,
                "content": content,
                "hash": hashlib.sha256(content).hexdigest()
            })
        
        # Create a subdirectory with more files
        subdir = location_path / "project1"
        subdir.mkdir()
        
        for i in range(2):
            file_path = subdir / f"video{i}.mp4"
            content = f"fake video data {i}".encode()
            file_path.write_bytes(content)
            files.append({
                "path": file_path,
                "content": content,
                "hash": hashlib.sha256(content).hexdigest()
            })
        
        return files
    
    def test_scan_local_location_discovery(self, registry, local_location, sample_media_files):
        """Test scanning discovers new files in local location."""
        # Register the location
        registry.register_location(local_location)
        
        # Scan the location
        result = registry._scan_local_location(local_location)
        
        assert result["location_id"] == "test_local"
        assert result["location_name"] == "Test Local Storage"
        assert result["files_discovered"] == 5  # 3 images + 2 videos
        assert result["files_updated"] == 0
        assert result["files_removed"] == 0
        assert "error" not in result
    
    def test_scan_local_location_updates(self, registry, local_location, sample_media_files):
        """Test scanning detects updated files."""
        registry.register_location(local_location)
        
        # First scan to discover files
        registry._scan_local_location(local_location)
        
        # Modify a file
        modified_file = Path(local_location.path) / "image0.jpg"
        modified_file.write_bytes(b"modified content")
        
        # Second scan should detect the update
        result = registry._scan_local_location(local_location)
        
        assert result["files_discovered"] == 0
        assert result["files_updated"] == 1
        assert result["files_removed"] == 0
    
    def test_scan_local_location_removals(self, registry, local_location, sample_media_files):
        """Test scanning detects removed files."""
        registry.register_location(local_location)
        
        # First scan to discover files
        registry._scan_local_location(local_location)
        
        # Remove a file
        removed_file = Path(local_location.path) / "image1.jpg"
        removed_file.unlink()
        
        # Second scan should detect the removal
        result = registry._scan_local_location(local_location)
        
        assert result["files_discovered"] == 0
        assert result["files_updated"] == 0
        assert result["files_removed"] == 1
        
        # Check that file is marked as missing
        missing_files = registry.conn.execute(
            "SELECT file_path FROM file_locations WHERE sync_status = 'missing' AND location_id = ?",
            ["test_local"]
        ).fetchall()
        
        assert len(missing_files) == 1
        assert missing_files[0][0] == "image1.jpg"
    
    def test_scan_nonexistent_location(self, registry):
        """Test scanning a location with non-existent path."""
        location = StorageLocation(
            location_id="bad_location",
            name="Bad Location",
            type=StorageType.LOCAL,
            path="/nonexistent/path",
            priority=1
        )
        
        result = registry._scan_local_location(location)
        
        assert result["error"] == "Path does not exist"
        assert result["files_discovered"] == 0
        assert result["files_updated"] == 0
        assert result["files_removed"] == 0
    
    def test_scan_location_with_non_media_files(self, registry, local_location):
        """Test that scanning ignores non-media files."""
        location_path = Path(local_location.path)
        
        # Create media and non-media files
        (location_path / "image.jpg").write_bytes(b"image")
        (location_path / "document.txt").write_bytes(b"text")
        (location_path / "script.py").write_bytes(b"code")
        (location_path / "video.mp4").write_bytes(b"video")
        
        registry.register_location(local_location)
        result = registry._scan_local_location(local_location)
        
        # Should only discover media files
        assert result["files_discovered"] == 2  # Only jpg and mp4
    
    def test_scan_location_with_hidden_directories(self, registry, local_location):
        """Test that scanning ignores hidden directories."""
        location_path = Path(local_location.path)
        
        # Create visible and hidden directories
        visible_dir = location_path / "visible"
        visible_dir.mkdir()
        (visible_dir / "image.jpg").write_bytes(b"visible image")
        
        hidden_dir = location_path / ".hidden"
        hidden_dir.mkdir()
        (hidden_dir / "image.jpg").write_bytes(b"hidden image")
        
        registry.register_location(local_location)
        result = registry._scan_local_location(local_location)
        
        # Should only find the visible file
        assert result["files_discovered"] == 1
        
        # Verify the discovered file
        files = registry.conn.execute(
            "SELECT file_path FROM file_locations WHERE location_id = ?",
            ["test_local"]
        ).fetchall()
        
        assert len(files) == 1
        assert "visible" in files[0][0]
        assert ".hidden" not in files[0][0]
    
    def test_scan_location_error_handling(self, registry, local_location):
        """Test error handling during file scanning."""
        location_path = Path(local_location.path)
        
        # Create a file that will cause an error when reading
        problem_file = location_path / "problem.jpg"
        problem_file.write_bytes(b"data")
        
        # Make file unreadable (platform-specific, may not work on all systems)
        try:
            problem_file.chmod(0o000)
            
            registry.register_location(local_location)
            
            # Should handle the error gracefully
            result = registry._scan_local_location(local_location)
            
            # The scan should complete, possibly with 0 or 1 file discovered
            # depending on whether the error prevented discovery
            assert "error" not in result  # No overall error
            assert isinstance(result["files_discovered"], int)
        finally:
            # Restore permissions for cleanup
            try:
                problem_file.chmod(0o644)
            except:
                pass
    
    def test_scan_s3_location_placeholder(self, registry):
        """Test S3 scanning returns placeholder result."""
        s3_location = StorageLocation(
            location_id="test_s3",
            name="Test S3 Bucket", 
            type=StorageType.S3,
            path="s3://test-bucket",
            priority=5
        )
        
        result = registry._scan_s3_location(s3_location)
        
        assert result["location_id"] == "test_s3"
        assert result["error"] == "S3 scanning not implemented"
        assert result["files_discovered"] == 0
        assert result["files_updated"] == 0
        assert result["files_removed"] == 0
    
    def test_scan_gcs_location_placeholder(self, registry):
        """Test GCS scanning returns placeholder result."""
        gcs_location = StorageLocation(
            location_id="test_gcs",
            name="Test GCS Bucket",
            type=StorageType.GCS, 
            path="gs://test-bucket",
            priority=5
        )
        
        result = registry._scan_gcs_location(gcs_location)
        
        assert result["location_id"] == "test_gcs"
        assert result["error"] == "GCS scanning not implemented"
        assert result["files_discovered"] == 0
        assert result["files_updated"] == 0
        assert result["files_removed"] == 0
    
    def test_scan_location_full_integration(self, registry, local_location, sample_media_files):
        """Test full scan_location method integration."""
        registry.register_location(local_location)
        
        # Mock the appropriate scan method based on type
        with patch.object(registry, '_scan_local_location') as mock_scan:
            mock_scan.return_value = {
                "location_id": "test_local",
                "location_name": "Test Local Storage",
                "scan_time": datetime.now().isoformat(),
                "files_discovered": 5,
                "files_updated": 0,
                "files_removed": 0
            }
            
            result = registry.scan_location("test_local")
            
            mock_scan.assert_called_once()
            assert result["files_discovered"] == 5
        
        # Verify last_scan was updated
        location = registry.get_location_by_id("test_local")
        assert location.last_scan is not None
    
    def test_scan_location_not_found(self, registry):
        """Test scanning non-existent location raises error."""
        with pytest.raises(ValueError) as exc_info:
            registry.scan_location("nonexistent_id")
        
        assert "Location nonexistent_id not found" in str(exc_info.value)
    
    def test_add_and_update_file_methods(self, registry, local_location):
        """Test the add and update file helper methods."""
        registry.register_location(local_location)
        
        # Test adding a new file
        registry.add_file_to_location(
            content_hash="test_hash_1",
            location_id="test_local",
            file_path="test/file1.jpg",
            file_size=1000
        )
        
        # Verify file was added
        files = registry.get_file_locations("test_hash_1")
        assert len(files) == 1
        assert files[0]["file_path"] == "test/file1.jpg"
        assert files[0]["file_size"] == 1000
        
        # Test updating the file
        registry.update_file_in_location(
            content_hash="test_hash_2",  # New hash (file changed)
            location_id="test_local",
            file_path="test/file1.jpg",
            file_size=2000
        )
        
        # Old hash should be gone, new hash should exist
        old_files = registry.get_file_locations("test_hash_1")
        new_files = registry.get_file_locations("test_hash_2")
        
        assert len(old_files) == 0
        assert len(new_files) == 1
        assert new_files[0]["file_size"] == 2000