# Leonardo.ai Provider

The Leonardo.ai provider enables AI image generation with advanced features like Phoenix, Flux, PhotoReal, and Alchemy models.

## Features

- **Multiple Models**: Phoenix, Flux, PhotoReal, SDXL models
- **Alchemy Enhancement**: Improved quality and resolution
- **Elements System**: Custom style control
- **ControlNet Support**: Advanced image control
- **Image-to-Image**: Use existing images as reference
- **Custom Model Training**: Use your own trained models

## Configuration

### API Key Setup

```bash
# Set via environment variable
export LEONARDO_API_KEY="your-api-key"

# Or use alice keys setup
alice keys setup
```

Get your API key from [Leonardo.ai](https://app.leonardo.ai/api).

## Available Models

### Phoenix Models
- `phoenix` or `phoenix-1.0`: Leonardo Phoenix 1.0 (default)
- `phoenix-0.9`: Leonardo Phoenix 0.9

### Flux Models
- `flux` or `flux-dev`: Flux Dev model
- `flux-schnell`: Flux Schnell (fast generation)

### SDXL Models (Alchemy V2 compatible)
- `vision-xl`: Leonardo Vision XL
- `diffusion-xl`: Leonardo Diffusion XL
- `kino-xl`: Leonardo Kino XL
- `albedo-xl`: AlbedoBase XL

## Parameters

### Basic Parameters
- `num_images`: Number of images to generate (1-8)
- `width`: Image width (512-1536, in 8px increments)
- `height`: Image height (512-1536, in 8px increments)
- `guidance_scale`: Guidance scale (1-30, depends on model)
- `seed`: Seed for reproducible results
- `negative_prompt`: What to avoid in generation

### PhotoReal Parameters
- `photo_real`: Enable PhotoReal mode (true/false)
- `photo_real_version`: "v1" or "v2"
- `preset_style`: CINEMATIC, CREATIVE, VIBRANT, or NONE
- `photo_real_strength`: Strength for PhotoReal v1

### Alchemy Parameters
- `alchemy`: Enable Alchemy enhancement
- `preset_style`: Style preset (see list below)

### Phoenix-Specific Parameters
- `contrast`: Contrast level (1.0-4.5)
- `enhance_prompt`: Enable AI prompt enhancement
- `enhance_prompt_instruction`: Custom enhancement instruction

### Advanced Parameters
- `elements`: List of Element IDs for style control
- `init_image_id`: Image ID for img2img
- `init_strength`: Strength for img2img (0.0-1.0)
- `control_net`: Enable ControlNet
- `control_net_type`: POSE, CANNY, or DEPTH

## Style Presets

### PhotoReal Styles
- CINEMATIC
- CREATIVE
- VIBRANT
- NONE

### Alchemy Styles
- ANIME
- CREATIVE
- DYNAMIC
- ENVIRONMENT
- GENERAL
- ILLUSTRATION
- PHOTOGRAPHY
- RAYTRACED
- RENDER_3D
- SKETCH_BW
- SKETCH_COLOR
- NONE

## Usage Examples

### Basic Image Generation

```python
from alicemultiverse.providers import get_provider
from alicemultiverse.providers.types import GenerationRequest, GenerationType

# Get provider
provider = get_provider("leonardo")

# Create request
request = GenerationRequest(
    prompt="A majestic phoenix rising from flames, digital art",
    generation_type=GenerationType.IMAGE,
    model="phoenix",
    parameters={
        "width": 1024,
        "height": 1024,
        "num_images": 1,
    }
)

# Generate
result = await provider.generate(request)
if result.success:
    print(f"Image saved to: {result.file_path}")
    print(f"Cost: ${result.cost:.3f}")
```

### PhotoReal Generation

```python
# PhotoReal v2 with cinematic style
request = GenerationRequest(
    prompt="Professional portrait of a software developer",
    generation_type=GenerationType.IMAGE,
    model="vision-xl",  # Required for PhotoReal v2
    parameters={
        "photo_real": True,
        "photo_real_version": "v2",
        "preset_style": "CINEMATIC",
        "width": 1024,
        "height": 1024,
    }
)
```

### Alchemy Enhancement

```python
# SDXL model with Alchemy v2
request = GenerationRequest(
    prompt="Epic fantasy landscape with dragons",
    generation_type=GenerationType.IMAGE,
    model="vision-xl",
    parameters={
        "alchemy": True,
        "preset_style": "FANTASY",
        "guidance_scale": 10,
    }
)
```

### Phoenix with Contrast Control

```python
# Phoenix with enhanced contrast
request = GenerationRequest(
    prompt="Cyberpunk city at night, neon lights",
    generation_type=GenerationType.IMAGE,
    model="phoenix",
    parameters={
        "contrast": 3.5,
        "enhance_prompt": True,
        "enhance_prompt_instruction": "Add more dramatic lighting",
    }
)
```

### Using Elements

```python
# First, list available elements
elements = await provider.list_elements()
for elem in elements:
    print(f"{elem['id']}: {elem['name']}")

# Use elements in generation
request = GenerationRequest(
    prompt="Futuristic vehicle design",
    generation_type=GenerationType.IMAGE,
    model="phoenix",
    parameters={
        "elements": ["element-id-1", "element-id-2"],
    }
)
```

## Cost Estimation

Leonardo uses a token-based pricing system:
- 1000 tokens = $1 on standard plan
- Cost varies by model, resolution, and features

```python
# Estimate cost before generation
cost = provider.estimate_cost(request)
print(f"Estimated cost: ${cost:.3f}")
```

### Cost Factors
- **Base model cost**: 15-25 tokens depending on model
- **Resolution**: Higher resolution = higher cost
- **Alchemy**: 1.5x-1.75x multiplier
- **PhotoReal**: Fixed 20 tokens
- **Multiple images**: Linear scaling

## Model Selection Guide

### For Speed
- `flux-schnell`: Fastest generation (~5 seconds)

### For Quality
- `phoenix`: Best overall quality
- `vision-xl` + Alchemy: Maximum quality

### For Photorealism
- PhotoReal v2 with CINEMATIC style

### For Specific Styles
- `kino-xl`: Cinematic/film style
- `albedo-xl`: 3D/rendering style

## Tips and Best Practices

1. **Use Alchemy for Quality**: Enable Alchemy for SDXL models to get 1.75x resolution boost
2. **Contrast with Alchemy**: When using Alchemy with Phoenix, contrast must be 2.5 or higher
3. **PhotoReal v1 vs v2**: 
   - v1: No model ID required, simpler
   - v2: Requires SDXL model, more control
4. **Elements for Style**: Use Elements to maintain consistent style across generations
5. **Batch Generation**: Generate multiple variations with different seeds

## Rate Limits

- 60 requests per minute
- Consider using batch generation (`num_images`) for efficiency

## Error Handling

Common errors:
- **Invalid model**: Check available models with `provider.capabilities.models`
- **Resolution limits**: Max 1536x1536
- **Alchemy requirements**: Some features require specific models
- **API limits**: Respect rate limits to avoid throttling