"""Tests for event persistence with Redis Streams."""

from unittest.mock import AsyncMock, patch

import pytest

# Skip tests if redis not installed
redis = pytest.importorskip("redis")

from alicemultiverse.events.asset_events_v2 import AssetDiscoveredEvent
from alicemultiverse.events.persistence import EventPersistence, get_persistence
from alicemultiverse.events.workflow_events_v2 import WorkflowStartedEvent


@pytest.fixture
async def mock_redis():
    """Create a mock Redis client."""
    mock = AsyncMock()

    # Mock basic Redis operations
    mock.xadd = AsyncMock(return_value="1234567890-0")
    mock.xrange = AsyncMock(
        return_value=[
            ("1234567890-0", {"event": '{"event_id": "test-123", "event_type": "test.event"}'})
        ]
    )
    mock.xreadgroup = AsyncMock(return_value=[])
    mock.xgroup_create = AsyncMock()
    mock.xack = AsyncMock()
    mock.xpending_range = AsyncMock(return_value=[])
    mock.xclaim = AsyncMock(return_value=[])
    mock.xtrim = AsyncMock()
    mock.xinfo_stream = AsyncMock(
        return_value={
            "length": 100,
            "first-entry": ["1234567890-0", {"event": "{}"}],
            "last-entry": ["1234567891-0", {"event": "{}"}],
        }
    )
    mock.xinfo_groups = AsyncMock(return_value=[])
    mock.close = AsyncMock()

    return mock


@pytest.fixture
async def persistence(mock_redis):
    """Create EventPersistence instance with mocked Redis."""
    with patch("alicemultiverse.events.persistence.redis.from_url", return_value=mock_redis):
        ep = EventPersistence()
        await ep.connect()
        yield ep
        await ep.disconnect()


