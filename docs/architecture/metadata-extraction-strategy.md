# Metadata Extraction Strategy

## Overview

This document outlines the strategy for extracting rich tag:value pairs from media assets to enable powerful search and organization capabilities.

## Evolution: From Tags to Tag:Value Pairs

### Current State: Simple Tags
```python
asset.tags = ["portrait", "cyberpunk", "night", "neon", "female"]
```

### Future State: Structured Tag:Value Pairs
```python
asset.metadata = {
    "subject_type": "portrait",
    "style": "cyberpunk",
    "lighting": ["neon", "dramatic"],
    "time_of_day": "night",
    "gender": "female",
    "mood": "mysterious",
    "color_dominant": "#FF00FF",
    "environment": "urban",
    "camera_angle": "low",
    "shot_type": "medium-shot"
}
```

## Extraction Sources

### 1. AI Generation Parameters
Extract structured data from prompts and generation parameters:

```python
# From prompt: "cyberpunk portrait of a female hacker, neon lighting, night scene, low angle"
extracted = {
    "subject_type": "portrait",
    "style": "cyberpunk",
    "character_role": "hacker",
    "gender": "female",
    "lighting": "neon",
    "time_of_day": "night",
    "camera_angle": "low"
}
```

### 2. Computer Vision Analysis
Use CV models to extract visual features:

```python
# From image analysis
visual_features = {
    "detected_objects": ["person", "computer", "neon_sign"],
    "face_count": 1,
    "dominant_colors": ["#FF00FF", "#00FFFF", "#000033"],
    "composition": "rule_of_thirds",
    "brightness": 0.3,  # 0-1 scale
    "contrast": 0.8,
    "saturation": 0.9
}
```

### 3. EXIF and Technical Metadata
```python
technical = {
    "camera_model": "Canon EOS R5",
    "focal_length": "85mm",
    "aperture": "f/1.4",
    "iso": 400,
    "resolution": "4096x4096",
    "bit_depth": 8,
    "color_space": "sRGB"
}
```

### 4. External AI Analysis (via API)
When enhanced tagging is needed, Alice can request analysis from external AI services:

```python
# Alice sends image to AI service endpoint
# AI service (not Alice) analyzes and returns:
semantic = {
    "narrative": "mysterious",
    "emotion": "contemplative", 
    "artistic_movement": "neo-noir",
    "cultural_reference": "blade-runner",
    "technical_quality": "professional"
}
```

Note: Alice orchestrates the request but doesn't perform AI analysis itself.

## Hierarchical Tag Structure

Some tags should support hierarchical relationships:

```python
{
    "location": "USA/California/Los_Angeles",
    "style": "realism/photorealism",
    "subject": "person/portrait/headshot",
    "genre": "scifi/cyberpunk"
}
```

This enables queries at different specificity levels:
- `location:USA` - All US locations
- `location:USA/California` - Just California
- `location:USA/California/Los_Angeles` - Specific city

## Extraction Pipeline

```python
class MetadataExtractor:
    def extract(self, asset_path: str) -> Dict[str, Any]:
        metadata = {}
        
        # 1. Extract from filename/path
        metadata.update(self.extract_from_path(asset_path))
        
        # 2. Extract from embedded metadata
        metadata.update(self.extract_embedded_metadata(asset_path))
        
        # 3. Extract from AI generation params
        metadata.update(self.extract_ai_params(asset_path))
        
        # 4. Visual analysis (if image/video)
        if is_visual_media(asset_path):
            metadata.update(self.extract_visual_features(asset_path))
        
        # 5. Semantic analysis (expensive, optional)
        if self.enable_semantic_analysis:
            metadata.update(self.extract_semantic_tags(asset_path))
        
        # 6. Normalize and validate
        return self.normalize_metadata(metadata)
```

## Storage Considerations

### Option 1: JSON Column (PostgreSQL)
```sql
CREATE TABLE assets (
    content_hash VARCHAR PRIMARY KEY,
    metadata JSONB,
    -- Create indexes on commonly queried fields
    CREATE INDEX idx_subject ON assets ((metadata->>'subject_type'));
    CREATE INDEX idx_style ON assets ((metadata->>'style'));
);
```

### Option 2: Separate Tag:Value Table
```sql
CREATE TABLE asset_tags (
    content_hash VARCHAR,
    tag_key VARCHAR,
    tag_value VARCHAR,
    confidence FLOAT,
    PRIMARY KEY (content_hash, tag_key, tag_value),
    INDEX idx_tag_lookup (tag_key, tag_value)
);
```

### Option 3: Hybrid Approach
- Store frequently queried tags in columns
- Store rich metadata in JSON
- Use materialized views for complex queries

## Query Examples

### Simple Queries
```sql
-- Find all cyberpunk portraits
SELECT * FROM assets 
WHERE metadata->>'style' = 'cyberpunk' 
AND metadata->>'subject_type' = 'portrait';
```

### Range Queries
```sql
-- Find images with 2-5 people
SELECT * FROM assets 
WHERE (metadata->>'face_count')::int BETWEEN 2 AND 5;
```

### Array Contains
```sql
-- Find images with neon lighting
SELECT * FROM assets 
WHERE metadata->'lighting' ? 'neon';
```

### Complex Queries
```sql
-- Find night scenes with warm colors in urban environments
SELECT * FROM assets 
WHERE metadata->>'time_of_day' = 'night'
AND metadata->>'environment' = 'urban'
AND metadata->>'color_temperature' = 'warm';
```

## Implementation Phases

### Phase 1: Basic Extraction
- Extract from filenames and paths
- Parse AI generation parameters
- Store as simple key:value pairs

### Phase 2: Enhanced Extraction
- Add computer vision analysis
- Implement hierarchical tags
- Add confidence scores

### Phase 3: Semantic Understanding
- AI-assisted tagging
- Relationship extraction
- Cross-reference with knowledge bases

### Phase 4: Advanced Features
- Tag synonyms and aliases
- Multi-language support
- Custom tag schemas per project

## Benefits of Tag:Value Approach

1. **Precise Queries**: Find exactly what you need
2. **Faceted Search**: Filter by multiple dimensions
3. **Analytics**: Understand your content distribution
4. **Automation**: Create rules based on tag combinations
5. **Consistency**: Standardized vocabulary across assets
6. **Extensibility**: Add new tag types without schema changes