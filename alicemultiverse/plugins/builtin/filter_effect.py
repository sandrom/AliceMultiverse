"""Image filter effect plugin with various artistic filters."""

import logging
from pathlib import Path
from typing import Any, Dict, List
import numpy as np
import cv2
from PIL import Image, ImageFilter, ImageEnhance

from ..base import EffectPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class FilterEffectPlugin(EffectPlugin):
    """Apply various artistic filters to images."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="filter_effect",
            version="1.0.0",
            type=PluginType.EFFECT,
            description="Apply artistic filters like vintage, noir, sepia, etc.",
            author="AliceMultiverse",
            dependencies=["opencv-python", "pillow", "numpy"],
            config_schema={
                "filter": {
                    "type": "string",
                    "enum": ["vintage", "noir", "sepia", "cool", "warm", "dramatic", "dreamy", "vibrant"],
                    "default": "vintage"
                },
                "strength": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.8
                }
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self.filter = self.config.get("filter", "vintage")
        self.strength = self.config.get("strength", 0.8)
        
        self._initialized = True
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
        """
        Apply filter effect to image.
        
        Args:
            input_path: Input image path
            output_path: Output image path
            parameters: Effect parameters (filter, strength)
            
        Returns:
            Path to filtered image
        """
        filter_name = parameters.get("filter", self.filter)
        strength = parameters.get("strength", self.strength)
        
        # Load image with PIL for filter effects
        pil_image = Image.open(input_path).convert("RGB")
        
        # Apply filter
        if filter_name == "vintage":
            result = self._apply_vintage(pil_image, strength)
        elif filter_name == "noir":
            result = self._apply_noir(pil_image, strength)
        elif filter_name == "sepia":
            result = self._apply_sepia(pil_image, strength)
        elif filter_name == "cool":
            result = self._apply_cool(pil_image, strength)
        elif filter_name == "warm":
            result = self._apply_warm(pil_image, strength)
        elif filter_name == "dramatic":
            result = self._apply_dramatic(pil_image, strength)
        elif filter_name == "dreamy":
            result = self._apply_dreamy(pil_image, strength)
        elif filter_name == "vibrant":
            result = self._apply_vibrant(pil_image, strength)
        else:
            result = pil_image
        
        # Save result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        result.save(output_path, quality=95)
        
        logger.info(f"Applied {filter_name} filter to {input_path.name}")
        return output_path
    
    def _apply_vintage(self, image: Image.Image, strength: float) -> Image.Image:
        """Apply vintage filter with faded colors and vignette."""
        # Reduce saturation
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(0.5 + 0.5 * (1 - strength))
        
        # Add warmth
        image = self._adjust_color_balance(image, 1.05, 1.0, 0.9)
        
        # Reduce contrast slightly
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(0.9 + 0.1 * (1 - strength))
        
        # Add vignette
        image = self._add_vignette(image, strength * 0.7)
        
        return image
    
    def _apply_noir(self, image: Image.Image, strength: float) -> Image.Image:
        """Apply film noir filter with high contrast B&W."""
        # Convert to grayscale
        image = image.convert("L").convert("RGB")
        
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2 + 0.8 * strength)
        
        # Darken shadows
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(0.9 - 0.1 * strength)
        
        # Add grain
        if strength > 0.5:
            image = self._add_grain(image, strength * 0.3)
        
        return image
    
    def _apply_sepia(self, image: Image.Image, strength: float) -> Image.Image:
        """Apply sepia tone filter."""
        # Convert to numpy array
        img_array = np.array(image)
        
        # Sepia transformation matrix
        sepia_matrix = np.array([
            [0.393, 0.769, 0.189],
            [0.349, 0.686, 0.168],
            [0.272, 0.534, 0.131]
        ])
        
        # Apply sepia effect
        sepia = img_array @ sepia_matrix.T
        sepia = np.clip(sepia, 0, 255).astype(np.uint8)
        
        # Blend with original based on strength
        result = cv2.addWeighted(img_array, 1 - strength, sepia, strength, 0)
        
        return Image.fromarray(result)
    
    def _apply_cool(self, image: Image.Image, strength: float) -> Image.Image:
        """Apply cool filter with blue tones."""
        # Adjust color balance toward blue
        image = self._adjust_color_balance(image, 0.9, 0.95, 1.1 + 0.1 * strength)
        
        # Slightly increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.05 + 0.05 * strength)
        
        return image
    
    def _apply_warm(self, image: Image.Image, strength: float) -> Image.Image:
        """Apply warm filter with orange/red tones."""
        # Adjust color balance toward warm colors
        image = self._adjust_color_balance(image, 1.1 + 0.1 * strength, 1.05, 0.9)
        
        # Slightly reduce contrast for softer look
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(0.95 + 0.05 * (1 - strength))
        
        return image
    
    def _apply_dramatic(self, image: Image.Image, strength: float) -> Image.Image:
        """Apply dramatic filter with high contrast and saturation."""
        # Increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.2 + 0.3 * strength)
        
        # Increase saturation
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.2 + 0.3 * strength)
        
        # Add slight vignette
        image = self._add_vignette(image, strength * 0.5)
        
        return image
    
    def _apply_dreamy(self, image: Image.Image, strength: float) -> Image.Image:
        """Apply dreamy filter with soft focus and light tones."""
        # Apply gaussian blur for soft focus
        blurred = image.filter(ImageFilter.GaussianBlur(radius=2 * strength))
        
        # Blend with original
        img_array = np.array(image)
        blur_array = np.array(blurred)
        result = cv2.addWeighted(img_array, 0.7, blur_array, 0.3, 0)
        image = Image.fromarray(result)
        
        # Increase brightness
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.05 + 0.05 * strength)
        
        # Reduce saturation slightly
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(0.9 + 0.1 * (1 - strength))
        
        return image
    
    def _apply_vibrant(self, image: Image.Image, strength: float) -> Image.Image:
        """Apply vibrant filter with boosted colors."""
        # Increase saturation
        enhancer = ImageEnhance.Color(image)
        image = enhancer.enhance(1.3 + 0.4 * strength)
        
        # Slightly increase contrast
        enhancer = ImageEnhance.Contrast(image)
        image = enhancer.enhance(1.1 + 0.1 * strength)
        
        # Boost brightness slightly
        enhancer = ImageEnhance.Brightness(image)
        image = enhancer.enhance(1.02 + 0.03 * strength)
        
        return image
    
    def _adjust_color_balance(self, image: Image.Image, r_factor: float, g_factor: float, b_factor: float) -> Image.Image:
        """Adjust color balance by channel."""
        img_array = np.array(image).astype(np.float32)
        
        img_array[:, :, 0] *= r_factor
        img_array[:, :, 1] *= g_factor
        img_array[:, :, 2] *= b_factor
        
        img_array = np.clip(img_array, 0, 255).astype(np.uint8)
        
        return Image.fromarray(img_array)
    
    def _add_vignette(self, image: Image.Image, strength: float) -> Image.Image:
        """Add vignette effect."""
        width, height = image.size
        
        # Create radial gradient
        x = np.linspace(-1, 1, width)
        y = np.linspace(-1, 1, height)
        X, Y = np.meshgrid(x, y)
        
        # Calculate distance from center
        dist = np.sqrt(X**2 + Y**2)
        
        # Create vignette mask
        vignette = 1 - (dist * strength)
        vignette = np.clip(vignette, 0, 1)
        vignette = np.stack([vignette] * 3, axis=-1)
        
        # Apply vignette
        img_array = np.array(image).astype(np.float32)
        result = img_array * vignette
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return Image.fromarray(result)
    
    def _add_grain(self, image: Image.Image, amount: float) -> Image.Image:
        """Add film grain effect."""
        img_array = np.array(image).astype(np.float32)
        
        # Generate random noise
        noise = np.random.normal(0, 10 * amount, img_array.shape)
        
        # Add noise to image
        result = img_array + noise
        result = np.clip(result, 0, 255).astype(np.uint8)
        
        return Image.fromarray(result)
    
    def get_supported_formats(self) -> List[str]:
        """Return supported image formats."""
        return [".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"]