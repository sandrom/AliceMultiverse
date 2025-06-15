#!/usr/bin/env python3
"""
DuckDB Integration Example - Demonstrating File-First Architecture

This example shows how DuckDB serves as a fast search cache while
files remain the source of truth with embedded metadata.
"""

import asyncio
import tempfile
from datetime import datetime
from pathlib import Path

import piexif
from PIL import Image

from alicemultiverse.metadata.embedder import MetadataEmbedder
from alicemultiverse.storage import DuckDBSearchCache, FileScanner


async def create_sample_image_with_metadata(output_path: Path, metadata: dict) -> Path:
    """Create a sample image with embedded Alice metadata."""
    # Create a simple test image
    img = Image.new('RGB', (512, 512), color='blue')

    # Prepare EXIF data
    exif_dict = {
        "0th": {},
        "Exif": {},
        "1st": {},
        "thumbnail": None
    }

    # Add ImageDescription with some basic info
    exif_dict["0th"][piexif.ImageIFD.ImageDescription] = "AI-generated test image"

    # Convert to bytes
    exif_bytes = piexif.dump(exif_dict)

    # Save with EXIF
    img.save(str(output_path), "JPEG", exif=exif_bytes)

    # Now add XMP metadata (Alice-specific)
    # In a real implementation, we'd use python-xmp-toolkit
    # For this demo, we'll simulate by using the MetadataEmbedder
    embedder = MetadataEmbedder()

    # Embed Alice metadata
    success = embedder.embed_metadata(output_path, metadata)
    if success:
        print(f"✅ Created image with embedded metadata: {output_path}")
    else:
        print(f"⚠️  Created image but metadata embedding failed: {output_path}")

    return output_path


