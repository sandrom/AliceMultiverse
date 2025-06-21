"""Tests for batch operations functionality."""

import json
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from alicemultiverse.storage.batch_operations import BatchOperationsMixin


class MockStorage(BatchOperationsMixin):
    """Mock storage class that includes batch operations."""
    
    def __init__(self):
        self.conn = MagicMock()
        self._batch_size = 100
    
    def upsert_asset(self, asset_data):
        """Mock individual upsert."""
        pass


class TestBatchOperations:
    """Test BatchOperationsMixin functionality."""
    
    @pytest.fixture
    def storage(self):
        """Create test storage instance."""
        return MockStorage()
    
    @pytest.fixture
    def sample_assets(self):
        """Create sample asset data."""
        return [
            {
                "content_hash": f"hash{i}",
                "file_path": f"/path/to/file{i}.jpg",
                "file_name": f"file{i}.jpg",
                "file_size": 1000 * i,
                "media_type": "image",
                "source_type": "midjourney",
                "date_taken": datetime(2024, 1, i + 1),
                "project": f"project{i % 3}",
                "metadata": {"width": 1024, "height": 768}
            }
            for i in range(5)
        ]
    
    def test_batch_upsert_assets(self, storage, sample_assets):
        """Test batch upserting assets."""
        # Mock execute to return rowcount
        storage.conn.execute.return_value.rowcount = len(sample_assets)
        
        result = storage.batch_upsert_assets(sample_assets)
        
        assert result == len(sample_assets)
        # Should have called execute multiple times (BEGIN, executemany for inserts, COMMIT)
        assert storage.conn.execute.call_count >= 2  # At least BEGIN and COMMIT
        
        # Check that executemany was called for batch insert
        storage.conn.executemany.assert_called()
        
        # Check the SQL in executemany calls
        for call in storage.conn.executemany.call_args_list:
            sql = call[0][0]
            if "INSERT" in sql and "assets" in sql:
                assert "INSERT OR REPLACE INTO assets" in sql
                assert "VALUES" in sql
                break
        else:
            assert False, "No INSERT statement for assets found"
    
    def test_batch_upsert_empty_list(self, storage):
        """Test batch upsert with empty list."""
        result = storage.batch_upsert_assets([])
        
        assert result == 0
        storage.conn.execute.assert_not_called()
    
    def test_batch_upsert_with_datetime_serialization(self, storage):
        """Test that datetime objects are properly serialized."""
        assets_with_datetime = [{
            "content_hash": "test_hash",
            "file_path": "/test.jpg",
            "file_name": "test.jpg", 
            "file_size": 1000,
            "media_type": "image",
            "source_type": "dalle",
            "date_taken": datetime(2024, 1, 15, 10, 30, 0),
            "metadata": {
                "created_at": datetime(2024, 1, 15, 10, 30, 0),
                "width": 512
            }
        }]
        
        storage.conn.execute.return_value.rowcount = 1
        result = storage.batch_upsert_assets(assets_with_datetime)
        
        assert result == 1
        # Check that executemany was called with properly serialized data
        storage.conn.executemany.assert_called()
        
        # Find the assets insert call
        for call in storage.conn.executemany.call_args_list:
            sql = call[0][0]
            if "INSERT OR REPLACE INTO assets" in sql:
                # Check the data passed to executemany
                data = call[0][1]
                assert len(data) == 1
                # metadata is at index 17 (18th parameter)
                metadata = data[0][17]
                # Metadata should be a dict (DuckDB can handle JSON natively)
                assert isinstance(metadata, dict)
                assert metadata["width"] == 512
                break
        else:
            assert False, "No INSERT statement for assets found"
    
    def test_batch_update_tags(self, storage):
        """Test batch updating tags."""
        tag_updates = [
            ("hash1", ["portrait", "outdoor", "sunset"]),
            ("hash2", ["landscape", "mountain", "snow"]),
            ("hash3", ["abstract", "colorful", "digital"])
        ]
        
        storage.conn.execute.return_value.rowcount = len(tag_updates)
        result = storage.batch_update_tags(tag_updates)
        
        assert result == len(tag_updates)
        # Should have multiple execute calls (BEGIN, DELETE, COMMIT) and executemany for INSERT and UPDATE
        assert storage.conn.execute.call_count >= 3  # BEGIN, DELETE, COMMIT
        assert storage.conn.executemany.call_count >= 2  # INSERT tags, UPDATE timestamps
        
        # Check that the correct SQL was used
        # Check DELETE was called
        delete_found = False
        for call in storage.conn.execute.call_args_list:
            sql = call[0][0]
            if "DELETE FROM tags" in sql:
                delete_found = True
                break
        assert delete_found, "DELETE FROM tags not found"
        
        # Check INSERT tags was called via executemany
        insert_found = False
        for call in storage.conn.executemany.call_args_list:
            sql = call[0][0]
            if "INSERT INTO tags" in sql:
                insert_found = True
                break
        assert insert_found, "INSERT INTO tags not found"
    
    def test_batch_update_tags_empty(self, storage):
        """Test batch update tags with empty list."""
        result = storage.batch_update_tags([])
        
        assert result == 0
        storage.conn.execute.assert_not_called()
    
    def test_batch_add_to_collection(self, storage):
        """Test batch adding assets to collection."""
        collection_items = [
            ("collection1", "hash1"),
            ("collection1", "hash2"),
            ("collection2", "hash3")
        ]
        
        storage.conn.execute.return_value.rowcount = len(collection_items)
        result = storage.batch_add_to_collection(collection_items)
        
        assert result == len(collection_items)
        storage.conn.execute.assert_called_once()
        
        # Check SQL
        sql_call = storage.conn.execute.call_args[0][0]
        assert "INSERT INTO collection_items" in sql_call
        assert "ON CONFLICT" in sql_call
        assert "DO NOTHING" in sql_call
    
    def test_batch_get_assets(self, storage):
        """Test batch getting assets by content hashes."""
        hashes = ["hash1", "hash2", "hash3"]
        
        # Mock return data
        mock_rows = [
            ("hash1", "/path1.jpg", "file1.jpg", 1000, "image", "midjourney"),
            ("hash2", "/path2.jpg", "file2.jpg", 2000, "image", "dalle"),
            ("hash3", "/path3.jpg", "file3.jpg", 3000, "video", "runway")
        ]
        storage.conn.execute.return_value.fetchall.return_value = mock_rows
        
        results = storage.batch_get_assets(hashes)
        
        assert len(results) == 3
        assert results[0]["content_hash"] == "hash1"
        assert results[1]["media_type"] == "image" 
        assert results[2]["source_type"] == "runway"
        
        # Check SQL uses IN clause
        sql_call = storage.conn.execute.call_args[0][0]
        assert "WHERE content_hash IN" in sql_call
        assert "?" in sql_call  # Parameterized query
    
    def test_batch_get_assets_empty(self, storage):
        """Test batch get with empty hash list."""
        results = storage.batch_get_assets([])
        
        assert results == []
        storage.conn.execute.assert_not_called()
    
    def test_batch_operations_with_chunks(self, storage):
        """Test that large batches are processed in chunks."""
        # Create more assets than batch size
        large_asset_list = [
            {
                "content_hash": f"hash{i}",
                "file_path": f"/path{i}.jpg",
                "file_name": f"file{i}.jpg",
                "file_size": 1000,
                "media_type": "image",
                "source_type": "flux",
                "date_taken": None,
                "metadata": {}
            }
            for i in range(250)  # More than default batch size of 100
        ]
        
        # Mock to return different rowcounts for each chunk
        storage.conn.execute.return_value.rowcount = 100
        
        result = storage.batch_upsert_assets(large_asset_list)
        
        # Should process in 3 chunks (100, 100, 50)
        assert storage.conn.execute.call_count == 3
        assert result == 300  # Total of all rowcounts
    
    def test_batch_upsert_error_handling(self, storage, sample_assets):
        """Test error handling in batch operations."""
        # Mock database error
        storage.conn.execute.side_effect = Exception("Database error")
        
        with pytest.raises(Exception) as exc_info:
            storage.batch_upsert_assets(sample_assets)
        
        assert "Database error" in str(exc_info.value)
    
    def test_batch_operations_preserve_order(self, storage):
        """Test that batch operations preserve asset order."""
        # Create assets with specific order
        assets = [
            {"content_hash": "z_last", "file_path": "/z.jpg", "file_name": "z.jpg", 
             "file_size": 1000, "media_type": "image", "source_type": "dalle"},
            {"content_hash": "a_first", "file_path": "/a.jpg", "file_name": "a.jpg",
             "file_size": 2000, "media_type": "image", "source_type": "midjourney"},
            {"content_hash": "m_middle", "file_path": "/m.jpg", "file_name": "m.jpg",
             "file_size": 3000, "media_type": "image", "source_type": "flux"}
        ]
        
        storage.conn.execute.return_value.rowcount = len(assets)
        storage.batch_upsert_assets(assets)
        
        # Check that values were passed in correct order
        call_args = storage.conn.execute.call_args[0][1]
        # First 8 parameters are for first asset
        assert call_args[0] == "z_last"
        assert call_args[1] == "/z.jpg"
        # Next 8 parameters are for second asset  
        assert call_args[9] == "a_first"
        assert call_args[10] == "/a.jpg"
    
    def test_batch_size_configuration(self):
        """Test that batch size can be configured."""
        storage = MockStorage()
        storage._batch_size = 50  # Custom batch size
        
        # Create 150 items
        large_list = [
            {"content_hash": f"hash{i}", "file_path": f"/file{i}.jpg", 
             "file_name": f"file{i}.jpg", "file_size": 1000,
             "media_type": "image", "source_type": "dalle"}
            for i in range(150)
        ]
        
        storage.conn.execute.return_value.rowcount = 50
        storage.batch_upsert_assets(large_list)
        
        # Should be 3 batches with size 50
        assert storage.conn.execute.call_count == 3