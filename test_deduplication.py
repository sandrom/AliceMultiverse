#!/usr/bin/env python3
"""Test the advanced deduplication functionality."""

import asyncio
import logging
from pathlib import Path

from alicemultiverse.deduplication import DuplicateFinder, SimilarityIndex

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_duplicate_finder():
    """Test duplicate finding functionality."""
    # Test directory - update this to your test images
    test_dir = Path.home() / "Documents" / "test_images"

    if not test_dir.exists():
        logger.warning(f"Test directory not found: {test_dir}")
        logger.info("Creating test directory with sample duplicates...")
        test_dir.mkdir(parents=True, exist_ok=True)

        # In production, you'd copy actual test images here
        # For now, just show the functionality

    # Create duplicate finder
    finder = DuplicateFinder(similarity_threshold=0.85)

    logger.info(f"Scanning {test_dir} for duplicates...")
    exact_count, similar_count = finder.scan_directory(test_dir)

    logger.info(f"Found {exact_count} exact duplicates and {similar_count} similar images")

    # Get detailed report
    report = finder.get_duplicate_report()

    # Print exact duplicates
    if report['exact_duplicates']['groups']:
        logger.info("\nExact Duplicates:")
        for group in report['exact_duplicates']['groups']:
            logger.info(f"  Master: {group['master']}")
            for dup in group['duplicates']:
                logger.info(f"    - {dup}")
            logger.info(f"    Savings: {group['potential_savings'] / 1_000_000:.2f} MB")

    # Print similar images
    if report['similar_images']['groups']:
        logger.info("\nSimilar Images:")
        for group in report['similar_images']['groups']:
            logger.info(f"  Master: {group['master']}")
            for dup, score in group['similarity_scores'].items():
                logger.info(f"    - {dup} (similarity: {score:.2f})")
            logger.info(f"    Savings: {group['potential_savings'] / 1_000_000:.2f} MB")

    logger.info(f"\nTotal potential savings: {report['potential_savings'] / 1_000_000:.2f} MB")

    # Test dry run removal
    logger.info("\nTesting duplicate removal (dry run)...")
    stats = finder.remove_duplicates(dry_run=True, remove_similar=False)
    logger.info(f"Would remove {stats['exact_removed']} exact duplicates")
    logger.info(f"Would free {stats['space_freed'] / 1_000_000:.2f} MB")


async def test_similarity_index():
    """Test similarity index functionality."""
    # Test directories
    test_dirs = [
        Path.home() / "Pictures",
        Path.home() / "Documents" / "AliceMultiverse" / "organized"
    ]

    # Filter existing directories
    existing_dirs = [d for d in test_dirs if d.exists()]

    if not existing_dirs:
        logger.warning("No test directories found")
        return

    # Create similarity index
    index = SimilarityIndex(index_type="IVF")

    # Collect images
    image_paths = []
    for directory in existing_dirs:
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            image_paths.extend(directory.rglob(f"*{ext}"))
            image_paths.extend(directory.rglob(f"*{ext.upper()}"))

    if not image_paths:
        logger.warning("No images found to index")
        return

    logger.info(f"Building similarity index for {len(image_paths)} images...")

    # Build index
    cache_dir = Path.home() / ".alice" / "cache" / "similarity"
    indexed_count = index.build_index(image_paths[:100], cache_dir=cache_dir)  # Limit for testing

    logger.info(f"Indexed {indexed_count} images")

    # Save index
    index_path = Path.home() / ".alice" / "test_similarity_index"
    index.save_index(index_path)
    logger.info(f"Saved index to {index_path}")

    # Test search
    if image_paths:
        query_image = image_paths[0]
        logger.info(f"\nSearching for images similar to: {query_image.name}")

        results = index.search(query_image, k=5, include_self=False)

        for i, result in enumerate(results):
            logger.info(f"  {i+1}. {result.path.name} (similarity: {result.similarity:.3f})")

    # Test clustering
    logger.info("\nFinding image clusters...")
    clusters = index.find_clusters(min_cluster_size=2, max_distance=0.3)

    logger.info(f"Found {len(clusters)} clusters")
    for i, cluster in enumerate(clusters[:3]):  # Show first 3 clusters
        logger.info(f"  Cluster {i+1}: {len(cluster)} images")
        for path in cluster[:3]:  # Show first 3 images
            logger.info(f"    - {Path(path).name}")


async def main():
    """Run all tests."""
    logger.info("Testing Advanced Deduplication System")
    logger.info("=" * 50)

    # Test duplicate finder
    logger.info("\n1. Testing Duplicate Finder")
    logger.info("-" * 30)
    await test_duplicate_finder()

    # Test similarity index
    logger.info("\n2. Testing Similarity Index")
    logger.info("-" * 30)
    await test_similarity_index()

    logger.info("\nAll tests completed!")


if __name__ == "__main__":
    asyncio.run(main())
