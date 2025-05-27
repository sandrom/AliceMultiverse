# Structured Interface Migration Guide

## Overview

AliceMultiverse is migrating from a natural language interface to a structured API. This guide explains the changes and how to migrate existing code.

## Why Structured APIs?

The structured interface provides:
- **Type Safety**: All parameters use typed enums and dictionaries
- **Performance**: Direct database queries without NLP overhead
- **Reliability**: No ambiguity in query interpretation
- **Testability**: Deterministic behavior for the same inputs
- **Flexibility**: Different AI assistants can have different NLP capabilities

## Key Principle

**Alice should NEVER process natural language.** All natural language processing happens at the AI assistant layer (Claude, ChatGPT, etc.), which then calls Alice with structured parameters.

## Migration Examples

### Search Operations

#### Old (Natural Language)
```python
from alicemultiverse.interface import AliceInterface

alice = AliceInterface()
results = alice.search_assets({
    "description": "cyberpunk portraits from last week",
    "min_quality_stars": 4
})
```

#### New (Structured)
```python
from alicemultiverse.interface import (
    AliceStructuredInterface,
    SearchRequest,
    SearchFilters,
    MediaType,
    DateRange,
    SortField
)

alice = AliceStructuredInterface()
results = alice.search_assets(SearchRequest(
    filters=SearchFilters(
        media_type=MediaType.IMAGE,
        tags=["cyberpunk", "portrait"],
        quality_rating={"min": 4},
        date_range=DateRange(
            start="2024-05-20"  # AI converts "last week" to actual date
        )
    ),
    sort_by=SortField.QUALITY_RATING,
    order="desc"
))
```

### Tag Operations

#### Old
```python
alice.tag_assets({
    "asset_ids": ["id1", "id2"],
    "tags": ["hero-shot"],
    "tag_type": "custom_tags"
})
```

#### New
```python
from alicemultiverse.interface import TagUpdateRequest

alice.update_tags(TagUpdateRequest(
    asset_ids=["id1", "id2"],
    add_tags=["hero-shot", "approved"]
))
```

### Complex Searches

#### Old
```python
results = alice.search_assets({
    "description": "dark fantasy landscapes excluding sketches",
    "source_types": ["stable-diffusion", "midjourney"],
    "time_reference": "October"
})
```

#### New
```python
results = alice.search_assets(SearchRequest(
    filters=SearchFilters(
        media_type=MediaType.IMAGE,
        tags=["fantasy", "landscape"],
        mood_tags=["dark"],
        exclude_tags=["sketch"],
        ai_source=["stable-diffusion", "midjourney"],
        date_range=DateRange(
            start="2024-10-01",
            end="2024-10-31"
        )
    )
))
```

## Available Filters

### Technical Filters
- `media_type`: MediaType enum (IMAGE, VIDEO, AUDIO, DOCUMENT)
- `file_formats`: List of extensions ["jpg", "png"]
- `file_size`: RangeFilter with min/max bytes
- `dimensions`: Width, height, aspect ratio ranges
- `quality_rating`: RangeFilter for star ratings

### Semantic Filters
- `tags`: AND operation - all must match
- `any_tags`: OR operation - at least one must match
- `exclude_tags`: NOT operation - none must match
- `tag_values`: (Future) Key-value pairs for semantic search

### Metadata Filters
- `ai_source`: List of AI generators
- `project`: Project name
- `content_hash`: Exact file match
- `has_metadata`: Required metadata fields
- `filename_pattern`: Regex pattern
- `prompt_keywords`: Keywords in generation prompt

### Temporal Filters
- `date_range`: ISO 8601 date strings with start/end

## Enums and Types

### MediaType
```python
class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    UNKNOWN = "unknown"
```

### SortField
```python
class SortField(str, Enum):
    CREATED_DATE = "created_date"
    MODIFIED_DATE = "modified_date"
    QUALITY_RATING = "quality_rating"
    FILE_SIZE = "file_size"
    FILENAME = "filename"
```

### AssetRole
```python
class AssetRole(str, Enum):
    HERO = "hero"
    B_ROLL = "b_roll"
    REFERENCE = "reference"
    WIP = "wip"
    FINAL = "final"
    REJECTED = "rejected"
```

## Transition Period

During the transition:
1. Both interfaces are available
2. The old interface is marked as deprecated
3. New code should use `AliceStructuredInterface`
4. The old interface internally uses the structured API

### Using the CLI
```bash
# Old interface (deprecated)
alice interface --demo

# New structured interface
alice interface --structured --demo
```

### Import Changes
```python
# Old (deprecated)
from alicemultiverse.interface import AliceInterface

# New (recommended)
from alicemultiverse.interface import AliceStructuredInterface
```

## AI Assistant Integration

When integrating with AI assistants:

1. **User Input**: "Find cyberpunk portraits from last week"
2. **AI Processing**: Claude/ChatGPT parses the natural language
3. **Structured Call**: AI converts to structured API call
4. **Alice Processing**: Executes efficient database queries
5. **Structured Response**: Returns typed results

Example AI integration:
```python
# AI assistant's code
def handle_user_request(user_input: str):
    # AI parses natural language
    if "cyberpunk" in user_input and "portrait" in user_input:
        tags = ["cyberpunk", "portrait"]
    
    if "last week" in user_input:
        start_date = (datetime.now() - timedelta(days=7)).isoformat()
    
    # AI makes structured call
    results = alice.search_assets(SearchRequest(
        filters=SearchFilters(
            tags=tags,
            date_range=DateRange(start=start_date)
        )
    ))
    
    # AI formats response for user
    return format_results_naturally(results)
```

## Best Practices

1. **Use Enums**: Always use enum values instead of strings
2. **Type Hints**: Leverage TypeScript/Python type hints
3. **Validation**: Validate parameters before calling Alice
4. **Error Handling**: Handle structured error responses
5. **Batch Operations**: Use lists for bulk operations

## Future Enhancements

### Tag:Value Pairs (Coming Soon)
```python
SearchFilters(
    tag_values={
        "subject": "portrait",
        "style": ["cyberpunk", "noir"],
        "lighting": "neon",
        "mood": "mysterious"
    },
    tag_ranges={
        "character_count": {"min": 1, "max": 3}
    }
)
```

### GraphQL Support (Planned)
```graphql
query SearchAssets($filters: SearchFilters!) {
  searchAssets(filters: $filters) {
    totalCount
    results {
      contentHash
      tags
      metadata {
        prompt
        dimensions { width height }
      }
    }
  }
}
```

## Timeline

- **Phase 1** (Current): Both interfaces available
- **Phase 2** (Q2 2025): Deprecation warnings added
- **Phase 3** (Q3 2025): Legacy interface removed

## Getting Help

- Run `alice interface --structured --demo` for examples
- See `tests/unit/test_alice_structured_interface.py` for usage
- Check `docs/developer/search-api-specification.md` for full API spec