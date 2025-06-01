"""Build and rebuild DuckDB search index from file metadata."""

import hashlib
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from tqdm import tqdm

from ..core.constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from ..core.structured_logging import get_logger
from .metadata_extractor import MetadataExtractor
from .duckdb_search import DuckDBSearch

logger = get_logger(__name__)


class SearchIndexBuilder:
    """Builds search index from file metadata."""
    
    def __init__(self, db_path: Optional[str] = None):
        """Initialize index builder.
        
        Args:
            db_path: Path to DuckDB database file
        """
        self.search_db = DuckDBSearch(db_path)
        self.extractor = MetadataExtractor()
    
    def rebuild_from_paths(self, paths: List[str], show_progress: bool = True) -> int:
        """Rebuild search index from files in given paths.
        
        Args:
            paths: List of directories to scan
            show_progress: Whether to show progress bar
            
        Returns:
            Number of assets indexed
        """
        # First collect all media files
        media_files = []
        extensions = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
        
        logger.info(f"Scanning {len(paths)} paths for media files...")
        
        for path_str in paths:
            path = Path(path_str)
            if not path.exists():
                logger.warning(f"Path does not exist: {path}")
                continue
            
            if path.is_file() and path.suffix.lower() in extensions:
                media_files.append(path)
            elif path.is_dir():
                for ext in extensions:
                    media_files.extend(path.rglob(f"*{ext}"))
        
        logger.info(f"Found {len(media_files)} media files to index")
        
        # Clear existing index
        logger.info("Clearing existing search index...")
        self.search_db.clear_index()
        
        # Index each file
        indexed_count = 0
        
        if show_progress:
            file_iterator = tqdm(media_files, desc="Indexing files")
        else:
            file_iterator = media_files
        
        for file_path in file_iterator:
            try:
                # Extract metadata
                metadata = self._extract_full_metadata(file_path)
                if metadata:
                    # Add to search index
                    self.search_db.index_asset(metadata)
                    indexed_count += 1
                    
                    if show_progress and indexed_count % 100 == 0:
                        logger.debug(f"Indexed {indexed_count} files...")
                        
            except Exception as e:
                logger.error(f"Failed to index {file_path}: {e}")
        
        logger.info(f"Successfully indexed {indexed_count} of {len(media_files)} files")
        
        # Get index statistics
        stats = self.search_db.get_statistics()
        logger.info(
            f"Index statistics: {stats.get('total_assets', 0)} assets, "
            f"{stats.get('unique_tags', 0)} unique tags"
        )
        
        return indexed_count
    
    def update_from_path(self, path: str) -> int:
        """Update index with new or modified files from a path.
        
        Args:
            path: Directory to scan for updates
            
        Returns:
            Number of files updated
        """
        path_obj = Path(path)
        if not path_obj.exists():
            logger.warning(f"Path does not exist: {path}")
            return 0
        
        updated_count = 0
        extensions = IMAGE_EXTENSIONS | VIDEO_EXTENSIONS
        
        # Find media files
        media_files = []
        if path_obj.is_file() and path_obj.suffix.lower() in extensions:
            media_files = [path_obj]
        elif path_obj.is_dir():
            for ext in extensions:
                media_files.extend(path_obj.rglob(f"*{ext}"))
        
        for file_path in media_files:
            try:
                # Extract metadata
                metadata = self._extract_full_metadata(file_path)
                if metadata:
                    # Check if already indexed
                    content_hash = metadata.get("content_hash")
                    if content_hash:
                        existing, _ = self.search_db.search({"content_hash": content_hash})
                        
                        # Update if modified or new
                        if not existing or existing[0]["modified_at"] < metadata.get("modified_at", ""):
                            self.search_db.index_asset(metadata)
                            updated_count += 1
                            
            except Exception as e:
                logger.error(f"Failed to update {file_path}: {e}")
        
        logger.info(f"Updated {updated_count} files in index")
        return updated_count
    
    def verify_index(self) -> dict:
        """Verify index integrity and find missing files.
        
        Returns:
            Dict with verification results
        """
        logger.info("Verifying search index...")
        
        # Get all indexed assets
        all_assets, total = self.search_db.search({}, limit=10000)
        
        missing_files = []
        valid_files = 0
        
        for asset in all_assets:
            file_path = Path(asset.get("file_path", ""))
            if file_path.exists():
                valid_files += 1
            else:
                missing_files.append(str(file_path))
        
        results = {
            "total_indexed": total,
            "valid_files": valid_files,
            "missing_files": len(missing_files),
            "missing_file_paths": missing_files[:100],  # Limit to first 100
        }
        
        logger.info(
            f"Index verification: {valid_files}/{total} files exist, "
            f"{len(missing_files)} missing"
        )
        
        return results
    
    def _extract_full_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract full metadata including content hash and required fields.
        
        Args:
            file_path: Path to media file
            
        Returns:
            Complete metadata dict ready for indexing
        """
        # Calculate content hash first
        content_hash = self._calculate_content_hash(file_path)
        
        # Check for cached metadata
        cached_metadata = self._load_cached_metadata(file_path, content_hash)
        if cached_metadata:
            # Use cached metadata as base
            metadata = self._extract_indexable_data(cached_metadata)
            metadata["content_hash"] = content_hash
            metadata["file_path"] = str(file_path)
            metadata["file_size"] = file_path.stat().st_size
            
            # Update timestamps from file
            stat = file_path.stat()
            metadata["created_at"] = datetime.fromtimestamp(stat.st_ctime)
            metadata["modified_at"] = datetime.fromtimestamp(stat.st_mtime)
            metadata["discovered_at"] = datetime.now()
        else:
            # Fallback to embedded metadata extraction
            metadata = self.extractor.extract_metadata(file_path)
            
            # Add required fields
            metadata["content_hash"] = content_hash
            metadata["file_path"] = str(file_path)
            metadata["file_size"] = file_path.stat().st_size
            
            # Add timestamps
            stat = file_path.stat()
            metadata["created_at"] = datetime.fromtimestamp(stat.st_ctime)
            metadata["modified_at"] = datetime.fromtimestamp(stat.st_mtime)
            metadata["discovered_at"] = datetime.now()
            
            # Ensure media type is set
            if "media_type" not in metadata:
                suffix = file_path.suffix.lower()
                if suffix in IMAGE_EXTENSIONS:
                    metadata["media_type"] = "image"
                elif suffix in VIDEO_EXTENSIONS:
                    metadata["media_type"] = "video"
                else:
                    metadata["media_type"] = "unknown"
            
            # Extract AI source from filename patterns
            filename = file_path.name.lower()
            if "midjourney" in filename or "miasmah" in filename:
                metadata["ai_source"] = "midjourney"
            elif "dalle" in filename or "dall-e" in filename:
                metadata["ai_source"] = "dalle"
            elif "stable" in filename or "sd" in filename:
                metadata["ai_source"] = "stablediffusion"
            elif "leonardo" in filename:
                metadata["ai_source"] = "leonardo"
            elif "firefly" in filename:
                metadata["ai_source"] = "firefly"
            
            # Extract prompt from filename if available
            if "prompt" not in metadata and "_" in filename:
                # Many AI tools put prompt in filename
                parts = filename.split("_")
                if len(parts) > 2:
                    # Skip the first part (usually tool name) and last part (ID/extension)
                    potential_prompt = "_".join(parts[1:-1])
                    if len(potential_prompt) > 10:  # Reasonable prompt length
                        metadata["prompt"] = potential_prompt.replace("_", " ")
        
        return metadata
    
    def _load_cached_metadata(self, file_path: Path, content_hash: str) -> Optional[Dict[str, Any]]:
        """Load metadata from cache if available.
        
        Args:
            file_path: Path to media file
            content_hash: SHA256 hash of file content
            
        Returns:
            Cached metadata dict or None
        """
        # Look for .metadata folder in parent directories
        current_dir = file_path.parent
        
        # First check immediate parent, then walk up to find .metadata
        while current_dir != current_dir.parent:  # Stop at root
            metadata_dir = current_dir / ".metadata"
            if metadata_dir.exists():
                # Build cache file path
                hash_prefix = content_hash[:2]
                cache_file = metadata_dir / hash_prefix / f"{content_hash}.json"
                
                if cache_file.exists():
                    try:
                        with open(cache_file, 'r') as f:
                            cached_data = json.load(f)
                            logger.debug(f"Loaded cached metadata for {file_path.name} from {cache_file}")
                            return cached_data
                    except Exception as e:
                        logger.warning(f"Failed to load cached metadata from {cache_file}: {e}")
                
                # If not found in the expected location, check if it's an older flat structure
                old_cache_file = metadata_dir / f"{content_hash}.json"
                if old_cache_file.exists():
                    try:
                        with open(old_cache_file, 'r') as f:
                            cached_data = json.load(f)
                            logger.debug(f"Loaded cached metadata for {file_path.name} from old location")
                            return cached_data
                    except Exception as e:
                        logger.warning(f"Failed to load cached metadata from old location: {e}")
                        
                # Only check the first .metadata directory found
                break
                
            current_dir = current_dir.parent
            
        return None
    
    def _extract_indexable_data(self, cached_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract indexable fields from cached metadata.
        
        Args:
            cached_data: Full cached metadata
            
        Returns:
            Metadata dict with indexable fields
        """
        metadata = {}
        
        # Direct fields from cache structure
        for field in ["content_hash", "file_size", "last_modified"]:
            if field in cached_data:
                metadata[field] = cached_data[field]
        
        # Extract from analysis section
        if "analysis" in cached_data:
            analysis = cached_data["analysis"]
            
            # Media type and AI source
            metadata["media_type"] = analysis.get("media_type", "unknown")
            # Handle MediaType enum values
            if hasattr(metadata["media_type"], "value"):
                metadata["media_type"] = metadata["media_type"].value
                
            metadata["ai_source"] = analysis.get("source_type")
            
            # Understanding data (tags)
            if "understanding" in analysis:
                understanding = analysis["understanding"]
                # Extract tags from understanding data
                tags = []
                for provider_data in understanding.values():
                    if isinstance(provider_data, dict) and "tags" in provider_data:
                        tags.extend(provider_data["tags"])
                if tags:
                    metadata["tags"] = list(set(tags))  # Deduplicate
            
            # Quality information (legacy - now using understanding system)
            if "quality_stars" in analysis:
                metadata["quality_rating"] = analysis["quality_stars"]
            if "final_combined_score" in analysis:
                metadata["quality_score"] = analysis["final_combined_score"]
        
        # Extract prompt from original path or filename
        original_path = cached_data.get("original_path", cached_data.get("file_name", ""))
        if original_path:
            filename = Path(original_path).name.lower()
            if "_" in filename:
                parts = filename.split("_")
                if len(parts) > 2:
                    potential_prompt = "_".join(parts[1:-1])
                    if len(potential_prompt) > 10:
                        metadata["prompt"] = potential_prompt.replace("_", " ")
        
        return metadata
    
    def _calculate_content_hash(self, file_path: Path) -> str:
        """Calculate SHA256 hash of file content.
        
        Args:
            file_path: Path to file
            
        Returns:
            Hex string of content hash
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            # Read in chunks to handle large files
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()