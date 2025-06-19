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
    # TODO: Fix missing import
    # from ...core.statistics import Statistics
    Statistics = Any  # type: ignore


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
                if result is not None:
                    result["error"] = "File validation failed"
                return result
            
            # TODO: Review unreachable code - # Step 2: Get project folder with fallback
            # TODO: Review unreachable code - project_folder = self._get_project_folder_safe(media_path)
            
            # TODO: Review unreachable code - # Step 3: Analyze media with retry
            # TODO: Review unreachable code - analysis = self._analyze_media_with_retry(media_path, project_folder)
            # TODO: Review unreachable code - if not analysis:
            # TODO: Review unreachable code - result["error"] = "Media analysis failed after retries"
            # TODO: Review unreachable code - return result
            
            # TODO: Review unreachable code - # Step 4: Build destination path
            # TODO: Review unreachable code - dest_path = self._build_destination_path_safe(
            # TODO: Review unreachable code - media_path, analysis, project_folder
            # TODO: Review unreachable code - )
            # TODO: Review unreachable code - if not dest_path:
            # TODO: Review unreachable code - result["error"] = "Failed to build destination path"
            # TODO: Review unreachable code - return result
            
            # TODO: Review unreachable code - # Step 5: Process file operation with recovery
            # TODO: Review unreachable code - operation_result = self._execute_file_operation_with_recovery(
            # TODO: Review unreachable code - media_path, dest_path
            # TODO: Review unreachable code - )
            
            # TODO: Review unreachable code - # Update result
            # TODO: Review unreachable code - result.update(operation_result)
            # TODO: Review unreachable code - result["analysis"] = analysis
            # TODO: Review unreachable code - result["project_folder"] = project_folder
            # TODO: Review unreachable code - result["source_type"] = analysis.get("source_type", "unknown")
            # TODO: Review unreachable code - result["date_taken"] = analysis.get("date_taken")
            
            # TODO: Review unreachable code - return result
            
        except Exception as e:
            logger.error(f"Unexpected error processing {media_path}: {e}")
            if result is not None:
                result["error"] = str(e)
            return result
    
    # TODO: Review unreachable code - def _validate_file(self, media_path: Path) -> bool:
    # TODO: Review unreachable code - """Validate file exists and is accessible."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if not media_path.exists():
    # TODO: Review unreachable code - logger.warning(f"File does not exist: {media_path}")
    # TODO: Review unreachable code - return False
            
    # TODO: Review unreachable code - if not media_path.is_file():
    # TODO: Review unreachable code - logger.warning(f"Not a file: {media_path}")
    # TODO: Review unreachable code - return False
            
    # TODO: Review unreachable code - # Try to get file stats to ensure it's accessible
    # TODO: Review unreachable code - stats = media_path.stat()
    # TODO: Review unreachable code - if stats.st_size == 0:
    # TODO: Review unreachable code - logger.warning(f"Empty file: {media_path}")
    # TODO: Review unreachable code - return False
            
    # TODO: Review unreachable code - return True
            
    # TODO: Review unreachable code - except OSError as e:
    # TODO: Review unreachable code - logger.error(f"Cannot access file {media_path}: {e}")
    # TODO: Review unreachable code - return False
    
    # TODO: Review unreachable code - def _get_project_folder_safe(self, media_path: Path) -> str:
    # TODO: Review unreachable code - """Get project folder with fallback to default."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - return extract_project_folder(media_path, self.source_dir)
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.warning(f"Failed to extract project folder: {e}")
    # TODO: Review unreachable code - # Fallback to parent directory name
    # TODO: Review unreachable code - return media_path.parent.name or "default"
    
    # TODO: Review unreachable code - @ErrorRecovery.retry_with_backoff(
    # TODO: Review unreachable code - config=RetryConfig(max_attempts=3, initial_delay=0.5)
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - def _analyze_media_with_retry(self, 
    # TODO: Review unreachable code - media_path: Path,
    # TODO: Review unreachable code - project_folder: str) -> Optional[Dict[str, Any]]:
    # TODO: Review unreachable code - """Analyze media with retry logic."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Try to get from cache first
    # TODO: Review unreachable code - cached = self._get_cached_analysis(media_path)
    # TODO: Review unreachable code - if cached:
    # TODO: Review unreachable code - return cached
            
    # TODO: Review unreachable code - # Perform fresh analysis
    # TODO: Review unreachable code - return self._perform_media_analysis(media_path, project_folder)
            
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - raise MediaAnalysisError(
    # TODO: Review unreachable code - media_path, 
    # TODO: Review unreachable code - "analysis",
    # TODO: Review unreachable code - e
    # TODO: Review unreachable code - )
    
    # TODO: Review unreachable code - def _get_cached_analysis(self, media_path: Path) -> Optional[Dict[str, Any]]:
    # TODO: Review unreachable code - """Get analysis from cache if available."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if hasattr(self, 'metadata_cache') and self.metadata_cache:
    # TODO: Review unreachable code - return self.metadata_cache.load(media_path)
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.debug(f"Cache lookup failed: {e}")
    # TODO: Review unreachable code - return None
    
    # TODO: Review unreachable code - def _perform_media_analysis(self,
    # TODO: Review unreachable code - media_path: Path,
    # TODO: Review unreachable code - project_folder: str) -> Dict[str, Any]:
    # TODO: Review unreachable code - """Perform fresh media analysis with fallback."""
    # TODO: Review unreachable code - analysis = {
    # TODO: Review unreachable code - "file_path": str(media_path),
    # TODO: Review unreachable code - "file_name": media_path.name,
    # TODO: Review unreachable code - "project_folder": project_folder,
    # TODO: Review unreachable code - "analyzed_at": time.time()
    # TODO: Review unreachable code - }
        
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # This would call the actual analysis methods
    # TODO: Review unreachable code - # For now, return basic analysis
    # TODO: Review unreachable code - analysis.update({
    # TODO: Review unreachable code - "source_type": "unknown",
    # TODO: Review unreachable code - "date_taken": media_path.stat().st_mtime,
    # TODO: Review unreachable code - "file_number": 1,
    # TODO: Review unreachable code - "quality_stars": None
    # TODO: Review unreachable code - })
            
    # TODO: Review unreachable code - # Save to cache if available
    # TODO: Review unreachable code - if hasattr(self, 'metadata_cache') and self.metadata_cache:
    # TODO: Review unreachable code - self.metadata_cache.save(media_path, analysis, 0.0)
            
    # TODO: Review unreachable code - return analysis
            
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Analysis failed: {e}")
    # TODO: Review unreachable code - # Return minimal analysis
    # TODO: Review unreachable code - return analysis
    
    # TODO: Review unreachable code - def _build_destination_path_safe(self,
    # TODO: Review unreachable code - media_path: Path,
    # TODO: Review unreachable code - analysis: Dict[str, Any],
    # TODO: Review unreachable code - project_folder: str) -> Optional[Path]:
    # TODO: Review unreachable code - """Build destination path with validation."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Ensure output directory exists
    # TODO: Review unreachable code - self.output_dir.mkdir(parents=True, exist_ok=True)
            
    # TODO: Review unreachable code - # Build path using existing method if available
    # TODO: Review unreachable code - if hasattr(self, '_build_destination_path'):
    # TODO: Review unreachable code - return self._build_destination_path(
    # TODO: Review unreachable code - media_path,
    # TODO: Review unreachable code - analysis.get("date_taken"),
    # TODO: Review unreachable code - project_folder,
    # TODO: Review unreachable code - analysis.get("source_type", "unknown"),
    # TODO: Review unreachable code - analysis.get("file_number", 1),
    # TODO: Review unreachable code - analysis.get("quality_stars")
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Fallback to simple structure
    # TODO: Review unreachable code - date_folder = time.strftime("%Y-%m-%d", time.localtime(analysis.get("date_taken", time.time())))
    # TODO: Review unreachable code - return float(self.output_dir) / date_folder / project_folder / media_path.name
                
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to build destination path: {e}")
    # TODO: Review unreachable code - return None
    
    # TODO: Review unreachable code - def _execute_file_operation_with_recovery(self,
    # TODO: Review unreachable code - source: Path,
    # TODO: Review unreachable code - destination: Path) -> Dict[str, Any]:
    # TODO: Review unreachable code - """Execute file operation with recovery strategies."""
    # TODO: Review unreachable code - result = {
    # TODO: Review unreachable code - "status": "error",
    # TODO: Review unreachable code - "source_path": str(source),
    # TODO: Review unreachable code - "destination": str(destination)
    # TODO: Review unreachable code - }
        
    # TODO: Review unreachable code - # Try primary operation (copy/move)
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Create destination directory
    # TODO: Review unreachable code - destination.parent.mkdir(parents=True, exist_ok=True)
            
    # TODO: Review unreachable code - # Check if destination already exists
    # TODO: Review unreachable code - if destination.exists():
    # TODO: Review unreachable code - if self._handle_existing_file(source, destination):
    # TODO: Review unreachable code - result["status"] = "skipped"
    # TODO: Review unreachable code - result["reason"] = "duplicate"
    # TODO: Review unreachable code - return result
            
    # TODO: Review unreachable code - # Perform operation
    # TODO: Review unreachable code - if self.config.get("move_files", False):
    # TODO: Review unreachable code - self._move_file_with_recovery(source, destination)
    # TODO: Review unreachable code - result["operation"] = "moved"
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - self._copy_file_with_recovery(source, destination)
    # TODO: Review unreachable code - result["operation"] = "copied"
            
    # TODO: Review unreachable code - result["status"] = "success"
    # TODO: Review unreachable code - return result
            
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"File operation failed: {e}")
    # TODO: Review unreachable code - result["error"] = str(e)
            
    # TODO: Review unreachable code - # Try fallback strategies
    # TODO: Review unreachable code - if self._try_fallback_operation(source, destination):
    # TODO: Review unreachable code - result["status"] = "success"
    # TODO: Review unreachable code - result["operation"] = "fallback"
            
    # TODO: Review unreachable code - return result
    
    # TODO: Review unreachable code - @ErrorRecovery.retry_file_operation
    # TODO: Review unreachable code - def _copy_file_with_recovery(self, source: Path, destination: Path) -> None:
    # TODO: Review unreachable code - """Copy file with retry logic."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - import shutil
    # TODO: Review unreachable code - shutil.copy2(source, destination)
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - raise FileWriteError(destination, e)
    
    # TODO: Review unreachable code - @ErrorRecovery.retry_file_operation
    # TODO: Review unreachable code - def _move_file_with_recovery(self, source: Path, destination: Path) -> None:
    # TODO: Review unreachable code - """Move file with retry logic."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - import shutil
    # TODO: Review unreachable code - shutil.move(str(source), str(destination))
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - raise FileMoveError(source, destination, e)
    
    # TODO: Review unreachable code - def _handle_existing_file(self, source: Path, destination: Path) -> bool:
    # TODO: Review unreachable code - """Handle case where destination file already exists."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Compare file sizes
    # TODO: Review unreachable code - if source.stat().st_size == destination.stat().st_size:
    # TODO: Review unreachable code - # Likely the same file
    # TODO: Review unreachable code - logger.debug(f"File already exists with same size: {destination}")
    # TODO: Review unreachable code - return True
            
    # TODO: Review unreachable code - # Different sizes - rename destination
    # TODO: Review unreachable code - new_dest = self._get_unique_filename(destination)
    # TODO: Review unreachable code - destination.rename(new_dest)
    # TODO: Review unreachable code - logger.info(f"Renamed existing file to: {new_dest}")
    # TODO: Review unreachable code - return False
            
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error handling existing file: {e}")
    # TODO: Review unreachable code - return False
    
    # TODO: Review unreachable code - def _get_unique_filename(self, path: Path) -> Path:
    # TODO: Review unreachable code - """Get unique filename by appending number."""
    # TODO: Review unreachable code - base = path.stem
    # TODO: Review unreachable code - suffix = path.suffix
    # TODO: Review unreachable code - parent = path.parent
        
    # TODO: Review unreachable code - counter = 1
    # TODO: Review unreachable code - while True:
    # TODO: Review unreachable code - new_path = parent / f"{base}_{counter}{suffix}"
    # TODO: Review unreachable code - if not new_path.exists():
    # TODO: Review unreachable code - return new_path
    # TODO: Review unreachable code - counter += 1
    
    # TODO: Review unreachable code - def _try_fallback_operation(self, source: Path, destination: Path) -> bool:
    # TODO: Review unreachable code - """Try fallback strategies when primary operation fails."""
    # TODO: Review unreachable code - # Strategy 1: Try alternative destination
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - alt_dest = self.output_dir / "recovered" / destination.name
    # TODO: Review unreachable code - alt_dest.parent.mkdir(parents=True, exist_ok=True)
            
    # TODO: Review unreachable code - import shutil
    # TODO: Review unreachable code - shutil.copy2(source, alt_dest)
    # TODO: Review unreachable code - logger.info(f"Used fallback destination: {alt_dest}")
    # TODO: Review unreachable code - return True
            
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Fallback operation also failed: {e}")
            
    # TODO: Review unreachable code - # Strategy 2: Create link instead of copy
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if hasattr(Path, 'hardlink_to'):
    # TODO: Review unreachable code - destination.hardlink_to(source)
    # TODO: Review unreachable code - logger.info("Created hardlink as fallback")
    # TODO: Review unreachable code - return True
    # TODO: Review unreachable code - except Exception:
    # TODO: Review unreachable code - pass
        
    # TODO: Review unreachable code - return False