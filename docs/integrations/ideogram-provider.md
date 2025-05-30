# Ideogram Provider

The Ideogram provider integrates Ideogram's advanced text-rendering AI capabilities into AliceMultiverse, excelling at typography, logo generation, and images with accurate text.

## Features

- **Superior Text Rendering**: Industry-leading accuracy for text in images
- **Multiple Models**:
  - **V3**: Latest model with best quality (estimated ~$0.10/image)
  - **V2**: Standard quality model ($0.08/image)
  - **V2 Turbo**: Fast generation for ideation ($0.05/image, 7-12 seconds)
- **Style Options**: Realistic, Design, 3D Render, Anime
- **Flexible Aspect Ratios**: Support for extreme ratios (3:1, 1:3)
- **Advanced Features**:
  - Color palette control
  - Magic prompt enhancement
  - Image upscaling
  - Negative prompts

## Setup

### API Access

1. Create an account at [ideogram.ai](https://ideogram.ai)
2. Set up API access (separate from user subscription)
3. Get your API key from the dashboard

### Configuration

```bash
# Set your API key
export IDEOGRAM_API_KEY="your_api_key_here"
```

**Important**: Image URLs from Ideogram expire! Always download and save images immediately.

## Usage Examples

### Text-Heavy Logo Generation

```python
from alicemultiverse.providers import get_provider
from alicemultiverse.providers.types import GenerationRequest, GenerationType

# Initialize provider
provider = get_provider("ideogram")

# Generate a logo with text
request = GenerationRequest(
    prompt="Modern minimalist logo for 'TechVision AI' company, "
           "clean typography, blue and white color scheme",
    generation_type=GenerationType.IMAGE,
    model="ideogram-v3",  # Best quality for text
    parameters={
        "style": "design",
        "aspect_ratio": "1:1",  # Square for logos
        "negative_prompt": "complex, cluttered, hard to read",
        "number_of_images": 4,  # Generate variations
    }
)

result = await provider.generate(request)
print(f"Logo saved to: {result.file_path}")
print(f"Cost: ${result.cost}")  # $0.40 for 4 images
```

### Fast Ideation with Turbo Model

```python
# Quick sketches and concepts
request = GenerationRequest(
    prompt="Restaurant menu design with 'Daily Specials' header",
    generation_type=GenerationType.IMAGE,
    model="turbo",  # Fast generation
    parameters={
        "style": "design",
        "aspect_ratio": "4:3",
        "magic_prompt_option": "AUTO",  # Enhance prompt
    }
)

result = await provider.generate(request)
# Generated in ~10 seconds
```

### Typography Poster

```python
# Create a typographic poster
request = GenerationRequest(
    prompt="Motivational poster with text 'Dream Big, Work Hard' "
           "in bold modern typography, gradient background",
    generation_type=GenerationType.IMAGE,
    model="ideogram-v2",
    parameters={
        "style": "design",
        "aspect_ratio": "9:16",  # Portrait for posters
        "color_palette": ["#FF6B6B", "#4ECDC4", "#45B7D1"],
        "number_of_images": 2,
    }
)

result = await provider.generate(request)
```

### 3D Text Rendering

```python
# 3D text effect
request = GenerationRequest(
    prompt="3D metallic text saying 'INNOVATION' with dramatic lighting",
    generation_type=GenerationType.IMAGE,
    model="ideogram-v3",
    parameters={
        "style": "3d",  # or "render_3d"
        "aspect_ratio": "16:9",
        "seed": 42,  # For reproducibility
    }
)

result = await provider.generate(request)
```

### Anime Style with Text

```python
# Anime poster with Japanese text
request = GenerationRequest(
    prompt="Anime movie poster with title '未来の戦士' (Future Warrior), "
           "dramatic character pose, vibrant colors",
    generation_type=GenerationType.IMAGE,
    model="ideogram-v2",
    parameters={
        "style": "anime",
        "aspect_ratio": "2:3",  # Typical poster ratio
    }
)

result = await provider.generate(request)
```

### Upscaling Generated Images

```python
# First generate an image
result = await provider.generate(request)

# Then upscale it
if result.success and result.file_path:
    upscaled_result = await provider.upscale_image(
        result.file_path,
        resolution="2048x2048"
    )
    print(f"Upscaled image: {upscaled_result.file_path}")
    # Additional $0.02 for upscaling
```

## Model Comparison

| Model | Speed | Quality | Text Accuracy | Cost | Best For |
|-------|-------|---------|---------------|------|----------|
| V3 | Slow | Highest | Excellent | $0.10 | Final designs, logos |
| V2 | Medium | High | Very Good | $0.08 | General use |
| V2 Turbo | Fast | Good | Good | $0.05 | Ideation, drafts |

## Style Guide

### Design Style
Best for: Logos, posters, UI mockups, marketing materials
```python
parameters={"style": "design"}
```

### Realistic Style
Best for: Product mockups, scene compositions with text
```python
parameters={"style": "realistic"}
```

### 3D Render Style
Best for: 3D text effects, dimensional typography
```python
parameters={"style": "3d"}
```

### Anime Style
Best for: Manga covers, anime posters, stylized text
```python
parameters={"style": "anime"}
```

## Advanced Features

### Color Palette Control

```python
# Specify exact colors for brand consistency
parameters={
    "color_palette": ["#1E88E5", "#FFC107", "#E91E63"],
    "style": "design",
}
```

### Magic Prompt Enhancement

```python
# Let Ideogram enhance your prompt
parameters={
    "magic_prompt_option": "ON",  # Force enhancement
    # or "OFF" to use exact prompt
    # or "AUTO" (default) to let Ideogram decide
}
```

### Extreme Aspect Ratios

```python
# Banner or header design
parameters={"aspect_ratio": "3:1"}  # Ultra-wide

# Mobile story format
parameters={"aspect_ratio": "1:3"}  # Ultra-tall
```

## Best Practices

1. **Be Specific About Text**: Always put the exact text you want in quotes within your prompt
   ```python
   prompt="Logo with text 'ACME Corp' in bold sans-serif font"
   ```

2. **Use Appropriate Models**:
   - V3 for final designs requiring perfect text
   - Turbo for quick iterations and concepts
   - V2 for balanced speed/quality

3. **Download Immediately**: Ideogram URLs expire! Always save images right after generation

4. **Leverage Styles**: Match style to your use case for best results

5. **Multiple Generations**: Generate 2-4 variations to get the best result

## Common Use Cases

### Business Cards
```python
prompt="Business card design for 'Jane Smith, CEO' with contact info, minimalist style"
parameters={"style": "design", "aspect_ratio": "16:9"}
```

### Social Media Posts
```python
prompt="Instagram post with text 'Summer Sale 50% Off' in trendy typography"
parameters={"style": "design", "aspect_ratio": "1:1"}
```

### Book Covers
```python
prompt="Book cover for 'The Last Algorithm' sci-fi novel, futuristic typography"
parameters={"style": "realistic", "aspect_ratio": "2:3"}
```

## Troubleshooting

### Text Not Rendering Correctly
- Put important text in quotes: `"Your Text Here"`
- Use simpler fonts for Turbo model
- Try V3 model for complex typography

### Expired Image URLs
```python
# Always download immediately after generation
if result.success and "url" in result.metadata:
    # Image is already downloaded and saved by the provider
    print(f"Image saved locally: {result.file_path}")
```

### Rate Limiting
- Default: 10 concurrent requests
- Implement retry logic for 429 errors
- Contact partnership@ideogram.ai for higher limits

## Cost Optimization

1. **Use Turbo for Drafts**: At $0.05/image, iterate quickly with Turbo
2. **Batch Variations**: Request multiple images in one call
3. **Skip Upscaling**: Only upscale final selections (+$0.02 each)
4. **Cache Results**: Ideogram images are deterministic with seeds

## API Limitations

- Images expire - must download immediately
- No direct image editing (use remix endpoint for variations)
- Text length limits vary by style and complexity
- Some unicode characters may not render perfectly

## Volume Pricing

For high-volume usage (>1M images/month), contact partnership@ideogram.ai for:
- Custom models trained for your brand
- Volume discounts
- Higher rate limits
- Priority support