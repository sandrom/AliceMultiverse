"""Image upscaling effect plugin using Real-ESRGAN."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

import cv2
import numpy as np
from PIL import Image

from ..base import EffectPlugin, PluginMetadata, PluginType

logger = logging.getLogger(__name__)


class UpscaleEffectPlugin(EffectPlugin):
    """Upscale images using various algorithms."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="upscale_effect",
            version="1.0.0",
            type=PluginType.EFFECT,
            description="Upscale images using various algorithms including Real-ESRGAN",
            author="AliceMultiverse",
            dependencies=["opencv-python", "pillow"],
            config_schema={
                "algorithm": {
                    "type": "string",
                    "enum": ["lanczos", "cubic", "esrgan"],
                    "default": "lanczos"
                },
                "scale_factor": {
                    "type": "number",
                    "minimum": 2,
                    "maximum": 8,
                    "default": 4
                }
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the plugin."""
        self.algorithm = self.config.get("algorithm", "lanczos")
        self.scale_factor = self.config.get("scale_factor", 4)
        
        # Check if Real-ESRGAN is available
        self.esrgan_available = False
        if self.algorithm == "esrgan":
            try:
                from basicsr.archs.rrdbnet_arch import RRDBNet
                from realesrgan import RealESRGANer
                self.esrgan_available = True
                logger.info("Real-ESRGAN is available")
            except ImportError:
                logger.warning("Real-ESRGAN not available, falling back to lanczos")
                self.algorithm = "lanczos"
        
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
        Apply upscaling effect to image.
        
        Args:
            input_path: Input image path
            output_path: Output image path
            parameters: Effect parameters (algorithm, scale_factor)
            
        Returns:
            Path to upscaled image
        """
        algorithm = parameters.get("algorithm", self.algorithm)
        scale_factor = parameters.get("scale_factor", self.scale_factor)
        
        # Load image
        image = cv2.imread(str(input_path))
        if image is None:
            raise ValueError(f"Could not load image: {input_path}")
        
        # Apply upscaling
        if algorithm == "esrgan" and self.esrgan_available:
            upscaled = await self._upscale_esrgan(image, scale_factor)
        elif algorithm == "cubic":
            upscaled = cv2.resize(
                image, 
                None, 
                fx=scale_factor, 
                fy=scale_factor,
                interpolation=cv2.INTER_CUBIC
            )
        else:  # lanczos
            upscaled = cv2.resize(
                image,
                None,
                fx=scale_factor,
                fy=scale_factor,
                interpolation=cv2.INTER_LANCZOS4
            )
        
        # Save result
        output_path.parent.mkdir(parents=True, exist_ok=True)
        cv2.imwrite(str(output_path), upscaled)
        
        logger.info(f"Upscaled {input_path.name} by {scale_factor}x using {algorithm}")
        return output_path
    
    async def _upscale_esrgan(self, image: np.ndarray, scale_factor: int) -> np.ndarray:
        """Upscale using Real-ESRGAN."""
        # This would require Real-ESRGAN installation
        # For now, fall back to lanczos
        logger.warning("Real-ESRGAN implementation pending, using lanczos")
        return cv2.resize(
            image,
            None,
            fx=scale_factor,
            fy=scale_factor,
            interpolation=cv2.INTER_LANCZOS4
        )
    
    def get_supported_formats(self) -> List[str]:
        """Return supported image formats."""
        return [".jpg", ".jpeg", ".png", ".webp", ".tiff", ".bmp"]