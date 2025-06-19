"""Find and manage duplicate/similar images."""

import logging
import shutil
from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from ...core.file_operations import FileHandler
from .perceptual_hasher import PerceptualHasher

logger = logging.getLogger(__name__)


@dataclass
class DuplicateGroup:
    """Group of duplicate/similar images."""
    master: Path
    duplicates: list[Path]
    similarity_scores: dict[str, float]
    total_size: int
    potential_savings: int
    group_type: str  # 'exact' or 'similar'


class DuplicateFinder:
    """Find and manage duplicate images in collection."""

    def __init__(
        self,
        hasher: PerceptualHasher | None = None,
        similarity_threshold: float = 0.9
    ):
        """
        Initialize duplicate finder.

        Args:
            hasher: Perceptual hasher instance
            similarity_threshold: Threshold for considering images similar
        """
        self.hasher = hasher or PerceptualHasher()
        self.similarity_threshold = similarity_threshold
        self.exact_duplicates: dict[str, list[Path]] = defaultdict(list)
        self.similar_groups: list[DuplicateGroup] = []
        self.file_handler = FileHandler()

    def scan_directory(
        self,
        directory: Path,
        recursive: bool = True,
        extensions: set[str] | None = None
    ) -> tuple[int, int]:
        """
        Scan directory for duplicates.

        Args:
            directory: Directory to scan
            recursive: Whether to scan subdirectories
            extensions: File extensions to include

        Returns:
            Tuple of (exact_duplicates_found, similar_images_found)
        """
        if extensions is None:
            extensions = {'.jpg', '.jpeg', '.png', '.webp', '.heic', '.heif'}

        # Collect all image files
        image_files = []
        pattern = "**/*" if recursive else "*"

        for ext in extensions:
            image_files.extend(directory.glob(f"{pattern}{ext}"))
            image_files.extend(directory.glob(f"{pattern}{ext.upper()}"))

        logger.info(f"Found {len(image_files)} images to analyze")

        # Phase 1: Find exact duplicates using MD5
        self._find_exact_duplicates(image_files)

        # Phase 2: Find similar images using perceptual hashing
        self._find_similar_images(image_files)

        exact_count = sum(len(group) - 1 for group in self.exact_duplicates.values())
        similar_count = sum(len(g.duplicates) for g in self.similar_groups)

        return exact_count, similar_count

    # TODO: Review unreachable code - def _find_exact_duplicates(self, image_files: list[Path]):
    # TODO: Review unreachable code - """Find exact duplicates using file hashes."""
    # TODO: Review unreachable code - logger.info("Phase 1: Finding exact duplicates...")

    # TODO: Review unreachable code - self.exact_duplicates.clear()
    # TODO: Review unreachable code - hash_to_files = defaultdict(list)

    # TODO: Review unreachable code - for img_path in image_files:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - file_hash = self.file_handler.get_file_hash(img_path)
    # TODO: Review unreachable code - hash_to_files[file_hash].append(img_path)
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error hashing {img_path}: {e}")

    # TODO: Review unreachable code - # Keep only groups with duplicates
    # TODO: Review unreachable code - for file_hash, files in hash_to_files.items():
    # TODO: Review unreachable code - if len(files) > 1:
    # TODO: Review unreachable code - self.exact_duplicates[file_hash] = sorted(files)

    # TODO: Review unreachable code - def _find_similar_images(self, image_files: list[Path]):
    # TODO: Review unreachable code - """Find similar images using perceptual hashing."""
    # TODO: Review unreachable code - logger.info("Phase 2: Finding similar images...")

    # TODO: Review unreachable code - self.similar_groups.clear()

    # TODO: Review unreachable code - # Skip files already marked as exact duplicates
    # TODO: Review unreachable code - exact_dup_files = set()
    # TODO: Review unreachable code - for files in self.exact_duplicates.values():
    # TODO: Review unreachable code - exact_dup_files.update(files[1:])  # Keep first as master

    # TODO: Review unreachable code - # Compute perceptual hashes for remaining files
    # TODO: Review unreachable code - hashes = {}
    # TODO: Review unreachable code - for img_path in image_files:
    # TODO: Review unreachable code - if img_path not in exact_dup_files:
    # TODO: Review unreachable code - img_hashes = self.hasher.compute_hashes(img_path)
    # TODO: Review unreachable code - if img_hashes:
    # TODO: Review unreachable code - hashes[str(img_path)] = img_hashes

    # TODO: Review unreachable code - # Find similar groups
    # TODO: Review unreachable code - groups = self.hasher.find_similar_groups(hashes, self.similarity_threshold)

    # TODO: Review unreachable code - # Convert to DuplicateGroup objects
    # TODO: Review unreachable code - for group_paths in groups:
    # TODO: Review unreachable code - paths = [Path(p) for p in group_paths]

    # TODO: Review unreachable code - # Choose master (prefer organized files, then largest)
    # TODO: Review unreachable code - master = self._choose_master(paths)
    # TODO: Review unreachable code - duplicates = [p for p in paths if p != master]

    # TODO: Review unreachable code - # Calculate similarity scores
    # TODO: Review unreachable code - master_hash = hashes[str(master)]
    # TODO: Review unreachable code - similarity_scores = {}
    # TODO: Review unreachable code - for dup in duplicates:
    # TODO: Review unreachable code - score = self.hasher.compute_similarity(
    # TODO: Review unreachable code - master_hash,
    # TODO: Review unreachable code - hashes[str(dup)]
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - similarity_scores[str(dup)] = score

    # TODO: Review unreachable code - # Calculate sizes
    # TODO: Review unreachable code - total_size = sum(p.stat().st_size for p in paths)
    # TODO: Review unreachable code - potential_savings = sum(p.stat().st_size for p in duplicates)

    # TODO: Review unreachable code - group = DuplicateGroup(
    # TODO: Review unreachable code - master=master,
    # TODO: Review unreachable code - duplicates=duplicates,
    # TODO: Review unreachable code - similarity_scores=similarity_scores,
    # TODO: Review unreachable code - total_size=total_size,
    # TODO: Review unreachable code - potential_savings=potential_savings,
    # TODO: Review unreachable code - group_type='similar'
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - self.similar_groups.append(group)

    # TODO: Review unreachable code - def _choose_master(self, paths: list[Path]) -> Path:
    # TODO: Review unreachable code - """Choose the master file from a group."""
    # TODO: Review unreachable code - # Scoring system for choosing master
    # TODO: Review unreachable code - scores = {}

    # TODO: Review unreachable code - for path in paths:
    # TODO: Review unreachable code - score = 0

    # TODO: Review unreachable code - # Prefer files in organized directories
    # TODO: Review unreachable code - if 'organized' in str(path):
    # TODO: Review unreachable code - score += 100

    # TODO: Review unreachable code - # Prefer files with metadata
    # TODO: Review unreachable code - if path.with_suffix('.json').exists():
    # TODO: Review unreachable code - score += 50

    # TODO: Review unreachable code - # Prefer larger files (likely higher quality)
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - size = path.stat().st_size
    # TODO: Review unreachable code - score += size / 1_000_000  # MB as score
    # TODO: Review unreachable code - except (OSError, AttributeError):
    # TODO: Review unreachable code - pass

    # TODO: Review unreachable code - # Prefer files with better names (no IMG_ prefix)
    # TODO: Review unreachable code - if not path.name.startswith('IMG_'):
    # TODO: Review unreachable code - score += 10

    # TODO: Review unreachable code - scores[path] = score

    # TODO: Review unreachable code - # Return path with highest score
    # TODO: Review unreachable code - return max(scores.items(), key=lambda x: x[1])[0]

    # TODO: Review unreachable code - def get_duplicate_report(self) -> dict:
    # TODO: Review unreachable code - """Generate comprehensive duplicate report."""
    # TODO: Review unreachable code - report = {
    # TODO: Review unreachable code - 'scan_time': datetime.now().isoformat(),
    # TODO: Review unreachable code - 'exact_duplicates': {
    # TODO: Review unreachable code - 'count': len(self.exact_duplicates),
    # TODO: Review unreachable code - 'total_files': sum(len(g) for g in self.exact_duplicates.values()),
    # TODO: Review unreachable code - 'groups': []
    # TODO: Review unreachable code - },
    # TODO: Review unreachable code - 'similar_images': {
    # TODO: Review unreachable code - 'count': len(self.similar_groups),
    # TODO: Review unreachable code - 'total_files': sum(len(g.duplicates) + 1 for g in self.similar_groups),
    # TODO: Review unreachable code - 'groups': []
    # TODO: Review unreachable code - },
    # TODO: Review unreachable code - 'potential_savings': 0
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Add exact duplicate groups
    # TODO: Review unreachable code - for file_hash, files in self.exact_duplicates.items():
    # TODO: Review unreachable code - master = files[0]
    # TODO: Review unreachable code - duplicates = files[1:]

    # TODO: Review unreachable code - total_size = sum(f.stat().st_size for f in files)
    # TODO: Review unreachable code - savings = sum(f.stat().st_size for f in duplicates)

    # TODO: Review unreachable code - report['exact_duplicates']['groups'].append({
    # TODO: Review unreachable code - 'master': str(master),
    # TODO: Review unreachable code - 'duplicates': [str(f) for f in duplicates],
    # TODO: Review unreachable code - 'total_size': total_size,
    # TODO: Review unreachable code - 'potential_savings': savings,
    # TODO: Review unreachable code - 'hash': file_hash[:8] + '...'
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - report['potential_savings'] += savings

    # TODO: Review unreachable code - # Add similar image groups
    # TODO: Review unreachable code - for group in self.similar_groups:
    # TODO: Review unreachable code - report['similar_images']['groups'].append({
    # TODO: Review unreachable code - 'master': str(group.master),
    # TODO: Review unreachable code - 'duplicates': [str(f) for f in group.duplicates],
    # TODO: Review unreachable code - 'similarity_scores': group.similarity_scores,
    # TODO: Review unreachable code - 'total_size': group.total_size,
    # TODO: Review unreachable code - 'potential_savings': group.potential_savings
    # TODO: Review unreachable code - })

    # TODO: Review unreachable code - report['potential_savings'] += group.potential_savings

    # TODO: Review unreachable code - return report

    # TODO: Review unreachable code - def remove_duplicates(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - dry_run: bool = True,
    # TODO: Review unreachable code - backup_dir: Path | None = None,
    # TODO: Review unreachable code - remove_similar: bool = False
    # TODO: Review unreachable code - ) -> dict[str, int]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Remove duplicate files.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - dry_run: If True, only report what would be removed
    # TODO: Review unreachable code - backup_dir: If provided, move files here instead of deleting
    # TODO: Review unreachable code - remove_similar: If True, also remove similar (not just exact)

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Statistics about removed files
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - stats = {
    # TODO: Review unreachable code - 'exact_removed': 0,
    # TODO: Review unreachable code - 'similar_removed': 0,
    # TODO: Review unreachable code - 'space_freed': 0,
    # TODO: Review unreachable code - 'errors': 0
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Process exact duplicates
    # TODO: Review unreachable code - for files in self.exact_duplicates.values():
    # TODO: Review unreachable code - master = files[0]
    # TODO: Review unreachable code - duplicates = files[1:]

    # TODO: Review unreachable code - for dup in duplicates:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if dry_run:
    # TODO: Review unreachable code - logger.info(f"Would remove: {dup} (duplicate of {master})")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - if backup_dir:
    # TODO: Review unreachable code - # Move to backup
    # TODO: Review unreachable code - backup_path = backup_dir / dup.name
    # TODO: Review unreachable code - backup_path.parent.mkdir(parents=True, exist_ok=True)
    # TODO: Review unreachable code - shutil.move(str(dup), str(backup_path))
    # TODO: Review unreachable code - logger.info(f"Moved to backup: {dup}")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Delete
    # TODO: Review unreachable code - dup.unlink()
    # TODO: Review unreachable code - logger.info(f"Removed: {dup}")

    # TODO: Review unreachable code - stats['exact_removed'] += 1
    # TODO: Review unreachable code - stats['space_freed'] += dup.stat().st_size

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error removing {dup}: {e}")
    # TODO: Review unreachable code - stats['errors'] += 1

    # TODO: Review unreachable code - # Process similar images if requested
    # TODO: Review unreachable code - if remove_similar:
    # TODO: Review unreachable code - for group in self.similar_groups:
    # TODO: Review unreachable code - for dup in group.duplicates:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if dry_run:
    # TODO: Review unreachable code - logger.info(
    # TODO: Review unreachable code - f"Would remove: {dup} "
    # TODO: Review unreachable code - f"(similar to {group.master}, "
    # TODO: Review unreachable code - f"score: {group.similarity_scores.get(str(dup), 0):.2f})"
    # TODO: Review unreachable code - )
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - if backup_dir:
    # TODO: Review unreachable code - backup_path = backup_dir / dup.name
    # TODO: Review unreachable code - backup_path.parent.mkdir(parents=True, exist_ok=True)
    # TODO: Review unreachable code - shutil.move(str(dup), str(backup_path))
    # TODO: Review unreachable code - logger.info(f"Moved to backup: {dup}")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - dup.unlink()
    # TODO: Review unreachable code - logger.info(f"Removed: {dup}")

    # TODO: Review unreachable code - stats['similar_removed'] += 1
    # TODO: Review unreachable code - stats['space_freed'] += dup.stat().st_size

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error removing {dup}: {e}")
    # TODO: Review unreachable code - stats['errors'] += 1

    # TODO: Review unreachable code - return stats

    # TODO: Review unreachable code - def create_hardlinks(self, dry_run: bool = True) -> dict[str, int]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Replace duplicates with hardlinks to save space.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - dry_run: If True, only report what would be done

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Statistics about created hardlinks
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - stats = {
    # TODO: Review unreachable code - 'hardlinks_created': 0,
    # TODO: Review unreachable code - 'space_saved': 0,
    # TODO: Review unreachable code - 'errors': 0
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - for files in self.exact_duplicates.values():
    # TODO: Review unreachable code - master = files[0]
    # TODO: Review unreachable code - duplicates = files[1:]

    # TODO: Review unreachable code - for dup in duplicates:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if dry_run:
    # TODO: Review unreachable code - logger.info(f"Would hardlink: {dup} -> {master}")
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Remove duplicate and create hardlink
    # TODO: Review unreachable code - dup.unlink()
    # TODO: Review unreachable code - dup.hardlink_to(master)
    # TODO: Review unreachable code - logger.info(f"Created hardlink: {dup} -> {master}")

    # TODO: Review unreachable code - stats['hardlinks_created'] += 1
    # TODO: Review unreachable code - stats['space_saved'] += dup.stat().st_size

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Error creating hardlink for {dup}: {e}")
    # TODO: Review unreachable code - stats['errors'] += 1

    # TODO: Review unreachable code - return stats
