# Google AI Provider (Imagen & Veo)

The Google AI provider integrates Google's cutting-edge generative AI models into AliceMultiverse, offering both image generation with Imagen 3 and video generation with Veo 2.

## Features

- **Imagen 3**: State-of-the-art text-to-image generation
  - High quality, detailed images with rich lighting
  - Natural language understanding without complex prompting
  - Wide range of styles from photorealistic to artistic
  - SynthID watermarking for AI-generated content identification

- **Veo 2**: Advanced video generation
  - 8-second video clips from text or image prompts
  - Text-to-video and image-to-video capabilities
  - Realistic physics simulation
  - Multiple aspect ratio support

## Setup

### Option 1: Gemini API (Recommended)

The easiest way to get started is through the Gemini API:

```bash
# Set your Gemini API key
export GEMINI_API_KEY="your_api_key_here"
# or
export GOOGLE_AI_API_KEY="your_api_key_here"
```

Get your API key from [Google AI Studio](https://aistudio.google.com/).

### Option 2: Vertex AI (Advanced)

For enterprise users with Google Cloud Platform:

```bash
# Set up authentication
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/service-account-key.json"
export GOOGLE_CLOUD_PROJECT="your-project-id"
```

## Usage Examples

### Text-to-Image with Imagen 3

```python
from alicemultiverse.providers import get_provider
from alicemultiverse.providers.types import GenerationRequest, GenerationType

# Initialize provider
provider = get_provider("google-ai")

# Generate an image
request = GenerationRequest(
    prompt="A serene Japanese tea garden with cherry blossoms",
    generation_type=GenerationType.IMAGE,
    model="imagen-3",
    parameters={
        "number_of_images": 1,
        "aspect_ratio": "16:9",
        "negative_prompt": "cartoon, anime",
    }
)

result = await provider.generate(request)
print(f"Generated image saved to: {result.file_path}")
print(f"Cost: ${result.cost}")  # $0.03 per image
```

### Multiple Images with Different Aspect Ratios

```python
# Generate multiple variations
request = GenerationRequest(
    prompt="A futuristic cityscape at sunset",
    generation_type=GenerationType.IMAGE,
    model="imagen-3",
    parameters={
        "number_of_images": 4,  # Up to 4 images
        "aspect_ratio": "9:16",  # Portrait for mobile
        "seed": 42,  # For reproducibility
    }
)

result = await provider.generate(request)
```

### Text-to-Video with Veo 2

```python
# Generate a video from text
request = GenerationRequest(
    prompt="A hummingbird hovering near colorful flowers, slow motion",
    generation_type=GenerationType.VIDEO,
    model="veo-2",
    parameters={
        "aspect_ratio": "16:9",  # Landscape video
        "negative_prompt": "low quality, blurry",
    }
)

result = await provider.generate(request)
print(f"Generated 8-second video: {result.file_path}")
```

### Image-to-Video Animation

```python
# Animate an existing image
with open("sunset.jpg", "rb") as f:
    image_data = f.read()

request = GenerationRequest(
    prompt="Gentle waves and moving clouds",  # Describe the motion
    generation_type=GenerationType.VIDEO,
    model="veo-2",
    reference_assets=["sunset.jpg"],
    parameters={
        "image_data": image_data,
        "aspect_ratio": "16:9",
    }
)

result = await provider.generate(request)
```

### Using Vertex AI Backend

```python
from alicemultiverse.providers.google_ai_provider import GoogleAIProvider, GoogleAIBackend

# Initialize with Vertex AI
provider = GoogleAIProvider(
    api_key="your_access_token",  # Or use service account
    backend=GoogleAIBackend.VERTEX,
    project_id="my-gcp-project",
    location="us-central1"
)

# Use the same as above
request = GenerationRequest(
    prompt="A majestic mountain landscape",
    generation_type=GenerationType.IMAGE,
    model="imagen-3",
)

result = await provider._generate(request)
```

## Model Aliases

The provider supports convenient aliases:

- **Imagen**: `imagen`, `imagen-3`, `imagen-3.0`, `imagen-3-fast`
- **Veo**: `veo`, `veo-2`, `veo-001`
- **Provider**: `google`, `google-ai`, `gemini`, `imagen`, `veo`

## Supported Parameters

### Imagen Parameters

- `number_of_images`: 1-4 images per request
- `aspect_ratio`: "1:1", "16:9", "9:16", "4:3", "3:4"
- `negative_prompt`: What to avoid in the generation
- `seed`: For reproducible results

### Veo Parameters

- `aspect_ratio`: "16:9" (landscape) or "9:16" (portrait)
- `negative_prompt`: What to avoid in the video
- `seed`: For reproducible results
- `image_data`: For image-to-video generation

## Pricing

- **Imagen 3**: $0.03 per image
- **Imagen 3 Fast**: $0.02 per image (lower quality, faster)
- **Veo 2**: ~$0.10 per 8-second video (estimated)

## Best Practices

1. **Natural Language Prompts**: Imagen 3 understands natural language well, so write prompts as you would describe to a person.

2. **Aspect Ratios**: Choose appropriate aspect ratios for your use case:
   - "1:1" for social media posts
   - "16:9" for landscape/desktop
   - "9:16" for mobile/stories

3. **Negative Prompts**: Use negative prompts to avoid unwanted elements rather than trying to over-specify in the main prompt.

4. **Batch Generation**: Generate up to 4 images at once for variations and better selection.

5. **SynthID Watermarking**: All Imagen 3 outputs include invisible watermarks. This is automatic and helps identify AI-generated content.

## Limitations

- **Image Size**: Maximum 2048x2048 pixels for Imagen
- **Video Duration**: Fixed 8-second clips for Veo 2
- **API Access**: Imagen 3 requires paid tier on Gemini API
- **Person Generation**: May require approval for generating people/children
- **Rate Limits**: Subject to API rate limits based on your tier

## Troubleshooting

### Authentication Issues

**Gemini API**:
```bash
# Check if API key is set
echo $GEMINI_API_KEY

# Test with curl
curl -H "x-goog-api-key: $GEMINI_API_KEY" \
  "https://generativelanguage.googleapis.com/v1beta/models"
```

**Vertex AI**:
```bash
# Check project and credentials
gcloud config get-value project
gcloud auth application-default print-access-token
```

### Common Errors

1. **"API key not valid"**: Ensure you have billing enabled for Gemini API
2. **"Quota exceeded"**: Check your API quotas in Google Cloud Console
3. **"Person generation blocked"**: Contact Google for approval if needed
4. **"Invalid aspect ratio"**: Use only supported ratios for each model

## Advanced Features

### Custom Safety Settings

```python
# In future versions
parameters={
    "safety_settings": {
        "harassment": "BLOCK_ONLY_HIGH",
        "hate_speech": "BLOCK_MEDIUM_AND_ABOVE",
    }
}
```

### Batch Processing

```python
# Generate multiple prompts efficiently
prompts = [
    "A serene lake at dawn",
    "A bustling city street",
    "A cozy cabin in the woods",
]

for prompt in prompts:
    request = GenerationRequest(
        prompt=prompt,
        generation_type=GenerationType.IMAGE,
        model="imagen-3",
    )
    result = await provider.generate(request)
```