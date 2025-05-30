# Adobe Firefly Provider

The Adobe Firefly provider integrates Adobe's generative AI capabilities into AliceMultiverse, offering advanced image generation, editing, and manipulation features.

## Features

- **Text to Image**: Generate images from text prompts using Firefly Image Model 3
- **Generative Fill**: Inpaint specific areas of images with AI-generated content
- **Generative Expand**: Extend images beyond their original boundaries
- **Object Composite**: Combine objects and elements seamlessly
- **Generate Similar**: Create variations of existing images
- **Style Transfer**: Apply artistic styles from reference images
- **Structure Reference**: Use images as structural guides for generation

## Setup

### API Access

Adobe Firefly API is currently under limited availability. Contact your Adobe representative to get access.

### Configuration

Set your Adobe credentials as environment variables:

```bash
export ADOBE_CLIENT_ID="your_client_id"
export ADOBE_CLIENT_SECRET="your_client_secret"
```

Or provide them when initializing the provider:

```python
provider = registry.get_provider("firefly", api_key="client_id:client_secret")
```

## Usage Examples

### Text to Image

```python
from alicemultiverse.providers import get_provider
from alicemultiverse.providers.base import GenerationRequest

# Initialize provider
provider = get_provider("firefly")

# Generate an image
request = GenerationRequest(
    prompt="A futuristic cityscape at sunset with flying cars",
    model="firefly-v3",
    width=1024,
    height=1024,
    num_images=1,
    extra_params={
        "style_preset": "cyberpunk",
        "content_class": "photo",
    }
)

result = await provider.generate(request)
```

### Generative Fill (Inpainting)

```python
# Fill a masked area with AI-generated content
request = GenerationRequest(
    prompt="A red sports car",
    model="firefly-fill",
    width=1024,
    height=1024,
    image=input_image_bytes,  # Original image
    mask=mask_image_bytes,    # Black and white mask
)

result = await provider.generate(request)
```

### Generative Expand (Outpainting)

```python
# Expand an image beyond its boundaries
request = GenerationRequest(
    model="firefly-expand",
    width=2048,  # Larger than original
    height=1536,
    image=input_image_bytes,
    extra_params={
        "placement": {
            "inset": {
                "left": 512,   # Expand 512px to the left
                "right": 512,  # Expand 512px to the right
                "top": 256,    # Expand 256px up
                "bottom": 256  # Expand 256px down
            }
        }
    }
)

result = await provider.generate(request)
```

### Style Reference

```python
# Generate with a style reference image
request = GenerationRequest(
    prompt="A portrait of a cat",
    model="firefly-v3",
    width=1024,
    height=1024,
    extra_params={
        "style_reference": style_image_bytes,
        "style_strength": 75,  # 0-100, higher = stronger style influence
    }
)

result = await provider.generate(request)
```

### Structure Reference

```python
# Use an image as a structural guide
request = GenerationRequest(
    prompt="A modern building",
    model="firefly-v3",
    width=1024,
    height=1024,
    extra_params={
        "structure_reference": structure_image_bytes,
        "structure_strength": 50,  # 0-100
    }
)

result = await provider.generate(request)
```

## Model Aliases

The provider supports several model aliases for convenience:

- `firefly`, `firefly-v3`, `firefly-image-3`: Text to image generation
- `firefly-fill`: Generative fill (inpainting)
- `firefly-expand`: Generative expand (outpainting)
- `firefly-composite`: Object composite
- `firefly-similar`: Generate similar images

## Style Presets

Firefly supports numerous style presets to influence the artistic direction:

**Artistic Styles**: art, watercolor, oil_paint, acrylic_paint, digital_art, 3d, isometric, vector, sketch, doodle, line_art

**Photography Styles**: photo, photography, film, portrait, landscape, still_life, double_exposure

**Color Styles**: b_and_w, cool_colors, warm_colors, muted_colors, vibrant_colors, pastel_colors, golden, monochromatic

**Genre Styles**: pop_art, psychedelic, cyberpunk, steampunk, synthwave, fantasy, sci_fi, anime, manga, comic_book, pixel_art

**Composition Styles**: minimalist, maximalist, chaotic, collage, graffiti, dramatic

## Advanced Features

### Custom Models

If you have access to custom Firefly models:

```python
request = GenerationRequest(
    prompt="Your prompt",
    model="firefly-v3",
    width=1024,
    height=1024,
    extra_params={
        "custom_model": "your-custom-model-id"
    }
)
```

### Tileable Images

Generate seamless patterns:

```python
request = GenerationRequest(
    prompt="Floral wallpaper pattern",
    model="firefly-v3",
    width=512,
    height=512,
    extra_params={
        "tileable": True
    }
)
```

### Region-Specific Content

Generate content relevant to specific regions:

```python
request = GenerationRequest(
    prompt="Traditional festival celebration",
    model="firefly-v3",
    width=1024,
    height=1024,
    extra_params={
        "locale": "ja-JP"  # Japanese content
    }
)
```

## Cost Estimation

- Base cost: ~$0.002 per generation
- Larger images (>1MP): +50% cost
- Image input operations: +20% cost

Actual costs may vary based on your Adobe agreement.

## Limitations

- Maximum image size: 2048x2048 pixels
- API is under limited availability
- Async operations may take 30-60 seconds
- No batch processing support
- Requires authentication for each session

## Error Handling

The provider includes comprehensive error handling:

```python
try:
    result = await provider.generate(request)
except Exception as e:
    if "Authentication failed" in str(e):
        # Handle auth errors
    elif "Generation failed" in str(e):
        # Handle generation errors
    elif "timed out" in str(e):
        # Handle timeout (5 minute limit)
```

## Best Practices

1. **Reuse Provider Instances**: The provider manages authentication tokens automatically
2. **Use Appropriate Models**: Choose the right model alias for your task
3. **Optimize Image Sizes**: Larger images cost more and take longer
4. **Cache Results**: Firefly operations can be expensive; cache when possible
5. **Handle Async Operations**: Some operations return immediately and require polling

## Troubleshooting

### Authentication Issues

Ensure your client ID and secret are correct:

```bash
# Test authentication
curl -X POST https://ims-na1.adobelogin.com/ims/token/v3 \
  -d "grant_type=client_credentials" \
  -d "client_id=YOUR_CLIENT_ID" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "scope=openid,AdobeID,firefly_api"
```

### Slow Generation

- Firefly operations are compute-intensive
- Expect 10-60 seconds for most operations
- Complex operations (expand, fill) take longer
- Consider implementing progress indicators

### Image Upload Failures

- Ensure images are in supported formats (PNG recommended)
- Check image size limits
- Verify network connectivity to Adobe services