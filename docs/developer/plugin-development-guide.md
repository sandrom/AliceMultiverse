# Plugin Development Guide

AliceMultiverse provides a flexible plugin system that allows you to extend its functionality without modifying core code. This guide covers everything you need to know about developing custom plugins.

## Overview

The plugin system supports four types of plugins:

1. **Provider Plugins** - Add new AI generation providers (image, video, audio, text)
2. **Effect Plugins** - Apply transformations or enhancements to media
3. **Analyzer Plugins** - Analyze content and provide insights
4. **Workflow Plugins** - Orchestrate complex multi-step processes

## Getting Started

### Quick Start

Create a new plugin template:

```bash
alice plugins create effect my_custom_effect
```

This creates a plugin file with all the boilerplate code you need.

### Plugin Structure

Every plugin must:
1. Inherit from the appropriate base class
2. Implement required methods
3. Define metadata including name, version, and dependencies

```python
from alicemultiverse.plugins.base import EffectPlugin, PluginMetadata, PluginType

class MyEffectPlugin(EffectPlugin):
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="my_effect",
            version="1.0.0",
            type=PluginType.EFFECT,
            description="My custom effect",
            author="Your Name",
            dependencies=["pillow", "numpy"]
        )
```

## Plugin Types

### Provider Plugins

Add support for new AI generation services:

```python
class CustomProviderPlugin(ProviderPlugin):
    async def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Generate content using your provider."""
        prompt = request.get("prompt")
        model = request.get("model", "default")
        
        # Call your API
        result = await self.call_api(prompt, model)
        
        return {
            "success": True,
            "file_path": result.output_path,
            "cost": result.cost,
            "metadata": {"model": model}
        }
```

### Effect Plugins

Transform or enhance images:

```python
class BlurEffectPlugin(EffectPlugin):
    async def apply(
        self, 
        input_path: Path, 
        output_path: Path, 
        parameters: Dict[str, Any]
    ) -> Path:
        """Apply blur effect to image."""
        image = cv2.imread(str(input_path))
        
        radius = parameters.get("radius", 5)
        blurred = cv2.GaussianBlur(image, (radius, radius), 0)
        
        cv2.imwrite(str(output_path), blurred)
        return output_path
```

### Analyzer Plugins

Extract insights from content:

```python
class ColorAnalyzerPlugin(AnalyzerPlugin):
    async def analyze(
        self, 
        inputs: List[Path], 
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Analyze color distribution."""
        colors = []
        
        for img_path in inputs:
            dominant_colors = self.extract_colors(img_path)
            colors.extend(dominant_colors)
        
        return {
            "success": True,
            "dominant_colors": colors,
            "color_harmony": self.check_harmony(colors)
        }
```

### Workflow Plugins

Orchestrate complex processes:

```python
class StyleTransferWorkflow(WorkflowPlugin):
    async def execute(
        self,
        inputs: Dict[str, Any],
        output_dir: Path,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute style transfer workflow."""
        # 1. Analyze source style
        style_features = await self.analyze_style(inputs["style_image"])
        
        # 2. Apply to target images
        results = []
        for target in inputs["target_images"]:
            result = await self.transfer_style(target, style_features)
            results.append(result)
        
        return {
            "success": True,
            "processed_count": len(results),
            "outputs": results
        }
```

## Configuration

### Schema Definition

Define configuration options in your metadata:

```python
config_schema={
    "api_key": {
        "type": "string",
        "required": True,
        "description": "API key for the service"
    },
    "timeout": {
        "type": "integer",
        "default": 30,
        "minimum": 1,
        "maximum": 300
    },
    "quality": {
        "type": "string",
        "enum": ["low", "medium", "high"],
        "default": "medium"
    }
}
```

### Using Configuration

Access configuration in your plugin:

```python
async def initialize(self) -> bool:
    self.api_key = self.config.get("api_key")
    if not self.api_key:
        logger.error("API key required")
        return False
    
    self.timeout = self.config.get("timeout", 30)
    return True
```

