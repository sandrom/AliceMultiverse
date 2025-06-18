"""Enhanced file processing with error recovery and resilience."""

import time
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Dict, Any

from ...core.logging import get_logger
from ...core.types import OrganizeResult
from ...core.exceptions_extended import (
    FileOperationError,
    MediaAnalysisError,
    MetadataExtractionError,
    FileReadError,
    FileWriteError,
    FileMoveError,
    ProcessingError
)
from ...core.error_recovery import ErrorRecovery, RetryConfig
from ..organization_helpers import extract_project_folder

logger = get_logger(__name__)

if TYPE_CHECKING:
    from ...core.protocols import HasConfig, HasMetadataCache, HasStats
    from ...core.config import Config
    from ...core.statistics import Statistics


class EnhancedProcessFileMixin:
    """Enhanced file processing with error recovery and resilience."""
    
    if TYPE_CHECKING:
        # Type hints for mypy
        metadata_cache: Any
        config: Config
        stats: Statistics
        source_dir: Path
        output_dir: Path
    
    def _process_file_with_recovery(self, media_path: Path) -> OrganizeResult:
        """Process a single media file with full error recovery."""
        result = OrganizeResult(
            status="error",
            source_path=str(media_path),
            error="Unknown error"
        )
        
        try:
            # Step 1: Validate file
            if not self._validate_file(media_path):
                result["error"] = "File validation failed"
                return result
            
            # Step 2: Get project folder with fallback
            project_folder = self._get_project_folder_safe(media_path)
            
            # Step 3: Analyze media with retry
            analysis = self._analyze_media_with_retry(media_path, project_folder)
            if not analysis:
                result["error"] = "Media analysis failed after retries"
                return result
            
            # Step 4: Build destination path
            dest_path = self._build_destination_path_safe(
                media_path, analysis, project_folder
            )
            if not dest_path:
                result["error"] = "Failed to build destination path"
                return result
            
            # Step 5: Process file operation with recovery
            operation_result = self._execute_file_operation_with_recovery(
                media_path, dest_path
            )
            
            # Update result
            result.update(operation_result)
            result["analysis"] = analysis
            result["project_folder"] = project_folder
            result["source_type"] = analysis.get("source_type", "unknown")
            result["date_taken"] = analysis.get("date_taken")
            
            return result
            
        except Exception as e:
            logger.error(f"Unexpected error processing {media_path}: {e}")
            result["error"] = str(e)
            return result
    
    def _validate_file(self, media_path: Path) -> bool:
        """Validate file exists and is accessible."""
        try:
            if not media_path.exists():
                logger.warning(f"File does not exist: {media_path}")
                return False
            
            if not media_path.is_file():
                logger.warning(f"Not a file: {media_path}")
                return False
            
            # Try to get file stats to ensure it's accessible
            stats = media_path.stat()
            if stats.st_size == 0:
                logger.warning(f"Empty file: {media_path}")
                return False
            
            return True
            
        except OSError as e:
            logger.error(f"Cannot access file {media_path}: {e}")
            return False
    
    def _get_project_folder_safe(self, media_path: Path) -> str:
        """Get project folder with fallback to default."""
        try:
            return extract_project_folder(media_path, self.source_dir)
        except Exception as e:
            logger.warning(f"Failed to extract project folder: {e}")
            # Fallback to parent directory name
            return media_path.parent.name or "default"
    
    @ErrorRecovery.retry_with_backoff(
        config=RetryConfig(max_attempts=3, initial_delay=0.5)
    )
    def _analyze_media_with_retry(self, 
                                  media_path: Path,
                                  project_folder: str) -> Optional[Dict[str, Any]]:
        """Analyze media with retry logic."""
        try:
            # Try to get from cache first
            cached = self._get_cached_analysis(media_path)
            if cached:
                return cached
            
            # Perform fresh analysis
            return self._perform_media_analysis(media_path, project_folder)
            
        except Exception as e:
            raise MediaAnalysisError(
                media_path, 
                "analysis",
                e
            )
    
    def _get_cached_analysis(self, media_path: Path) -> Optional[Dict[str, Any]]:
        """Get analysis from cache if available."""
        try:
            if hasattr(self, 'metadata_cache') and self.metadata_cache:
                return self.metadata_cache.load(media_path)
        except Exception as e:
            logger.debug(f"Cache lookup failed: {e}")
        return None
    
    def _perform_media_analysis(self,
                               media_path: Path,
                               project_folder: str) -> Dict[str, Any]:
        """Perform fresh media analysis with fallback."""
        analysis = {
            "file_path": str(media_path),
            "file_name": media_path.name,
            "project_folder": project_folder,
            "analyzed_at": time.time()
        }
        
        try:
            # This would call the actual analysis methods
            # For now, return basic analysis
            analysis.update({
                "source_type": "unknown",
                "date_taken": media_path.stat().st_mtime,
                "file_number": 1,
                "quality_stars": None
            })
            
            # Save to cache if available
            if hasattr(self, 'metadata_cache') and self.metadata_cache:
                self.metadata_cache.save(media_path, analysis, 0.0)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            # Return minimal analysis
            return analysis
    
    def _build_destination_path_safe(self,
                                    media_path: Path,
                                    analysis: Dict[str, Any],
                                    project_folder: str) -> Optional[Path]:
        """Build destination path with validation."""
        try:
            # Ensure output directory exists
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            # Build path using existing method if available
            if hasattr(self, '_build_destination_path'):
                return self._build_destination_path(
                    media_path,
                    analysis.get("date_taken"),
                    project_folder,
                    analysis.get("source_type", "unknown"),
                    analysis.get("file_number", 1),
                    analysis.get("quality_stars")
                )
            else:
                # Fallback to simple structure
                date_folder = time.strftime("%Y-%m-%d", time.localtime(analysis.get("date_taken", time.time())))
                return self.output_dir / date_folder / project_folder / media_path.name
                
        except Exception as e:
            logger.error(f"Failed to build destination path: {e}")
            return None
    
    def _execute_file_operation_with_recovery(self,
                                            source: Path,
                                            destination: Path) -> Dict[str, Any]:
        """Execute file operation with recovery strategies."""
        result = {
            "status": "error",
            "source_path": str(source),
            "destination": str(destination)
        }
        
        # Try primary operation (copy/move)
        try:
            # Create destination directory
            destination.parent.mkdir(parents=True, exist_ok=True)
            
            # Check if destination already exists
            if destination.exists():
                if self._handle_existing_file(source, destination):
                    result["status"] = "skipped"
                    result["reason"] = "duplicate"
                    return result
            
            # Perform operation
            if self.config.get("move_files", False):
                self._move_file_with_recovery(source, destination)
                result["operation"] = "moved"
            else:
                self._copy_file_with_recovery(source, destination)
                result["operation"] = "copied"
            
            result["status"] = "success"
            return result
            
        except Exception as e:
            logger.error(f"File operation failed: {e}")
            result["error"] = str(e)
            
            # Try fallback strategies
            if self._try_fallback_operation(source, destination):
                result["status"] = "success"
                result["operation"] = "fallback"
            
            return result
    
    @ErrorRecovery.retry_file_operation
    def _copy_file_with_recovery(self, source: Path, destination: Path) -> None:
        """Copy file with retry logic."""
        try:
            import shutil
            shutil.copy2(source, destination)
        except Exception as e:
            raise FileWriteError(destination, e)
    
    @ErrorRecovery.retry_file_operation
    def _move_file_with_recovery(self, source: Path, destination: Path) -> None:
        """Move file with retry logic."""
        try:
            import shutil
            shutil.move(str(source), str(destination))
        except Exception as e:
            raise FileMoveError(source, destination, e)
    
    def _handle_existing_file(self, source: Path, destination: Path) -> bool:
        """Handle case where destination file already exists."""
        try:
            # Compare file sizes
            if source.stat().st_size == destination.stat().st_size:
                # Likely the same file
                logger.debug(f"File already exists with same size: {destination}")
                return True
            
            # Different sizes - rename destination
            new_dest = self._get_unique_filename(destination)
            destination.rename(new_dest)
            logger.info(f"Renamed existing file to: {new_dest}")
            return False
            
        except Exception as e:
            logger.error(f"Error handling existing file: {e}")
            return False
    
    def _get_unique_filename(self, path: Path) -> Path:
        """Get unique filename by appending number."""
        base = path.stem
        suffix = path.suffix
        parent = path.parent
        
        counter = 1
        while True:
            new_path = parent / f"{base}_{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1
    
    def _try_fallback_operation(self, source: Path, destination: Path) -> bool:
        """Try fallback strategies when primary operation fails."""
        # Strategy 1: Try alternative destination
        try:
            alt_dest = self.output_dir / "recovered" / destination.name
            alt_dest.parent.mkdir(parents=True, exist_ok=True)
            
            import shutil
            shutil.copy2(source, alt_dest)
            logger.info(f"Used fallback destination: {alt_dest}")
            return True
            
        except Exception as e:
            logger.error(f"Fallback operation also failed: {e}")
            
        # Strategy 2: Create link instead of copy
        try:
            if hasattr(Path, 'hardlink_to'):
                destination.hardlink_to(source)
                logger.info("Created hardlink as fallback")
                return True
        except Exception:
            pass
        
        return False