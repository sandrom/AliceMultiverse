"""Tests for event system."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from alicemultiverse.events.file_events import FileBasedEventSystem


class TestEventSystem:
    """Test event system functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.event_dir = Path(self.temp_dir) / "events"
        self.event_dir.mkdir(parents=True, exist_ok=True)

    def teardown_method(self):
        """Clean up test environment."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_publish_event(self):
        """Test publishing events to file system."""
        event_system = FileBasedEventSystem(self.event_dir)
        
        # Publish an event
        event_data = {
            "asset_id": "test123",
            "file_path": "/test/path.jpg",
            "quality_score": 4.5
        }
        
        event_id = event_system.publish("asset.processed", event_data)
        
        # Verify event was created
        assert event_id is not None
        assert len(event_id) == 36  # UUID format
        
        # Verify event file exists
        event_files = list(self.event_dir.glob("*.jsonl"))
        assert len(event_files) > 0
        
        # Verify event content
        with open(event_files[0], 'r') as f:
            lines = f.readlines()
            assert len(lines) == 1
            event = json.loads(lines[0])
            assert event["id"] == event_id
            assert event["type"] == "asset.processed"
            assert event["data"]["asset_id"] == "test123"

    def test_publish_with_metadata(self):
        """Test publishing events with metadata."""
        event_system = FileBasedEventSystem(self.event_dir)
        
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
        
        # Verify metadata is preserved
        event_files = list(self.event_dir.glob("*.jsonl"))
        with open(event_files[0], 'r') as f:
            event = json.loads(f.readline())
            assert event["data"]["metadata"]["user_id"] == "alice"
            assert event["data"]["metadata"]["session_id"] == "abc123"

    def test_different_event_types(self):
        """Test various event types can be published."""
        event_system = FileBasedEventSystem(self.event_dir)
        
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

        # Verify all events were written
        event_files = list(self.event_dir.glob("*.jsonl"))
        assert len(event_files) > 0
        
        with open(event_files[0], 'r') as f:
            lines = f.readlines()
            assert len(lines) == len(event_types)
            
            # Verify each event type
            for i, (event_type, _) in enumerate(event_types):
                event = json.loads(lines[i])
                assert event["type"] == event_type

    def test_event_file_rotation(self):
        """Test that events are organized by date."""
        event_system = FileBasedEventSystem(self.event_dir)
        
        # Publish event
        event_system.publish("asset.processed", {"test": "data"})
        
        # Check file naming
        today = datetime.now().strftime("%Y-%m-%d")
        expected_file = self.event_dir / f"events_{today}.jsonl"
        assert expected_file.exists()

    def test_error_handling(self):
        """Test error handling in event publishing."""
        # Create event system with invalid directory
        event_system = FileBasedEventSystem("/invalid/path/that/does/not/exist")
        
        # Should not raise, but handle gracefully
        event_id = event_system.publish("test.event", {"data": "test"})
        
        # Event ID should still be returned
        assert event_id is not None

    def test_event_data_serialization(self):
        """Test that event data is properly serialized."""
        event_system = FileBasedEventSystem(self.event_dir)
        
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
        event_id = event_system.publish("test.complex", data)
        assert event_id is not None
        
        # Verify data integrity
        event_files = list(self.event_dir.glob("*.jsonl"))
        with open(event_files[0], 'r') as f:
            event = json.loads(f.readline())
            assert event["data"]["nested"]["list"] == [1, 2, 3]
            assert event["data"]["nested"]["dict"]["key"] == "value"
            assert event["data"]["number"] == 42.5
            assert event["data"]["boolean"] is True
            assert event["data"]["null"] is None

    def test_subscribe_to_events(self):
        """Test event subscription functionality."""
        event_system = FileBasedEventSystem(self.event_dir)
        
        # Publish some events
        event_system.publish("asset.processed", {"id": "1"})
        event_system.publish("asset.organized", {"id": "2"})
        event_system.publish("workflow.started", {"id": "3"})
        
        # Subscribe and collect events
        events = []
        for event in event_system.subscribe(event_types=["asset.*"]):
            events.append(event)
            if len(events) >= 2:  # Stop after asset events
                break
        
        # Verify we got only asset events
        assert len(events) == 2
        assert all(e["type"].startswith("asset.") for e in events)
        assert events[0]["data"]["id"] == "1"
        assert events[1]["data"]["id"] == "2"