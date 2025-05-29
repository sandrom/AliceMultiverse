"""Tests for PostgreSQL event system."""

from datetime import datetime
from unittest.mock import Mock, patch

import pytest

from alicemultiverse.events.postgres_events import PostgresEventSystem


class TestPostgresEventSystem:
    """Test PostgreSQL event system functionality."""

    @patch('alicemultiverse.events.postgres_events.get_session')
    def test_publish_event(self, mock_get_session):
        """Test publishing events to PostgreSQL."""
        # Mock session
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        # Create event system
        event_system = PostgresEventSystem()
        
        # Publish an event
        event_data = {
            "asset_id": "test123",
            "file_path": "/test/path.jpg",
            "quality_score": 4.5
        }
        
        event_id = event_system.publish("asset.processed", event_data)
        
        # Verify event was inserted
        assert event_id is not None
        assert len(event_id) == 36  # UUID format
        
        # Verify database calls
        assert mock_session.execute.call_count == 2  # INSERT and NOTIFY
        
    @patch('alicemultiverse.events.postgres_events.get_session')
    def test_publish_with_metadata(self, mock_get_session):
        """Test publishing events with metadata."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        event_system = PostgresEventSystem()
        
        # Publish with metadata included in data
        event_data = {
            "test": "data",
            "metadata": {"user_id": "alice", "session_id": "abc123"}
        }
        
        event_id = event_system.publish(
            "workflow.started", 
            event_data
        )
        
        assert event_id is not None
        assert mock_session.execute.call_count == 2
        
    @patch('alicemultiverse.events.postgres_events.get_session')
    def test_different_event_types(self, mock_get_session):
        """Test various event types can be published."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        event_system = PostgresEventSystem()
        
        # Test different event types
        event_types = [
            ("asset.discovered", {"path": "/new/file.png"}),
            ("asset.organized", {"from": "/inbox", "to": "/organized"}),
            ("quality.assessed", {"score": 4.2, "method": "brisque"}),
            ("project.created", {"name": "Test Project"}),
            ("workflow.completed", {"duration": 123.45}),
        ]
        
        for event_type, data in event_types:
            event_id = event_system.publish(event_type, data)
            assert event_id is not None
            
    @patch('alicemultiverse.events.postgres_events.get_session')
    def test_event_channel_naming(self, mock_get_session):
        """Test that events use correct channel names."""
        mock_session = Mock()
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        event_system = PostgresEventSystem()
        
        # Publish event
        event_system.publish("asset.processed", {"test": "data"})
        
        # Check NOTIFY was called with correct channel
        notify_call = mock_session.execute.call_args_list[1]
        assert "alice_events" in str(notify_call)
        assert "asset.processed" in str(notify_call)
        
    @patch('alicemultiverse.events.postgres_events.get_session')
    def test_error_handling(self, mock_get_session):
        """Test error handling in event publishing."""
        mock_session = Mock()
        mock_session.execute.side_effect = Exception("Database error")
        mock_get_session.return_value.__enter__.return_value = mock_session
        
        event_system = PostgresEventSystem()
        
        # Should not raise, but log error
        event_id = event_system.publish("test.event", {"data": "test"})
        
        # Event ID should still be returned (generated before DB call)
        assert event_id is not None
        
    def test_event_data_serialization(self):
        """Test that event data is properly serialized."""
        event_system = PostgresEventSystem()
        
        # Complex data structure
        data = {
            "timestamp": datetime.now().isoformat(),
            "nested": {
                "list": [1, 2, 3],
                "dict": {"key": "value"}
            },
            "number": 42.5,
            "boolean": True,
            "null": None
        }
        
        # Should not raise during serialization
        with patch('alicemultiverse.events.postgres_events.get_session'):
            event_id = event_system.publish("test.complex", data)
            assert event_id is not None