## Built-in Plugins

AliceMultiverse includes several built-in plugins as examples:

### Effects
- **upscale_effect** - Image upscaling with multiple algorithms
- **style_transfer** - Artistic style transfer
- **filter_effect** - Artistic filters (vintage, noir, etc.)
- **watermark_effect** - Add text or image watermarks

### Analyzers
- **style_consistency_analyzer** - Check visual consistency across images

### Workflows
- **batch_enhancement_workflow** - Apply multiple effects to image batches

## Plugin Management

### Loading Plugins

Load a plugin from file:
```bash
alice plugins load path/to/my_plugin.py --config config.yaml
```

Load from module:
```bash
alice plugins load mypackage.plugins.custom_effect
```

### Configuration Management

Set plugin configuration:
```bash
alice plugins set-config my_effect config.yaml
```

View current configuration:
```bash
alice plugins config my_effect
```

### Using Plugins

Apply an effect:
```bash
alice plugins apply-effect blur_effect image.jpg -o output/ -p '{"radius": 10}'
```

Use in MCP tools:
```python
# Through MCP
result = await use_plugin_provider(
    plugin_name="custom_ai_provider",
    prompt="A beautiful sunset",
    model="pro"
)
```

## Best Practices

### 1. Error Handling

Always handle errors gracefully:

```python
async def apply(self, input_path: Path, output_path: Path, parameters: Dict[str, Any]) -> Path:
    try:
        # Your code here
        return output_path
    except Exception as e:
        logger.error(f"Effect failed: {e}")
        raise RuntimeError(f"Failed to apply effect: {str(e)}")
```

### 2. Resource Management

Clean up resources properly:

```python
async def cleanup(self):
    """Release any resources."""
    if hasattr(self, 'session'):
        await self.session.close()
    self._initialized = False
```

### 3. Validation

Validate inputs and parameters:

```python
def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
    if "image_paths" not in inputs:
        return False
    
    for path in inputs["image_paths"]:
        if not Path(path).exists():
            logger.error(f"File not found: {path}")
            return False
    
    return True
```

### 4. Logging

Use structured logging:

```python
logger.info("Processing image", extra={
    "plugin": self.metadata.name,
    "input": str(input_path),
    "parameters": parameters
})
```

## Advanced Topics

### Async Operations

All plugin methods are async for better performance:

```python
async def process_batch(self, images: List[Path]) -> List[Path]:
    # Process images concurrently
    tasks = [self.process_single(img) for img in images]
    results = await asyncio.gather(*tasks)
    return results
```

### Plugin Dependencies

Manage dependencies between plugins:

```python
async def initialize(self) -> bool:
    # Check if required plugin is available
    registry = PluginRegistry()
    upscaler = registry.get_plugin("upscale_effect")
    if not upscaler:
        logger.error("Requires upscale_effect plugin")
        return False
    
    self.upscaler = upscaler
    return True
```

### Custom Plugin Paths

Add custom directories for plugin discovery:

```python
# In your settings.yaml
plugins:
  paths:
    - ~/.alice/plugins
    - /opt/alice-plugins
    - ./project_plugins
```

## Testing Plugins

### Unit Tests

```python
import pytest
from pathlib import Path
from my_plugin import MyEffectPlugin

@pytest.mark.asyncio
async def test_effect_application():
    plugin = MyEffectPlugin()
    await plugin.initialize()
    
    input_path = Path("test_input.jpg")
    output_path = Path("test_output.jpg")
    
    result = await plugin.apply(
        input_path, 
        output_path,
        {"intensity": 0.5}
    )
    
    assert result.exists()
    assert result == output_path
```

### Integration Tests

```python
@pytest.mark.asyncio
async def test_plugin_with_registry():
    registry = PluginRegistry()
    await registry.initialize()
    
    # Load plugin
    plugin = registry.loader.load_plugin("./my_plugin.py")
    registry.register_plugin(plugin)
    
    # Use plugin
    effect = registry.get_plugin("my_effect")
    assert effect is not None
```

