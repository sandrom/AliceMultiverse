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

    def _find_exact_duplicates(self, image_files: list[Path]):
        """Find exact duplicates using file hashes."""
        logger.info("Phase 1: Finding exact duplicates...")

        self.exact_duplicates.clear()
        hash_to_files = defaultdict(list)

        for img_path in image_files:
            try:
                file_hash = self.file_handler.get_file_hash(img_path)
                hash_to_files[file_hash].append(img_path)
            except Exception as e:
                logger.error(f"Error hashing {img_path}: {e}")

        # Keep only groups with duplicates
        for file_hash, files in hash_to_files.items():
            if len(files) > 1:
                self.exact_duplicates[file_hash] = sorted(files)

    def _find_similar_images(self, image_files: list[Path]):
        """Find similar images using perceptual hashing."""
        logger.info("Phase 2: Finding similar images...")

        self.similar_groups.clear()

        # Skip files already marked as exact duplicates
        exact_dup_files = set()
        for files in self.exact_duplicates.values():
            exact_dup_files.update(files[1:])  # Keep first as master

        # Compute perceptual hashes for remaining files
        hashes = {}
        for img_path in image_files:
            if img_path not in exact_dup_files:
                img_hashes = self.hasher.compute_hashes(img_path)
                if img_hashes:
                    hashes[str(img_path)] = img_hashes

        # Find similar groups
        groups = self.hasher.find_similar_groups(hashes, self.similarity_threshold)

        # Convert to DuplicateGroup objects
        for group_paths in groups:
            paths = [Path(p) for p in group_paths]

            # Choose master (prefer organized files, then largest)
            master = self._choose_master(paths)
            duplicates = [p for p in paths if p != master]

            # Calculate similarity scores
            master_hash = hashes[str(master)]
            similarity_scores = {}
            for dup in duplicates:
                score = self.hasher.compute_similarity(
                    master_hash,
                    hashes[str(dup)]
                )
                similarity_scores[str(dup)] = score

            # Calculate sizes
            total_size = sum(p.stat().st_size for p in paths)
            potential_savings = sum(p.stat().st_size for p in duplicates)

            group = DuplicateGroup(
                master=master,
                duplicates=duplicates,
                similarity_scores=similarity_scores,
                total_size=total_size,
                potential_savings=potential_savings,
                group_type='similar'
            )

            self.similar_groups.append(group)

    def _choose_master(self, paths: list[Path]) -> Path:
        """Choose the master file from a group."""
        # Scoring system for choosing master
        scores = {}

        for path in paths:
            score = 0

            # Prefer files in organized directories
            if 'organized' in str(path):
                score += 100

            # Prefer files with metadata
            if path.with_suffix('.json').exists():
                score += 50

            # Prefer larger files (likely higher quality)
            try:
                size = path.stat().st_size
                score += size / 1_000_000  # MB as score
            except (OSError, AttributeError):
                pass

            # Prefer files with better names (no IMG_ prefix)
            if not path.name.startswith('IMG_'):
                score += 10

            scores[path] = score

        # Return path with highest score
        return max(scores.items(), key=lambda x: x[1])[0]

    def get_duplicate_report(self) -> dict:
        """Generate comprehensive duplicate report."""
        report = {
            'scan_time': datetime.now().isoformat(),
            'exact_duplicates': {
                'count': len(self.exact_duplicates),
                'total_files': sum(len(g) for g in self.exact_duplicates.values()),
                'groups': []
            },
            'similar_images': {
                'count': len(self.similar_groups),
                'total_files': sum(len(g.duplicates) + 1 for g in self.similar_groups),
                'groups': []
            },
            'potential_savings': 0
        }

        # Add exact duplicate groups
        for file_hash, files in self.exact_duplicates.items():
            master = files[0]
            duplicates = files[1:]

            total_size = sum(f.stat().st_size for f in files)
            savings = sum(f.stat().st_size for f in duplicates)

            report['exact_duplicates']['groups'].append({
                'master': str(master),
                'duplicates': [str(f) for f in duplicates],
                'total_size': total_size,
                'potential_savings': savings,
                'hash': file_hash[:8] + '...'
            })

            report['potential_savings'] += savings

        # Add similar image groups
        for group in self.similar_groups:
            report['similar_images']['groups'].append({
                'master': str(group.master),
                'duplicates': [str(f) for f in group.duplicates],
                'similarity_scores': group.similarity_scores,
                'total_size': group.total_size,
                'potential_savings': group.potential_savings
            })

            report['potential_savings'] += group.potential_savings

        return report

    def remove_duplicates(
        self,
        dry_run: bool = True,
        backup_dir: Path | None = None,
        remove_similar: bool = False
    ) -> dict[str, int]:
        """
        Remove duplicate files.

        Args:
            dry_run: If True, only report what would be removed
            backup_dir: If provided, move files here instead of deleting
            remove_similar: If True, also remove similar (not just exact)

        Returns:
            Statistics about removed files
        """
        stats = {
            'exact_removed': 0,
            'similar_removed': 0,
            'space_freed': 0,
            'errors': 0
        }

        # Process exact duplicates
        for files in self.exact_duplicates.values():
            master = files[0]
            duplicates = files[1:]

            for dup in duplicates:
                try:
                    if dry_run:
                        logger.info(f"Would remove: {dup} (duplicate of {master})")
                    else:
                        if backup_dir:
                            # Move to backup
                            backup_path = backup_dir / dup.name
                            backup_path.parent.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(dup), str(backup_path))
                            logger.info(f"Moved to backup: {dup}")
                        else:
                            # Delete
                            dup.unlink()
                            logger.info(f"Removed: {dup}")

                    stats['exact_removed'] += 1
                    stats['space_freed'] += dup.stat().st_size

                except Exception as e:
                    logger.error(f"Error removing {dup}: {e}")
                    stats['errors'] += 1

        # Process similar images if requested
        if remove_similar:
            for group in self.similar_groups:
                for dup in group.duplicates:
                    try:
                        if dry_run:
                            logger.info(
                                f"Would remove: {dup} "
                                f"(similar to {group.master}, "
                                f"score: {group.similarity_scores.get(str(dup), 0):.2f})"
                            )
                        else:
                            if backup_dir:
                                backup_path = backup_dir / dup.name
                                backup_path.parent.mkdir(parents=True, exist_ok=True)
                                shutil.move(str(dup), str(backup_path))
                                logger.info(f"Moved to backup: {dup}")
                            else:
                                dup.unlink()
                                logger.info(f"Removed: {dup}")

                        stats['similar_removed'] += 1
                        stats['space_freed'] += dup.stat().st_size

                    except Exception as e:
                        logger.error(f"Error removing {dup}: {e}")
                        stats['errors'] += 1

        return stats

    def create_hardlinks(self, dry_run: bool = True) -> dict[str, int]:
        """
        Replace duplicates with hardlinks to save space.

        Args:
            dry_run: If True, only report what would be done

        Returns:
            Statistics about created hardlinks
        """
        stats = {
            'hardlinks_created': 0,
            'space_saved': 0,
            'errors': 0
        }

        for files in self.exact_duplicates.values():
            master = files[0]
            duplicates = files[1:]

            for dup in duplicates:
                try:
                    if dry_run:
                        logger.info(f"Would hardlink: {dup} -> {master}")
                    else:
                        # Remove duplicate and create hardlink
                        dup.unlink()
                        dup.hardlink_to(master)
                        logger.info(f"Created hardlink: {dup} -> {master}")

                    stats['hardlinks_created'] += 1
                    stats['space_saved'] += dup.stat().st_size

                except Exception as e:
                    logger.error(f"Error creating hardlink for {dup}: {e}")
                    stats['errors'] += 1

        return stats
