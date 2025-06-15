#!/usr/bin/env python3
"""
Demonstration of similarity search using perceptual hashing.

This example shows how to find similar images in your organized collection
using the perceptual hashing feature.
"""

import sys
from pathlib import Path

from alicemultiverse.assets.perceptual_hashing import calculate_perceptual_hash
from alicemultiverse.storage.unified_duckdb import DuckDBSearch


def demo_similarity_search(target_image_path: str, threshold: int = 10):
    """
    Find images similar to a target image using perceptual hashing.
    
    Args:
        target_image_path: Path to the image to find similar images for
        threshold: Maximum hamming distance for similarity (default: 10)
    """
    target_path = Path(target_image_path)

    if not target_path.exists():
        print(f"Error: Image not found: {target_path}")
        return

    # Initialize search database
    db = DuckDBSearch("data/search.duckdb")

    # Calculate perceptual hash for target image
    print(f"Calculating perceptual hash for: {target_path.name}")
    target_hash = calculate_perceptual_hash(target_path)

    if not target_hash:
        print("Error: Could not calculate perceptual hash")
        return

    print(f"Target image hash: {target_hash}")
    print(f"\nSearching for similar images (threshold: {threshold})...\n")

    # Find similar images
    similar_images = db.find_similar_by_phash(target_hash, threshold=threshold)

    if not similar_images:
        print("No similar images found in the database.")
        print("\nTip: Make sure you've organized some images first with:")
        print("  alice -i ~/Downloads/AI-Images -o ~/Pictures/AI-Organized")
        return

    print(f"Found {len(similar_images)} similar images:\n")

    for content_hash, file_path, distance in similar_images:
        print(f"Distance: {distance:2d} | {Path(file_path).name}")
        print(f"  Path: {file_path}")

        # Get more details about the image
        results, _ = db.search({"content_hash": content_hash})
        if results:
            asset = results[0]
            if asset.get("tags"):
                # Show some tags
                all_tags = []
                for category, tag_list in asset["tags"].items():
                    all_tags.extend(tag_list[:3])  # First 3 tags per category
                print(f"  Tags: {', '.join(all_tags[:10])}")
            if asset.get("ai_source"):
                print(f"  Source: {asset['ai_source']}")
        print()

    # Show statistics about perceptual hashes
    print("\n" + "="*50)
    print("Database Statistics:")
    stats = db.get_statistics()
    print(f"  Total assets: {stats.get('total_assets', 0)}")
    print(f"  Unique tags: {stats.get('unique_tags', 0)}")

    # Check how many have perceptual hashes
    conn = db.conn
    hash_count = conn.execute("SELECT COUNT(*) FROM perceptual_hashes WHERE phash IS NOT NULL").fetchone()[0]
    print(f"  Images with perceptual hashes: {hash_count}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python similarity_search_demo.py <image_path> [threshold]")
        print("\nExample:")
        print("  python similarity_search_demo.py ~/Pictures/example.png")
        print("  python similarity_search_demo.py ~/Pictures/example.png 15")
        print("\nThreshold: Maximum hamming distance (0-64, default: 10)")
        print("  0-5:   Nearly identical images")
        print("  6-10:  Very similar images")
        print("  11-20: Similar style/composition")
        print("  21+:   Loosely related")
        sys.exit(1)

    image_path = sys.argv[1]
    threshold = int(sys.argv[2]) if len(sys.argv) > 2 else 10

    demo_similarity_search(image_path, threshold)


if __name__ == "__main__":
    main()
