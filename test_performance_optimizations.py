#!/usr/bin/env python3
"""Test script to demonstrate DuckDB performance optimizations."""

import time
from pathlib import Path
from alicemultiverse.storage.unified_duckdb import UnifiedDuckDBStorage

def test_batch_insert_performance():
    """Test batch insert vs individual inserts."""
    print("\n=== Testing Batch Insert Performance ===")
    
    # Create test database
    db = UnifiedDuckDBStorage(Path("test_performance.duckdb"))
    
    # Test data
    test_assets = []
    for i in range(1000):
        test_assets.append((
            f"hash_{i}",
            Path(f"/test/file_{i}.png"),
            {
                "media_type": "image",
                "file_size": 1024 * (i + 1),
                "width": 1920,
                "height": 1080,
                "ai_source": ["midjourney", "stable-diffusion", "dalle"][i % 3],
                "tags": {
                    "style": ["cyberpunk", "abstract", "realistic"][i % 3],
                    "mood": ["dark", "bright", "neutral"][i % 3],
                    "subject": ["portrait", "landscape", "object"][i % 3]
                }
            },
            "local"
        ))
    
    # Test individual inserts
    start_time = time.time()
    for asset in test_assets[:100]:  # Just test first 100
        db.upsert_asset(*asset)
    individual_time = time.time() - start_time
    print(f"Individual inserts (100 assets): {individual_time:.2f} seconds")
    
    # Test batch insert
    start_time = time.time()
    db.upsert_assets_batch(test_assets[100:200])  # Next 100
    batch_time = time.time() - start_time
    print(f"Batch insert (100 assets): {batch_time:.2f} seconds")
    print(f"Speed improvement: {individual_time / batch_time:.1f}x faster")
    
    return db

def test_search_performance(db):
    """Test search performance with caching."""
    print("\n=== Testing Search Performance ===")
    
    # Complex search query
    filters = {
        "media_type": "image",
        "ai_source": ["midjourney", "stable-diffusion"],
        "tags": ["cyberpunk", "abstract"]
    }
    
    # First search (no cache)
    start_time = time.time()
    results1, count1 = db.search(filters, limit=50)
    first_search_time = time.time() - start_time
    print(f"First search (no cache): {first_search_time:.3f} seconds, {count1} results")
    
    # Second search (with cache)
    start_time = time.time()
    results2, count2 = db.search_with_cache(filters, limit=50)
    cached_search_time = time.time() - start_time
    print(f"Cached search: {cached_search_time:.3f} seconds")
    print(f"Cache speedup: {first_search_time / cached_search_time:.1f}x faster")

def test_facet_performance(db):
    """Test facet calculation performance."""
    print("\n=== Testing Facet Performance ===")
    
    # First facet calculation
    start_time = time.time()
    facets1 = db.get_facets()
    first_facet_time = time.time() - start_time
    print(f"First facet calculation: {first_facet_time:.3f} seconds")
    print(f"Found {len(facets1['tags'])} tag facets")
    
    # Second facet calculation (cached)
    start_time = time.time()
    facets2 = db.get_facets()
    cached_facet_time = time.time() - start_time
    print(f"Cached facet calculation: {cached_facet_time:.3f} seconds")
    print(f"Cache speedup: {first_facet_time / cached_facet_time:.1f}x faster")

def test_tag_search_performance(db):
    """Test optimized tag search."""
    print("\n=== Testing Tag Search Performance ===")
    
    tags = {
        "style": ["cyberpunk", "abstract"],
        "mood": ["dark", "bright"]
    }
    
    # Test ANY mode
    start_time = time.time()
    results_any = db.search_by_tags(tags, mode="any", limit=50)
    any_time = time.time() - start_time
    print(f"Tag search (ANY mode): {any_time:.3f} seconds, {len(results_any)} results")
    
    # Test ALL mode
    start_time = time.time()
    results_all = db.search_by_tags(tags, mode="all", limit=50)
    all_time = time.time() - start_time
    print(f"Tag search (ALL mode): {all_time:.3f} seconds, {len(results_all)} results")

def test_query_analysis(db):
    """Test query performance analysis."""
    print("\n=== Testing Query Analysis ===")
    
    # Analyze a complex query
    query = """
        SELECT a.*, t.tags
        FROM assets a
        LEFT JOIN asset_tags t ON a.content_hash = t.content_hash
        WHERE a.media_type = ? AND a.ai_source IN (?, ?)
        ORDER BY a.created_at DESC
        LIMIT 50
    """
    
    analysis = db.analyze_query_performance(query, ["image", "midjourney", "stable-diffusion"])
    print(f"Query analysis:")
    for suggestion in analysis.get("suggestions", []):
        print(f"  - {suggestion}")
    
    if "execution_time_ms" in analysis:
        print(f"  Execution time: {analysis['execution_time_ms']:.1f}ms")

def test_database_optimization(db):
    """Test database optimization."""
    print("\n=== Testing Database Optimization ===")
    
    # Get table statistics before
    stats_before = db.get_table_stats()
    print("Table statistics:")
    for table, stats in stats_before.items():
        if "row_count" in stats:
            print(f"  {table}: {stats['row_count']} rows, ~{stats['size_estimate_mb']:.1f} MB")
    
    # Run optimization
    optimization_results = db.optimize_database()
    print("\nOptimization results:")
    for key, value in optimization_results.items():
        if key != "error":
            print(f"  {key}: {value}")

def main():
    """Run all performance tests."""
    print("AliceMultiverse DuckDB Performance Optimization Tests")
    print("=" * 50)
    
    # Clean up any existing test database
    test_db_path = Path("test_performance.duckdb")
    if test_db_path.exists():
        test_db_path.unlink()
    
    try:
        # Run tests
        db = test_batch_insert_performance()
        test_search_performance(db)
        test_facet_performance(db)
        test_tag_search_performance(db)
        test_query_analysis(db)
        test_database_optimization(db)
        
        print("\n" + "=" * 50)
        print("Performance tests completed successfully!")
        
    finally:
        # Clean up
        db.close()
        if test_db_path.exists():
            test_db_path.unlink()

if __name__ == "__main__":
    main()