async def main():
    """Demonstrate DuckDB integration with file-first architecture."""

    print("🚀 DuckDB Integration Example\n")
    print("This demonstrates how DuckDB acts as a search cache")
    print("while files remain the source of truth.\n")

    # Create temporary directory for demo
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # 1. Create sample images with embedded metadata
        print("1️⃣  Creating sample images with embedded metadata...")

        images = []

        # Cyberpunk portrait
        metadata1 = {
            "content_hash": "abc123",
            "media_type": "image",
            "tags": {
                "style": ["cyberpunk", "neon"],
                "mood": ["dramatic", "futuristic"],
                "subject": ["woman", "portrait"],
                "color": ["blue", "purple", "pink"],
                "technical": ["high-contrast", "rim-lighting"],
                "setting": ["night-city", "urban"]  # Custom tag
            },
            "understanding": {
                "description": "A cyberpunk portrait of a woman with neon lighting",
                "generated_prompt": "cyberpunk woman portrait, neon lights, dramatic lighting",
                "negative_prompt": "blurry, low quality",
                "provider": "openai",
                "model": "gpt-4-vision",
                "cost": 0.002,
                "analyzed_at": datetime.now().isoformat()
            },
            "generation": {
                "provider": "midjourney",
                "model": "v6",
                "prompt": "beautiful cyberpunk woman, neon city lights --ar 1:1 --v 6",
                "parameters": {"aspect_ratio": "1:1", "version": 6},
                "cost": 0.05,
                "generated_at": datetime.now().isoformat()
            }
        }

        img1 = await create_sample_image_with_metadata(
            temp_path / "cyberpunk_portrait.jpg",
            metadata1
        )
        images.append(img1)

        # Fantasy landscape
        metadata2 = {
            "content_hash": "def456",
            "media_type": "image",
            "tags": {
                "style": ["fantasy", "painterly"],
                "mood": ["serene", "mystical"],
                "subject": ["landscape", "mountains"],
                "color": ["green", "blue", "gold"],
                "technical": ["soft-lighting", "atmospheric"],
                "time": ["sunrise", "golden-hour"]  # Custom tag
            },
            "understanding": {
                "description": "A fantasy landscape with mountains at sunrise",
                "generated_prompt": "fantasy landscape, mountains, sunrise, painterly style",
                "provider": "anthropic",
                "model": "claude-3-opus",
                "cost": 0.003,
                "analyzed_at": datetime.now().isoformat()
            },
            "generation": {
                "provider": "leonardo",
                "model": "leonardo-diffusion-xl",
                "prompt": "epic fantasy landscape with mountains, sunrise",
                "parameters": {"guidance_scale": 7.5, "steps": 50},
                "cost": 0.02,
                "generated_at": datetime.now().isoformat()
            }
        }

        img2 = await create_sample_image_with_metadata(
            temp_path / "fantasy_landscape.jpg",
            metadata2
        )
        images.append(img2)

        # Anime character
        metadata3 = {
            "content_hash": "ghi789",
            "media_type": "image",
            "tags": {
                "style": ["anime", "colorful"],
                "mood": ["cheerful", "energetic"],
                "subject": ["character", "girl"],
                "color": ["pink", "blue", "white"],
                "technical": ["cel-shaded", "clean-lines"],
                "franchise": ["original"]  # Custom tag
            },
            "understanding": {
                "description": "An anime-style character with colorful hair",
                "generated_prompt": "anime girl character, colorful hair, cheerful expression",
                "provider": "google",
                "model": "gemini-pro-vision",
                "cost": 0.001,
                "analyzed_at": datetime.now().isoformat()
            },
            "generation": {
                "provider": "stablediffusion",
                "model": "sdxl-anime",
                "prompt": "anime girl, colorful hair, school uniform, happy",
                "parameters": {"sampler": "DPM++", "cfg_scale": 8},
                "cost": 0.01,
                "generated_at": datetime.now().isoformat()
            }
        }

        img3 = await create_sample_image_with_metadata(
            temp_path / "anime_character.jpg",
            metadata3
        )
        images.append(img3)

        print(f"✅ Created {len(images)} sample images\n")

        # 2. Initialize DuckDB cache
        print("2️⃣  Initializing DuckDB search cache...")
        cache = DuckDBSearchCache()  # In-memory for demo
        scanner = FileScanner(cache)

        # 3. Scan directory to populate cache
        print("3️⃣  Scanning directory to populate cache from file metadata...")
        files_processed = await scanner.scan_directory(temp_path, show_progress=False)
        print(f"✅ Processed {files_processed} files\n")

        # 4. Demonstrate search capabilities
        print("4️⃣  Demonstrating search capabilities:\n")

        # Search by style
        print("🔍 Search by style=['cyberpunk']:")
        results = cache.search_by_tags({"style": ["cyberpunk"]})
        for r in results:
            print(f"  - {r['content_hash']}: {r['tags']}")

        # Search by multiple styles (OR)
        print("\n🔍 Search by style=['anime', 'fantasy'] (OR):")
        results = cache.search_by_tags({"style": ["anime", "fantasy"]})
        for r in results:
            print(f"  - {r['content_hash']}: {r['tags'].get('style')}")

        # Search by mood
        print("\n🔍 Search by mood=['dramatic']:")
        results = cache.search_by_tags({"mood": ["dramatic"]})
        for r in results:
            print(f"  - {r['content_hash']}: {r['understanding']['description']}")

        # Search by custom tags
        print("\n🔍 Search by custom tag setting=['night-city']:")
        results = cache.search_by_tags({"setting": ["night-city"]})
        for r in results:
            print(f"  - {r['content_hash']}: Found in {r['locations'][0]['path']}")

        # Text search
        print("\n🔍 Text search for 'landscape':")
        results = cache.search_by_text("landscape")
        for r in results:
            print(f"  - {r['content_hash']}: {r['understanding']['description']}")

        # 5. Show statistics
        print("\n5️⃣  Cache Statistics:")
        stats = cache.get_statistics()
        print(f"  - Total assets: {stats['total_assets']}")
        print(f"  - By media type: {stats['by_media_type']}")
        print(f"  - Assets with tags: {stats['assets_with_tags']}")
        print(f"  - Assets with AI understanding: {stats['assets_with_understanding']}")
        print(f"  - Storage locations: {stats['by_storage_type']}")

        # 6. Demonstrate file movement (content-addressed)
        print("\n6️⃣  Demonstrating content-addressed storage:")

        # Move a file to a new location
        new_location = temp_path / "moved" / "cyberpunk_renamed.jpg"
        new_location.parent.mkdir(exist_ok=True)
        img1.rename(new_location)

        # Re-scan to add new location
        print("  - Moved file to new location, re-scanning...")
        await scanner.scan_directory(temp_path / "moved", show_progress=False)

        # Show that both locations are tracked
        locations = cache.get_all_locations("abc123")
        print(f"  - Asset abc123 now exists in {len(locations)} locations:")
        for loc in locations:
            print(f"    • {loc['path']}")

        # 7. Demonstrate cache rebuild
        print("\n7️⃣  Demonstrating cache rebuild from files:")
        print("  - Clearing cache...")
        cache.rebuild_from_scratch()
        stats = cache.get_statistics()
        print(f"  - Assets after clear: {stats['total_assets']}")

        print("  - Rebuilding from files...")
        await scanner.rebuild_cache([(temp_path, "local")])
        stats = cache.get_statistics()
        print(f"  - Assets after rebuild: {stats['total_assets']}")

        # 8. Export to Parquet for analytics
        print("\n8️⃣  Exporting to Parquet for analytics:")
        export_dir = temp_path / "analytics"
        export_files = cache.export_to_parquet(export_dir)
        print("  - Exported tables:")
        for table, path in export_files.items():
            print(f"    • {table}: {path.name}")

        print("\n✅ Demo complete!")
        print("\n💡 Key Takeaways:")
        print("  - Files are the source of truth with embedded metadata")
        print("  - DuckDB provides fast search without being critical")
        print("  - Content-addressed storage tracks files across locations")
        print("  - Cache can be rebuilt anytime from files")
        print("  - No dependency on database for asset integrity")


if __name__ == "__main__":
    asyncio.run(main())
