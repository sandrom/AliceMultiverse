"""Watermark effect plugin for adding text or image watermarks."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from ..base import EffectPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class WatermarkEffectPlugin(EffectPlugin):
    """Add watermarks to images."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="watermark_effect",
            version="1.0.0",
            type=PluginType.EFFECT,
            description="Add text or image watermarks with customizable positioning",
            author="AliceMultiverse",
            dependencies=["opencv-python", "pillow", "numpy"],
            config_schema={
                "type": {
                    "type": "string",
                    "enum": ["text", "image"],
                    "default": "text"
                },
                "text": {
                    "type": "string",
                    "default": "© AliceMultiverse"
                },
                "image_path": {
                    "type": "string",
                    "description": "Path to watermark image"
                },
                "position": {
                    "type": "string",
                    "enum": ["top-left", "top-right", "bottom-left", "bottom-right", "center"],
                    "default": "bottom-right"
                },
                "opacity": {
                    "type": "number",
                    "minimum": 0.0,
                    "maximum": 1.0,
                    "default": 0.3
                },
                "scale": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 0.5,
                    "default": 0.2,
                    "description": "Scale relative to image size"
                },
                "margin": {
                    "type": "integer",
                    "minimum": 0,
                    "default": 20,
                    "description": "Margin from edges in pixels"
                },
                "font_size": {
                    "type": "integer",
                    "minimum": 10,
                    "maximum": 200,
                    "default": 36
                },
                "font_color": {
                    "type": "string",
                    "default": "white",
                    "description": "Color name or hex code"
                }
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self.watermark_type = self.config.get("type", "text")
        self.text = self.config.get("text", "© AliceMultiverse")
        self.image_path = self.config.get("image_path")
        self.position = self.config.get("position", "bottom-right")
        self.opacity = self.config.get("opacity", 0.3)
        self.scale = self.config.get("scale", 0.2)
        self.margin = self.config.get("margin", 20)
        self.font_size = self.config.get("font_size", 36)
        self.font_color = self.config.get("font_color", "white")
        
        # Load watermark image if specified
        self.watermark_img = None
        if self.watermark_type == "image" and self.image_path:
            try:
                self.watermark_img = cv2.imread(self.image_path, cv2.IMREAD_UNCHANGED)
                if self.watermark_img is None:
                    logger.error(f"Could not load watermark image: {self.image_path}")
                    return False
            except Exception as e:
                logger.error(f"Error loading watermark image: {e}")
                return False
        
        self._initialized = True
        return True
    
    async def cleanup(self):
        """Clean up resources."""
        self._initialized = False
        self.watermark_img = None
    
    async def apply(
        self, 
        input_path: Path, 
        output_path: Path, 
        parameters: Dict[str, Any]
    ) -> Path:
        """
        Apply watermark to image.
        
        Args:
            input_path: Input image path
            output_path: Output image path
            parameters: Effect parameters
            
        Returns:
            Path to watermarked image
        """
        # Get parameters
        watermark_type = parameters.get("type", self.watermark_type)
        position = parameters.get("position", self.position)
        opacity = parameters.get("opacity", self.opacity)
        scale = parameters.get("scale", self.scale)
        margin = parameters.get("margin", self.margin)
        
        # Load image
        image = cv2.imread(str(input_path))
        if image is None:
            raise ValueError(f"Could not load image: {input_path}")
        
        # Apply watermark
        if watermark_type == "text":
            result = await self._apply_text_watermark(
                image, parameters
            )
        else:
            result = await self._apply_image_watermark(
                image, position, opacity, scale, margin
            )
        
        # Save result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), result)
        
        logger.info(f"Added {watermark_type} watermark to {input_path.name}")
        return output_path
    
    async def _apply_text_watermark(
        self, 
        image: np.ndarray, 
        parameters: Dict[str, Any]
    ) -> np.ndarray:
        """Apply text watermark."""
        text = parameters.get("text", self.text)
        position = parameters.get("position", self.position)
        opacity = parameters.get("opacity", self.opacity)
        font_size = parameters.get("font_size", self.font_size)
        font_color = parameters.get("font_color", self.font_color)
        margin = parameters.get("margin", self.margin)
        
        # Convert to PIL for text rendering
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Create watermark layer
        watermark = Image.new('RGBA', pil_image.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(watermark)
        
        # Try to load a nice font, fall back to default
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            font = ImageFont.load_default()
        
        # Get text bbox
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        # Calculate position
        x, y = self._calculate_position(
            pil_image.size, (text_width, text_height), position, margin
        )
        
        # Parse color
        color = self._parse_color(font_color)
        
        # Draw text with opacity
        draw.text((x, y), text, fill=(*color, int(255 * opacity)), font=font)
        
        # Composite watermark onto image
        watermarked = Image.alpha_composite(
            pil_image.convert('RGBA'), 
            watermark
        )
        
        # Convert back to OpenCV format
        result = cv2.cvtColor(np.array(watermarked.convert('RGB')), cv2.COLOR_RGB2BGR)
        
        return result
    
    async def _apply_image_watermark(
        self, 
        image: np.ndarray,
        position: str,
        opacity: float,
        scale: float,
        margin: int
    ) -> np.ndarray:
        """Apply image watermark."""
        if self.watermark_img is None:
            logger.warning("No watermark image loaded, returning original")
            return image
        
        h, w = image.shape[:2]
        wm_h, wm_w = self.watermark_img.shape[:2]
        
        # Scale watermark
        max_dim = max(w, h)
        target_size = int(max_dim * scale)
        scale_factor = target_size / max(wm_w, wm_h)
        
        new_w = int(wm_w * scale_factor)
        new_h = int(wm_h * scale_factor)
        
        watermark_resized = cv2.resize(
            self.watermark_img, 
            (new_w, new_h), 
            interpolation=cv2.INTER_AREA
        )
        
        # Calculate position
        x, y = self._calculate_position(
            (w, h), (new_w, new_h), position, margin
        )
        
        # Apply watermark with opacity
        if watermark_resized.shape[2] == 4:  # Has alpha channel
            # Extract alpha channel
            alpha = watermark_resized[:, :, 3] / 255.0 * opacity
            
            # Create ROI
            roi = image[y:y+new_h, x:x+new_w]
            
            # Blend using alpha
            for c in range(3):
                roi[:, :, c] = (1 - alpha) * roi[:, :, c] + alpha * watermark_resized[:, :, c]
        else:
            # No alpha channel, use simple blending
            roi = image[y:y+new_h, x:x+new_w]
            cv2.addWeighted(roi, 1 - opacity, watermark_resized[:, :, :3], opacity, 0, roi)
        
        return image
    
    def _calculate_position(
        self, 
        image_size: Tuple[int, int],
        watermark_size: Tuple[int, int],
        position: str,
        margin: int
    ) -> Tuple[int, int]:
        """Calculate watermark position."""
        img_w, img_h = image_size
        wm_w, wm_h = watermark_size
        
        if position == "top-left":
            x, y = margin, margin
        elif position == "top-right":
            x, y = img_w - wm_w - margin, margin
        elif position == "bottom-left":
            x, y = margin, img_h - wm_h - margin
        elif position == "bottom-right":
            x, y = img_w - wm_w - margin, img_h - wm_h - margin
        elif position == "center":
            x, y = (img_w - wm_w) // 2, (img_h - wm_h) // 2
        else:
            x, y = margin, margin
        
        # Ensure within bounds
        x = max(0, min(x, img_w - wm_w))
        y = max(0, min(y, img_h - wm_h))
        
        return x, y
    
    def _parse_color(self, color_str: str) -> Tuple[int, int, int]:
        """Parse color string to RGB tuple."""
        # Common color names
        colors = {
            "white": (255, 255, 255),
            "black": (0, 0, 0),
            "red": (255, 0, 0),
            "green": (0, 255, 0),
            "blue": (0, 0, 255),
            "yellow": (255, 255, 0),
            "cyan": (0, 255, 255),
            "magenta": (255, 0, 255),
            "gray": (128, 128, 128)
        }
        
        if color_str.lower() in colors:
            return colors[color_str.lower()]
        
        # Try to parse hex color
        if color_str.startswith("#"):
            try:
                hex_color = color_str[1:]
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    return (r, g, b)
            except:
                pass
        
        # Default to white
        return (255, 255, 255)
    
    def get_supported_formats(self) -> List[str]:
        """Return supported image formats."""
        return [".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"]