# Search API Specification

## Overview

This document specifies the structured search API for AliceMultiverse. All search operations must use structured parameters - natural language processing happens at the AI assistant layer, not in Alice.

## Core Types

### MediaType (Enum)
```python
class MediaType(str, Enum):
    IMAGE = "image"
    VIDEO = "video" 
    AUDIO = "audio"
    DOCUMENT = "document"
    UNKNOWN = "unknown"
```

### Tag System Evolution

We're transitioning from simple tags to tag:value pairs for more expressive metadata:

#### Simple Tags (Current)
```
["portrait", "cyberpunk", "dark", "high-detail"]
```

#### Tag:Value Pairs (Future Direction)
```
{
  "subject": "portrait",
  "style": "cyberpunk", 
  "mood": "dark",
  "lighting": "neon",
  "color_palette": "blue-purple",
  "quality": "high-detail",
  "camera_angle": "low-angle",
  "time_of_day": "night",
  "environment": "urban",
  "character_count": "1",
  "gender": "female",
  "age_appearance": "young-adult"
}
```

This enables much more powerful queries:
- Find all portraits with `lighting:neon` and `mood:dark`
- Search for `environment:forest` with `time_of_day:sunset`
- Filter by `character_count:>2` or `age_appearance:elderly`

Common tag keys might include:
- **Visual**: `style`, `mood`, `lighting`, `color_palette`, `composition`
- **Subject**: `subject_type`, `character_count`, `gender`, `age_appearance`, `species`
- **Scene**: `environment`, `time_of_day`, `weather`, `season`, `location`
- **Technical**: `render_style`, `quality_level`, `camera_angle`, `shot_type`
- **Creative**: `theme`, `genre`, `emotion`, `narrative_element`

## Search Request Schema

```typescript
interface SearchRequest {
  filters: SearchFilters;
  sort_by?: SortField;
  order?: SortOrder;
  limit?: number;  // Default: 50, Max: 1000
  offset?: number; // Default: 0
}

interface SearchFilters {
  // Technical filters
  media_type?: MediaType;
  file_formats?: string[];
  file_size?: RangeFilter;
  dimensions?: DimensionFilter;
  quality_rating?: RangeFilter;
  
  // Semantic filters (current: simple tags)
  tags?: string[];         // AND operation
  any_tags?: string[];     // OR operation
  exclude_tags?: string[]; // NOT operation
  
  // Semantic filters (future: tag:value pairs)
  tag_values?: Record<string, string | string[]>;  // Exact match
  tag_ranges?: Record<string, RangeFilter>;        // Numeric ranges
  tag_patterns?: Record<string, string>;           // Regex patterns
  
  // Metadata filters
  ai_source?: AISource[];
  project?: string;
  content_hash?: string;
  has_metadata?: string[];
  
  // Temporal filters
  date_range?: DateRange;
  
  // Text search (structured)
  filename_pattern?: string; // Regex pattern
  prompt_keywords?: string[]; // Keywords in prompt
}
```

## Filter Types

### RangeFilter
```typescript
interface RangeFilter {
  min?: number;
  max?: number;
}
```

### DimensionFilter
```typescript
interface DimensionFilter {
  width?: RangeFilter;
  height?: RangeFilter;
  aspect_ratio?: RangeFilter; // e.g., 1.77 for 16:9
}
```

### DateRange
```typescript
interface DateRange {
  start?: string; // ISO 8601 date
  end?: string;   // ISO 8601 date
}
```

## Response Schema

```typescript
interface SearchResponse {
  total_count: number;
  results: Asset[];
  facets?: SearchFacets;
  query_time_ms: number;
}

interface Asset {
  content_hash: string;
  file_path: string;
  media_type: MediaType;
  file_size: number;
  
  // Metadata
  tags: string[];
  ai_source?: string;
  quality_rating?: number;
  
  // Timestamps
  created_at: string;
  modified_at: string;
  discovered_at: string;
  
  // Additional metadata
  metadata: {
    dimensions?: { width: number; height: number };
    prompt?: string;
    generation_params?: Record<string, any>;
    [key: string]: any;
  };
}

interface SearchFacets {
  tags: { tag: string; count: number }[];
  ai_sources: { source: string; count: number }[];
  quality_ratings: { rating: number; count: number }[];
  media_types: { type: string; count: number }[];
}
```

## Example Queries

### 1. Find High-Quality Portraits
```json
{
  "filters": {
    "media_type": "image",
    "tags": ["portrait"],
    "quality_rating": { "min": 4 }
  },
  "sort_by": "quality_rating",
  "order": "desc",
  "limit": 20
}
```

### 2. Recent Cyberpunk Images Excluding NSFW
```json
{
  "filters": {
    "media_type": "image",
    "tags": ["cyberpunk"],
    "exclude_tags": ["nsfw", "explicit"],
    "date_range": {
      "start": "2024-05-01"
    }
  },
  "sort_by": "created_date",
  "order": "desc"
}
```

### 3. Find Specific Generation Parameters
```json
{
  "filters": {
    "ai_source": ["stable-diffusion"],
    "has_metadata": ["prompt", "seed", "cfg_scale"],
    "prompt_keywords": ["fantasy", "dragon"]
  }
}
```

### 4. Complex Multi-Tag Query
```json
{
  "filters": {
    "media_type": "image",
    "tags": ["character", "fantasy"],
    "any_tags": ["elf", "wizard", "warrior"],
    "exclude_tags": ["sketch", "wip"],
    "quality_rating": { "min": 3 },
    "dimensions": {
      "width": { "min": 1024 },
      "aspect_ratio": { "min": 0.8, "max": 1.2 }
    }
  }
}
```

### 5. Tag:Value Pair Query (Future)
```json
{
  "filters": {
    "media_type": "image",
    "tag_values": {
      "subject": "portrait",
      "style": ["cyberpunk", "noir"],
      "lighting": "neon",
      "mood": "mysterious"
    },
    "tag_ranges": {
      "character_count": { "min": 1, "max": 3 }
    },
    "quality_rating": { "min": 4 }
  }
}
```

### 6. Advanced Tag:Value Query (Future)
```json
{
  "filters": {
    "media_type": "image",
    "tag_values": {
      "environment": "urban",
      "time_of_day": ["night", "twilight"],
      "weather": "rain"
    },
    "tag_patterns": {
      "color_palette": ".*blue.*"  // Contains blue
    },
    "exclude_tags": ["wip", "test"]
  }
}
```

## Implementation Notes

1. **Tag Matching**: 
   - Tags are case-insensitive
   - Exact match only (no partial matching)
   - Use stemming/aliases at the AI layer if needed

2. **Performance**:
   - Create indexes on commonly filtered fields
   - Use faceted search for tag discovery
   - Cache frequent queries

3. **Validation**:
   - Validate all enum values
   - Ensure date ranges are valid
   - Limit result set sizes

4. **Extensibility**:
   - New filter types can be added to SearchFilters
   - New metadata fields don't break existing queries
   - Facets help discover available tags

## Anti-Patterns to Avoid

❌ **Don't do this:**
```python
# Natural language in search
alice.search("cyberpunk portraits from last week")

# Mixing technical and semantic
alice.search_by_type("portrait")  # "portrait" is not a type!

# Unstructured tag strings
alice.search(tags="cyberpunk AND portrait NOT sketch")
```

✅ **Do this instead:**
```python
# Structured search
alice.search_assets({
    "filters": {
        "media_type": "image",
        "tags": ["cyberpunk", "portrait"],
        "exclude_tags": ["sketch"],
        "date_range": {"start": "2024-05-19"}
    }
})