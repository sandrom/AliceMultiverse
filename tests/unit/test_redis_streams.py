"""Tests for Redis Streams event system."""

import asyncio
import json
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

# Skip all tests if Redis is not available
try:
    from redis.exceptions import ResponseError

    from alicemultiverse.events.redis_streams import (
        RedisStreamsEventSystem,
        get_event_system,
        publish_event,
        publish_event_sync,
        subscribe_to_events,
    )
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    # Create dummy classes to prevent NameError
    ResponseError = Exception
    RedisStreamsEventSystem = None

pytestmark = pytest.mark.skipif(not REDIS_AVAILABLE, reason="Redis not installed")


@pytest.fixture
def mock_redis():
    """Create a mock Redis client."""
    redis_mock = AsyncMock()

    # Mock basic Redis operations
    redis_mock.xadd = AsyncMock(return_value="1234567890-0")
    redis_mock.xreadgroup = AsyncMock(return_value=[])
    redis_mock.xack = AsyncMock(return_value=1)
    redis_mock.xrange = AsyncMock(return_value=[])
    redis_mock.xrevrange = AsyncMock(return_value=[])
    redis_mock.xpending = AsyncMock(return_value=[0, None, None, None])
    redis_mock.xpending_range = AsyncMock(return_value=[])
    redis_mock.xclaim = AsyncMock(return_value=[])
    redis_mock.xgroup_create = AsyncMock()
    redis_mock.close = AsyncMock()

    return redis_mock


@pytest.fixture
async def event_system(mock_redis):
    """Create event system with mocked Redis."""
    # Mock redis.from_url as a coroutine that returns the mock
    async def mock_from_url(*args, **kwargs):
        return mock_redis

    with patch("alicemultiverse.events.redis_streams.redis.from_url", side_effect=mock_from_url):
        system = RedisStreamsEventSystem("redis://localhost:6379")
        yield system
        await system.stop_listening()


