#!/usr/bin/env python3
"""Simple event monitor that works with both Redis and file-based backends.

This script monitors events from the event system (either Redis Streams or file-based)
and displays them in real-time.
"""

import asyncio
import json
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alicemultiverse.events import get_event_system


class SimpleEventMonitor:
    """Monitor that displays events in real-time."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.event_count = 0
        self.start_time = time.time()
        
    async def handle_event(self, event: Dict[str, Any]) -> None:
        """Display an event."""
        self.event_count += 1
        
        # Extract event details
        event_id = event.get("id", "unknown")
        event_type = event.get("type", "unknown")
        timestamp = event.get("timestamp", datetime.now().isoformat())
        data = event.get("data", {})
        
        # Parse timestamp if string
        if isinstance(timestamp, str):
            try:
                dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
                timestamp = dt.strftime("%H:%M:%S")
            except:
                timestamp = timestamp[:19]  # Just date and time part
        
        # Color coding by event type
        color_map = {
            "asset.": "\033[94m",      # Blue for asset events
            "generation.": "\033[92m",  # Green for generation events
            "workflow.": "\033[96m",    # Cyan for workflow events
            "project.": "\033[93m",     # Yellow for project events
            "selection.": "\033[95m",   # Magenta for selection events
        }
        
        color = "\033[0m"  # Default
        for prefix, code in color_map.items():
            if event_type.startswith(prefix):
                color = code
                break
        
        # Print event header
        print(f"\n{color}[{timestamp}] {event_type} #{self.event_count}\033[0m")
        print(f"  ID: {event_id}")
        
        # Print event data
        if self.verbose and data:
            print("  Data:")
            # Pretty print the data
            if isinstance(data, dict):
                for key, value in data.items():
                    if isinstance(value, (dict, list)) and len(str(value)) > 80:
                        print(f"    {key}: <{type(value).__name__} with {len(value)} items>")
                    else:
                        print(f"    {key}: {value}")
            else:
                print(f"    {data}")
                
    async def show_stats(self) -> None:
        """Show monitoring statistics."""
        runtime = time.time() - self.start_time
        rate = self.event_count / runtime if runtime > 0 else 0
        
        print(f"\n📊 Stats: {self.event_count} events in {runtime:.1f}s ({rate:.1f} events/sec)")


async def monitor_live_events(verbose: bool = False):
    """Monitor events as they happen (Redis Streams only)."""
    event_system = get_event_system()
    monitor = SimpleEventMonitor(verbose)
    
    # Check if we're using Redis
    is_redis = hasattr(event_system, "start_listening")
    
    if is_redis:
        print("📡 Monitoring live events from Redis Streams...")
        print("Press Ctrl+C to stop.\n")
        
        # Subscribe to all events
        await event_system.subscribe("*", monitor.handle_event)
        
        # Start listening
        await event_system.start_listening()
        
        try:
            # Keep running until interrupted
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping monitor...")
            await monitor.show_stats()
            await event_system.stop_listening()
    else:
        print("📁 File-based event system detected.")
        print("Monitoring recent events from log files...")
        print("Press Ctrl+C to stop.\n")
        
        last_event_count = 0
        
        try:
            while True:
                # Get recent events
                events = await event_system.get_recent_events(limit=100)
                
                # Show only new events
                new_events = events[:len(events) - last_event_count]
                for event in reversed(new_events):
                    await monitor.handle_event(event)
                
                last_event_count = len(events)
                
                # Check for new events every second
                await asyncio.sleep(1)
                
        except KeyboardInterrupt:
            print("\n\n🛑 Stopping monitor...")
            await monitor.show_stats()


async def show_recent_events(limit: int = 20, verbose: bool = False):
    """Show recent events from the event system."""
    event_system = get_event_system()
    monitor = SimpleEventMonitor(verbose)
    
    print(f"📜 Showing last {limit} events...\n")
    
    # Get recent events
    events = await event_system.get_recent_events(limit=limit)
    
    if not events:
        print("No events found.")
        return
    
    # Display events
    for event in reversed(events):  # Show oldest first
        await monitor.handle_event(event)
    
    await monitor.show_stats()


async def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor AliceMultiverse events")
    parser.add_argument(
        "--recent", "-r",
        type=int,
        metavar="N",
        help="Show N most recent events instead of live monitoring"
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show full event data"
    )
    
    args = parser.parse_args()
    
    print("🔍 AliceMultiverse Event Monitor")
    print("=" * 50)
    
    try:
        if args.recent:
            await show_recent_events(args.recent, args.verbose)
        else:
            await monitor_live_events(args.verbose)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())