# Selection Tracking System

The selection tracking system in AliceMultiverse provides a powerful way to manage curated collections of assets for various purposes. It integrates seamlessly with the similarity search feature to help you build cohesive collections.

## Overview

Selections are project-based collections that allow you to:
- Curate assets for specific purposes
- Track why items were selected
- Organize assets into groups
- Export collections for delivery
- Find similar assets to expand your selections

## Key Features

### 1. Purpose-Driven Selections
Each selection has a defined purpose:
- **Curation**: General collection building
- **Presentation**: Client presentations
- **Export**: Final delivery
- **Reference**: Style/mood boards
- **Training**: ML model training data
- **Portfolio**: Portfolio pieces
- **Social Media**: Content planning

### 2. Selection Metadata
Track important information for each item:
- Selection reason
- Quality notes
- Usage notes
- Role in selection
- Custom tags

### 3. Similarity Search Integration
**NEW**: Find visually similar images to expand your selections:
```python
# Find images similar to your selection
similar = alice.find_similar_to_selection(
    project_id="my-project",
    selection_id="selection-123",
    threshold=10,
    limit=50
)
```

See the [Similarity Search Guide](./similarity-search-guide.md) for details.

### 4. History Tracking
All changes are tracked:
- When items were added/removed
- Who made changes
- Reason for changes

## Creating Selections

```python
from alicemultiverse.interface.alice_structured import AliceStructuredInterface
from alicemultiverse.interface.structured_models import (
    SelectionCreateRequest,
    SelectionPurpose
)

alice = AliceStructuredInterface()

# Create a new selection
request = SelectionCreateRequest(
    project_id="my-project",
    name="Hero Images Q4 2024",
    purpose=SelectionPurpose.PRESENTATION,
    description="Top images for Q4 marketing campaign",
    criteria={
        "quality": "high",
        "style": "modern",
        "mood": "energetic"
    },
    tags=["marketing", "q4-2024", "hero"]
)

result = alice.create_selection(request)
```

## Adding Items

```python
from alicemultiverse.interface.structured_models import SelectionUpdateRequest

# Add items to selection
update_request = SelectionUpdateRequest(
    project_id="my-project",
    selection_id=selection_id,
    action="add_items",
    items=[
        {
            "asset_hash": "abc123...",
            "file_path": "/path/to/image.jpg",
            "selection_reason": "Perfect hero image energy",
            "quality_notes": "Sharp, vibrant colors",
            "usage_notes": "Homepage banner",
            "tags": ["hero", "primary"],
            "role": "primary"
        }
    ],
    notes="Initial hero image selection"
)

alice.update_selection(update_request)
```

## Workflow Example

Here's a complete workflow combining selections with similarity search:

```python
# 1. Create selection for a specific aesthetic
selection = alice.create_selection(SelectionCreateRequest(
    project_id=project_id,
    name="Minimalist Product Shots",
    purpose=SelectionPurpose.CURATION
))

# 2. Add initial reference images
alice.update_selection(SelectionUpdateRequest(
    project_id=project_id,
    selection_id=selection_id,
    action="add_items",
    items=initial_items
))

# 3. Find similar images to expand the selection
similar = alice.find_similar_to_selection(
    project_id=project_id,
    selection_id=selection_id,
    threshold=12  # Moderate similarity
)

# 4. Review and add the best matches
for result in similar.data['results']:
    if result['similarity']['recommendation_score'] > 0.75:
        # This is a good match, add it
        alice.update_selection(...)

# 5. Export the final selection
alice.export_selection(SelectionExportRequest(
    project_id=project_id,
    selection_id=selection_id,
    export_path="/exports/minimalist-products"
))
```

## Best Practices

1. **Clear Naming**: Use descriptive names that indicate purpose and timeframe
2. **Document Reasons**: Always provide selection reasons for future reference
3. **Use Roles**: Assign roles (hero, supporting, alternate) to organize items
4. **Regular Reviews**: Periodically review and update selections
5. **Leverage Similarity**: Use similarity search to find related content efficiently

## Selection States

- **Draft**: Work in progress
- **Active**: Currently in use
- **Archived**: Kept for reference
- **Exported**: Delivered to client

## Export Options

Selections can be exported with:
- Metadata preservation
- Folder structure organization
- Delivery documentation
- Asset manifests

## Integration with Projects

Selections are tied to projects, allowing:
- Budget tracking per selection
- Multiple selections per project
- Cross-selection asset sharing
- Project-wide asset discovery

## See Also

- [Similarity Search Guide](./similarity-search-guide.md)
- [Project Management](./project-management.md)
- Example: `examples/selection_example.py`
- Example: `examples/similarity_search_with_selections.py`