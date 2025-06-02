#!/usr/bin/env python3
"""
Demonstration of semantic search using tags and metadata.

This example shows how to search for images using semantic tags,
AI source, date ranges, and other metadata.
"""

from datetime import datetime, timedelta
from alicemultiverse.storage.duckdb_search import DuckDBSearch
from pathlib import Path

def print_results(results, title="Search Results"):
    """Pretty print search results."""
    print(f"\n{title}")
    print("=" * 50)
    
    if not results:
        print("No results found.")
        return
    
    print(f"Found {len(results)} images:\n")
    
    for asset in results[:10]:  # Show first 10
        file_name = Path(asset['file_path']).name
        print(f"• {file_name}")
        
        # Show tags
        if asset.get('tags'):
            all_tags = []
            for category, tag_list in asset['tags'].items():
                if tag_list:
                    all_tags.append(f"{category}: {', '.join(tag_list[:3])}")
            if all_tags:
                print(f"  Tags: {'; '.join(all_tags[:3])}")
        
        # Show other metadata
        if asset.get('ai_source'):
            print(f"  Source: {asset['ai_source']}")
        if asset.get('file_size'):
            size_mb = asset['file_size'] / (1024 * 1024)
            print(f"  Size: {size_mb:.1f} MB")
        print()


def demo_semantic_search():
    """Demonstrate various search capabilities."""
    # Initialize search database
    db = DuckDBSearch("data/search.duckdb")
    
    # Get total count
    stats = db.get_statistics()
    print(f"\nDatabase contains {stats['total_assets']} assets")
    print(f"Unique tags: {stats['unique_tags']}")
    
    # 1. Search by tags (AND operation)
    print("\n" + "="*70)
    print("1. SEARCH BY TAGS (must have all)")
    filters = {
        "tags": ["futuristic", "portrait"]  # Must have both tags
    }
    results, total = db.search(filters, limit=5)
    print_results(results, f"Images with 'futuristic' AND 'portrait' tags ({total} total)")
    
    # 2. Search by any tags (OR operation)
    print("\n" + "="*70)
    print("2. SEARCH BY ANY TAGS (has at least one)")
    filters = {
        "any_tags": ["cyberpunk", "sci-fi", "neon"]  # Has any of these
    }
    results, total = db.search(filters, limit=5)
    print_results(results, f"Images with cyberpunk OR sci-fi OR neon ({total} total)")
    
    # 3. Search by AI source
    print("\n" + "="*70)
    print("3. SEARCH BY AI SOURCE")
    filters = {
        "ai_source": ["midjourney", "dalle"]  # From these sources
    }
    results, total = db.search(filters, limit=5)
    print_results(results, f"Images from Midjourney or DALL-E ({total} total)")
    
    # 4. Search by date range
    print("\n" + "="*70)
    print("4. SEARCH BY DATE RANGE")
    filters = {
        "date_range": {
            "start": datetime.now() - timedelta(days=7),  # Last week
            "end": datetime.now()
        }
    }
    results, total = db.search(filters, limit=5)
    print_results(results, f"Images from the last 7 days ({total} total)")
    
    # 5. Complex search combining multiple filters
    print("\n" + "="*70)
    print("5. COMPLEX SEARCH")
    filters = {
        "media_type": "image",
        "any_tags": ["portrait", "fashion"],
        "ai_source": "midjourney",
        "file_size": {
            "min": 500 * 1024,  # At least 500KB
            "max": 10 * 1024 * 1024  # At most 10MB
        }
    }
    results, total = db.search(filters, limit=5)
    print_results(results, f"Midjourney portraits/fashion 500KB-10MB ({total} total)")
    
    # 6. Get facets (tag counts)
    print("\n" + "="*70)
    print("6. TAG FACETS (Most Common Tags)")
    facets = db.get_facets()
    
    print("\nTop 10 Tags:")
    for tag_info in facets['tags'][:10]:
        print(f"  {tag_info['value']}: {tag_info['count']} images")
    
    print("\nAI Sources:")
    for source_info in facets['ai_sources']:
        print(f"  {source_info['value']}: {source_info['count']} images")
    
    # 7. Search with exclusions
    print("\n" + "="*70)
    print("7. SEARCH WITH EXCLUSIONS")
    filters = {
        "tags": ["portrait"],  # Must have portrait
        "exclude_tags": ["dark", "moody"]  # But not dark or moody
    }
    results, total = db.search(filters, limit=5)
    print_results(results, f"Portraits excluding dark/moody ({total} total)")


def main():
    """Run the semantic search demonstration."""
    print("="*70)
    print("SEMANTIC SEARCH DEMONSTRATION")
    print("="*70)
    
    # Check if database exists
    db_path = Path("data/search.duckdb")
    if not db_path.exists():
        print("\nError: No search database found!")
        print("Please organize some images first:")
        print("  alice -i ~/Downloads/AI-Images -o ~/Pictures/AI-Organized")
        return
    
    try:
        demo_semantic_search()
    except Exception as e:
        print(f"\nError: {e}")
        print("\nMake sure you have organized images with understanding enabled.")


if __name__ == "__main__":
    main()