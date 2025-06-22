#!/usr/bin/env python3
"""Quick start example for using the restored AliceMultiverse system."""

import asyncio
from pathlib import Path

from alicemultiverse.interface import AliceInterface
from alicemultiverse.interface.models import (
    OrganizeRequest,
    SearchRequest,
    TagUpdateRequest,
)


async def main():
    """Demonstrate basic AliceMultiverse functionality."""
    
    # Initialize Alice
    alice = AliceInterface()
    print("✅ Alice initialized successfully!")
    
    # Example 1: Search for cyberpunk images
    print("\n🔍 Searching for cyberpunk images...")
    search = SearchRequest(
        query="cyberpunk",
        media_types=["image"],
        limit=10
    )
    results = await alice.search_assets(search)
    print(f"Found {len(results.assets)} cyberpunk images")
    
    # Example 2: Organize media with understanding
    print("\n📁 Organizing media files...")
    organize = OrganizeRequest(
        inbox_path="~/Downloads/ai-images",
        dry_run=True,  # Preview only
        understanding_enabled=True  # Enable AI analysis
    )
    stats = await alice.organize_media(organize)
    print(f"Would organize {stats.get('total_files', 0)} files")
    
    # Example 3: Update tags on an asset
    if results.assets:
        print("\n🏷️  Updating tags on first result...")
        first_asset = results.assets[0]
        tag_update = TagUpdateRequest(
            content_hash=first_asset.content_hash,
            add_tags=["favorite", "portfolio"],
            remove_tags=["draft"]
        )
        success = await alice.update_tags(tag_update)
        print(f"Tag update: {'✅ Success' if success else '❌ Failed'}")
    
    # Example 4: Check system capabilities
    print("\n🚀 System Capabilities:")
    print("- AI-powered media understanding")
    print("- Semantic search across collections")
    print("- Automated organization")
    print("- Multi-provider support (OpenAI, Anthropic, Google)")
    print("- Event-driven architecture")
    print("- Performance tracking")
    
    print("\n✨ AliceMultiverse is ready for creative workflows!")


if __name__ == "__main__":
    asyncio.run(main())