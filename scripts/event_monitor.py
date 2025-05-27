#!/usr/bin/env python3
"""Simple event monitor to demonstrate the event system.

This script subscribes to all events and displays them in real-time,
useful for debugging and understanding system behavior.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alicemultiverse.events import Event, EventSubscriber, get_event_bus
from alicemultiverse.events.middleware import EventLogger, EventMetrics, EventPersistence


class EventMonitor(EventSubscriber):
    """Simple monitor that prints all events."""

    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.event_count = 0

    @property
    def event_types(self):
        """Subscribe to all events."""
        return ["*"]  # Wildcard subscription

    async def handle_event(self, event: Event):
        """Display the event."""
        self.event_count += 1

        # Format timestamp
        timestamp = event.timestamp.strftime("%H:%M:%S.%f")[:-3]

        # Color coding by event type
        color_map = {
            "asset.discovered": "\033[94m",  # Blue
            "asset.processed": "\033[92m",  # Green
            "asset.organized": "\033[93m",  # Yellow
            "quality.assessed": "\033[95m",  # Magenta
            "workflow.": "\033[96m",  # Cyan
            "creative.": "\033[91m",  # Red
        }

        color = "\033[0m"  # Default
        for prefix, code in color_map.items():
            if event.event_type.startswith(prefix):
                color = code
                break

        # Print event summary
        print(f"{color}[{timestamp}] {event.event_type} #{self.event_count}\033[0m")
        print(f"  Source: {event.source}")
        print(f"  Event ID: {event.event_id}")

        if self.verbose:
            # Print full event data
            event_dict = event.to_dict()
            # Remove common fields for cleaner output
            for field in ["event_id", "timestamp", "source", "version", "event_type"]:
                event_dict.pop(field, None)

            if event_dict:
                print("  Data:")
                for key, value in event_dict.items():
                    if isinstance(value, dict):
                        print(f"    {key}:")
                        for k, v in value.items():
                            print(f"      {k}: {v}")
                    elif isinstance(value, list) and len(value) > 3:
                        print(f"    {key}: [{len(value)} items]")
                    else:
                        print(f"    {key}: {value}")

        print()  # Empty line between events


async def main():
    """Run the event monitor."""
    print("AliceMultiverse Event Monitor")
    print("=" * 50)
    print("Monitoring all events. Press Ctrl+C to stop.")
    print()

    # Parse arguments
    verbose = "--verbose" in sys.argv or "-v" in sys.argv
    persist = "--persist" in sys.argv or "-p" in sys.argv
    metrics = "--metrics" in sys.argv or "-m" in sys.argv

    # Get event bus
    bus = get_event_bus()

    # Add middleware
    if persist:
        storage_dir = Path.home() / ".alicemultiverse" / "event_logs"
        bus.add_middleware(EventPersistence(storage_dir))
        print(f"Event persistence enabled: {storage_dir}")

    if metrics:
        event_metrics = EventMetrics()
        bus.add_middleware(event_metrics)
        print("Event metrics collection enabled")

    # Always add logger in debug mode
    bus.add_middleware(EventLogger())

    # Create and subscribe monitor
    monitor = EventMonitor(verbose=verbose)
    bus.subscribe(monitor)

    # Keep running
    try:
        while True:
            await asyncio.sleep(1)

            # Print metrics periodically if enabled
            if metrics and monitor.event_count > 0 and monitor.event_count % 10 == 0:
                stats = event_metrics.get_stats()
                print("\n--- Event Metrics ---")
                print(f"Total events: {stats['total_events']}")
                print(f"Events/second: {stats['events_per_second']:.2f}")
                print(f"Event types: {', '.join(stats['event_types'])}")
                print("-------------------\n")

    except KeyboardInterrupt:
        print("\n\nStopping event monitor...")

        if metrics and monitor.event_count > 0:
            stats = event_metrics.get_stats()
            print("\n--- Final Statistics ---")
            print(f"Total events: {stats['total_events']}")
            print(f"Runtime: {stats['runtime_seconds']:.1f} seconds")
            print(f"Events/second: {stats['events_per_second']:.2f}")
            print("\nEvent counts by type:")
            for event_type, count in sorted(stats["event_counts"].items()):
                print(f"  {event_type}: {count}")
            print("----------------------")


if __name__ == "__main__":
    # Handle command line help
    if "--help" in sys.argv or "-h" in sys.argv:
        print("Usage: event_monitor.py [options]")
        print()
        print("Options:")
        print("  -v, --verbose    Show full event data")
        print("  -p, --persist    Save events to disk")
        print("  -m, --metrics    Collect and display metrics")
        print("  -h, --help       Show this help message")
        sys.exit(0)

    asyncio.run(main())
