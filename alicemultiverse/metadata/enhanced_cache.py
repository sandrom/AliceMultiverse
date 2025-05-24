"""Enhanced metadata cache that stores rich metadata for AI navigation.

DEPRECATED: This module is deprecated and will be removed in v3.0.
Please use alicemultiverse.core.unified_cache.UnifiedCache instead.
"""

import json
import logging
import warnings
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any, List

from ..core.metadata_cache import MetadataCache
from ..core.types import AnalysisResult, MediaType
from .models import AssetMetadata, AssetRole
from .extractor import MetadataExtractor

logger = logging.getLogger(__name__)

# Issue deprecation warning when module is imported
warnings.warn(
    "EnhancedMetadataCache is deprecated and will be removed in v3.0. "
    "Please use UnifiedCache instead. "
    "Current code uses adapters for compatibility.",
    DeprecationWarning,
    stacklevel=2
)


class EnhancedMetadataCache(MetadataCache):
    """Extended metadata cache that stores rich metadata for AI navigation."""
    
    def __init__(self, source_root: Path, project_id: str, force_reindex: bool = False):
        """Initialize enhanced metadata cache.
        
        Args:
            source_root: Root directory for source files
            project_id: Current project identifier
            force_reindex: Whether to bypass cache and force re-analysis
        """
        super().__init__(source_root, force_reindex)
        self.project_id = project_id
        self.extractor = MetadataExtractor()
        
        # In-memory index for quick searches
        self.metadata_index: Dict[str, AssetMetadata] = {}
        self._load_metadata_index()
    
    def _load_metadata_index(self) -> None:
        """Load all metadata into memory for quick searching."""
        if self.force_reindex or not self._cache_dir.exists():
            return
        
        logger.info("Loading metadata index...")
        loaded_count = 0
        
        for cache_file in self._cache_dir.glob("*.json"):
            try:
                with open(cache_file, 'r') as f:
                    data = json.load(f)
                
                # Check if it has enhanced metadata
                if 'enhanced_metadata' in data:
                    asset_id = data['content_hash']
                    # Convert dict back to AssetMetadata
                    enhanced = data['enhanced_metadata']
                    # Convert datetime strings back to datetime objects
                    for date_field in ['created_at', 'modified_at', 'imported_at']:
                        if date_field in enhanced and enhanced[date_field]:
                            enhanced[date_field] = datetime.fromisoformat(enhanced[date_field])
                    
                    self.metadata_index[asset_id] = enhanced
                    loaded_count += 1
                    
            except Exception as e:
                logger.warning(f"Failed to load metadata from {cache_file}: {e}")
        
        logger.info(f"Loaded {loaded_count} enhanced metadata entries")
    
    def save_enhanced(
        self,
        media_path: Path,
        analysis: AnalysisResult,
        analysis_time: float,
        enhanced_metadata: Optional[AssetMetadata] = None
    ) -> None:
        """Save both basic and enhanced metadata.
        
        Args:
            media_path: Path to the media file
            analysis: Basic analysis results
            analysis_time: Time taken for analysis
            enhanced_metadata: Rich metadata for AI navigation
        """
        # Get content hash
        content_hash = self.get_content_hash(media_path)
        
        # Generate enhanced metadata if not provided
        if enhanced_metadata is None:
            enhanced_metadata = self.extractor.extract_metadata(
                media_path, analysis, self.project_id, content_hash
            )
        
        # Store in memory index
        self.metadata_index[content_hash] = enhanced_metadata
        
        # Prepare for JSON serialization
        enhanced_dict = dict(enhanced_metadata)
        
        # Convert datetime objects to ISO format strings
        for key, value in enhanced_dict.items():
            if isinstance(value, datetime):
                enhanced_dict[key] = value.isoformat()
            elif isinstance(value, AssetRole):
                enhanced_dict[key] = value.value
        
        # Save using parent method but add enhanced metadata
        try:
            # First save basic metadata
            super().save(media_path, analysis, analysis_time)
            
            # Then add enhanced metadata to the cache file
            cache_path = self._get_cache_path(content_hash)
            
            # Read existing cache
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            # Add enhanced metadata
            cache_data['enhanced_metadata'] = enhanced_dict
            
            # Write back
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
                
            logger.debug(f"Saved enhanced metadata for {media_path.name}")
            
        except Exception as e:
            logger.error(f"Failed to save enhanced metadata for {media_path.name}: {e}")
    
    def load_enhanced(self, media_path: Path) -> Optional[AssetMetadata]:
        """Load enhanced metadata for a media file.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            Enhanced metadata if available, None otherwise
        """
        # Try memory index first
        content_hash = self.get_content_hash(media_path)
        if content_hash in self.metadata_index:
            return self.metadata_index[content_hash]
        
        # Try loading from disk
        cache_data = self.load(media_path)
        if cache_data and 'enhanced_metadata' in cache_data:
            enhanced = cache_data['enhanced_metadata']
            
            # Convert datetime strings back
            for date_field in ['created_at', 'modified_at', 'imported_at']:
                if date_field in enhanced and enhanced[date_field]:
                    enhanced[date_field] = datetime.fromisoformat(enhanced[date_field])
            
            # Store in memory index
            self.metadata_index[content_hash] = enhanced
            return enhanced
        
        return None
    
    def get_all_metadata(self) -> Dict[str, AssetMetadata]:
        """Get all metadata in the cache.
        
        Returns:
            Dictionary mapping asset IDs to metadata
        """
        return self.metadata_index.copy()
    
    def update_metadata(self, asset_id: str, updates: Dict[str, Any]) -> bool:
        """Update specific fields in asset metadata.
        
        Args:
            asset_id: Asset ID (content hash)
            updates: Dictionary of fields to update
            
        Returns:
            True if successful, False otherwise
        """
        if asset_id not in self.metadata_index:
            logger.warning(f"Asset {asset_id} not found in metadata index")
            return False
        
        try:
            # Update in memory
            metadata = self.metadata_index[asset_id]
            for key, value in updates.items():
                if key in metadata:
                    metadata[key] = value
            
            # Update on disk
            cache_path = self._get_cache_path(asset_id)
            if cache_path.exists():
                with open(cache_path, 'r') as f:
                    cache_data = json.load(f)
                
                # Update enhanced metadata
                if 'enhanced_metadata' in cache_data:
                    for key, value in updates.items():
                        if key in cache_data['enhanced_metadata']:
                            # Convert datetime to string if needed
                            if isinstance(value, datetime):
                                value = value.isoformat()
                            elif isinstance(value, AssetRole):
                                value = value.value
                            cache_data['enhanced_metadata'][key] = value
                
                # Write back
                with open(cache_path, 'w') as f:
                    json.dump(cache_data, f, indent=2)
                
                logger.debug(f"Updated metadata for asset {asset_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to update metadata for {asset_id}: {e}")
            return False
    
    def add_tags(self, asset_id: str, tag_type: str, tags: List[str]) -> bool:
        """Add tags to an asset.
        
        Args:
            asset_id: Asset ID (content hash)
            tag_type: Type of tags (style_tags, mood_tags, etc.)
            tags: List of tags to add
            
        Returns:
            True if successful, False otherwise
        """
        if asset_id not in self.metadata_index:
            return False
        
        metadata = self.metadata_index[asset_id]
        current_tags = metadata.get(tag_type, [])
        
        # Add new tags (avoid duplicates)
        for tag in tags:
            if tag not in current_tags:
                current_tags.append(tag)
        
        return self.update_metadata(asset_id, {tag_type: current_tags})
    
    def set_relationship(
        self,
        from_asset: str,
        to_asset: str,
        relationship_type: str
    ) -> bool:
        """Set a relationship between two assets.
        
        Args:
            from_asset: Source asset ID
            to_asset: Target asset ID
            relationship_type: Type of relationship
            
        Returns:
            True if successful, False otherwise
        """
        if from_asset not in self.metadata_index:
            return False
        
        metadata = self.metadata_index[from_asset]
        
        if relationship_type == "parent":
            return self.update_metadata(from_asset, {"parent_id": to_asset})
        elif relationship_type == "variation":
            return self.update_metadata(from_asset, {"variation_of": to_asset})
        elif relationship_type == "similar":
            similar = metadata.get("similar_to", [])
            if to_asset not in similar:
                similar.append(to_asset)
            return self.update_metadata(from_asset, {"similar_to": similar})
        elif relationship_type == "grouped":
            grouped = metadata.get("grouped_with", [])
            if to_asset not in grouped:
                grouped.append(to_asset)
            return self.update_metadata(from_asset, {"grouped_with": grouped})
        
        return False