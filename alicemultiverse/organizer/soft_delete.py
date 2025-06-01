"""Soft delete functionality for moving rejected images."""

import shutil
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class SoftDeleteManager:
    """Manages soft deletion of assets by moving them to sorted folders."""
    
    def __init__(self, sorted_out_path: str = "sorted-out"):
        """Initialize soft delete manager.
        
        Args:
            sorted_out_path: Base path for sorted-out files
        """
        self.sorted_out_path = Path(sorted_out_path)
        
        # Standard sorted-out categories
        self.categories = {
            "broken": "Files with defects or artifacts",
            "duplicate": "Duplicate files",
            "maybe-later": "Files that might be useful later",
            "rejected": "Files that didn't make the cut",
            "archive": "Old files for archival",
        }
    
    def soft_delete(
        self,
        file_path: Path,
        category: str = "rejected",
        reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Path]:
        """Soft delete a file by moving it to sorted-out folder.
        
        Args:
            file_path: Path to file to soft delete
            category: Category for sorting (broken, duplicate, etc.)
            reason: Optional reason for deletion
            metadata: Optional metadata to preserve
            
        Returns:
            New path if moved successfully, None otherwise
        """
        if not file_path.exists():
            logger.warning(f"File not found for soft delete: {file_path}")
            return None
        
        # Ensure category exists
        if category not in self.categories:
            logger.warning(f"Unknown category '{category}', using 'rejected'")
            category = "rejected"
        
        # Create category folder
        category_path = self.sorted_out_path / category
        category_path.mkdir(parents=True, exist_ok=True)
        
        # Add date subfolder for organization
        date_folder = datetime.now().strftime("%Y-%m-%d")
        target_dir = category_path / date_folder
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine target path
        target_path = target_dir / file_path.name
        
        # Handle name conflicts
        if target_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{stem}_{counter}{suffix}"
                counter += 1
        
        try:
            # Move the file
            shutil.move(str(file_path), str(target_path))
            logger.info(
                f"Soft deleted file",
                source=str(file_path),
                target=str(target_path),
                category=category,
                reason=reason
            )
            
            # Save deletion metadata
            if reason or metadata:
                self._save_deletion_metadata(target_path, category, reason, metadata)
            
            return target_path
            
        except Exception as e:
            logger.error(f"Failed to soft delete {file_path}: {e}")
            return None
    
    def soft_delete_batch(
        self,
        file_paths: List[Path],
        category: str = "rejected",
        reason: Optional[str] = None
    ) -> Dict[str, List[Path]]:
        """Soft delete multiple files.
        
        Args:
            file_paths: List of file paths to soft delete
            category: Category for all files
            reason: Reason for deletion (applies to all)
            
        Returns:
            Dict with 'moved' and 'failed' lists
        """
        results = {
            "moved": [],
            "failed": []
        }
        
        for file_path in file_paths:
            new_path = self.soft_delete(file_path, category, reason)
            if new_path:
                results["moved"].append(new_path)
            else:
                results["failed"].append(file_path)
        
        logger.info(
            f"Batch soft delete complete",
            moved=len(results["moved"]),
            failed=len(results["failed"]),
            category=category
        )
        
        return results
    
    def restore(self, file_path: Path, target_dir: Optional[Path] = None) -> Optional[Path]:
        """Restore a soft-deleted file.
        
        Args:
            file_path: Path to file in sorted-out folder
            target_dir: Where to restore to (defaults to original location)
            
        Returns:
            Restored path if successful, None otherwise
        """
        if not file_path.exists():
            logger.warning(f"File not found for restore: {file_path}")
            return None
        
        # Check if file is in sorted-out directory
        try:
            file_path.relative_to(self.sorted_out_path)
        except ValueError:
            logger.warning(f"File is not in sorted-out directory: {file_path}")
            return None
        
        # Determine target directory
        if not target_dir:
            # Try to restore to original location from metadata
            metadata = self._load_deletion_metadata(file_path)
            if metadata and "original_path" in metadata:
                target_dir = Path(metadata["original_path"]).parent
            else:
                # Default to current directory
                target_dir = Path.cwd()
        
        target_dir = Path(target_dir)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        # Determine target path
        target_path = target_dir / file_path.name
        
        # Handle name conflicts
        if target_path.exists():
            stem = file_path.stem
            suffix = file_path.suffix
            counter = 1
            while target_path.exists():
                target_path = target_dir / f"{stem}_restored_{counter}{suffix}"
                counter += 1
        
        try:
            # Move the file back
            shutil.move(str(file_path), str(target_path))
            logger.info(
                f"Restored file",
                source=str(file_path),
                target=str(target_path)
            )
            
            # Remove metadata file
            metadata_path = file_path.with_suffix(file_path.suffix + ".deleted.json")
            if metadata_path.exists():
                metadata_path.unlink()
            
            return target_path
            
        except Exception as e:
            logger.error(f"Failed to restore {file_path}: {e}")
            return None
    
    def list_sorted_out(self, category: Optional[str] = None) -> Dict[str, List[Path]]:
        """List all sorted-out files.
        
        Args:
            category: Optional category filter
            
        Returns:
            Dict mapping categories to file lists
        """
        results = {}
        
        if not self.sorted_out_path.exists():
            return results
        
        categories = [category] if category else self.categories.keys()
        
        for cat in categories:
            cat_path = self.sorted_out_path / cat
            if cat_path.exists():
                files = []
                for file_path in cat_path.rglob("*"):
                    if file_path.is_file() and not file_path.suffix.endswith(".deleted.json"):
                        files.append(file_path)
                if files:
                    results[cat] = sorted(files)
        
        return results
    
    def get_exclusion_patterns(self) -> List[str]:
        """Get glob patterns to exclude sorted-out folders.
        
        Returns:
            List of glob patterns to exclude
        """
        patterns = [
            str(self.sorted_out_path),
            f"{self.sorted_out_path}/**",
        ]
        
        # Add category-specific patterns
        for category in self.categories:
            patterns.extend([
                f"**/{category}/**",
                f"**/sorted-out/{category}/**",
                f"**/sorted_out/{category}/**",
            ])
        
        return patterns
    
    def _save_deletion_metadata(
        self,
        file_path: Path,
        category: str,
        reason: Optional[str],
        metadata: Optional[Dict[str, Any]]
    ):
        """Save metadata about the deletion."""
        import json
        
        deletion_info = {
            "deleted_at": datetime.now().isoformat(),
            "category": category,
            "reason": reason,
            "original_path": str(file_path),
            "additional_metadata": metadata or {}
        }
        
        metadata_path = file_path.with_suffix(file_path.suffix + ".deleted.json")
        try:
            with open(metadata_path, 'w') as f:
                json.dump(deletion_info, f, indent=2)
        except Exception as e:
            logger.warning(f"Failed to save deletion metadata: {e}")
    
    def _load_deletion_metadata(self, file_path: Path) -> Optional[Dict[str, Any]]:
        """Load metadata about the deletion."""
        import json
        
        metadata_path = file_path.with_suffix(file_path.suffix + ".deleted.json")
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load deletion metadata: {e}")
        
        return None