#!/usr/bin/env python3
"""Demonstration of the AliceMultiverse event system.

This example shows how events flow through the system during
media organization, enabling monitoring and future service extraction.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from alicemultiverse.events import (
    AssetDiscoveredEvent,
    AssetOrganizedEvent,
    Event,
    EventSubscriber,
    QualityAssessedEvent,
    get_event_bus,
)
from alicemultiverse.events.middleware import EventLogger, EventMetrics


class DemoSubscriber(EventSubscriber):
    """Example subscriber that reacts to specific events."""

    def __init__(self):
        self.discovered_count = 0
        self.organized_count = 0
        self.quality_count = 0

    @property
    def event_types(self):
        """Subscribe to asset-related events."""
        return ["asset.discovered", "asset.organized", "quality.assessed"]

    async def handle_event(self, event: Event):
        """Handle events with custom logic."""
        if event.event_type == "asset.discovered":
            self.discovered_count += 1
            print(f"📸 Discovered: {Path(event.file_path).name} ({event.media_type})")

        elif event.event_type == "asset.organized":
            self.organized_count += 1
            dest = Path(event.destination_path)
            print(f"📁 Organized: {dest.name} → {event.quality_folder or 'no-quality'}")

        elif event.event_type == "quality.assessed":
            self.quality_count += 1
            stars = "⭐" * event.star_rating
            print(f"⭐ Quality: {stars} (BRISQUE: {event.brisque_score:.1f})")


async def simulate_organization():
    """Simulate media organization with events."""
    print("Simulating media organization with events...\n")

    # Simulate discovering an asset
    discovery = AssetDiscoveredEvent(
        source="DemoOrganizer",
        file_path="/inbox/my-project/image_flux_001.png",
        content_hash="abc123",
        file_size=1024000,
        media_type="image",
        project_name="my-project",
        source_type="flux",
        inbox_path="/inbox",
    )
    await publish_event(discovery)
    await asyncio.sleep(0.5)

    # Simulate quality assessment
    quality = QualityAssessedEvent(
        source="DemoOrganizer",
        content_hash="abc123",
        file_path="/inbox/my-project/image_flux_001.png",
        brisque_score=23.5,
        star_rating=5,
        combined_score=0.85,
        pipeline_mode="basic",
    )
    await publish_event(quality)
    await asyncio.sleep(0.5)

    # Simulate organizing the asset
    organized = AssetOrganizedEvent(
        source="DemoOrganizer",
        content_hash="abc123",
        source_path="/inbox/my-project/image_flux_001.png",
        destination_path="/organized/2024-01-15/my-project/flux/5-star/my-project-00001.png",
        project_name="my-project",
        source_type="flux",
        date_folder="2024-01-15",
        quality_folder="5-star",
        operation="copy",
        sequence_number=1,
    )
    await publish_event(organized)


async def main():
    """Run the event demonstration."""
    print("AliceMultiverse Event System Demo")
    print("=" * 50)

    # Get event bus and add middleware
    bus = get_event_bus()
    bus.add_middleware(EventLogger())

    # Add metrics collection
    metrics = EventMetrics()
    bus.add_middleware(metrics)

    # Create and subscribe demo subscriber
    subscriber = DemoSubscriber()
    bus.subscribe(subscriber)

    # Run simulation
    await simulate_organization()

    # Show statistics
    print("\n" + "=" * 50)
    print("Event Statistics:")
    print(f"  Assets discovered: {subscriber.discovered_count}")
    print(f"  Quality assessed: {subscriber.quality_count}")
    print(f"  Assets organized: {subscriber.organized_count}")

    stats = metrics.get_stats()
    print("\nMetrics:")
    print(f"  Total events: {stats['total_events']}")
    print(f"  Event types: {', '.join(stats['event_types'])}")


# Import publish_event after defining everything else
from alicemultiverse.events import publish_event

if __name__ == "__main__":
    asyncio.run(main())
