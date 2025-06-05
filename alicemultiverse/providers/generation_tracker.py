"""Track and store generation context for reproducibility."""

import yaml
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

from ..metadata.embedder import MetadataEmbedder
from ..core.file_operations import FileHandler
from ..core.structured_logging import get_logger
from .types import GenerationRequest, GenerationResult

logger = get_logger(__name__)


class GenerationTracker:
    """Tracks generation context and ensures it's stored in multiple places."""
    
    def __init__(self):
        self.asset_repo = None
        self.embedder = MetadataEmbedder()
        self.file_handler = FileHandler()
    
    async def track_generation(
        self,
        request: GenerationRequest,
        result: GenerationResult,
        provider_name: str
    ) -> Optional[str]:
        """Track a generation by storing all context.
        
        Args:
            request: Original generation request
            result: Generation result
            provider_name: Provider used
            
        Returns:
            Asset ID (content hash) if successful
        """
        if not result.file_path or not result.file_path.exists():
            logger.warning("No file path in generation result")
            return None
        
        try:
            # Calculate content hash
            content_hash = self.file_handler.calculate_file_hash(result.file_path)
            
            # Build comprehensive generation context
            generation_context = self._build_generation_context(
                request, result, provider_name
            )
            
            # 1. Embed metadata directly in the file
            await self._embed_metadata(result.file_path, generation_context)
            
            # 2. Store in database
            await self._store_in_database(
                content_hash,
                result.file_path,
                generation_context
            )
            
            # 3. Create sidecar YAML file for easy access
            await self._create_sidecar_file(result.file_path, generation_context)
            
            logger.info(
                "Generation tracked successfully",
                asset_id=content_hash,
                provider=provider_name,
                model=result.model
            )
            
            return content_hash
            
        except Exception as e:
            logger.error(
                "Failed to track generation",
                error=str(e),
                exc_info=True
            )
            return None
    
    def _build_generation_context(
        self,
        request: GenerationRequest,
        result: GenerationResult,
        provider_name: str
    ) -> Dict[str, Any]:
        """Build comprehensive generation context.
        
        This includes everything needed to recreate the generation.
        """
        context = {
            # Core generation info
            "prompt": request.prompt,
            "model": result.model or request.model,
            "provider": provider_name,
            "generation_type": request.generation_type.value,
            "timestamp": result.timestamp.isoformat() if result.timestamp else datetime.now().isoformat(),
            
            # Full parameters
            "parameters": request.parameters or {},
            
            # Reference assets (for image-to-image, kontext, etc.)
            "reference_assets": request.reference_assets or [],
            "reference_weights": getattr(request, 'reference_weights', None),
            
            # Cost and performance
            "cost": result.cost,
            "generation_time": result.generation_time,
            
            # Project context
            "project_id": request.project_id,
            
            # Output details
            "output_format": request.output_format,
            
            # Provider-specific metadata
            "provider_metadata": result.metadata or {},
            
            # Version info for compatibility
            "alice_version": "1.0",
            "metadata_version": "1.0"
        }
        
        # For video generation from images, include source image context
        if request.generation_type.value == "video" and request.reference_assets:
            context["source_images"] = []
            for ref_asset in request.reference_assets:
                # Try to get asset info from database
                asset_info = self.asset_repo.get(ref_asset)
                if asset_info:
                    context["source_images"].append({
                        "asset_id": ref_asset,
                        "prompt": asset_info.generation_params.get("prompt", ""),
                        "model": asset_info.generation_params.get("model", ""),
                        "role": asset_info.role
                    })
                else:
                    context["source_images"].append({
                        "asset_id": ref_asset,
                        "prompt": "Unknown",
                        "model": "Unknown"
                    })
        
        # Clean up None values
        context = {k: v for k, v in context.items() if v is not None}
        
        return context
    
    async def _embed_metadata(self, file_path: Path, context: Dict[str, Any]):
        """Embed metadata directly in the file."""
        try:
            # Prepare metadata for embedding
            embed_data = {
                "prompt": context["prompt"],
                "negative_prompt": context.get("parameters", {}).get("negative_prompt", ""),
                "model": context["model"],
                "provider": context["provider"],
                "generation_params": yaml.dump(context),  # Full context as YAML
                "timestamp": context["timestamp"]
            }
            
            # Use our embedder
            success = self.embedder.embed_metadata(str(file_path), embed_data)
            if success:
                logger.debug("Metadata embedded in file", file_path=str(file_path))
            else:
                logger.warning("Failed to embed metadata", file_path=str(file_path))
                
        except Exception as e:
            logger.error(
                "Error embedding metadata",
                file_path=str(file_path),
                error=str(e)
            )
    
    async def _store_in_database(
        self,
        content_hash: str,
        file_path: Path,
        context: Dict[str, Any]
    ):
        """Store generation context in database."""
        try:
            # Determine media type
            media_type = self._get_media_type(file_path)
            
            # Extract metadata for database
            metadata = {
                "width": context.get("parameters", {}).get("width"),
                "height": context.get("parameters", {}).get("height"),
                "duration": context.get("parameters", {}).get("duration"),
                "format": file_path.suffix.lstrip('.'),
                "file_size": file_path.stat().st_size
            }
            
            # Create or update asset
            self.asset_repo.create_or_update_asset(
                content_hash=content_hash,
                file_path=str(file_path),
                media_type=media_type,
                metadata=metadata,
                project_id=context.get("project_id")
            )
            
            # Update with generation params
            self.asset_repo.update_metadata(
                content_hash=content_hash,
                generation_params=context,
                analysis_results={
                    "provider": context["provider"],
                    "model": context["model"],
                    "cost": context.get("cost", 0),
                    "generation_time": context.get("generation_time", 0)
                }
            )
            
            # Add relationships if there are reference assets
            if context.get("reference_assets"):
                for ref_asset in context["reference_assets"]:
                    self.asset_repo.add_relationship(
                        parent_hash=ref_asset,
                        child_hash=content_hash,
                        relationship_type="generated_from",
                        metadata={
                            "generation_type": context["generation_type"],
                            "model": context["model"]
                        }
                    )
            
            logger.debug("Generation context stored in database", asset_id=content_hash)
            
        except Exception as e:
            logger.error(
                "Error storing in database",
                asset_id=content_hash,
                error=str(e)
            )
    
    async def _create_sidecar_file(self, file_path: Path, context: Dict[str, Any]):
        """Create a sidecar YAML file with full context."""
        try:
            # Create .yaml file alongside the media file
            sidecar_path = file_path.with_suffix(file_path.suffix + '.yaml')
            
            # Write formatted YAML with nice formatting
            with open(sidecar_path, 'w') as f:
                yaml.dump(
                    context, 
                    f, 
                    default_flow_style=False,  # Use block style, not inline
                    sort_keys=True,
                    width=120,  # Wider lines before wrapping
                    indent=2    # 2-space indentation
                )
            
            logger.debug("Sidecar file created", path=str(sidecar_path))
            
        except Exception as e:
            logger.error(
                "Error creating sidecar file",
                file_path=str(file_path),
                error=str(e)
            )
    
    def _get_media_type(self, file_path: Path) -> str:
        """Determine media type from file extension."""
        ext = file_path.suffix.lower()
        if ext in ['.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif']:
            return 'image'
        elif ext in ['.mp4', '.mov', '.avi', '.webm']:
            return 'video'
        elif ext in ['.mp3', '.wav', '.ogg', '.m4a']:
            return 'audio'
        else:
            return 'unknown'
    
    async def get_generation_context(self, asset_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve generation context for an asset.
        
        Args:
            asset_id: Content hash of the asset
            
        Returns:
            Generation context if found
        """
        try:
            asset = self.asset_repo.get(asset_id)
            if asset and asset.generation_params:
                return asset.generation_params
            return None
        except Exception as e:
            logger.error(
                "Error retrieving generation context",
                asset_id=asset_id,
                error=str(e)
            )
            return None
    
    async def recreate_generation(self, asset_id: str) -> Optional[GenerationRequest]:
        """Create a generation request to recreate an asset.
        
        Args:
            asset_id: Content hash of the asset to recreate
            
        Returns:
            GenerationRequest that can be used to recreate the asset
        """
        context = await self.get_generation_context(asset_id)
        if not context:
            return None
        
        try:
            # Rebuild generation request
            from .types import GenerationType
            
            request = GenerationRequest(
                prompt=context["prompt"],
                generation_type=GenerationType(context["generation_type"]),
                model=context.get("model"),
                parameters=context.get("parameters", {}),
                reference_assets=context.get("reference_assets", []),
                reference_weights=context.get("reference_weights"),
                output_format=context.get("output_format"),
                project_id=context.get("project_id")
            )
            
            logger.info(
                "Recreation request built",
                asset_id=asset_id,
                model=request.model
            )
            
            return request
            
        except Exception as e:
            logger.error(
                "Error building recreation request",
                asset_id=asset_id,
                error=str(e)
            )
            return None


# Global tracker instance
_tracker: Optional[GenerationTracker] = None


def get_generation_tracker() -> GenerationTracker:
    """Get global generation tracker instance."""
    global _tracker
    if _tracker is None:
        _tracker = GenerationTracker()
    return _tracker