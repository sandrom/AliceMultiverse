"""Batch enhancement workflow plugin for processing multiple images."""

import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
import asyncio
from datetime import datetime

from ..base import WorkflowPlugin, PluginMetadata, PluginType
from ..registry import PluginRegistry

logger = logging.getLogger(__name__)


class BatchEnhancementWorkflowPlugin(WorkflowPlugin):
    """Workflow for batch processing images with multiple effects."""
    
    @property
    def metadata(self) -> PluginMetadata:
        return PluginMetadata(
            name="batch_enhancement_workflow",
            version="1.0.0",
            type=PluginType.WORKFLOW,
            description="Apply multiple enhancement effects to a batch of images",
            author="AliceMultiverse",
            dependencies=[],
            config_schema={
                "effects": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "plugin": {"type": "string"},
                            "parameters": {"type": "object"}
                        }
                    },
                    "default": [
                        {
                            "plugin": "filter_effect",
                            "parameters": {"filter": "vibrant", "strength": 0.6}
                        },
                        {
                            "plugin": "upscale_effect", 
                            "parameters": {"algorithm": "lanczos", "scale_factor": 2}
                        }
                    ]
                },
                "output_format": {
                    "type": "string",
                    "enum": ["jpg", "png", "webp"],
                    "default": "jpg"
                },
                "parallel_processing": {
                    "type": "boolean",
                    "default": True
                },
                "max_concurrent": {
                    "type": "integer",
                    "minimum": 1,
                    "maximum": 10,
                    "default": 3
                }
            }
        )
    
    async def initialize(self) -> bool:
        """Initialize the workflow."""
        self.effects = self.config.get("effects", [])
        self.output_format = self.config.get("output_format", "jpg")
        self.parallel_processing = self.config.get("parallel_processing", True)
        self.max_concurrent = self.config.get("max_concurrent", 3)
        
        # Get plugin registry
        self.registry = PluginRegistry()
        
        # Validate effect plugins exist
        for effect_config in self.effects:
            plugin_name = effect_config.get("plugin")
            if not self.registry.get_plugin(plugin_name):
                logger.error(f"Effect plugin not found: {plugin_name}")
                return False
        
        self._initialized = True
        return True
    
    async def cleanup(self):
        """Clean up resources."""
        self._initialized = False
    
    async def execute(
        self, 
        inputs: Dict[str, Any], 
        output_dir: Path,
        parameters: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute batch enhancement workflow.
        
        Args:
            inputs: Workflow inputs (image_paths, effects override)
            output_dir: Directory for output files
            parameters: Additional parameters
            
        Returns:
            Workflow results
        """
        # Get input images
        image_paths = inputs.get("image_paths", [])
        if not image_paths:
            return {
                "success": False,
                "error": "No input images provided"
            }
        
        # Override effects if provided
        effects = parameters.get("effects", self.effects)
        
        # Create output directory
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create workflow subdirectory with timestamp
        workflow_dir = output_dir / f"batch_enhancement_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        workflow_dir.mkdir(exist_ok=True)
        
        # Process images
        results = []
        errors = []
        
        if self.parallel_processing:
            # Process in parallel with semaphore
            sem = asyncio.Semaphore(self.max_concurrent)
            
            async def process_with_sem(img_path):
                async with sem:
                    return await self._process_single_image(
                        img_path, workflow_dir, effects
                    )
            
            # Create tasks
            tasks = [process_with_sem(Path(img)) for img in image_paths]
            
            # Execute and gather results
            processed = await asyncio.gather(*tasks, return_exceptions=True)
            
            for img_path, result in zip(image_paths, processed):
                if isinstance(result, Exception):
                    errors.append({
                        "image": str(img_path),
                        "error": str(result)
                    })
                elif result["success"]:
                    results.append(result)
                else:
                    errors.append(result)
        else:
            # Process sequentially
            for img_path in image_paths:
                try:
                    result = await self._process_single_image(
                        Path(img_path), workflow_dir, effects
                    )
                    if result["success"]:
                        results.append(result)
                    else:
                        errors.append(result)
                except Exception as e:
                    errors.append({
                        "image": str(img_path),
                        "error": str(e)
                    })
        
        # Generate summary
        success_rate = len(results) / len(image_paths) if image_paths else 0
        
        return {
            "success": len(errors) == 0,
            "workflow_dir": str(workflow_dir),
            "processed_count": len(results),
            "error_count": len(errors),
            "success_rate": success_rate,
            "results": results,
            "errors": errors,
            "summary": {
                "total_images": len(image_paths),
                "effects_applied": len(effects),
                "output_format": self.output_format
            }
        }
    
    async def _process_single_image(
        self, 
        image_path: Path,
        output_dir: Path,
        effects: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Process a single image through the effect pipeline."""
        try:
            current_path = image_path
            applied_effects = []
            
            # Apply each effect in sequence
            for i, effect_config in enumerate(effects):
                plugin_name = effect_config.get("plugin")
                parameters = effect_config.get("parameters", {})
                
                # Get effect plugin
                plugin = self.registry.get_plugin(plugin_name)
                if not plugin:
                    return {
                        "success": False,
                        "image": str(image_path),
                        "error": f"Plugin not found: {plugin_name}"
                    }
                
                # Determine output path for this step
                if i == len(effects) - 1:
                    # Final output
                    output_name = f"{image_path.stem}_enhanced.{self.output_format}"
                    effect_output = output_dir / output_name
                else:
                    # Intermediate output
                    effect_output = output_dir / f".temp_{image_path.stem}_{i}.png"
                
                # Apply effect
                try:
                    result_path = await plugin.apply(
                        current_path, 
                        effect_output,
                        parameters
                    )
                    applied_effects.append({
                        "effect": plugin_name,
                        "parameters": parameters
                    })
                    
                    # Clean up intermediate files
                    if i > 0 and current_path != image_path:
                        current_path.unlink()
                    
                    current_path = result_path
                    
                except Exception as e:
                    # Clean up any intermediate files
                    if current_path != image_path and current_path.exists():
                        current_path.unlink()
                    
                    return {
                        "success": False,
                        "image": str(image_path),
                        "error": f"Effect {plugin_name} failed: {str(e)}",
                        "applied_effects": applied_effects
                    }
            
            return {
                "success": True,
                "image": str(image_path),
                "output": str(current_path),
                "applied_effects": applied_effects
            }
            
        except Exception as e:
            return {
                "success": False,
                "image": str(image_path),
                "error": str(e)
            }
    
    def get_supported_inputs(self) -> List[str]:
        """Return supported input types."""
        return ["image_paths"]
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate workflow inputs."""
        if "image_paths" not in inputs:
            return False
        
        image_paths = inputs["image_paths"]
        if not isinstance(image_paths, list) or not image_paths:
            return False
        
        # Check that all paths exist
        for img_path in image_paths:
            if not Path(img_path).exists():
                logger.error(f"Image not found: {img_path}")
                return False
        
        return True