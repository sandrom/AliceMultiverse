# Alice Interface Design Guidelines

## Overview

Alice serves as the orchestration layer between AI assistants and technical systems. This document defines the design principles for Alice's API and interfaces.

## Core Principle: Structured Over Natural

Alice should **never** process natural language. All API calls must use structured, computer-friendly formats. Natural language processing is the responsibility of the AI assistant layer.

### ❌ Bad: Natural Language in Alice
```python
# Alice should NOT do this
alice.search("that cool cyberpunk portrait from last week")
alice.organize("put all the dark fantasy images in a new project")
```

### ✅ Good: Structured API
```python
# AI assistant translates user intent into structured calls
alice.search_assets({
    "filters": {
        "media_type": "image",
        "tags": ["cyberpunk", "portrait"],
        "date_range": {
            "start": "2024-05-19",
            "end": "2024-05-26"
        }
    },
    "sort_by": "quality_score",
    "limit": 10
})

alice.create_project({
    "name": "Dark Fantasy Collection",
    "filters": {
        "tags": ["dark", "fantasy"],
        "media_type": "image"
    },
    "action": "move"  # or "copy"
})
```

## Search API Design

### Media Types vs Tags

Maintain a clear distinction between technical and semantic metadata:

- **Media Types**: Technical classification of the file
  - `image`, `video`, `audio`, `document`
  - These are finite and system-defined

- **Tags**: Semantic/creative concepts
  - Style: `cyberpunk`, `anime`, `photorealistic`, `abstract`
  - Subject: `portrait`, `landscape`, `architecture`, `character`
  - Mood: `dark`, `cheerful`, `mysterious`, `romantic`
  - Technical: `high-detail`, `sketch`, `3d-render`
  - Any other creative descriptor

### Search Structure

```python
{
    "filters": {
        # Technical filters
        "media_type": "image",  # Required: image|video|audio
        "file_formats": ["jpg", "png"],  # Optional: specific formats
        "quality_rating": {"min": 4},  # Optional: 1-5 stars
        
        # Semantic filters
        "tags": ["tag1", "tag2"],  # All must match (AND)
        "any_tags": ["tag3", "tag4"],  # At least one must match (OR)
        "exclude_tags": ["tag5"],  # None must match
        
        # Temporal filters
        "date_range": {
            "start": "2024-05-01",  # ISO date
            "end": "2024-05-31"
        },
        
        # Source filters
        "ai_source": ["stable-diffusion", "midjourney"],
        "project": "project-name",
        
        # Advanced filters
        "has_metadata": ["prompt", "camera_model"],
        "content_hash": "abc123..."  # For exact match
    },
    
    "sort_by": "created_date",  # Options: created_date, quality_score, file_size
    "order": "desc",  # asc or desc
    "limit": 50,
    "offset": 0
}
```

## Common API Patterns

### Asset Discovery
```python
# Find recently added high-quality images
{
    "filters": {
        "media_type": "image",
        "quality_rating": {"min": 4},
        "date_range": {
            "start": "7_days_ago"  # AI translates relative dates
        }
    },
    "sort_by": "created_date",
    "order": "desc"
}
```

### Project Organization
```python
# Organize assets into projects
{
    "project_name": "Summer Campaign",
    "filters": {
        "tags": ["summer", "beach", "vacation"],
        "date_range": {"start": "2024-06-01", "end": "2024-08-31"}
    },
    "organization_rules": {
        "group_by": ["ai_source", "quality_rating"],
        "naming_pattern": "{project}-{sequence:05d}"
    }
}
```

### Workflow Triggers
```python
# Process assets matching criteria
{
    "workflow": "enhance_quality",
    "filters": {
        "media_type": "image",
        "quality_rating": {"max": 3},
        "tags": ["needs-enhancement"]
    },
    "parameters": {
        "upscale": 2,
        "denoise": true
    }
}
```

## Implementation Guidelines

1. **No String Parsing**: Alice should never parse free-form strings to extract meaning
2. **Explicit Parameters**: Every search criterion should be an explicit parameter
3. **Type Safety**: Use enums for fixed values (media_type, sort_by, etc.)
4. **Validation**: Validate all inputs against schema before processing
5. **Extensibility**: New tag types can be added without API changes

## Migration Path

For existing code with natural language search:

1. Mark natural language methods as deprecated
2. Add structured alternatives
3. Move NLP logic to AI assistant layer
4. Update documentation and examples
5. Remove deprecated methods in next major version

## Benefits

- **Performance**: Structured queries can use indexes efficiently
- **Reliability**: No ambiguity in query interpretation  
- **Testability**: Deterministic behavior for same inputs
- **Maintainability**: Clear contract between AI and Alice layers
- **Flexibility**: Different AI assistants can have different NLP capabilities