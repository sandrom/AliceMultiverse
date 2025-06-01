# Image Presentation API Design

## Overview

The Image Presentation API enables AI assistants to retrieve and display images in chat interfaces for collaborative browsing and selection. This is the foundation for the creative workflow where users explore thousands of images with AI assistance.

## User Stories

1. **Browse by Query**: "Show me cyberpunk portraits"
2. **Browse Similar**: "Show me more like these three"
3. **Browse with Exclusions**: "Show me landscapes but not forests"
4. **Browse Recent**: "Show me what I generated yesterday"

## API Design

### Core Endpoints

```python
# 1. Search and retrieve images for display
async def search_images(
    query: Optional[str] = None,
    tags: Optional[List[str]] = None,
    similar_to: Optional[List[str]] = None,  # Image hashes
    exclude_tags: Optional[List[str]] = None,
    exclude_folders: Optional[List[str]] = None,
    date_range: Optional[Tuple[datetime, datetime]] = None,
    limit: int = 20,
    offset: int = 0
) -> ImageSearchResult:
    """
    Search images based on various criteria.
    
    Returns:
        ImageSearchResult with images ready for display in chat
    """

# 2. Track user selections and feedback
async def track_selection(
    image_hash: str,
    selected: bool,
    reason: Optional[str] = None,
    session_id: Optional[str] = None
) -> None:
    """
    Record user's selection decision and reasoning.
    """

# 3. Soft delete unwanted images
async def soft_delete_image(
    image_hash: str,
    reason: str,
    category: str = "rejected"  # rejected, broken, maybe-later
) -> str:
    """
    Move image to sorted-out folder.
    
    Returns:
        New path in sorted-out structure
    """
```

### Data Models

```python
@dataclass
class ImageSearchResult:
    """Results formatted for AI chat display"""
    images: List[PresentableImage]
    total_count: int
    has_more: bool
    query_interpretation: str  # How we understood the query
    suggestions: List[str]  # Suggested refinements

@dataclass
class PresentableImage:
    """Image data optimized for chat display"""
    hash: str
    path: str
    thumbnail_url: str  # Base64 or file:// URL
    display_url: str    # Full resolution for detail view
    
    # Key metadata for display
    tags: List[str]
    source: str  # midjourney, dalle, etc.
    created_date: datetime
    
    # Understanding data
    description: str  # AI-generated description
    mood: List[str]
    style: List[str]
    colors: List[str]
    
    # Selection history
    previously_selected: bool
    selection_reason: Optional[str]
    
    # Technical info
    dimensions: Tuple[int, int]
    file_size: int
```

## Implementation Plan

### Phase 1: Basic Search and Display
- Implement search_images with tag-based search
- Create thumbnail generation for fast display
- Return images in chat-friendly format
- Add to alice interface module

### Phase 2: Selection Tracking
- Implement track_selection with DuckDB storage
- Add selection history to image metadata
- Enable "previously selected" indicators

### Phase 3: Similarity Search
- Add vector embeddings for images
- Implement similar_to parameter
- Use DuckDB VSS extension

### Phase 4: Soft Delete
- Implement soft_delete_image
- Create sorted-out folder structure
- Update search to exclude these folders

## Integration with AI Assistants

### Claude Desktop (via MCP)
```python
# MCP tool definition
@mcp_tool(
    name="search_images",
    description="Search and display images for user selection"
)
async def mcp_search_images(params: Dict) -> Dict:
    result = await search_images(**params)
    return {
        "images": [img.to_display_dict() for img in result.images],
        "total": result.total_count,
        "suggestions": result.suggestions
    }
```

### Response Format for Chat
```json
{
  "images": [
    {
      "id": "abc123",
      "thumbnail": "data:image/jpeg;base64,...",
      "caption": "Cyberpunk portrait with neon lighting",
      "tags": ["portrait", "cyberpunk", "neon"],
      "selectable": true
    }
  ],
  "instructions": "Click images to select. Tell me what you like/dislike.",
  "suggestions": [
    "Try 'more neon colors'",
    "Try 'less busy backgrounds'",
    "Show similar to selected"
  ]
}
```

## Testing Strategy

### Unit Tests
- Test search query parsing
- Test tag filtering logic
- Test exclusion logic
- Test pagination

### Integration Tests
- Test with real image database
- Test thumbnail generation
- Test selection persistence
- Test soft delete file operations

### Performance Tests
- Search 10k+ images < 100ms
- Thumbnail generation < 50ms/image
- Concurrent request handling

## Documentation

### User Documentation
- How to browse images with AI
- Selection workflow guide
- Soft delete explanation

### API Documentation
- OpenAPI spec for REST endpoints
- MCP tool documentation
- Response format examples

## Migration Notes

- No breaking changes to existing APIs
- Soft delete is additive feature
- Selection tracking is optional