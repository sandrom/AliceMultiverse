"""Media analysis operations for media organizer."""

from datetime import datetime
from pathlib import Path

from PIL import Image

from ...core.constants import OUTPUT_DATE_FORMAT
from ...core.logging import get_logger
from ...core.types import MediaType
from ..organization_helpers import match_ai_source_patterns

logger = get_logger(__name__)


class MediaAnalysisMixin:
    """Mixin for media analysis operations."""

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
        matched_source = match_ai_source_patterns(filename, generators)
        if matched_source:
            return matched_source

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

    def _get_date_taken(self, media_path: Path, media_type: MediaType) -> str:
        """Extract date taken from media file."""
        _ = media_type  # Reserved for future metadata extraction
        # Try file modification time first
        try:
            mtime = media_path.stat().st_mtime
            return datetime.fromtimestamp(mtime).strftime(OUTPUT_DATE_FORMAT)
        except Exception:
            return datetime.now().strftime(OUTPUT_DATE_FORMAT)

    def _get_or_analyze_media(self, media_path: Path, project_folder: str) -> dict:
        """Get cached analysis or analyze media file.

        Args:
            media_path: Path to media file
            project_folder: Project folder name

        Returns:
            Analysis results dictionary
        """
        # Use the metadata cache to get or create analysis
        metadata = self.metadata_cache.get_metadata(media_path)

        if metadata:
            # Convert cached metadata to analysis format
            return {
                "source_type": metadata.get("source_type", "unknown"),
                "date_taken": metadata.get("date_taken", self._get_date_taken(media_path, self._get_media_type(media_path))),
                "project_folder": project_folder,
                "media_type": self._get_media_type(media_path),
                "file_number": metadata.get("file_number", self._get_next_file_number(project_folder, metadata.get("source_type", "unknown"))),
                "quality_stars": metadata.get("quality_stars"),
                "brisque_score": metadata.get("brisque_score"),
                "pipeline_result": None,
                "content_hash": metadata.get("content_hash"),
            }
        else:
            # Analyze from scratch
            return self._analyze_media(media_path, project_folder)
