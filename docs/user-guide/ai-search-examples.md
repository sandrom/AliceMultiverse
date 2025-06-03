# AI-Native Search Examples

This guide shows how I search and organize my AI-generated media through natural conversation with Claude Desktop.

## Setup

Make sure Alice is configured in Claude Desktop:
```json
{
  "mcpServers": {
    "alice": {
      "command": "alice",
      "args": ["mcp-server"]
    }
  }
}
```

## Real Conversation Examples

### Finding Specific Images

```
Me: Hey Claude, can you find all my cyberpunk images with neon lighting?

Claude: I'll search for your cyberpunk images with neon lighting.

[Claude uses search_images tool]

I found 47 cyberpunk images with neon lighting. Here are some highlights:
- 12 character portraits with neon accents
- 8 cityscape scenes with neon signs
- 15 abstract compositions with neon colors
[Shows image grid]

Would you like to see a specific subset or shall I help you select some for a project?
```

### Similarity Search

```
Me: I really like this one [image hash]. Can you find more like it?

Claude: I'll find images similar to the one you selected.

[Claude uses find_similar_assets tool]

Found 23 similar images based on:
- Visual style: Cyberpunk portrait with rim lighting
- Color palette: Purple/cyan neon with dark backgrounds  
- Composition: Close-up character portrait
[Shows similar images]

Me: Perfect! Mark the first 5 as selected for my video project

Claude: I'll track your selections for the video project.

[Claude uses track_selection tool]
```

### Curation Workflow

```
Me: Show me the landscape images from last week. I need to clean up the bad ones.

Claude: I'll show you landscape images from last week.

[Shows images]

Me: These 3 are blurry, and those 2 don't fit my style. Move them out.

Claude: I'll move those 5 images to the sorted-out folder.

[Claude uses soft_delete_image tool]

Moved to sorted-out:
- 3 images → sorted-out/quality-issues/ (blurry)
- 2 images → sorted-out/style-mismatch/

These won't appear in future searches unless you specifically include sorted-out folders.
```

### Understanding Content

```
Me: What's in this batch of images I just generated?

Claude: I'll analyze the content of your recently generated images.

[Claude uses search_images with time filter]

Your recent batch contains:
- **Portraits (18)**: Mix of realistic and stylized characters
  - 8 cyberpunk style with neon lighting
  - 6 fantasy characters with magical elements
  - 4 photorealistic headshots
  
- **Environments (12)**: 
  - 7 sci-fi cityscapes
  - 5 fantasy landscapes
  
- **Abstract (5)**: Geometric patterns with gradient colors

The dominant style is cyberpunk/sci-fi with a purple/cyan color palette.
```

### Cost-Aware Workflow

```
Me: I have 500 new images. What would it cost to run understanding on them?

Claude: Let me calculate the understanding costs for 500 images:

With your current provider configuration:
- OpenAI GPT-4V: ~$2.50 (500 × $0.005 per image)
- Anthropic Claude: ~$1.25 (500 × $0.0025 per image)
- Google Gemini: Free tier should cover it
- Total estimate: ~$3.75

Would you like to:
1. Run understanding on all 500 images
2. Run on a sample first (maybe 50?)
3. Use only free providers (Google)
4. Skip understanding and just organize by metadata
```

### Project-Based Search

```
Me: Show me what I've selected for the "Neon Dreams" video project

Claude: I'll get the selection summary for your "Neon Dreams" project.

[Claude uses get_selection_summary tool]

"Neon Dreams" video project selections:
- **Hero shots (5)**: Main character in different poses
- **Establishing shots (3)**: Wide cityscapes  
- **Transition frames (8)**: Abstract neon patterns
- **B-roll (12)**: Supporting character shots and details

Selection reasons you noted:
- "Perfect mood for opening sequence"
- "Great transition potential with motion"
- "Matches the chorus energy"

Total: 28 images selected across 4 sessions
```

## Advanced Patterns

### Iterative Refinement

```
Me: Show me cyberpunk portraits

[Shows results]

Me: Too much neon. Show me more subtle ones.

[Refines search with exclude_tags: ["high-neon"]]

Me: Better. Now just the ones with single characters.

[Further refinement]

Me: Perfect! These 5 are exactly what I need.
```

### Batch Operations

```
Me: I want to review everything from yesterday's Midjourney session. 
    Show me 10 at a time and I'll tell you which to keep.

Claude: I'll show you yesterday's Midjourney images in batches of 10.

[Shows first 10]

Me: Keep 1, 3, 7. Trash 2, 5. The rest are maybe.

Claude: Tracked your decisions:
- Selected: 3 images (1, 3, 7)
- Rejected: 2 images (2, 5) - moved to sorted-out
- Undecided: 5 images

[Shows next 10...]
```

## Tips for Natural Search

1. **Be conversational**: "Find that moody portrait from last week"
2. **Use descriptive language**: Claude understands style, mood, and content
3. **Iterate naturally**: Start broad, then refine based on what you see
4. **Track your reasoning**: Tell Claude why you're selecting/rejecting
5. **Think in projects**: Group selections by intended use

## No Need for Manual Tagging

The understanding system automatically generates semantic tags when you organize images:
- Content tags: "portrait", "landscape", "cat", "building"
- Style tags: "cyberpunk", "minimalist", "photorealistic"  
- Mood tags: "energetic", "melancholic", "serene"
- Technical tags: "shallow-dof", "high-contrast", "neon-lighting"

These tags are embedded in the image files and indexed for instant search.