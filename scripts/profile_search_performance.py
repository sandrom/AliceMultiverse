#!/usr/bin/env python3
"""Profile search performance to identify N+1 queries and bottlenecks."""

import asyncio
import cProfile
import logging
import pstats
import time
from io import StringIO
from pathlib import Path

from sqlalchemy import event
from sqlalchemy.engine import Engine

from alicemultiverse.database.config import get_session
from alicemultiverse.database.repository import AssetRepository
from alicemultiverse.interface.alice_structured import AliceStructuredInterface
from alicemultiverse.interface.structured_models import (
    MediaType,
    SearchRequest,
    SortField,
    SortOrder,
)

# Track SQL queries
query_count = 0
queries = []


@event.listens_for(Engine, "before_cursor_execute", propagate=True)
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    """Log each SQL query."""
    global query_count, queries
    query_count += 1
    queries.append({
        "query": statement,
        "params": parameters,
        "count": query_count
    })


def reset_query_tracking():
    """Reset query tracking."""
    global query_count, queries
    query_count = 0
    queries = []


def analyze_queries():
    """Analyze captured queries for N+1 patterns."""
    global queries
    
    # Group queries by pattern
    query_patterns = {}
    for q in queries:
        # Simplify query to identify pattern
        query = q["query"].strip()
        if query.startswith("SELECT"):
            # Extract table and basic pattern
            pattern = query.split("FROM")[1].split("WHERE")[0].strip() if "FROM" in query else query
            pattern = pattern.split()[0] if pattern else "unknown"
        else:
            pattern = query.split()[0]
        
        if pattern not in query_patterns:
            query_patterns[pattern] = []
        query_patterns[pattern].append(q)
    
    print("\n=== Query Analysis ===")
    print(f"Total queries: {query_count}")
    print("\nQuery patterns:")
    for pattern, pattern_queries in query_patterns.items():
        print(f"  {pattern}: {len(pattern_queries)} queries")
        
        # Check for N+1 pattern
        if len(pattern_queries) > 10:
            print(f"    ⚠️  Potential N+1 query detected!")
            # Show first few queries
            for i, q in enumerate(pattern_queries[:3]):
                print(f"    Query {i+1}: {q['query'][:100]}...")


async def profile_search_operations():
    """Profile different search operations."""
    interface = AliceStructuredInterface()
    repo = AssetRepository()
    
    print("=== Profiling Search Operations ===\n")
    
    # Test 1: Basic search
    print("1. Basic search (no filters):")
    reset_query_tracking()
    start_time = time.time()
    
    request = SearchRequest(
        limit=50,
        sort_by=SortField.CREATED_DATE,
        order=SortOrder.DESC
    )
    
    result = interface.search_assets(request)
    
    elapsed = time.time() - start_time
    print(f"   Time: {elapsed:.3f}s")
    print(f"   Queries: {query_count}")
    print(f"   Results: {result['data']['total_count']} assets")
    analyze_queries()
    
    # Test 2: Search with tags
    print("\n2. Search with tag filters:")
    reset_query_tracking()
    start_time = time.time()
    
    request = SearchRequest(
        filters={
            "tags": ["cyberpunk", "futuristic"],
            "media_type": MediaType.IMAGE
        },
        limit=50
    )
    
    result = interface.search_assets(request)
    
    elapsed = time.time() - start_time
    print(f"   Time: {elapsed:.3f}s")
    print(f"   Queries: {query_count}")
    print(f"   Results: {result['data']['total_count']} assets")
    analyze_queries()
    
    # Test 3: Complex search with multiple filters
    print("\n3. Complex search (multiple filters):")
    reset_query_tracking()
    start_time = time.time()
    
    request = SearchRequest(
        filters={
            "media_type": MediaType.IMAGE,
            "quality_rating": {"min": 4},
            "ai_source": ["fal.ai", "comfyui"],
            "tags": ["portrait"],
            "date_range": {
                "start": "2024-01-01",
                "end": "2024-12-31"
            }
        },
        sort_by=SortField.QUALITY,
        order=SortOrder.DESC,
        limit=100
    )
    
    result = interface.search_assets(request)
    
    elapsed = time.time() - start_time
    print(f"   Time: {elapsed:.3f}s")
    print(f"   Queries: {query_count}")
    print(f"   Results: {result['data']['total_count']} assets")
    analyze_queries()
    
    # Test 4: Direct repository search
    print("\n4. Direct repository search:")
    reset_query_tracking()
    start_time = time.time()
    
    assets = repo.search(
        media_type="image",
        tags={"style": ["cyberpunk"], "mood": ["dark"]},
        min_rating=4,
        limit=50
    )
    
    elapsed = time.time() - start_time
    print(f"   Time: {elapsed:.3f}s")
    print(f"   Queries: {query_count}")
    print(f"   Results: {len(assets)} assets")
    
    # Access relationships to trigger potential N+1
    for asset in assets[:10]:
        _ = asset.tags  # This might trigger N+1
        _ = asset.project  # This might trigger N+1
    
    print(f"   Queries after accessing relationships: {query_count}")
    analyze_queries()
    
    # Profile with cProfile for detailed analysis
    print("\n=== Detailed Profile ===")
    profiler = cProfile.Profile()
    
    reset_query_tracking()
    profiler.enable()
    
    # Run a typical search operation
    for _ in range(5):
        result = interface.search_assets(SearchRequest(
            filters={"media_type": MediaType.IMAGE},
            limit=20
        ))
    
    profiler.disable()
    
    # Print profiling results
    s = StringIO()
    ps = pstats.Stats(profiler, stream=s).sort_stats('cumulative')
    ps.print_stats(20)  # Top 20 functions
    print(s.getvalue())


def main():
    """Run profiling."""
    # Set up logging to see SQL queries
    logging.basicConfig(level=logging.INFO)
    logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
    
    # Run async profiling
    asyncio.run(profile_search_operations())


if __name__ == "__main__":
    main()