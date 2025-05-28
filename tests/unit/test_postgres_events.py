"""Tests for the PostgreSQL-native event system."""

import asyncio
import json
import time
from unittest.mock import MagicMock, patch

import pytest

from alicemultiverse.events.postgres_events import (
    PostgresEventSystem,
    get_event_system,
    publish_event,
    subscribe_to_events,
)


class TestPostgresEventSystem:
    """Test PostgreSQL event system."""
    
    def test_publish_event(self):
        """Test synchronous event publishing."""
        event_system = PostgresEventSystem()
        
        # Publish an event
        event_id = event_system.publish("test.event", {"message": "Hello"})
        
        assert event_id is not None
        assert len(event_id) == 36  # UUID format
        
    def test_get_recent_events(self):
        """Test retrieving recent events."""
        event_system = PostgresEventSystem()
        
        # Publish some events
        event_system.publish("test.event1", {"value": 1})
        event_system.publish("test.event2", {"value": 2})
        event_system.publish("test.event3", {"value": 3})
        
        # Get recent events
        events = event_system.get_recent_events(limit=2)
        
        assert len(events) <= 2
        if events:  # May include events from other tests
            assert "id" in events[0]
            assert "type" in events[0]
            assert "data" in events[0]
            assert "timestamp" in events[0]
    
    def test_get_recent_events_by_type(self):
        """Test filtering events by type."""
        event_system = PostgresEventSystem()
        
        # Publish different types
        event_system.publish("asset.created", {"path": "/test1"})
        event_system.publish("workflow.started", {"id": "123"})
        event_system.publish("asset.processed", {"path": "/test2"})
        
        # Get only asset events
        asset_events = event_system.get_recent_events(event_type="asset.created")
        
        # All returned events should be asset.created
        for event in asset_events:
            event_data = event if isinstance(event, dict) else json.loads(event)
            assert event_data["type"] == "asset.created"
    
    def test_subscribe_unsubscribe(self):
        """Test subscription management."""
        event_system = PostgresEventSystem()
        
        handler1 = MagicMock()
        handler2 = MagicMock()
        
        # Subscribe
        event_system.subscribe("test.event", handler1)
        event_system.subscribe("test.event", handler2)
        event_system.subscribe("other.event", handler1)
        
        assert len(event_system._listeners["test.event"]) == 2
        assert len(event_system._listeners["other.event"]) == 1
        
        # Unsubscribe
        event_system.unsubscribe("test.event", handler1)
        
        assert len(event_system._listeners["test.event"]) == 1
        assert handler2 in event_system._listeners["test.event"]
    
    def test_pattern_matching(self):
        """Test event pattern matching."""
        event_system = PostgresEventSystem()
        
        # Test exact match
        assert event_system._matches_pattern("asset.created", "asset.created")
        assert not event_system._matches_pattern("asset.created", "asset.processed")
        
        # Test wildcard patterns
        assert event_system._matches_pattern("asset.created", "asset.*")
        assert event_system._matches_pattern("asset.processed", "asset.*")
        assert not event_system._matches_pattern("workflow.started", "asset.*")
        
        # Test global wildcard
        assert event_system._matches_pattern("anything.goes", "*")
        assert event_system._matches_pattern("asset.created", "*")
    
    @pytest.mark.asyncio
    async def test_async_publish(self):
        """Test asynchronous event publishing."""
        event_system = PostgresEventSystem()
        
        # Publish async
        event_id = await event_system.publish_async("test.async", {"async": True})
        
        assert event_id is not None
        assert len(event_id) == 36
        
        # Clean up connection
        if event_system._connection:
            await event_system._connection.close()
    
    def test_global_convenience_functions(self):
        """Test global convenience functions."""
        # Test publish
        event_id = publish_event("test.global", {"global": True})
        assert event_id is not None
        
        # Test subscribe
        handler = MagicMock()
        subscribe_to_events("test.global", handler)
        
        # Verify subscription
        event_system = get_event_system()
        assert handler in event_system._listeners.get("test.global", [])