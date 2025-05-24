# AI Integration Guide for AliceMultiverse

This guide explains how AI assistants should interact with Alice to manage creative workflows.

## Core Principle

**Alice is the sole orchestration layer between AI and creative tools.** AI assistants communicate exclusively with Alice using structured function calls, never directly accessing files, APIs, or technical systems.

## Integration Architecture

```
User → AI Assistant → Alice (Functions) → Actual Systems
                ↑                             ↓
                └─────── Response ────────────┘
```

## Available Functions

### 1. search_assets
Find assets using creative concepts, not file paths.

```python
# Function signature
search_assets(
    description: str = None,        # "dark moody landscape"
    style_tags: List[str] = None,   # ["cyberpunk", "minimalist"]
    mood_tags: List[str] = None,    # ["energetic", "calm"]
    subject_tags: List[str] = None, # ["portrait", "landscape"]
    time_reference: str = None,     # "last week", "March 2024"
    min_quality_stars: int = None,  # 1-5
    limit: int = 20
) -> AliceResponse
```

### 2. organize_media
Process and organize media files with quality assessment.

```python
organize_media(
    source_path: str = None,        # Defaults to configured inbox
    quality_assessment: bool = True,
    enhanced_metadata: bool = True,
    pipeline: str = "standard"      # "basic", "standard", "premium"
) -> AliceResponse
```

### 3. tag_assets
Add semantic tags to help with future discovery.

```python
tag_assets(
    asset_ids: List[str],           # Required: list of asset IDs
    style_tags: List[str] = None,
    mood_tags: List[str] = None,
    subject_tags: List[str] = None,
    role: str = None                # "hero", "b_roll", "reference"
) -> AliceResponse
```

### 4. find_similar_assets
Find visually or conceptually similar assets.

```python
find_similar_assets(
    asset_id: str,                  # Reference asset
    threshold: float = 0.8          # Similarity threshold (0-1)
) -> AliceResponse
```

### 5. get_asset_info
Get detailed metadata about a specific asset.

```python
get_asset_info(
    asset_id: str
) -> AliceResponse
```

## Integration Patterns

### Pattern 1: Natural Language Search

**User says:** "Show me ethereal portraits with soft lighting"

**AI translates to:**
```python
response = alice.search_assets(
    description="ethereal portraits with soft lighting",
    subject_tags=["portrait"],
    mood_tags=["ethereal", "soft"]
)
```

**AI responds with:** "I found 12 ethereal portraits. The highest rated ones feature dreamy, soft lighting with pastel tones..."

### Pattern 2: Quality-Based Curation

**User says:** "Find my best cyberpunk images for the portfolio"

**AI translates to:**
```python
response = alice.search_assets(
    style_tags=["cyberpunk"],
    min_quality_stars=5,
    sort_by="quality",
    limit=10
)
```

### Pattern 3: Project-Based Workflow

**User says:** "Organize my new renders and prepare them for the sci-fi project"

**AI executes sequence:**
```python
# Step 1: Organize with quality assessment
org_response = alice.organize_media(
    quality_assessment=True,
    enhanced_metadata=True,
    pipeline="standard"
)

# Step 2: Search for sci-fi content from organized files
sci_fi_assets = alice.search_assets(
    style_tags=["sci-fi", "futuristic"],
    min_quality_stars=4
)

# Step 3: Tag for project
alice.tag_assets(
    asset_ids=[a['id'] for a in sci_fi_assets['data']['assets']],
    custom_tags=["sci-fi-project-2024"],
    role="hero"
)
```

## Response Handling

### Always handle responses gracefully:

```python
response = alice.search_assets(description="cyberpunk")

if response['success']:
    assets = response['data']['assets']
    # Format for user...
else:
    error = response['error']
    # Provide helpful feedback...
```

### Never expose technical details:

❌ **Wrong:**
```
"Found file at /Users/john/organized/2024-03-15/project/midjourney/5-star/image_123.png"
```

✅ **Correct:**
```
"Found a 5-star Midjourney image from March 15th with cyberpunk styling"
```

## Complete Integration Example

Here's how an AI assistant might handle a complex request:

```python
class AIAssistant:
    def __init__(self):
        self.alice = AliceInterface()
    
    def handle_request(self, user_input: str):
        # User: "Create a mood board of dark atmospheric images for my horror game"
        
        # 1. Search for appropriate images
        search_response = self.alice.search_assets(
            description="dark atmospheric horror",
            mood_tags=["dark", "ominous", "creepy"],
            style_tags=["atmospheric", "horror"],
            min_quality_stars=4,
            limit=30
        )
        
        if not search_response['success']:
            return "I couldn't find suitable images. Try being more specific."
        
        assets = search_response['data']['assets']
        
        # 2. Categorize by specific moods
        categories = {
            'abandoned': [],
            'supernatural': [],
            'psychological': []
        }
        
        for asset in assets:
            # Use prompt and tags to categorize
            # (In reality, this would use more sophisticated logic)
            if any(tag in asset['tags'] for tag in ['abandoned', 'decay']):
                categories['abandoned'].append(asset)
            # etc...
        
        # 3. Create response for user
        return f"""
I've found {len(assets)} atmospheric horror images for your game mood board:

🏚️ **Abandoned/Decay** ({len(categories['abandoned'])} images)
- Focus on derelict buildings and forgotten places
- Perfect for environment design inspiration

👻 **Supernatural** ({len(categories['supernatural'])} images)  
- Ethereal and otherworldly elements
- Great for creature and effect concepts

🧠 **Psychological** ({len(categories['psychological'])} images)
- Abstract and unsettling imagery
- Ideal for UI/UX horror elements

All images are 4-5 star quality. Would you like me to:
- Create separate collections for each category?
- Find more images in a specific style?
- Search for complementary sound/music references?
"""
```

## Best Practices

1. **Always use asset IDs**, never file paths
2. **Translate technical details** into creative language
3. **Batch operations** when possible for efficiency
4. **Handle errors gracefully** with helpful suggestions
5. **Maintain context** between related requests
6. **Focus on creative intent** rather than technical process

## What NOT to Do

❌ **Don't expose file system details**
```python
# Wrong
"Processing /Users/jane/Downloads/render_001.png"
```

❌ **Don't mention technical implementation**
```python
# Wrong  
"Running BRISQUE algorithm for quality assessment"
```

❌ **Don't bypass Alice to access systems directly**
```python
# Wrong
subprocess.run(['ffmpeg', '-i', 'video.mp4', ...])
```

❌ **Don't expose API keys or credentials**
```python
# Wrong
"Using SightEngine API key sk_live_..."
```

## Testing Your Integration

1. **Verify function calls** match the expected schema
2. **Ensure responses** use creative language only
3. **Test error handling** with invalid inputs
4. **Validate that no file paths** appear in output
5. **Check that asset IDs** are used consistently

## Future Capabilities

As Alice evolves, new functions will be added for:
- Content generation orchestration
- Multi-modal asset creation
- Collaborative workflows
- Real-time creative assistance

The integration pattern will remain the same: AI calls Alice functions, Alice handles the complexity.