# FLUX Kontext Multi-Reference Guide

The multi-reference variants of FLUX Kontext allow you to combine elements from multiple images into a single coherent generation.

## Overview

Multi-reference models excel at:
- **Style mixing** from multiple sources
- **Character fusion** combining features from different references
- **Scene composition** using elements from various images
- **Consistent theming** across diverse references
- **Weighted blending** with customizable influence per image

## Multi-Reference Models

```python
# Available multi-reference models
"flux-kontext-pro-multi"  # Fast multi-reference synthesis
"flux-kontext-max-multi"  # Premium quality with multiple references
```

## Basic Multi-Reference Usage

```python
from alicemultiverse.providers import get_provider, GenerationRequest, GenerationType

provider = get_provider("fal")

# Combine multiple reference images
request = GenerationRequest(
    prompt="A warrior combining the armor styles from all references",
    generation_type=GenerationType.IMAGE,
    model="flux-kontext-pro-multi",
    reference_assets=[
        "https://example.com/medieval_armor.jpg",
        "https://example.com/futuristic_suit.jpg",
        "https://example.com/samurai_armor.jpg"
    ],
    parameters={
        "num_inference_steps": 28,
        "guidance_scale": 3.5,
    }
)

result = await provider.generate(request)
```

## Weighted References

Control the influence of each reference image:

```python
request = GenerationRequest(
    prompt="Blend these character designs with emphasis on the first",
    model="flux-kontext-max-multi",
    reference_assets=[
        "character1.jpg",  # Main reference
        "character2.jpg",  # Secondary elements
        "character3.jpg"   # Minor details
    ],
    reference_weights=[2.0, 1.0, 0.5],  # Relative importance
    parameters={
        "num_inference_steps": 50,  # Higher for better blending
    }
)
```

## Use Cases

### 1. Character Design Fusion

Combine character features from multiple references:

```python
# Create a new character combining traits
request = GenerationRequest(
    prompt="Create a character with the face from first image, outfit from second, and pose from third",
    model="flux-kontext-pro-multi",
    reference_assets=[
        "face_reference.jpg",
        "outfit_reference.jpg",
        "pose_reference.jpg"
    ],
    reference_weights=[1.5, 1.2, 1.0]
)
```

### 2. Style Interpolation

Blend artistic styles from different sources:

```python
# Mix art styles
request = GenerationRequest(
    prompt="Paint a landscape combining these artistic styles",
    model="flux-kontext-max-multi",
    reference_assets=[
        "van_gogh_style.jpg",
        "monet_style.jpg",
        "modern_digital_art.jpg"
    ],
    reference_weights=[1.0, 1.0, 1.0]  # Equal blending
)
```

### 3. Scene Composition

Build complex scenes using elements from multiple images:

```python
# Compose a scene
request = GenerationRequest(
    prompt="Create a fantasy scene using the castle from first image, creatures from second, and sky from third",
    model="flux-kontext-max-multi",
    reference_assets=[
        "castle_reference.jpg",
        "fantasy_creatures.jpg",
        "dramatic_sky.jpg"
    ],
    parameters={
        "guidance_scale": 4.0,  # Higher for more literal interpretation
    }
)
```

### 4. Product Design Iteration

Combine product features from different designs:

```python
# Product design fusion
request = GenerationRequest(
    prompt="Design a shoe combining the sole from first, upper from second, and colorway from third",
    model="flux-kontext-pro-multi",
    reference_assets=[
        "shoe_sole_design.jpg",
        "shoe_upper_design.jpg",
        "shoe_colorway.jpg"
    ]
)
```

## Advanced Techniques

### Progressive Refinement

Use multi-reference for iterative improvements:

```python
# Start with broad concepts
initial = await provider.generate(GenerationRequest(
    prompt="Futuristic vehicle design",
    model="flux-kontext-pro-multi",
    reference_assets=["car1.jpg", "car2.jpg", "spaceship.jpg"],
    reference_weights=[1.0, 1.0, 0.5]
))

# Refine with more specific references
refined = await provider.generate(GenerationRequest(
    prompt="Refine the vehicle with these detail references",
    model="flux-kontext-max-multi",
    reference_assets=[
        initial.file_path,  # Previous result
        "detail_reference1.jpg",
        "detail_reference2.jpg"
    ],
    reference_weights=[2.0, 1.0, 1.0]  # Emphasize continuity
))
```

### Style Transfer Grid

Create variations with different weight combinations:

```python
# Generate multiple variants
variants = []
weight_combinations = [
    [2.0, 1.0, 0.5],
    [1.0, 2.0, 0.5],
    [0.5, 1.0, 2.0],
    [1.0, 1.0, 1.0]
]

for weights in weight_combinations:
    result = await provider.generate(GenerationRequest(
        prompt="Artistic portrait in mixed styles",
        model="flux-kontext-pro-multi",
        reference_assets=references,
        reference_weights=weights
    ))
    variants.append(result)
```

## Best Practices

### 1. Reference Selection
- Choose references with clear, distinct elements
- Avoid too similar references (wastes potential)
- Consider complementary rather than conflicting styles

### 2. Weight Tuning
- Start with equal weights (1.0 each)
- Increase weight for dominant references
- Use fractional weights (0.5) for subtle influence

### 3. Prompt Engineering
- Be specific about what to take from each reference
- Use positional language ("first image", "second reference")
- Describe desired blending approach

### 4. Quality Settings
```python
# For best results with multi-reference
parameters = {
    "num_inference_steps": 50,  # Higher than single reference
    "guidance_scale": 3.5,      # Balanced creativity/adherence
    "num_images": 4             # Generate variants
}
```

## Limitations and Tips

### Current Limitations
- Maximum 3-5 reference images (provider dependent)
- Processing time increases with reference count
- Some style conflicts may produce artifacts

### Pro Tips
1. **Order matters**: First reference often has more influence
2. **Resolution matching**: Use similar resolution references
3. **Semantic alignment**: References should be conceptually compatible
4. **Iterative approach**: Use outputs as new references

## Cost Optimization

Multi-reference models cost slightly more:
- `flux-kontext-pro-multi`: ~$0.07 per generation
- `flux-kontext-max-multi`: ~$0.09 per generation

Optimize by:
- Testing with Pro before using Max
- Reusing successful combinations
- Batch processing similar requests

## Integration with Alice

Alice can manage multi-reference workflows:

```python
# Using Alice orchestrator
from alicemultiverse.interface import AliceOrchestrator

alice = AliceOrchestrator()

# Search for reference assets
style_refs = await alice.search_assets({
    "tags": {"style": ["cyberpunk", "neon"]},
    "limit": 3
})

# Generate with found references
result = await alice.generate_creative_asset({
    "prompt": "Blend these cyberpunk styles",
    "model": "flux-kontext-pro-multi",
    "reference_assets": [asset['id'] for asset in style_refs]
})
```