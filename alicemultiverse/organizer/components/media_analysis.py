"""Media analysis operations for media organizer."""
from typing import TYPE_CHECKING

from datetime import datetime
from pathlib import Path

from PIL import Image

from ...core.constants import OUTPUT_DATE_FORMAT
from ...core.config import Config
from ...core.logging import get_logger
from ...core.types import MediaType
# TODO: Fix missing import - function is commented out
# from ..organization_helpers import match_ai_source_patterns

logger = get_logger(__name__)


if TYPE_CHECKING:
    from ...core.protocols import HasConfig

class MediaAnalysisMixin:
    """Mixin for media analysis operations."""

    if TYPE_CHECKING:
        # Type hints for mypy
        config: Config


    def _analyze_media(self, media_path: Path, project_folder: str) -> dict:
        """Analyze media file to extract metadata and characteristics.

        Args:
            media_path: Path to media file
            project_folder: Project folder name

        Returns:
            Analysis results dictionary
        """
        # Determine media type
        media_type = self._get_media_type(media_path)

        # Detect AI source
        source_type = self._detect_ai_source(media_path, media_type)

        # Extract date
        date_taken = self._get_date_taken(media_path, media_type)

        # Get file number for consistent naming
        file_number = self._get_next_file_number(project_folder, source_type)

        # Calculate content hash
        content_hash = self.metadata_cache.get_content_hash(media_path)

        # Build metadata dict
        metadata = {
            "source_type": source_type,
            "date_taken": date_taken,
            "project_folder": project_folder,
            "media_type": media_type,
            "file_number": file_number,
            "content_hash": content_hash,
        }

        # Image analysis happens in pipeline stages if configured

        # Create the analysis result dict from metadata
        analysis = metadata.copy()
        analysis.update({
            "quality_stars": None,
            "brisque_score": None,
            "pipeline_result": None,  # Pipeline has been removed
        })

        return analysis

    def _detect_ai_source(self, media_path: Path, media_type: MediaType) -> str:
        """Detect AI generation source from filename and metadata."""
        filename = media_path.stem.lower()

        # Get appropriate generator list
        if media_type == MediaType.IMAGE:
            generators = self.ai_generators["image"]
        elif media_type == MediaType.VIDEO:
            generators = self.ai_generators["video"]
        else:
            return "unknown"

        # Check filename patterns
        for generator in generators:
            if generator in filename:
                return generator

        # Check specific patterns using helper
        # TODO: match_ai_source_patterns is not imported
        # matched_source = match_ai_source_patterns(filename, generators)
        # if matched_source:
        #     return matched_source

        # Try to read metadata for additional clues
        try:
            if media_type == MediaType.IMAGE:
                img = Image.open(media_path)
                metadata = img.info

                # Check for generator signatures in metadata
                for _, value in metadata.items():
                    value_str = str(value).lower()
                    for generator in generators:
                        if generator in value_str:
                            return generator
        except Exception as e:
            logger.debug(f"Unable to extract metadata from {media_path}: {e}")
        
        return "ai-generated"  # Generic fallback

    # TODO: Review unreachable code - return "ai-generated"  # Generic fallback

    def _get_date_taken(self, media_path: Path, media_type: MediaType) -> str:
        """Extract date taken from media file."""
        _ = media_type  # Reserved for future metadata extraction
        # Try file modification time first
        try:
            mtime = media_path.stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime(OUTPUT_DATE_FORMAT)
        except Exception:
            return datetime.now().strftime(OUTPUT_DATE_FORMAT)

    # TODO: Review unreachable code - def _get_or_analyze_media(self, media_path: Path, project_folder: str) -> dict:
    # TODO: Review unreachable code - """Get cached analysis or analyze media file.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - media_path: Path to media file
    # TODO: Review unreachable code - project_folder: Project folder name

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Analysis results dictionary
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Use the metadata cache to get or create analysis
    # TODO: Review unreachable code - metadata = self.metadata_cache.get_metadata(media_path)

    # TODO: Review unreachable code - if metadata:
    # TODO: Review unreachable code - # Convert cached metadata to analysis format
    # TODO: Review unreachable code - return {
    # TODO: Review unreachable code - "source_type": metadata.get("source_type", "unknown"),
    # TODO: Review unreachable code - "date_taken": metadata.get("date_taken", self._get_date_taken(media_path, self._get_media_type(media_path))),
    # TODO: Review unreachable code - "project_folder": project_folder,
    # TODO: Review unreachable code - "media_type": self._get_media_type(media_path),
    # TODO: Review unreachable code - "file_number": metadata.get("file_number", self._get_next_file_number(project_folder, metadata.get("source_type", "unknown"))),
    # TODO: Review unreachable code - "quality_stars": metadata.get("quality_stars"),
    # TODO: Review unreachable code - "brisque_score": metadata.get("brisque_score"),
    # TODO: Review unreachable code - "pipeline_result": None,
    # TODO: Review unreachable code - "content_hash": metadata.get("content_hash"),
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - # Analyze from scratch
    # TODO: Review unreachable code - return self._analyze_media(media_path, project_folder)