## Distribution

### Packaging Plugins

Create a package structure:
```
my_alice_plugins/
├── __init__.py
├── effects/
│   ├── __init__.py
│   └── blur_effect.py
├── providers/
│   └── custom_provider.py
└── setup.py
```

### Publishing

Share plugins via:
1. GitHub repositories
2. PyPI packages
3. Direct file sharing

## Examples

### Complete Effect Plugin

```python
"""Sharpen effect plugin for enhancing image details."""

import logging
from pathlib import Path
from typing import Any, Dict, List
import cv2
import numpy as np

from alicemultiverse.plugins.base import EffectPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class SharpenEffectPlugin(EffectPlugin):
    """Sharpen images using unsharp masking."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="sharpen_effect",
            version="1.0.0",
            type=PluginType.EFFECT,
            description="Enhance image sharpness using unsharp masking",
            author="Your Name",
            email="your.email@example.com",
            url="https://github.com/yourusername/sharpen-plugin",
            dependencies=["opencv-python", "numpy"],
            config_schema={
                "amount": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 5.0,
                    "default": 1.0,
                    "description": "Sharpening strength"
                },
                "radius": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 10.0,
                    "default": 1.0,
                    "description": "Blur radius for unsharp mask"
                },
                "threshold": {
                    "type": "integer",
                    "minimum": 0,
                    "maximum": 255,
                    "default": 0,
                    "description": "Minimum brightness change"
                }
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self.amount = self.config.get("amount", 1.0)
        self.radius = self.config.get("radius", 1.0)
        self.threshold = self.config.get("threshold", 0)
        
        self._initialized = True
        logger.info(f"Initialized sharpen effect with amount={self.amount}")
        return True
    
    async def cleanup(self):
        """Clean up resources."""
        self._initialized = False
    
    async def apply(
        self, 
        input_path: Path, 
        output_path: Path, 
        parameters: Dict[str, Any]
    ) -> Path:
        """Apply sharpening effect."""
        # Get parameters
        amount = parameters.get("amount", self.amount)
        radius = parameters.get("radius", self.radius)
        threshold = parameters.get("threshold", self.threshold)
        
        # Load image
        image = cv2.imread(str(input_path))
        if image is None:
            raise ValueError(f"Could not load image: {input_path}")
        
        # Apply unsharp masking
        blurred = cv2.GaussianBlur(image, (0, 0), radius)
        sharpened = cv2.addWeighted(image, 1.0 + amount, blurred, -amount, 0)
        
        # Apply threshold
        if threshold > 0:
            diff = cv2.absdiff(image, sharpened)
            mask = cv2.cvtColor(diff, cv2.COLOR_BGR2GRAY)
            mask = cv2.threshold(mask, threshold, 255, cv2.THRESH_BINARY)[1]
            mask = cv2.cvtColor(mask, cv2.COLOR_GRAY2BGR) / 255.0
            sharpened = image * (1 - mask) + sharpened * mask
        
        # Save result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), sharpened)
        
        logger.info(f"Sharpened {input_path.name} with amount={amount}")
        return output_path
    
    def get_supported_formats(self) -> List[str]:
        """Return supported formats."""
        return [".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"]
```

## Troubleshooting

### Common Issues

1. **Plugin not found**
   - Ensure plugin is in a discoverable location
   - Check plugin name matches metadata

2. **Configuration errors**
   - Validate config against schema
   - Check required fields are present

3. **Import errors**
   - Install plugin dependencies
   - Check Python path

### Debug Mode

Enable debug logging:
```bash
export ALICE_LOG_LEVEL=DEBUG
alice plugins list -v
```

## Next Steps

1. Browse built-in plugins for examples
2. Create your first plugin using templates
3. Share your plugins with the community
4. Contribute improvements to the plugin system