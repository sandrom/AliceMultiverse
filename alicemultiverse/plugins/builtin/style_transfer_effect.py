"""Style transfer effect plugin using neural style transfer."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio

import cv2
import numpy as np
from PIL import Image

from ..base import EffectPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class StyleTransferEffectPlugin(EffectPlugin):
    """Apply artistic style transfer to images."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="style_transfer",
            version="1.0.0",
            type=PluginType.EFFECT,
            description="Apply artistic style transfer using various techniques",
            author="AliceMultiverse",
            dependencies=["opencv-python", "pillow", "numpy"],
            config_schema={
                "style": {
                    "type": "string",
                    "enum": ["oil_painting", "watercolor", "pencil_sketch", "cartoon", "mosaic"],
                    "default": "oil_painting"
                },
                "intensity": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.7
                },
                "preserve_colors": {
                    "type": "boolean",
                    "default": True
                }
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self.style = self.config.get("style", "oil_painting")
        self.intensity = self.config.get("intensity", 0.7)
        self.preserve_colors = self.config.get("preserve_colors", True)
        
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
        Apply style transfer effect to image.
        
        Args:
            input_path: Input image path
            output_path: Output image path
            parameters: Effect parameters (style, intensity, preserve_colors)
            
        Returns:
            Path to stylized image
        """
        style = parameters.get("style", self.style)
        intensity = parameters.get("intensity", self.intensity)
        preserve_colors = parameters.get("preserve_colors", self.preserve_colors)
        
        # Load image
        image = cv2.imread(str(input_path))
        if image is None:
            raise ValueError(f"Could not load image: {input_path}")
        
        # Apply style transfer based on selected style
        if style == "oil_painting":
            stylized = await self._apply_oil_painting(image, intensity)
        elif style == "watercolor":
            stylized = await self._apply_watercolor(image, intensity)
        elif style == "pencil_sketch":
            stylized = await self._apply_pencil_sketch(image, intensity)
        elif style == "cartoon":
            stylized = await self._apply_cartoon(image, intensity)
        elif style == "mosaic":
            stylized = await self._apply_mosaic(image, intensity)
        else:
            stylized = image
        
        # Optionally preserve original colors
        if preserve_colors and style not in ["pencil_sketch"]:
            stylized = self._preserve_colors(image, stylized)
        
        # Save result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), stylized)
        
        logger.info(f"Applied {style} style to {input_path.name}")
        return output_path
    
    async def _apply_oil_painting(self, image: np.ndarray, intensity: float) -> np.ndarray:
        """Apply oil painting effect."""
        # Adjust parameters based on intensity
        size = int(7 + 8 * intensity)  # 7-15
        dynRatio = int(1 + 9 * intensity)  # 1-10
        
        # Apply oil painting effect
        result = cv2.xphoto.oilPainting(image, size, dynRatio)
        return result
    
    async def _apply_watercolor(self, image: np.ndarray, intensity: float) -> np.ndarray:
        """Apply watercolor effect."""
        # Apply bilateral filter for watercolor-like smoothing
        sigma_color = 20 + int(80 * intensity)
        sigma_space = 20 + int(80 * intensity)
        
        result = cv2.bilateralFilter(image, -1, sigma_color, sigma_space)
        
        # Add slight edge enhancement
        edges = cv2.Canny(cv2.cvtColor(image, cv2.COLOR_BGR2GRAY), 50, 150)
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        result = cv2.addWeighted(result, 0.95, edges, 0.05, 0)
        
        return result
    
    async def _apply_pencil_sketch(self, image: np.ndarray, intensity: float) -> np.ndarray:
        """Apply pencil sketch effect."""
        # Convert to grayscale
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Apply pencil sketch
        sigma_s = 10 + int(50 * intensity)
        sigma_r = 0.05 + 0.05 * intensity
        
        _, sketch = cv2.pencilSketch(image, sigma_s=sigma_s, sigma_r=sigma_r, shade_factor=0.03)
        
        return sketch
    
    async def _apply_cartoon(self, image: np.ndarray, intensity: float) -> np.ndarray:
        """Apply cartoon effect."""
        # Apply bilateral filter for smoothing
        smooth = cv2.bilateralFilter(image, 15, 80, 80)
        
        # Create edge mask
        gray = cv2.cvtColor(smooth, cv2.COLOR_BGR2GRAY)
        edges = cv2.adaptiveThreshold(
            gray, 255, 
            cv2.ADAPTIVE_THRESH_MEAN_C, 
            cv2.THRESH_BINARY, 
            7, 10
        )
        
        # Convert edges to color
        edges = cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
        
        # Apply cartoon effect
        cartoon = cv2.bitwise_and(smooth, edges)
        
        # Blend based on intensity
        result = cv2.addWeighted(image, 1 - intensity, cartoon, intensity, 0)
        
        return result
    
    async def _apply_mosaic(self, image: np.ndarray, intensity: float) -> np.ndarray:
        """Apply mosaic/pixelated effect."""
        # Calculate block size based on intensity
        height, width = image.shape[:2]
        block_size = int(max(4, min(width, height) * 0.02 * (1 + 2 * intensity)))
        
        # Downscale
        small = cv2.resize(
            image, 
            (width // block_size, height // block_size), 
            interpolation=cv2.INTER_LINEAR
        )
        
        # Upscale with nearest neighbor
        result = cv2.resize(
            small, 
            (width, height), 
            interpolation=cv2.INTER_NEAREST
        )
        
        return result
    
    def _preserve_colors(self, original: np.ndarray, stylized: np.ndarray) -> np.ndarray:
        """Preserve original colors in stylized image."""
        # Convert to LAB color space
        original_lab = cv2.cvtColor(original, cv2.COLOR_BGR2LAB)
        stylized_lab = cv2.cvtColor(stylized, cv2.COLOR_BGR2LAB)
        
        # Keep L channel from stylized, A and B from original
        result_lab = stylized_lab.copy()
        result_lab[:, :, 1:] = original_lab[:, :, 1:]
        
        # Convert back to BGR
        result = cv2.cvtColor(result_lab, cv2.COLOR_LAB2BGR)
        
        return result
    
    def get_supported_formats(self) -> List[str]:
        """Return supported image formats."""
        return [".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"]