class TestRedisStreamsEventSystem:
    """Test Redis Streams event system functionality."""

    @pytest.mark.asyncio
    async def test_publish_event(self, event_system, mock_redis):
        """Test publishing an event."""
        event_data = {"user_id": "123", "action": "test"}

        # Publish event
        stream_id = await event_system.publish("user.action", event_data)

        # Verify Redis calls
        assert mock_redis.xadd.call_count == 2  # Event stream + global stream

        # Check event stream call
        event_call = mock_redis.xadd.call_args_list[0]
        assert event_call[0][0] == "events:user.action"
        assert json.loads(event_call[0][1]["data"]) == event_data
        assert "timestamp" in event_call[0][1]

        # Check global stream call
        global_call = mock_redis.xadd.call_args_list[1]
        assert global_call[0][0] == "events:all"

    def test_publish_sync(self, mock_redis):
        """Test synchronous event publishing."""
        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("alicemultiverse.events.redis_streams.redis.from_url", side_effect=mock_from_url):
            system = RedisStreamsEventSystem()

            event_data = {"test": "data"}
            stream_id = system.publish_sync("test.event", event_data)

            assert stream_id == "1234567890-0"
            assert mock_redis.xadd.called

    @pytest.mark.asyncio
    async def test_subscribe_unsubscribe(self, event_system):
        """Test subscribing and unsubscribing from events."""
        handler = AsyncMock()

        # Subscribe
        await event_system.subscribe("test.event", handler)
        assert "test.event" in event_system._listeners
        assert handler in event_system._listeners["test.event"]

        # Unsubscribe
        await event_system.unsubscribe("test.event", handler)
        assert "test.event" not in event_system._listeners

    @pytest.mark.asyncio
    async def test_pattern_matching(self, event_system):
        """Test event type pattern matching."""
        # Exact match
        assert event_system._matches_pattern("asset.processed", "asset.processed")

        # Wildcard prefix
        assert event_system._matches_pattern("asset.processed", "asset.*")
        assert event_system._matches_pattern("asset.created", "asset.*")
        assert not event_system._matches_pattern("user.login", "asset.*")

        # Global wildcard
        assert event_system._matches_pattern("anything", "*")

    @pytest.mark.asyncio
    async def test_consumer_group_creation(self, event_system, mock_redis):
        """Test consumer group creation."""
        # Subscribe to trigger consumer creation
        handler = AsyncMock()
        await event_system.subscribe("test.event", handler)

        # Start listening but stop immediately
        await event_system.start_listening()

        # Give a moment for consumer to start
        await asyncio.sleep(0.1)

        # Verify consumer group was created
        mock_redis.xgroup_create.assert_called_once()
        call_args = mock_redis.xgroup_create.call_args[0]
        assert call_args[0] == "events:test.event"
        assert call_args[1] == event_system._consumer_group

    @pytest.mark.asyncio
    async def test_consumer_group_already_exists(self, event_system, mock_redis):
        """Test handling when consumer group already exists."""
        # Mock BUSYGROUP error
        mock_redis.xgroup_create.side_effect = ResponseError("BUSYGROUP Consumer Group name already exists")

        # Should not raise error
        handler = AsyncMock()
        await event_system.subscribe("test.event", handler)
        await event_system.start_listening()

        # Give a moment for consumer to start
        await asyncio.sleep(0.1)

        # Verify it tried to create group
        assert mock_redis.xgroup_create.called

    @pytest.mark.asyncio
    async def test_message_processing(self, event_system, mock_redis):
        """Test processing messages from stream."""
        # Set up test data
        handler = AsyncMock()
        await event_system.subscribe("test.event", handler)

        # Mock message data
        test_data = {"key": "value"}
        message_data = {
            "id": str(uuid.uuid4()),
            "type": "test.event",
            "data": json.dumps(test_data),
            "timestamp": "2024-01-01T00:00:00Z"
        }

        # Process message
        await event_system._process_message("test.event", "1234567890-0", message_data)

        # Verify handler was called with parsed data
        handler.assert_called_once()
        call_data = handler.call_args[0][0]
        assert call_data["data"] == test_data

    @pytest.mark.asyncio
    async def test_wildcard_handler_called(self, event_system):
        """Test wildcard handlers are called for matching events."""
        specific_handler = AsyncMock()
        wildcard_handler = AsyncMock()
        global_handler = AsyncMock()

        await event_system.subscribe("asset.processed", specific_handler)
        await event_system.subscribe("asset.*", wildcard_handler)
        await event_system.subscribe("*", global_handler)

        # Process an asset.processed event
        message_data = {
            "id": "123",
            "type": "asset.processed",
            "data": json.dumps({"file": "test.jpg"}),
            "timestamp": "2024-01-01T00:00:00Z"
        }

        await event_system._process_message("asset.processed", "1234567890-0", message_data)

        # All handlers should be called
        assert specific_handler.called
        assert wildcard_handler.called
        assert global_handler.called

    @pytest.mark.asyncio
    async def test_sync_handler_execution(self, event_system):
        """Test synchronous handlers are executed properly."""
        sync_handler = MagicMock()

        await event_system.subscribe("test.event", sync_handler)

        message_data = {
            "id": "123",
            "type": "test.event",
            "data": json.dumps({"test": "data"}),
            "timestamp": "2024-01-01T00:00:00Z"
        }

        await event_system._process_message("test.event", "1234567890-0", message_data)

        # Sync handler should be called
        sync_handler.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_recent_events_by_type(self, event_system, mock_redis):
        """Test getting recent events filtered by type."""
        # Mock Redis response
        mock_redis.xrange.return_value = [
            ("1234567890-0", {
                "id": "event1",
                "type": "test.event",
                "data": json.dumps({"value": 1}),
                "timestamp": "2024-01-01T00:00:00Z"
            }),
            ("1234567890-1", {
                "id": "event2",
                "type": "test.event",
                "data": json.dumps({"value": 2}),
                "timestamp": "2024-01-01T00:01:00Z"
            })
        ]

        # Get events
        events = await event_system.get_recent_events(limit=10, event_type="test.event")

        # Verify Redis call
        mock_redis.xrange.assert_called_once_with(
            "events:test.event", "-", "+", count=10
        )

        # Verify returned data
        assert len(events) == 2
        assert events[0]["data"]["value"] == 1
        assert events[1]["data"]["value"] == 2

    @pytest.mark.asyncio
    async def test_get_recent_events_global(self, event_system, mock_redis):
        """Test getting recent events from global stream."""
        # Mock Redis response
        mock_redis.xrevrange.return_value = [
            ("1234567890-1", {
                "id": "event2",
                "type": "user.login",
                "data": json.dumps({"user": "alice"}),
                "timestamp": "2024-01-01T00:01:00Z"
            }),
            ("1234567890-0", {
                "id": "event1",
                "type": "asset.created",
                "data": json.dumps({"file": "test.jpg"}),
                "timestamp": "2024-01-01T00:00:00Z"
            })
        ]

        # Get all events
        events = await event_system.get_recent_events(limit=50)

        # Verify Redis call
        mock_redis.xrevrange.assert_called_once_with(
            "events:all", "+", "-", count=50
        )

        # Verify returned data (newest first)
        assert len(events) == 2
        assert events[0]["type"] == "user.login"
        assert events[1]["type"] == "asset.created"

    @pytest.mark.asyncio
    async def test_get_pending_messages(self, event_system, mock_redis):
        """Test getting pending messages."""
        # Mock pending response
        mock_redis.xpending.return_value = [2, "1234567890-0", "1234567890-1", [["consumer1", "2"]]]
        mock_redis.xpending_range.return_value = [
            ["1234567890-0", "consumer1", 5000, 1],
            ["1234567890-1", "consumer1", 3000, 2]
        ]

        # Get pending messages
        pending = await event_system.get_pending_messages("test.event")

        # Verify results
        assert len(pending) == 2
        assert pending[0]["message_id"] == "1234567890-0"
        assert pending[0]["idle_time_ms"] == 5000
        assert pending[0]["delivery_count"] == 1

    @pytest.mark.asyncio
    async def test_claim_abandoned_messages(self, event_system, mock_redis):
        """Test claiming abandoned messages."""
        # Mock pending messages
        mock_redis.xpending.return_value = [1, "1234567890-0", "1234567890-0", [["consumer1", "1"]]]
        mock_redis.xpending_range.return_value = [
            ["1234567890-0", "consumer1", 70000, 3]  # Idle for 70 seconds
        ]

        # Mock successful claim
        mock_redis.xclaim.return_value = [("1234567890-0", {"data": "test"})]

        # Claim messages
        claimed = await event_system.claim_abandoned_messages("test.event", idle_time_ms=60000)

        # Verify claim was made
        assert claimed == 1
        mock_redis.xclaim.assert_called_once()

    @pytest.mark.asyncio
    async def test_error_handling_in_handler(self, event_system):
        """Test error handling when handler raises exception."""
        # Handler that raises error
        error_handler = AsyncMock(side_effect=Exception("Handler error"))
        good_handler = AsyncMock()

        await event_system.subscribe("test.event", error_handler)
        await event_system.subscribe("test.event", good_handler)

        message_data = {
            "id": "123",
            "type": "test.event",
            "data": json.dumps({"test": "data"}),
            "timestamp": "2024-01-01T00:00:00Z"
        }

        # Should not raise error
        await event_system._process_message("test.event", "1234567890-0", message_data)

        # Good handler should still be called
        assert error_handler.called
        assert good_handler.called

    @pytest.mark.asyncio
    async def test_global_instance(self):
        """Test global event system instance."""
        async def mock_from_url(*args, **kwargs):
            return AsyncMock()

        with patch("alicemultiverse.events.redis_streams.redis.from_url", side_effect=mock_from_url):
            # Get instance
            system1 = get_event_system()
            system2 = get_event_system()

            # Should be the same instance
            assert system1 is system2

    @pytest.mark.asyncio
    async def test_convenience_functions(self, mock_redis):
        """Test convenience functions."""
        async def mock_from_url(*args, **kwargs):
            return mock_redis

        with patch("alicemultiverse.events.redis_streams.redis.from_url", side_effect=mock_from_url):
            # Test async publish
            await publish_event("test.event", {"data": "test"})
            assert mock_redis.xadd.called

            # Reset mock
            mock_redis.reset_mock()

            # Skip sync publish test in async context (would need threading)
            # publish_event_sync("test.event", {"data": "test"})
            # assert mock_redis.xadd.called

            # Test subscribe
            handler = AsyncMock()
            await subscribe_to_events("test.*", handler)
            system = get_event_system()
            assert "test.*" in system._listeners
