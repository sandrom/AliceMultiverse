"""Build and rebuild DuckDB search index from file metadata."""

import logging
from pathlib import Path
from typing import List, Optional

from tqdm import tqdm

from ..core.constants import IMAGE_EXTENSIONS, VIDEO_EXTENSIONS
from ..core.structured_logging import get_logger
from ..metadata.extractor import MetadataExtractor
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
                metadata = self.extractor.extract_metadata(file_path)
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
                metadata = self.extractor.extract_metadata(file_path)
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