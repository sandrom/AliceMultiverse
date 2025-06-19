"""Enhanced media organizer with rich metadata support."""

import asyncio
import contextlib
import logging
from datetime import datetime
from pathlib import Path

from omegaconf import DictConfig

from ..assets.metadata.embedder import MetadataEmbedder
from ..assets.metadata.models import AssetMetadata, AssetRole
from ..core.types import AnalysisResult, MediaType, OrganizeResult
from ..core.unified_cache import UnifiedCache as EnhancedMetadataCache
from ..understanding.simple_analysis import analyze_image, should_analyze_image
from .media_organizer import MediaOrganizer

logger = logging.getLogger(__name__)


class EnhancedMediaOrganizer(MediaOrganizer):
    """Media organizer with enhanced metadata and AI-navigable features."""

    def __init__(self, config: DictConfig):
        """Initialize enhanced organizer.

        Args:
            config: Configuration object
        """
        super().__init__(config)

        # Extract understanding config for direct function calls
        self.understanding_enabled = getattr(config.processing, "understanding", False)
        self.understanding_provider = None
        self.understanding_detailed = False

        if self.understanding_enabled:
            # Try to get understanding config from pipeline
            if hasattr(config, "pipeline") and hasattr(config.pipeline, "understanding"):
                understanding_config = config.pipeline.understanding
                self.understanding_provider = getattr(understanding_config, "preferred_provider", None)
                self.understanding_detailed = getattr(understanding_config, "detailed", False)

        # Replace standard cache with enhanced cache
        project_id = self._get_project_id(config)

        # Check if understanding is enabled
        enable_understanding = getattr(config.processing, "understanding", False)
        understanding_provider = None
        if enable_understanding and hasattr(config, "pipeline") and hasattr(config.pipeline, "understanding"):
            understanding_provider = getattr(config.pipeline.understanding, "preferred_provider", None)

        self.metadata_cache = EnhancedMetadataCache(
            source_root=Path(config.paths.inbox),
            project_id=project_id,
            force_reindex=getattr(config.processing, "force_reindex", False),
            enable_understanding=enable_understanding,
            understanding_provider=understanding_provider
        )

        # Initialize metadata embedder if configured
        self.metadata_embedder = None
        self.embed_metadata = getattr(config, "embed_metadata", True)  # Default to embedding
        if self.embed_metadata:
            self.metadata_embedder = MetadataEmbedder()
            logger.info("Metadata embedding enabled")

        # Create search engine
        self.search_engine = None
        self._update_search_engine()

    def _get_project_id(self, config) -> str:
        """Extract or generate project ID from config."""
        # Could be enhanced to detect from folder structure or config
        return getattr(config, "project_id", "default_project")

    # TODO: Review unreachable code - def _update_search_engine(self):
    # TODO: Review unreachable code - """Update search engine with current metadata."""
    # TODO: Review unreachable code - self.metadata_cache.get_all_metadata()
    # TODO: Review unreachable code - # Always create search engine, even with empty metadata
    # TODO: Review unreachable code - # Search engine removed - use DuckDBSearch instead

    # TODO: Review unreachable code - def _analyze_media(self, media_path: Path, project_folder: str) -> dict:
    # TODO: Review unreachable code - """Analyze media file to extract metadata with AI understanding.

    # TODO: Review unreachable code - This overrides the parent method to add direct AI understanding
    # TODO: Review unreachable code - without using the pipeline system.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - media_path: Path to media file
    # TODO: Review unreachable code - project_folder: Project folder name

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Analysis result as dictionary
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Call parent to get basic analysis
    # TODO: Review unreachable code - analysis = super()._analyze_media(media_path, project_folder)

    # TODO: Review unreachable code - # Skip if not an image or understanding is disabled
    # TODO: Review unreachable code - if not self.understanding_enabled or analysis["media_type"] != MediaType.IMAGE:
    # TODO: Review unreachable code - return analysis

    # TODO: Review unreachable code - # Check if we should analyze
    # TODO: Review unreachable code - metadata = {
    # TODO: Review unreachable code - "media_type": analysis["media_type"],
    # TODO: Review unreachable code - "understanding_provider": analysis.get("understanding_provider"),
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - if not should_analyze_image(metadata):
    # TODO: Review unreachable code - return analysis

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Run async analysis in sync context
    # TODO: Review unreachable code - loop = asyncio.new_event_loop()
    # TODO: Review unreachable code - asyncio.set_event_loop(loop)

    # TODO: Review unreachable code - understanding_result = loop.run_until_complete(
    # TODO: Review unreachable code - analyze_image(
    # TODO: Review unreachable code - media_path,
    # TODO: Review unreachable code - provider=self.understanding_provider,
    # TODO: Review unreachable code - detailed=self.understanding_detailed,
    # TODO: Review unreachable code - extract_tags=True,
    # TODO: Review unreachable code - generate_prompt=True,
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Merge understanding results into analysis
    # TODO: Review unreachable code - if understanding_result:
    # TODO: Review unreachable code - # Store understanding data in the analysis
    # TODO: Review unreachable code - analysis["understanding"] = understanding_result

    # TODO: Review unreachable code - # Also merge top-level fields for compatibility
    # TODO: Review unreachable code - for key in ["tags", "description", "positive_prompt", "negative_prompt",
    # TODO: Review unreachable code - "understanding_provider", "understanding_model", "understanding_cost"]:
    # TODO: Review unreachable code - if key in understanding_result:
    # TODO: Review unreachable code - analysis[key] = understanding_result[key]

    # TODO: Review unreachable code - provider = understanding_result.get('understanding_provider')
    # TODO: Review unreachable code - cost = understanding_result.get('understanding_cost', 0)
    # TODO: Review unreachable code - logger.info(
    # TODO: Review unreachable code - f"Analyzed {media_path.name} with {provider} (${cost:.4f})"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Image understanding failed for {media_path.name}: {e}")

    # TODO: Review unreachable code - finally:
    # TODO: Review unreachable code - # Clean up event loop
    # TODO: Review unreachable code - with contextlib.suppress(Exception):
    # TODO: Review unreachable code - loop.close()

    # TODO: Review unreachable code - return analysis

    # TODO: Review unreachable code - def _process_file(self, media_path: Path) -> OrganizeResult:
    # TODO: Review unreachable code - """Process a single media file with enhanced metadata.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - media_path: Path to the media file

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Organization result
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # First do standard processing
    # TODO: Review unreachable code - result = super()._process_file(media_path)

    # TODO: Review unreachable code - # If successful, enhance metadata
    # TODO: Review unreachable code - if result is not None and result["status"] == "success":
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Get the basic analysis
    # TODO: Review unreachable code - analysis = AnalysisResult(
    # TODO: Review unreachable code - source_type=result.get("source_type", "unknown"),
    # TODO: Review unreachable code - date_taken=result.get("date", ""),
    # TODO: Review unreachable code - project_folder=result.get("project_folder", "unknown"),
    # TODO: Review unreachable code - media_type=result.get("media_type", MediaType.UNKNOWN),
    # TODO: Review unreachable code - file_number=result.get("file_number"),
    # TODO: Review unreachable code - quality_stars=None,
    # TODO: Review unreachable code - brisque_score=None,
    # TODO: Review unreachable code - pipeline_result=result.get("pipeline_result"),
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Extract enhanced metadata
    # TODO: Review unreachable code - content_hash = self.metadata_cache.get_content_hash(media_path)
    # TODO: Review unreachable code - enhanced_metadata = self.metadata_cache.extractor.extract_metadata(
    # TODO: Review unreachable code - media_path, analysis, self.metadata_cache.project_id, content_hash
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Auto-detect relationships
    # TODO: Review unreachable code - self._detect_relationships(enhanced_metadata)

    # TODO: Review unreachable code - # Save enhanced metadata
    # TODO: Review unreachable code - self.metadata_cache.save_enhanced(
    # TODO: Review unreachable code - media_path,
    # TODO: Review unreachable code - analysis,
    # TODO: Review unreachable code - analysis_time=0.0,  # Could track actual time
    # TODO: Review unreachable code - enhanced_metadata=enhanced_metadata,
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Save to persistent storage if enabled
    # TODO: Review unreachable code - if self.metadata_embedder and result.get("destination"):
    # TODO: Review unreachable code - output_path = Path(result["destination"])
    # TODO: Review unreachable code - if output_path.exists():
    # TODO: Review unreachable code - # Prepare metadata for embedding
    # TODO: Review unreachable code - embed_metadata = {
    # TODO: Review unreachable code - "asset_id": enhanced_metadata["asset_id"],
    # TODO: Review unreachable code - "prompt": enhanced_metadata.get("prompt"),
    # TODO: Review unreachable code - "generation_params": enhanced_metadata.get("generation_params"),
    # TODO: Review unreachable code - # Semantic tags
    # TODO: Review unreachable code - "style_tags": enhanced_metadata.get("style_tags", []),
    # TODO: Review unreachable code - "mood_tags": enhanced_metadata.get("mood_tags", []),
    # TODO: Review unreachable code - "subject_tags": enhanced_metadata.get("subject_tags", []),
    # TODO: Review unreachable code - "color_tags": enhanced_metadata.get("color_tags", []),
    # TODO: Review unreachable code - "custom_tags": enhanced_metadata.get("custom_tags", []),
    # TODO: Review unreachable code - # Relationships and role
    # TODO: Review unreachable code - "relationships": enhanced_metadata.get("relationships", {}),
    # TODO: Review unreachable code - "role": (
    # TODO: Review unreachable code - enhanced_metadata.get("role").value
    # TODO: Review unreachable code - if hasattr(enhanced_metadata.get("role"), "value")
    # TODO: Review unreachable code - else enhanced_metadata.get("role")
    # TODO: Review unreachable code - ),
    # TODO: Review unreachable code - "project_id": enhanced_metadata.get("project_id"),
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Include any pipeline results
    # TODO: Review unreachable code - if result is not None and "sightengine_quality" in result:
    # TODO: Review unreachable code - embed_metadata.update(
    # TODO: Review unreachable code - {
    # TODO: Review unreachable code - "sightengine_quality": result.get("sightengine_quality"),
    # TODO: Review unreachable code - "sightengine_sharpness": result.get("sightengine_sharpness"),
    # TODO: Review unreachable code - "sightengine_contrast": result.get("sightengine_contrast"),
    # TODO: Review unreachable code - "sightengine_brightness": result.get("sightengine_brightness"),
    # TODO: Review unreachable code - "sightengine_ai_generated": result.get(
    # TODO: Review unreachable code - "sightengine_ai_generated"
    # TODO: Review unreachable code - ),
    # TODO: Review unreachable code - "sightengine_ai_probability": result.get(
    # TODO: Review unreachable code - "sightengine_ai_probability"
    # TODO: Review unreachable code - ),
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - if result is not None and "claude_defects_found" in result:
    # TODO: Review unreachable code - embed_metadata.update(
    # TODO: Review unreachable code - {
    # TODO: Review unreachable code - "claude_defects_found": result.get("claude_defects_found"),
    # TODO: Review unreachable code - "claude_defect_count": result.get("claude_defect_count"),
    # TODO: Review unreachable code - "claude_severity": result.get("claude_severity"),
    # TODO: Review unreachable code - "claude_confidence": result.get("claude_confidence"),
    # TODO: Review unreachable code - "claude_quality_score": result.get("claude_quality_score"),
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Save to image
    # TODO: Review unreachable code - success = self.metadata_embedder.embed_metadata(
    # TODO: Review unreachable code - output_path, embed_metadata
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - if success:
    # TODO: Review unreachable code - logger.debug(f"Embedded metadata in {output_path.name}")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - logger.warning(f"Failed to embed metadata in {output_path.name}")

    # TODO: Review unreachable code - # Update search engine
    # TODO: Review unreachable code - self._update_search_engine()

    # TODO: Review unreachable code - logger.debug(f"Enhanced metadata for {media_path.name}")

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to enhance metadata for {media_path.name}: {e}")

    # TODO: Review unreachable code - return result

    # TODO: Review unreachable code - def _detect_relationships(self, metadata: AssetMetadata) -> None:
    # TODO: Review unreachable code - """Automatically detect relationships with existing assets."""
    # TODO: Review unreachable code - if not self.search_engine:
    # TODO: Review unreachable code - return

    # TODO: Review unreachable code - # Find similar assets
    # TODO: Review unreachable code - similar_assets = self.search_engine.find_similar_assets(
    # TODO: Review unreachable code - metadata["asset_id"], similarity_threshold=0.7, limit=5
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - similar_ids = [asset["asset_id"] for asset in similar_assets]
    # TODO: Review unreachable code - metadata["similar_to"] = similar_ids

    # TODO: Review unreachable code - # Detect if this is a variation based on filename
    # TODO: Review unreachable code - filename = metadata["file_name"].lower()
    # TODO: Review unreachable code - if any(pattern in filename for pattern in ["_v2", "_v3", "variation", "alt"]):
    # TODO: Review unreachable code - # Try to find the original
    # TODO: Review unreachable code - base_name = (
    # TODO: Review unreachable code - filename.split("_v")[0]
    # TODO: Review unreachable code - if "_v" in filename
    # TODO: Review unreachable code - else filename.replace("variation", "").replace("alt", "")
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Search for potential parent
    # TODO: Review unreachable code - results = self.search_engine.search_by_description(base_name, limit=5)
    # TODO: Review unreachable code - for result in results:
    # TODO: Review unreachable code - if result is not None and result["created_at"] < metadata["created_at"]:
    # TODO: Review unreachable code - # This could be the parent
    # TODO: Review unreachable code - metadata["parent_id"] = result["asset_id"]
    # TODO: Review unreachable code - metadata["variation_of"] = result["asset_id"]
    # TODO: Review unreachable code - break

    # TODO: Review unreachable code - def search_assets(self, **kwargs) -> list[AssetMetadata]:
    # TODO: Review unreachable code - """Search for assets using various criteria.

    # TODO: Review unreachable code - This is the main interface for AI to find assets.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - **kwargs: Search parameters matching SearchQuery fields

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of matching assets
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not self.search_engine:
    # TODO: Review unreachable code - logger.warning("No search engine available")
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - from ..assets.metadata.models import SearchQuery

    # TODO: Review unreachable code - query = SearchQuery(**kwargs)
    # TODO: Review unreachable code - return self.search_engine.search_assets(query)

    # TODO: Review unreachable code - def find_similar(self, asset_id: str, threshold: float = 0.7) -> list[AssetMetadata]:
    # TODO: Review unreachable code - """Find assets similar to a given asset.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - asset_id: Reference asset ID
    # TODO: Review unreachable code - threshold: Similarity threshold (0-1)

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - List of similar assets
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not self.search_engine:
    # TODO: Review unreachable code - return []

    # TODO: Review unreachable code - return self.search_engine.find_similar_assets(asset_id, threshold)

    # TODO: Review unreachable code - def tag_asset(self, asset_id: str, tags: list[str], tag_type: str = "custom_tags") -> bool:
    # TODO: Review unreachable code - """Add tags to an asset.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - asset_id: Asset ID
    # TODO: Review unreachable code - tags: List of tags to add
    # TODO: Review unreachable code - tag_type: Type of tags (style_tags, mood_tags, custom_tags, etc.)

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - True if successful
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - success = self.metadata_cache.add_tags(asset_id, tag_type, tags)
    # TODO: Review unreachable code - if success:
    # TODO: Review unreachable code - self._update_search_engine()
    # TODO: Review unreachable code - return success

    # TODO: Review unreachable code - def set_asset_role(self, asset_id: str, role: AssetRole) -> bool:
    # TODO: Review unreachable code - """Set the creative role of an asset.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - asset_id: Asset ID
    # TODO: Review unreachable code - role: Asset role

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - True if successful
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - success = self.metadata_cache.update_metadata(asset_id, {"role": role})
    # TODO: Review unreachable code - if success:
    # TODO: Review unreachable code - self._update_search_engine()
    # TODO: Review unreachable code - return success

    # TODO: Review unreachable code - def group_assets(self, asset_ids: list[str], group_name: str) -> bool:
    # TODO: Review unreachable code - """Group multiple assets together.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - asset_ids: List of asset IDs to group
    # TODO: Review unreachable code - group_name: Name for the group

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - True if successful
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # For now, we'll use the grouped_with relationship
    # TODO: Review unreachable code - # In future, could create a proper group entity
    # TODO: Review unreachable code - success = True

    # TODO: Review unreachable code - for i, asset_id in enumerate(asset_ids):
    # TODO: Review unreachable code - other_assets = [aid for j, aid in enumerate(asset_ids) if j != i]
    # TODO: Review unreachable code - if not self.metadata_cache.update_metadata(
    # TODO: Review unreachable code - asset_id, {"grouped_with": other_assets, "custom_tags": [f"group:{group_name}"]}
    # TODO: Review unreachable code - ):
    # TODO: Review unreachable code - success = False

    # TODO: Review unreachable code - if success:
    # TODO: Review unreachable code - self._update_search_engine()

    # TODO: Review unreachable code - return success

    # TODO: Review unreachable code - def get_project_context(self) -> dict:
    # TODO: Review unreachable code - """Get current project context for AI understanding.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Project context information
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - all_metadata = self.metadata_cache.get_all_metadata()

    # TODO: Review unreachable code - # Analyze metadata to build context
    # TODO: Review unreachable code - style_counts = {}
    # TODO: Review unreachable code - mood_counts = {}
    # TODO: Review unreachable code - role_counts = {}
    # TODO: Review unreachable code - source_counts = {}

    # TODO: Review unreachable code - for metadata in all_metadata.values():
    # TODO: Review unreachable code - # Count styles
    # TODO: Review unreachable code - for style in metadata.get("style_tags", []):
    # TODO: Review unreachable code - style_counts[style] = style_counts.get(style, 0) + 1

    # TODO: Review unreachable code - # Count moods
    # TODO: Review unreachable code - for mood in metadata.get("mood_tags", []):
    # TODO: Review unreachable code - mood_counts[mood] = mood_counts.get(mood, 0) + 1

    # TODO: Review unreachable code - # Count roles
    # TODO: Review unreachable code - role = metadata.get("role")
    # TODO: Review unreachable code - if role:
    # TODO: Review unreachable code - role_counts[role.value] = role_counts.get(role.value, 0) + 1

    # TODO: Review unreachable code - # Count sources
    # TODO: Review unreachable code - source = metadata.get("source_type")
    # TODO: Review unreachable code - if source:
    # TODO: Review unreachable code - source_counts[source] = source_counts.get(source, 0) + 1

    # TODO: Review unreachable code - # Get most used styles
    # TODO: Review unreachable code - favorite_styles = sorted(style_counts.items(), key=lambda x: x[1], reverse=True)[:5]

    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "project_id": self.metadata_cache.project_id,
    # TODO: Review unreachable code - "total_assets": len(all_metadata),
    # TODO: Review unreachable code - "assets_by_role": role_counts,
    # TODO: Review unreachable code - "assets_by_source": source_counts,
    # TODO: Review unreachable code - "favorite_styles": [style for style, _ in favorite_styles],
    # TODO: Review unreachable code - "style_distribution": style_counts,
    # TODO: Review unreachable code - "mood_distribution": mood_counts,
    # TODO: Review unreachable code - "last_import": datetime.now().isoformat(),
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - def get_organization_summary(self) -> str:
    # TODO: Review unreachable code - """Get enhanced organization summary.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Summary text with metadata statistics
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Build summary from stats
    # TODO: Review unreachable code - summary = "\nOrganization Summary:\n"
    # TODO: Review unreachable code - summary += f"  Total files processed: {self.stats['total']}\n"
    # TODO: Review unreachable code - summary += f"  Successfully organized: {self.stats['organized']}"

    # TODO: Review unreachable code - # Add metadata statistics
    # TODO: Review unreachable code - if self.search_engine:
    # TODO: Review unreachable code - all_metadata = self.metadata_cache.get_all_metadata()

    # TODO: Review unreachable code - summary += "\n\nMetadata Enrichment:"
    # TODO: Review unreachable code - summary += f"\n  Enhanced assets: {len(all_metadata)}"

    # TODO: Review unreachable code - # Count assets with various metadata
    # TODO: Review unreachable code - with_prompts = sum(1 for m in all_metadata.values() if m.get("prompt"))
    # TODO: Review unreachable code - with_styles = sum(1 for m in all_metadata.values() if m.get("style_tags"))
    # TODO: Review unreachable code - with_relationships = sum(
    # TODO: Review unreachable code - 1 for m in all_metadata.values() if m.get("parent_id") or m.get("similar_to")
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - summary += f"\n  With prompts: {with_prompts}"
    # TODO: Review unreachable code - summary += f"\n  With style tags: {with_styles}"
    # TODO: Review unreachable code - summary += f"\n  With relationships: {with_relationships}"

    # TODO: Review unreachable code - return summary
