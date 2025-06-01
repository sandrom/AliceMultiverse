#!/usr/bin/env python3
"""
Redis Streams Event Migration Example

This example shows how to migrate from PostgreSQL events to Redis Streams
and demonstrates the improved features and performance.
"""

import asyncio
import json
import time
from datetime import datetime
from typing import Dict, Any

# Old PostgreSQL event system (for comparison)
# from alicemultiverse.events.postgres_events import PostgresEventSystem

# New Redis Streams event system
from alicemultiverse.events.redis_streams import (
    RedisStreamsEventSystem,
    publish_event,
    subscribe_to_events
)


class EventProcessor:
    """Example event processor showing old vs new patterns."""
    
    def __init__(self):
        self.events_processed = 0
        self.processing_times = []
    
    async def handle_asset_event(self, event: Dict[str, Any]) -> None:
        """Handle asset-related events."""
        start_time = time.time()
        
        event_type = event.get("type", "unknown")
        event_data = event.get("data", {})
        
        print(f"📸 Asset Event: {event_type}")
        print(f"   ID: {event.get('id')}")
        print(f"   Data: {json.dumps(event_data, indent=2)}")
        
        # Simulate processing
        await asyncio.sleep(0.1)
        
        self.events_processed += 1
        self.processing_times.append(time.time() - start_time)
    
    async def handle_workflow_event(self, event: Dict[str, Any]) -> None:
        """Handle workflow events."""
        event_type = event.get("type", "unknown")
        workflow_id = event.get("data", {}).get("workflow_id", "unknown")
        
        print(f"🔄 Workflow Event: {event_type}")
        print(f"   Workflow ID: {workflow_id}")
        print(f"   Status: {event.get('data', {}).get('status', 'unknown')}")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get processing statistics."""
        if not self.processing_times:
            return {"events_processed": 0}
            
        return {
            "events_processed": self.events_processed,
            "avg_processing_time": sum(self.processing_times) / len(self.processing_times),
            "min_processing_time": min(self.processing_times),
            "max_processing_time": max(self.processing_times)
        }


async def demonstrate_basic_pubsub():
    """Demonstrate basic publish/subscribe with Redis Streams."""
    print("🚀 Basic Publish/Subscribe Demo\n")
    
    # Create event system
    event_system = RedisStreamsEventSystem()
    
    # Create processor
    processor = EventProcessor()
    
    # Subscribe to events
    await event_system.subscribe("asset.processed", processor.handle_asset_event)
    await event_system.subscribe("asset.*", processor.handle_asset_event)  # Wildcard
    await event_system.subscribe("workflow.*", processor.handle_workflow_event)
    
    # Start listening
    await event_system.start_listening()
    
    print("✅ Subscribed to events, publishing test events...\n")
    
    # Publish some events
    events = [
        ("asset.processed", {
            "file_path": "/images/test1.jpg",
            "size": 1024000,
            "duration": 2.5
        }),
        ("asset.created", {
            "file_path": "/images/test2.png",
            "provider": "stablediffusion",
            "cost": 0.02
        }),
        ("workflow.started", {
            "workflow_id": "wf-123",
            "status": "running",
            "steps": 5
        }),
        ("asset.analyzed", {
            "file_path": "/images/test1.jpg",
            "tags": ["portrait", "woman", "cyberpunk"],
            "understanding": {
                "provider": "openai",
                "description": "A cyberpunk portrait"
            }
        }),
        ("workflow.completed", {
            "workflow_id": "wf-123",
            "status": "success",
            "duration": 10.5,
            "outputs": ["/images/final.jpg"]
        })
    ]
    
    for event_type, data in events:
        await publish_event(event_type, data)
        await asyncio.sleep(0.2)  # Small delay to see events process
    
    # Give time for processing
    await asyncio.sleep(1)
    
    # Show stats
    print(f"\n📊 Processing Stats: {processor.get_stats()}")
    
    # Stop listening
    await event_system.stop_listening()


async def demonstrate_consumer_groups():
    """Demonstrate consumer groups for scaling."""
    print("\n\n🏭 Consumer Groups Demo (Scaling)\n")
    
    # Create multiple consumers (simulating multiple workers)
    consumers = []
    processors = []
    
    for i in range(3):
        system = RedisStreamsEventSystem()
        processor = EventProcessor()
        
        # All consumers subscribe to same events
        await system.subscribe("asset.processed", processor.handle_asset_event)
        await system.start_listening()
        
        consumers.append(system)
        processors.append(processor)
        
    print(f"✅ Started {len(consumers)} consumers\n")
    
    # Publish many events
    print("Publishing 10 events...")
    for i in range(10):
        await publish_event("asset.processed", {
            "file_path": f"/images/test{i}.jpg",
            "index": i
        })
    
    # Wait for processing
    await asyncio.sleep(2)
    
    # Show how work was distributed
    print("\n📊 Work Distribution:")
    for i, processor in enumerate(processors):
        stats = processor.get_stats()
        print(f"   Consumer {i}: {stats['events_processed']} events")
    
    # Cleanup
    for system in consumers:
        await system.stop_listening()


async def demonstrate_reliability():
    """Demonstrate reliability features of Redis Streams."""
    print("\n\n🛡️  Reliability Features Demo\n")
    
    event_system = RedisStreamsEventSystem()
    
    # Simulate a handler that fails sometimes
    fail_count = 0
    
    async def unreliable_handler(event: Dict[str, Any]) -> None:
        nonlocal fail_count
        fail_count += 1
        
        if fail_count % 3 == 0:
            print(f"❌ Handler failed for event: {event.get('id')}")
            raise Exception("Simulated failure")
        else:
            print(f"✅ Successfully processed: {event.get('id')}")
    
    await event_system.subscribe("reliability.test", unreliable_handler)
    await event_system.start_listening()
    
    # Publish events
    for i in range(5):
        await publish_event("reliability.test", {"index": i})
    
    await asyncio.sleep(1)
    
    # Check for pending messages
    pending = await event_system.get_pending_messages("reliability.test")
    print(f"\n📋 Pending messages: {len(pending)}")
    for msg in pending:
        print(f"   - {msg['message_id']}: idle for {msg['idle_time_ms']}ms")
    
    # Claim and reprocess abandoned messages
    if pending:
        print("\n♻️  Claiming abandoned messages...")
        claimed = await event_system.claim_abandoned_messages("reliability.test", idle_time_ms=100)
        print(f"   Claimed {claimed} messages for reprocessing")
    
    await event_system.stop_listening()


async def demonstrate_event_history():
    """Demonstrate event history and querying."""
    print("\n\n📚 Event History Demo\n")
    
    event_system = RedisStreamsEventSystem()
    
    # Publish events with timestamps
    events_to_publish = [
        ("user.login", {"user_id": "123", "ip": "192.168.1.1"}),
        ("asset.created", {"file": "test1.jpg", "size": 1024}),
        ("user.action", {"user_id": "123", "action": "upload"}),
        ("asset.processed", {"file": "test1.jpg", "duration": 2.5}),
        ("user.logout", {"user_id": "123"}),
    ]
    
    print("Publishing events with timestamps...")
    for event_type, data in events_to_publish:
        await publish_event(event_type, data)
        await asyncio.sleep(0.1)
    
    # Query recent events
    print("\n🔍 Recent events (all types):")
    recent = await event_system.get_recent_events(limit=10)
    for event in recent:
        print(f"   - {event.get('type')}: {event.get('timestamp')}")
    
    # Query by event type
    print("\n🔍 User events only:")
    user_events = await event_system.get_recent_events(limit=10, event_type="user.login")
    for event in user_events:
        data = event.get('data', {})
        print(f"   - User {data.get('user_id')} from {data.get('ip')}")
    
    # Show stream info
    print("\n📊 Stream Statistics:")
    print(f"   - Total events in demo: {len(recent)}")
    print(f"   - Event types: {set(e.get('type') for e in recent)}")


async def compare_with_postgresql():
    """Compare Redis Streams advantages over PostgreSQL NOTIFY/LISTEN."""
    print("\n\n🔄 PostgreSQL vs Redis Streams Comparison\n")
    
    comparison = """
    PostgreSQL NOTIFY/LISTEN:
    ❌ No persistence - missed events are lost
    ❌ No consumer groups - hard to scale
    ❌ No built-in retry mechanism
    ❌ Limited to 8000 byte payloads
    ❌ No event history/replay
    
    Redis Streams:
    ✅ Persistent event storage
    ✅ Consumer groups for horizontal scaling
    ✅ Automatic retry with pending messages
    ✅ No payload size limits
    ✅ Event history and time-based queries
    ✅ Built-in trimming to control memory
    ✅ Better performance for high throughput
    """
    
    print(comparison)
    
    # Performance comparison
    print("\n⚡ Performance Test:")
    
    event_system = RedisStreamsEventSystem()
    
    # Measure publish performance
    start_time = time.time()
    publish_count = 1000
    
    print(f"Publishing {publish_count} events...")
    for i in range(publish_count):
        await publish_event("perf.test", {"index": i})
    
    elapsed = time.time() - start_time
    rate = publish_count / elapsed
    
    print(f"✅ Published {publish_count} events in {elapsed:.2f}s")
    print(f"   Rate: {rate:.0f} events/second")
    print(f"   Avg latency: {(elapsed/publish_count)*1000:.2f}ms per event")


async def main():
    """Run all demonstrations."""
    print("🎯 Redis Streams Event System Demo\n")
    print("This demo shows the migration from PostgreSQL to Redis Streams")
    print("and highlights the improvements in reliability and performance.\n")
    
    # Run demos
    await demonstrate_basic_pubsub()
    await demonstrate_consumer_groups()
    await demonstrate_reliability()
    await demonstrate_event_history()
    await compare_with_postgresql()
    
    print("\n✅ Demo complete!")
    print("\n💡 Key Benefits of Redis Streams:")
    print("  - Persistent event storage (survives restarts)")
    print("  - Consumer groups for easy scaling")
    print("  - Automatic retry and failure handling")
    print("  - Rich querying of event history")
    print("  - Better performance for event-heavy workloads")


if __name__ == "__main__":
    # Note: Requires Redis server running
    try:
        asyncio.run(main())
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\n💡 Make sure Redis is running:")
        print("   docker run -d -p 6379:6379 redis:alpine")
        print("   or: brew services start redis")