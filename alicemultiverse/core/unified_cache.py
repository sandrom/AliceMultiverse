"""Unified cache implementation that consolidates all caching functionality."""

import logging
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime

from .metadata_cache import MetadataCache
from .types import AnalysisResult, MediaType
from ..metadata.models import AssetMetadata
from ..metadata.embedder import MetadataEmbedder
from ..metadata.extractor import MetadataExtractor  
from ..quality.scorer import QualityScorer

logger = logging.getLogger(__name__)


class UnifiedCache:
    """Unified cache that consolidates all metadata functionality.
    
    This class combines:
    - Basic file caching (from MetadataCache)
    - Enhanced metadata and search (from EnhancedMetadataCache)
    - Image embedding (from PersistentMetadataManager)
    - Quality scoring (extracted to QualityScorer)
    
    The goal is to have a single, clean interface for all metadata operations
    while maintaining backward compatibility.
    """
    
    def __init__(
        self,
        source_root: Path,
        project_id: str = 'default',
        force_reindex: bool = False,
        quality_thresholds: Optional[Dict[str, Dict[str, float]]] = None
    ):
        """Initialize unified cache.
        
        Args:
            source_root: Root directory for source files
            project_id: Current project identifier
            force_reindex: Whether to bypass cache and force re-analysis
            quality_thresholds: Quality thresholds for star ratings
        """
        # Core components
        self.cache = MetadataCache(source_root, force_reindex)
        self.embedder = MetadataEmbedder()
        self.extractor = MetadataExtractor()
        self.scorer = QualityScorer(quality_thresholds)
        
        # Ensure cache directory exists
        cache_dir = source_root / ".metadata"
        if not force_reindex:
            cache_dir.mkdir(parents=True, exist_ok=True)
        
        # State
        self.source_root = source_root
        self.project_id = project_id
        self.force_reindex = force_reindex
        
        # In-memory index for enhanced search
        self.metadata_index: Dict[str, AssetMetadata] = {}
        if not force_reindex:
            self._load_metadata_index()
    
    # ===== Core Cache Interface (backward compatible) =====
    
    def load(self, media_path: Path) -> Optional[Dict[str, Any]]:
        """Load metadata for a media file (backward compatible).
        
        First tries embedded metadata, then falls back to cache.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            Cached metadata if available, None otherwise
        """
        # Check if file exists first
        if not media_path.exists():
            self.cache.cache_misses += 1
            return None
            
        # Try embedded metadata first (self-contained assets)
        if media_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif'}:
            try:
                embedded = self.embedder.extract_metadata(media_path)
                if embedded:
                    # Check various possible locations for our metadata
                    if 'alice_metadata' in embedded:
                        logger.debug(f"Loaded alice_metadata from image: {media_path.name}")
                        return embedded['alice_metadata']
                    elif 'metadata' in embedded:
                        logger.debug(f"Loaded metadata from image: {media_path.name}")
                        return embedded['metadata']
                    elif any(key.startswith('claude_') for key in embedded):
                        # This is the format the embedder extracts
                        logger.debug(f"Loaded embedded metadata from image: {media_path.name}")
                        return embedded
            except Exception as e:
                logger.debug(f"Could not extract embedded metadata: {e}")
        
        # Fall back to cache
        result = self.cache.load(media_path)
        
        # Track cache hit/miss
        if result is not None:
            self.cache.cache_hits += 1
        else:
            self.cache.cache_misses += 1
            
        return result
    
    def save(
        self,
        media_path: Path,
        analysis: AnalysisResult,
        analysis_time: float
    ) -> None:
        """Save metadata for a media file (backward compatible).
        
        Saves to both cache and embeds in image if possible.
        
        Args:
            media_path: Path to the media file
            analysis: Analysis results to cache
            analysis_time: Time taken for analysis
        """
        # First embed in image if supported (this modifies the file)
        if media_path.suffix.lower() in {'.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif'}:
            # The embedder expects the metadata directly, not wrapped
            metadata_to_embed = dict(analysis)
            metadata_to_embed['analysis_time'] = analysis_time
            metadata_to_embed['cached_at'] = datetime.now().isoformat()
            
            success = self.embedder.embed_metadata(media_path, metadata_to_embed)
            if success:
                logger.debug(f"Embedded metadata in image: {media_path.name}")
        
        # Save to cache AFTER embedding (so hash is correct)
        self.cache.save(media_path, analysis, analysis_time)
    
    # ===== Enhanced Metadata Interface =====
    
    def load_enhanced(self, media_path: Path) -> Optional[AssetMetadata]:
        """Load enhanced metadata with rich information.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            Enhanced metadata if available
        """
        # Get basic metadata
        basic = self.load(media_path)
        if not basic:
            return None
        
        # Check if already enhanced
        if 'enhanced_metadata' in basic:
            return basic['enhanced_metadata']
        
        # Generate enhanced metadata
        content_hash = self.cache.get_content_hash(media_path)
        # Extract just the analysis from the full metadata structure
        analysis = basic.get('analysis', basic) if isinstance(basic, dict) else basic
        enhanced = self.extractor.extract_metadata(
            file_path=media_path,
            analysis=analysis,
            project_id=self.project_id,
            content_hash=content_hash
        )
        
        # Store it
        self.metadata_index[content_hash] = enhanced
        return enhanced
    
    def save_enhanced(
        self,
        media_path: Path,
        analysis: AnalysisResult,
        analysis_time: float,
        enhanced_metadata: Optional[AssetMetadata] = None
    ) -> None:
        """Save enhanced metadata.
        
        Args:
            media_path: Path to the media file
            analysis: Basic analysis results
            analysis_time: Time taken for analysis
            enhanced_metadata: Rich metadata information
        """
        # Merge enhanced metadata into analysis
        if enhanced_metadata:
            analysis = dict(analysis)
            analysis['enhanced_metadata'] = enhanced_metadata
            
            # Update index
            content_hash = self.cache.get_content_hash(media_path)
            self.metadata_index[content_hash] = enhanced_metadata
        
        # Save through normal interface
        self.save(media_path, analysis, analysis_time)
    
    # ===== Quality Scoring Interface =====
    
    def calculate_quality(self, media_path: Path) -> Optional[Dict[str, Any]]:
        """Calculate quality scores for a media file.
        
        Args:
            media_path: Path to the media file
            
        Returns:
            Quality analysis results
        """
        # Get existing metadata
        metadata = self.load(media_path)
        if not metadata:
            return None
        
        # Extract raw scores
        analysis = metadata.get('analysis', {})
        brisque = analysis.get('brisque_score')
        sightengine = analysis.get('sightengine_results')
        claude = analysis.get('claude_results')
        
        # Calculate merged quality
        return self.scorer.merge_pipeline_results(
            brisque_score=brisque,
            sightengine_results=sightengine,
            claude_results=claude
        )
    
    # ===== Search Interface =====
    
    def search_by_tags(self, tags: List[str], tag_type: Optional[str] = None) -> List[AssetMetadata]:
        """Search for assets by tags.
        
        Args:
            tags: Tags to search for
            tag_type: Optional tag type filter (style, mood, subject, etc.)
            
        Returns:
            List of matching assets
        """
        results = []
        
        for asset in self.metadata_index.values():
            # AssetMetadata is a TypedDict, access as dict
            asset_tags = asset.get('tags', {})
            
            # Check each tag type
            for t_type, t_list in asset_tags.items():
                if tag_type and t_type != tag_type:
                    continue
                    
                if any(tag in t_list for tag in tags):
                    results.append(asset)
                    break
        
        return results
    
    def search_by_quality(self, min_stars: int = 1, max_stars: int = 5) -> List[AssetMetadata]:
        """Search for assets by quality rating.
        
        Args:
            min_stars: Minimum star rating (inclusive)
            max_stars: Maximum star rating (inclusive)
            
        Returns:
            List of matching assets
        """
        results = []
        
        for asset in self.metadata_index.values():
            # AssetMetadata is a TypedDict, access as dict
            quality = asset.get('quality', {})
            rating = quality.get('star_rating', 0)
            if min_stars <= rating <= max_stars:
                results.append(asset)
        
        return results
    
    # ===== Utility Methods =====
    
    def rebuild_from_images(self, image_dir: Path) -> int:
        """Rebuild cache from embedded image metadata.
        
        Args:
            image_dir: Directory containing images
            
        Returns:
            Number of images processed
        """
        count = 0
        
        for img_path in image_dir.rglob("*"):
            if img_path.suffix.lower() not in {'.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif'}:
                continue
                
            # Extract embedded metadata
            metadata = self.embedder.extract_metadata(img_path)
            if metadata and 'alice_metadata' in metadata:
                # Save to cache
                analysis = metadata['alice_metadata']
                analysis_time = metadata.get('analysis_time', 0.0)
                self.cache.save(img_path, analysis, analysis_time)
                count += 1
                
        logger.info(f"Rebuilt cache from {count} images")
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.
        
        Returns:
            Cache performance statistics
        """
        stats = self.cache.get_stats()
        stats['indexed_assets'] = len(self.metadata_index)
        stats['project_id'] = self.project_id
        return stats
    
    # ===== Private Methods =====
    
    def _load_metadata_index(self) -> None:
        """Load metadata index from cache."""
        logger.info("Loading metadata index...")
        
        cache_dir = self.source_root / ".metadata"
        if not cache_dir.exists():
            return
        
        loaded = 0
        for cache_file in cache_dir.rglob("*.json"):
            try:
                # Use cache's load method
                dummy_path = Path("dummy")  # We'll extract from the metadata
                metadata = self.cache.load(dummy_path)
                
                if metadata and 'enhanced_metadata' in metadata:
                    enhanced = metadata['enhanced_metadata']
                    content_hash = cache_file.stem
                    self.metadata_index[content_hash] = enhanced
                    loaded += 1
                    
            except Exception as e:
                logger.debug(f"Skipping invalid cache file {cache_file}: {e}")
                
        logger.info(f"Loaded {loaded} enhanced metadata entries")


# Backward compatibility aliases
def get_file_hash(file_path: Path) -> str:
    """Get SHA256 hash of a file (backward compatible)."""
    cache = MetadataCache(file_path.parent)
    return cache.get_content_hash(file_path)


def get_content_hash(file_path: Path) -> str:
    """Get content hash for a file (backward compatible)."""
    return get_file_hash(file_path)