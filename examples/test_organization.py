#!/usr/bin/env python3
"""Test the media organization capabilities."""

import asyncio
from pathlib import Path
from alicemultiverse.interface import AliceInterface
from alicemultiverse.interface.models import OrganizeRequest

async def test_organization():
    """Test organizing AI-generated media."""
    alice = AliceInterface()
    
    # Configure paths (update these to your actual directories)
    inbox = Path("~/Downloads/ai-images").expanduser()
    organized = Path("~/Pictures/AI-Organized").expanduser()
    
    print(f"🔍 Checking inbox: {inbox}")
    if not inbox.exists():
        print("❌ Inbox directory doesn't exist. Creating it...")
        inbox.mkdir(parents=True, exist_ok=True)
        print("📁 Please add some AI-generated images to:", inbox)
        return
    
    # Count files
    image_extensions = {'.png', '.jpg', '.jpeg', '.webp', '.heic'}
    images = [f for f in inbox.rglob('*') if f.suffix.lower() in image_extensions]
    print(f"📸 Found {len(images)} images to organize")
    
    if not images:
        print("❌ No images found. Add some AI-generated images to the inbox.")
        return
    
    # Dry run first
    print("\n🧪 Running dry run to preview organization...")
    request = OrganizeRequest(
        inbox_path=str(inbox),
        output_path=str(organized),
        dry_run=True,
        understanding_enabled=False  # Start without AI analysis
    )
    
    stats = await alice.organize_media(request)
    print(f"✅ Would organize {stats.get('processed', 0)} files")
    print(f"📊 By source: {stats.get('by_source', {})}")
    
    # Ask user to proceed
    response = input("\n🤔 Proceed with actual organization? (y/n): ")
    if response.lower() == 'y':
        request.dry_run = False
        stats = await alice.organize_media(request)
        print(f"\n✅ Successfully organized {stats.get('processed', 0)} files!")
        print(f"📁 Check your organized folder: {organized}")

if __name__ == "__main__":
    asyncio.run(test_organization())