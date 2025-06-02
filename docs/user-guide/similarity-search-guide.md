# Similarity Search with Selections

AliceMultiverse now includes powerful similarity search functionality that integrates with the selection system. This feature uses perceptual hashing to find images visually similar to those in your selections, helping you discover more content that matches your aesthetic preferences.

## Overview

The similarity search feature allows you to:
- Find images similar to those in a selection
- Expand selections with visually similar content
- Discover related assets based on visual similarity
- Build cohesive collections efficiently

## How It Works

### Perceptual Hashing

AliceMultiverse uses three types of perceptual hashes:
1. **pHash (DCT-based)** - Most robust to scaling and minor changes
2. **dHash (Difference Hash)** - Fast and effective for similar images
3. **aHash (Average Hash)** - Simple but effective for basic similarity

These hashes create "fingerprints" of images that remain similar even when images are:
- Scaled or resized
- Slightly color-adjusted
- Compressed differently
- Have minor variations

### Similarity Scoring

The system calculates similarity using:
- **Hamming Distance**: Measures bit differences between hashes (0-64 range)
- **Recommendation Score**: Combines distance and coverage metrics
  - 70% based on visual similarity (lower distance = higher score)
  - 30% based on how many selection items it matches

## Using Similarity Search

### Through AI Assistants

When using AliceMultiverse through Claude or other AI assistants:

```
"Find images similar to my cyberpunk selection"
"Expand my portrait selection with similar photos"
"Show me more images like the ones I've selected"
```

### Programmatic Usage

```python
from alicemultiverse.interface.alice_structured import AliceStructuredInterface

alice = AliceStructuredInterface()

# Find similar images to a selection
similar_result = alice.find_similar_to_selection(
    project_id="my-project",
    selection_id="selection-123",
    threshold=10,        # Lower = more similar (0-64)
    limit=50,           # Max results
    exclude_existing=True  # Don't show already selected
)

# Process results
for result in similar_result.data['results']:
    asset = result['asset']
    similarity = result['similarity']
    print(f"{asset['file_path']}")
    print(f"Score: {similarity['recommendation_score']:.2%}")
    print(f"Distance: {similarity['min_distance']}")
```

## Parameters

### Threshold
- Range: 0-64 (Hamming distance)
- Lower values = more similar
- Recommended values:
  - 0-5: Nearly identical images
  - 6-10: Very similar (same style/subject)
  - 11-15: Similar (related aesthetic)
  - 16-25: Somewhat similar
  - 26+: Loosely related

### Limit
- Maximum number of results to return
- Default: 50
- Consider your use case:
  - Quick preview: 10-20
  - Thorough search: 50-100
  - Exhaustive: 200+

### Exclude Existing
- Whether to exclude items already in the selection
- Default: True
- Set to False to see all matches

## Best Practices

### 1. Start with Quality Seeds
Select high-quality representative images as your initial selection. The similarity search works best when starting from clear examples of what you want.

### 2. Use Appropriate Thresholds
- For style matching: Use threshold 10-15
- For finding variations: Use threshold 5-10
- For broad discovery: Use threshold 15-20

### 3. Iterate and Refine
1. Start with a small selection (3-5 images)
2. Find similar images
3. Add the best matches
4. Search again with the expanded selection
5. Remove any false positives

### 4. Combine with Tags
Use similarity search alongside tag-based search for best results:
```python
# First search by tags
tagged_results = alice.search(SearchRequest(
    tags=["portrait", "dramatic lighting"],
    media_type=MediaType.IMAGE
))

# Then find similar to refine
similar_results = alice.find_similar_to_selection(...)
```

## Example Workflow

Here's a complete workflow for building a themed collection:

```python
# 1. Create initial selection
selection = alice.create_selection(SelectionCreateRequest(
    project_id=project_id,
    name="Moody Portraits Collection",
    purpose=SelectionPurpose.CURATION
))

# 2. Add seed images
alice.update_selection(SelectionUpdateRequest(
    project_id=project_id,
    selection_id=selection_id,
    action="add_items",
    items=[{"asset_hash": hash, "file_path": path}]
))

# 3. Find similar images
similar = alice.find_similar_to_selection(
    project_id=project_id,
    selection_id=selection_id,
    threshold=12,
    limit=30
)

# 4. Review and add best matches
for result in similar.data['results'][:10]:
    if result['similarity']['recommendation_score'] > 0.8:
        # Add to selection
        alice.update_selection(...)
```

## Understanding Results

Each similarity result includes:

```json
{
  "asset": {
    "content_hash": "abc123...",
    "file_path": "/path/to/image.jpg",
    "ai_source": "midjourney",
    "tags": ["portrait", "moody", "dramatic"]
  },
  "similarity": {
    "min_distance": 8,              // Hamming distance (lower = more similar)
    "recommendation_score": 0.85,    // 0-1 score (higher = better match)
    "similar_to_count": 3,          // Number of selection items it matches
    "similar_to_items": [           // Which items it's similar to
      {
        "hash": "def456...",
        "path": "/path/to/selected1.jpg",
        "role": "seed",
        "reason": "Initial selection"
      }
    ]
  }
}
```

## Performance Considerations

- **Initial indexing**: Perceptual hashes are calculated when images are first organized
- **Search speed**: Depends on total number of images (typically <1s for 10k images)
- **Memory usage**: Minimal - hashes are compact 64-bit values
- **Storage**: Hashes are stored in DuckDB for fast retrieval

## Troubleshooting

### No results found
- Check if images have been indexed with `--force-reindex`
- Increase threshold for broader matches
- Verify selection has items

### Poor quality matches
- Decrease threshold for stricter matching
- Ensure seed images are representative
- Check if perceptual hashes were generated correctly

### Performance issues
- Reduce limit parameter
- Check DuckDB index status
- Consider batch processing for large collections

## Future Enhancements

Planned improvements include:
- Color histogram similarity
- Composition analysis
- Style transfer detection
- Multi-modal similarity (combining visual + semantic)
- Cluster visualization
- Similarity explanations

## See Also

- [Selection System Guide](./selection-system-guide.md)
- [Search API Documentation](../developer/search-api-specification.md)
- Example: `examples/similarity_search_with_selections.py`