"""Enhanced media organizer with rich metadata support."""

import logging
from datetime import datetime
from pathlib import Path

from omegaconf import DictConfig

from ..core.cache_migration import EnhancedMetadataCacheAdapter as EnhancedMetadataCache
from ..core.cache_migration import PersistentMetadataManagerAdapter as PersistentMetadataManager
from ..core.types import AnalysisResult, MediaType, OrganizeResult
from ..metadata.models import AssetMetadata, AssetRole
from ..metadata.search import AssetSearchEngine
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

        # Replace standard cache with enhanced cache
        project_id = self._get_project_id(config)
        self.metadata_cache = EnhancedMetadataCache(
            source_root=Path(config.paths.inbox),
            project_id=project_id,
            force_reindex=getattr(config.processing, "force_reindex", False),
        )

        # Initialize persistent metadata manager if configured
        self.persistent_metadata = None
        self.embed_metadata = getattr(config, "embed_metadata", True)  # Default to embedding
        if self.embed_metadata:
            cache_dir = Path(
                getattr(config.paths, "cache_dir", Path.home() / ".alicemultiverse" / "cache")
            )
            self.persistent_metadata = PersistentMetadataManager(cache_dir, {})
            logger.info("Persistent metadata embedding enabled")

        # Create search engine
        self.search_engine = None
        self._update_search_engine()

    def _get_project_id(self, config) -> str:
        """Extract or generate project ID from config."""
        # Could be enhanced to detect from folder structure or config
        return getattr(config, "project_id", "default_project")

    def _update_search_engine(self):
        """Update search engine with current metadata."""
        metadata_store = self.metadata_cache.get_all_metadata()
        # Always create search engine, even with empty metadata
        self.search_engine = AssetSearchEngine(metadata_store or {})

    def _process_file(self, media_path: Path) -> OrganizeResult:
        """Process a single media file with enhanced metadata.

        Args:
            media_path: Path to the media file

        Returns:
            Organization result
        """
        # First do standard processing
        result = super()._process_file(media_path)

        # If successful, enhance metadata
        if result["status"] == "success":
            try:
                # Get the basic analysis
                analysis = AnalysisResult(
                    source_type=result.get("source_type", "unknown"),
                    date_taken=result.get("date", ""),
                    project_folder=result.get("project_folder", "unknown"),
                    media_type=result.get("media_type", MediaType.UNKNOWN),
                    file_number=result.get("file_number"),
                    quality_stars=None,
                    brisque_score=None,
                    pipeline_result=result.get("pipeline_result"),
                )

                # Extract enhanced metadata
                content_hash = self.metadata_cache.get_content_hash(media_path)
                enhanced_metadata = self.metadata_cache.extractor.extract_metadata(
                    media_path, analysis, self.metadata_cache.project_id, content_hash
                )

                # Auto-detect relationships
                self._detect_relationships(enhanced_metadata)

                # Save enhanced metadata
                self.metadata_cache.save_enhanced(
                    media_path,
                    analysis,
                    analysis_time=0.0,  # Could track actual time
                    enhanced_metadata=enhanced_metadata,
                )

                # Save to persistent storage if enabled
                if self.persistent_metadata and result.get("destination"):
                    output_path = Path(result["destination"])
                    if output_path.exists():
                        # Prepare metadata for embedding
                        embed_metadata = {
                            "asset_id": enhanced_metadata["asset_id"],
                            "prompt": enhanced_metadata.get("prompt"),
                            "generation_params": enhanced_metadata.get("generation_params"),
                            # Semantic tags
                            "style_tags": enhanced_metadata.get("style_tags", []),
                            "mood_tags": enhanced_metadata.get("mood_tags", []),
                            "subject_tags": enhanced_metadata.get("subject_tags", []),
                            "color_tags": enhanced_metadata.get("color_tags", []),
                            "custom_tags": enhanced_metadata.get("custom_tags", []),
                            # Relationships and role
                            "relationships": enhanced_metadata.get("relationships", {}),
                            "role": (
                                enhanced_metadata.get("role").value
                                if hasattr(enhanced_metadata.get("role"), "value")
                                else enhanced_metadata.get("role")
                            ),
                            "project_id": enhanced_metadata.get("project_id"),
                        }

                        # Include any pipeline results
                        if "sightengine_quality" in result:
                            embed_metadata.update(
                                {
                                    "sightengine_quality": result.get("sightengine_quality"),
                                    "sightengine_sharpness": result.get("sightengine_sharpness"),
                                    "sightengine_contrast": result.get("sightengine_contrast"),
                                    "sightengine_brightness": result.get("sightengine_brightness"),
                                    "sightengine_ai_generated": result.get(
                                        "sightengine_ai_generated"
                                    ),
                                    "sightengine_ai_probability": result.get(
                                        "sightengine_ai_probability"
                                    ),
                                }
                            )

                        if "claude_defects_found" in result:
                            embed_metadata.update(
                                {
                                    "claude_defects_found": result.get("claude_defects_found"),
                                    "claude_defect_count": result.get("claude_defect_count"),
                                    "claude_severity": result.get("claude_severity"),
                                    "claude_confidence": result.get("claude_confidence"),
                                    "claude_quality_score": result.get("claude_quality_score"),
                                }
                            )

                        # Save to image
                        success = self.persistent_metadata.save_metadata(
                            output_path, embed_metadata
                        )
                        if success:
                            logger.debug(f"Embedded metadata in {output_path.name}")
                        else:
                            logger.warning(f"Failed to embed metadata in {output_path.name}")

                # Update search engine
                self._update_search_engine()

                logger.debug(f"Enhanced metadata for {media_path.name}")

            except Exception as e:
                logger.error(f"Failed to enhance metadata for {media_path.name}: {e}")

        return result

    def _detect_relationships(self, metadata: AssetMetadata) -> None:
        """Automatically detect relationships with existing assets."""
        if not self.search_engine:
            return

        # Find similar assets
        similar_assets = self.search_engine.find_similar_assets(
            metadata["asset_id"], similarity_threshold=0.7, limit=5
        )

        similar_ids = [asset["asset_id"] for asset in similar_assets]
        metadata["similar_to"] = similar_ids

        # Detect if this is a variation based on filename
        filename = metadata["file_name"].lower()
        if any(pattern in filename for pattern in ["_v2", "_v3", "variation", "alt"]):
            # Try to find the original
            base_name = (
                filename.split("_v")[0]
                if "_v" in filename
                else filename.replace("variation", "").replace("alt", "")
            )

            # Search for potential parent
            results = self.search_engine.search_by_description(base_name, limit=5)
            for result in results:
                if result["created_at"] < metadata["created_at"]:
                    # This could be the parent
                    metadata["parent_id"] = result["asset_id"]
                    metadata["variation_of"] = result["asset_id"]
                    break

    def search_assets(self, **kwargs) -> list[AssetMetadata]:
        """Search for assets using various criteria.

        This is the main interface for AI to find assets.

        Args:
            **kwargs: Search parameters matching SearchQuery fields

        Returns:
            List of matching assets
        """
        if not self.search_engine:
            logger.warning("No search engine available")
            return []

        from ..metadata.models import SearchQuery

        query = SearchQuery(**kwargs)
        return self.search_engine.search_assets(query)

    def find_similar(self, asset_id: str, threshold: float = 0.7) -> list[AssetMetadata]:
        """Find assets similar to a given asset.

        Args:
            asset_id: Reference asset ID
            threshold: Similarity threshold (0-1)

        Returns:
            List of similar assets
        """
        if not self.search_engine:
            return []

        return self.search_engine.find_similar_assets(asset_id, threshold)

    def tag_asset(self, asset_id: str, tags: list[str], tag_type: str = "custom_tags") -> bool:
        """Add tags to an asset.

        Args:
            asset_id: Asset ID
            tags: List of tags to add
            tag_type: Type of tags (style_tags, mood_tags, custom_tags, etc.)

        Returns:
            True if successful
        """
        success = self.metadata_cache.add_tags(asset_id, tag_type, tags)
        if success:
            self._update_search_engine()
        return success

    def set_asset_role(self, asset_id: str, role: AssetRole) -> bool:
        """Set the creative role of an asset.

        Args:
            asset_id: Asset ID
            role: Asset role

        Returns:
            True if successful
        """
        success = self.metadata_cache.update_metadata(asset_id, {"role": role})
        if success:
            self._update_search_engine()
        return success

    def group_assets(self, asset_ids: list[str], group_name: str) -> bool:
        """Group multiple assets together.

        Args:
            asset_ids: List of asset IDs to group
            group_name: Name for the group

        Returns:
            True if successful
        """
        # For now, we'll use the grouped_with relationship
        # In future, could create a proper group entity
        success = True

        for i, asset_id in enumerate(asset_ids):
            other_assets = [aid for j, aid in enumerate(asset_ids) if j != i]
            if not self.metadata_cache.update_metadata(
                asset_id, {"grouped_with": other_assets, "custom_tags": [f"group:{group_name}"]}
            ):
                success = False

        if success:
            self._update_search_engine()

        return success

    def get_project_context(self) -> dict:
        """Get current project context for AI understanding.

        Returns:
            Project context information
        """
        all_metadata = self.metadata_cache.get_all_metadata()

        # Analyze metadata to build context
        style_counts = {}
        mood_counts = {}
        role_counts = {}
        source_counts = {}

        for metadata in all_metadata.values():
            # Count styles
            for style in metadata.get("style_tags", []):
                style_counts[style] = style_counts.get(style, 0) + 1

            # Count moods
            for mood in metadata.get("mood_tags", []):
                mood_counts[mood] = mood_counts.get(mood, 0) + 1

            # Count roles
            role = metadata.get("role")
            if role:
                role_counts[role.value] = role_counts.get(role.value, 0) + 1

            # Count sources
            source = metadata.get("source_type")
            if source:
                source_counts[source] = source_counts.get(source, 0) + 1

        # Get most used styles
        favorite_styles = sorted(style_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "project_id": self.metadata_cache.project_id,
            "total_assets": len(all_metadata),
            "assets_by_role": role_counts,
            "assets_by_source": source_counts,
            "favorite_styles": [style for style, _ in favorite_styles],
            "style_distribution": style_counts,
            "mood_distribution": mood_counts,
            "last_import": datetime.now().isoformat(),
        }

    def get_organization_summary(self) -> str:
        """Get enhanced organization summary.

        Returns:
            Summary text with metadata statistics
        """
        # Build summary from stats
        summary = "\nOrganization Summary:\n"
        summary += f"  Total files processed: {self.stats['total']}\n"
        summary += f"  Successfully organized: {self.stats['organized']}"

        # Add metadata statistics
        if self.search_engine:
            all_metadata = self.metadata_cache.get_all_metadata()

            summary += "\n\nMetadata Enrichment:"
            summary += f"\n  Enhanced assets: {len(all_metadata)}"

            # Count assets with various metadata
            with_prompts = sum(1 for m in all_metadata.values() if m.get("prompt"))
            with_styles = sum(1 for m in all_metadata.values() if m.get("style_tags"))
            with_relationships = sum(
                1 for m in all_metadata.values() if m.get("parent_id") or m.get("similar_to")
            )

            summary += f"\n  With prompts: {with_prompts}"
            summary += f"\n  With style tags: {with_styles}"
            summary += f"\n  With relationships: {with_relationships}"

        return summary