class TestEventPersistence:
    """Test event persistence functionality."""

    async def test_persist_event(self, persistence, mock_redis):
        """Test persisting an event to Redis."""
        event = AssetDiscoveredEvent(
            file_path="/test.jpg",
            content_hash="abc123",
            file_size=1024,
            media_type="image",
            project_name="test-project",
        )

        # Persist event
        entry_id = await persistence.persist_event(event)

        # Verify Redis calls
        assert mock_redis.xadd.call_count == 2  # Type-specific and global stream
        assert entry_id == "1234567890-0"

        # Check type-specific stream call
        call_args = mock_redis.xadd.call_args_list[0]
        assert call_args[0][0] == "alice:events:asset.discovered"
        assert "event" in call_args[0][1]

        # Check global stream call
        call_args = mock_redis.xadd.call_args_list[1]
        assert call_args[0][0] == "alice:events:all"
        assert "type" in call_args[0][1]
        assert call_args[0][1]["type"] == "asset.discovered"

    async def test_get_events(self, persistence, mock_redis):
        """Test retrieving events from a stream."""
        # Set up mock response
        mock_redis.xrange.return_value = [
            ("1234567890-0", {"event": '{"event_id": "e1", "event_type": "asset.discovered"}'}),
            ("1234567891-0", {"event": '{"event_id": "e2", "event_type": "asset.discovered"}'}),
        ]

        # Get events
        events = await persistence.get_events("asset.discovered", count=10)

        # Verify
        assert len(events) == 2
        assert events[0]["stream_id"] == "1234567890-0"
        assert events[0]["event"]["event_id"] == "e1"
        assert events[1]["stream_id"] == "1234567891-0"
        assert events[1]["event"]["event_id"] == "e2"

        # Check Redis call
        mock_redis.xrange.assert_called_once()
        call_args = mock_redis.xrange.call_args
        assert call_args[0][0] == "alice:events:asset.discovered"

    async def test_consume_events(self, persistence, mock_redis):
        """Test consuming events with consumer groups."""
        # Set up mock response
        mock_redis.xreadgroup.return_value = [
            (
                "alice:events:asset.discovered",
                [
                    (
                        "1234567890-0",
                        {"event": '{"event_id": "e1", "event_type": "asset.discovered"}'},
                    )
                ],
            )
        ]

        # Consume events
        consumed = []
        consumer = persistence.consume_events(
            ["asset.discovered"], "test-consumer", block_ms=100, count=1
        )

        # Get one event
        async for event_data in consumer:
            consumed.append(event_data)
            await event_data["ack"]()  # Test acknowledgment
            break

        # Verify
        assert len(consumed) == 1
        assert consumed[0]["event"]["event_id"] == "e1"
        assert consumed[0]["message_id"] == "1234567890-0"

        # Check acknowledgment was called
        mock_redis.xack.assert_called_once_with(
            "alice:events:asset.discovered", "alice-main", "1234567890-0"
        )

    async def test_get_pending_events(self, persistence, mock_redis):
        """Test retrieving pending events."""
        # Set up mock response
        mock_redis.xpending_range.return_value = [
            {
                "message_id": "1234567890-0",
                "consumer": "test-consumer",
                "idle": 70000,
                "times_delivered": 2,
            }
        ]

        mock_redis.xclaim.return_value = [
            ("1234567890-0", {"event": '{"event_id": "e1", "event_type": "asset.discovered"}'})
        ]

        # Get pending events
        pending = await persistence.get_pending_events(
            "asset.discovered", consumer_name="test-consumer"
        )

        # Verify
        assert len(pending) == 1
        assert pending[0]["stream_id"] == "1234567890-0"
        assert pending[0]["event"]["event_id"] == "e1"
        assert pending[0]["idle_ms"] == 70000
        assert pending[0]["delivery_count"] == 2

    async def test_trim_old_events(self, persistence, mock_redis):
        """Test trimming old events."""
        # Trim events
        await persistence.trim_old_events("asset.discovered", max_age_days=7)

        # Verify Redis call
        mock_redis.xtrim.assert_called_once()
        call_args = mock_redis.xtrim.call_args
        assert call_args[0][0] == "alice:events:asset.discovered"
        assert "minid" in call_args[1]

    async def test_get_stream_info(self, persistence, mock_redis):
        """Test getting stream information."""
        # Get info
        info = await persistence.get_stream_info("asset.discovered")

        # Verify
        assert info["length"] == 100
        assert "first-entry" in info
        assert "last-entry" in info
        assert "consumer_groups" in info

        # Check Redis calls
        mock_redis.xinfo_stream.assert_called_once_with("alice:events:asset.discovered")

    async def test_context_manager(self, mock_redis):
        """Test using persistence as a context manager."""
        with patch("alicemultiverse.events.persistence.redis.from_url", return_value=mock_redis):
            async with EventPersistence() as ep:
                # Should connect
                assert ep._redis is not None

                # Use it
                event = AssetDiscoveredEvent(
                    file_path="/test.jpg",
                    content_hash="abc123",
                    file_size=1024,
                    media_type="image",
                    project_name="test",
                )
                await ep.persist_event(event)

            # Should disconnect
            mock_redis.close.assert_called_once()

    async def test_get_persistence_singleton(self, mock_redis):
        """Test get_persistence returns singleton."""
        with patch("alicemultiverse.events.persistence.redis.from_url", return_value=mock_redis):
            # Reset global
            import alicemultiverse.events.persistence

            alicemultiverse.events.persistence._persistence = None

            # Get instance twice
            p1 = await get_persistence()
            p2 = await get_persistence()

            # Should be same instance
            assert p1 is p2

            # Cleanup
            await p1.disconnect()
            alicemultiverse.events.persistence._persistence = None


class TestEventPersistenceIntegration:
    """Integration tests with multiple event types."""

    async def test_persist_multiple_event_types(self, persistence, mock_redis):
        """Test persisting different event types."""
        # Create different events
        asset_event = AssetDiscoveredEvent(
            file_path="/test.jpg",
            content_hash="abc123",
            file_size=1024,
            media_type="image",
            project_name="test",
        )

        workflow_event = WorkflowStartedEvent(
            workflow_id="wf-123", workflow_type="processing", workflow_name="Process Images"
        )

        # Persist both
        await persistence.persist_event(asset_event)
        await persistence.persist_event(workflow_event)

        # Verify different streams were used
        calls = mock_redis.xadd.call_args_list
        stream_keys = [call[0][0] for call in calls]

        assert "alice:events:asset.discovered" in stream_keys
        assert "alice:events:workflow.started" in stream_keys
        assert stream_keys.count("alice:events:all") == 2  # Both in global stream
