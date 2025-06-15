"""Tests for file-based event system."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from alicemultiverse.events.file_events import (
    FileBasedEventSystem,
    get_event_system,
    publish_event_sync,
)


@pytest.fixture
def temp_event_dir():
    """Create a temporary directory for event logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def event_system(temp_event_dir):
    """Create event system with temporary directory."""
    return FileBasedEventSystem(event_log_dir=Path(temp_event_dir))


def test_publish_sync(event_system, temp_event_dir):
    """Test synchronous event publishing."""
    # Publish an event
    event_id = event_system.publish_sync(
        "test.event",
        {"message": "Hello, World!", "value": 42}
    )

    # Check event was written
    event_files = list(Path(temp_event_dir).glob("events_*.jsonl"))
    assert len(event_files) == 1

    # Read and verify event
    with open(event_files[0]) as f:
        line = f.readline()
        event = json.loads(line)

    assert event["id"] == event_id
    assert event["type"] == "test.event"
    assert event["data"]["message"] == "Hello, World!"
    assert event["data"]["value"] == 42
    assert "timestamp" in event


@pytest.mark.asyncio
async def test_publish_async(event_system, temp_event_dir):
    """Test asynchronous event publishing."""
    # Publish an event
    event_id = await event_system.publish(
        "test.async",
        {"async": True}
    )

    # Check event was written
    event_files = list(Path(temp_event_dir).glob("events_*.jsonl"))
    assert len(event_files) == 1

    # Read and verify event
    with open(event_files[0]) as f:
        line = f.readline()
        event = json.loads(line)

    assert event["id"] == event_id
    assert event["type"] == "test.async"
    assert event["data"]["async"] is True


def test_publish_multiple_events(event_system, temp_event_dir):
    """Test publishing multiple events."""
    # Publish several events
    event_ids = []
    for i in range(5):
        event_id = event_system.publish_sync(
            f"test.event.{i}",
            {"index": i}
        )
        event_ids.append(event_id)

    # Read all events
    event_files = list(Path(temp_event_dir).glob("events_*.jsonl"))
    assert len(event_files) == 1

    with open(event_files[0]) as f:
        events = [json.loads(line) for line in f]

    assert len(events) == 5
    for i, event in enumerate(events):
        assert event["id"] == event_ids[i]
        assert event["type"] == f"test.event.{i}"
        assert event["data"]["index"] == i


def test_local_listeners(event_system):
    """Test local event listeners."""
    received_events = []

    def handler(event):
        received_events.append(event)

    # Subscribe to events
    event_system._listeners["test.event"] = [handler]

    # Publish event
    event_system.publish_sync("test.event", {"test": True})

    # Check handler was called
    assert len(received_events) == 1
    assert received_events[0]["type"] == "test.event"
    assert received_events[0]["data"]["test"] is True


def test_wildcard_listeners(event_system):
    """Test wildcard event listeners."""
    received_events = []

    def handler(event):
        received_events.append(event)

    # Subscribe with wildcard
    event_system._listeners["test.*"] = [handler]
    event_system._listeners["*"] = [handler]

    # Publish events
    event_system.publish_sync("test.one", {"num": 1})
    event_system.publish_sync("other.event", {"num": 2})

    # Check handlers were called
    assert len(received_events) == 3  # test.one matches both wildcards, other.event matches *

    # Group by event type
    by_type = {}
    for event in received_events:
        event_type = event["type"]
        by_type[event_type] = by_type.get(event_type, 0) + 1

    assert by_type["test.one"] == 2  # Matched by test.* and *
    assert by_type["other.event"] == 1  # Matched by * only


@pytest.mark.asyncio
async def test_get_recent_events(event_system):
    """Test retrieving recent events."""
    # Publish some events
    for i in range(10):
        event_system.publish_sync("test.event", {"index": i})

    # Get recent events
    events = await event_system.get_recent_events(limit=5)

    assert len(events) == 5
    # Should be in reverse order (most recent first)
    for i, event in enumerate(events):
        assert event["data"]["index"] == 9 - i


@pytest.mark.asyncio
async def test_get_recent_events_with_filter(event_system):
    """Test retrieving events with type filter."""
    # Publish different types of events
    event_system.publish_sync("asset.created", {"name": "image1.jpg"})
    event_system.publish_sync("workflow.started", {"id": "wf1"})
    event_system.publish_sync("asset.processed", {"name": "image2.jpg"})

    # Get only asset events
    events = await event_system.get_recent_events(event_type="asset.created")

    assert len(events) == 1
    assert events[0]["type"] == "asset.created"
    assert events[0]["data"]["name"] == "image1.jpg"


def test_error_handling(event_system):
    """Test that publish doesn't crash on errors."""
    # Mock file writing to raise an error
    with patch("builtins.open", side_effect=OSError("Disk full")):
        # Should not raise an exception
        event_id = event_system.publish_sync("test.event", {"test": True})

        # Should still return an event ID
        assert event_id is not None


def test_pattern_matching(event_system):
    """Test event pattern matching."""
    assert event_system._matches_pattern("asset.created", "*") is True
    assert event_system._matches_pattern("asset.created", "asset.*") is True
    assert event_system._matches_pattern("asset.created", "asset.created") is True
    assert event_system._matches_pattern("asset.created", "workflow.*") is False
    assert event_system._matches_pattern("asset.created", "other") is False


def test_global_event_system():
    """Test global event system functions."""
    # Get global instance
    system1 = get_event_system()
    system2 = get_event_system()

    # Should be the same instance
    assert system1 is system2

    # Test convenience functions
    event_id = publish_event_sync("test.global", {"global": True})
    assert event_id is not None
