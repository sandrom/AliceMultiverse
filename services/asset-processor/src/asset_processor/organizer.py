"""Asset organization planning."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from alice_config import get_config
from alice_models import QualityRating, SourceType

from .models import OrganizePlanResponse

logger = logging.getLogger(__name__)


class AssetOrganizer:
    """Plans asset organization without moving files."""

    def __init__(self):
        """Initialize organizer."""
        self.logger = logger.getChild("organizer")
        self.config = get_config()

        # Get organized path from config
        self.organized_root = (
            Path(self.config.get("paths.organized", "./organized")).expanduser().resolve()
        )

    async def plan_organization(
        self,
        file_path: Path,
        content_hash: str,
        metadata: dict[str, Any],
        quality_rating: QualityRating | None = None,
    ) -> OrganizePlanResponse:
        """Generate organization plan for an asset."""

        # Extract components
        date_folder = self._extract_date_folder(file_path, metadata)
        project_name = self._extract_project_name(file_path, metadata)
        source_type = self._extract_source_type(metadata)
        quality_folder = self._get_quality_folder(quality_rating) if quality_rating else None

        # Get next sequence number
        sequence_number = await self._get_next_sequence_number(
            date_folder, project_name, source_type, quality_folder
        )

        # Build destination path
        dest_components = [str(self.organized_root), date_folder, project_name, source_type]
        if quality_folder:
            dest_components.append(quality_folder)

        dest_dir = Path(*dest_components)

        # Generate filename
        suggested_filename = self._generate_filename(
            project_name, sequence_number, file_path.suffix
        )

        destination_path = dest_dir / suggested_filename

        return OrganizePlanResponse(
            destination_path=str(destination_path),
            date_folder=date_folder,
            project_name=project_name,
            source_type=source_type,
            quality_folder=quality_folder,
            sequence_number=sequence_number,
            suggested_filename=suggested_filename,
            organization_rule="date-project-source-quality",
            preserve_original_name=False,
        )

    def _extract_date_folder(self, file_path: Path, metadata: dict[str, Any]) -> str:
        """Extract date folder from file or metadata."""
        # Try to get from metadata first
        if "created" in metadata:
            try:
                dt = datetime.fromisoformat(metadata["created"])
                return dt.strftime("%Y-%m-%d")
            except Exception:
                pass

        # Try file modification time
        try:
            mtime = file_path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime)
            return dt.strftime("%Y-%m-%d")
        except Exception:
            pass

        # Default to today
        return datetime.now().strftime("%Y-%m-%d")

    def _extract_project_name(self, file_path: Path, metadata: dict[str, Any]) -> str:
        """Extract project name from file path or metadata."""
        # Check if file is in a project folder structure
        parts = file_path.parts

        # Look for common project folder patterns
        for i, part in enumerate(parts):
            if part.lower() in ["inbox", "downloads", "desktop", "documents"]:
                # Next folder might be project
                if i + 1 < len(parts) - 1:  # Not the file itself
                    project = parts[i + 1]
                    # Clean project name
                    project = re.sub(r"[^\w\-_]", "_", project)
                    if project and project != "_":
                        return project

        # Try to extract from filename
        filename = file_path.stem

        # Remove common prefixes/suffixes
        patterns_to_remove = [
            r"^\d{4}-\d{2}-\d{2}[_\-\s]*",  # Date prefix
            r"[_\-\s]*\d{4}-\d{2}-\d{2}$",  # Date suffix
            r"[_\-\s]*v?\d+$",  # Version suffix
            r"^IMG[_\-]?\d+",  # IMG prefix
            r"^DSC[_\-]?\d+",  # DSC prefix
        ]

        cleaned = filename
        for pattern in patterns_to_remove:
            cleaned = re.sub(pattern, "", cleaned)

        # Extract project-like name
        if cleaned and len(cleaned) > 3:
            project = re.sub(r"[^\w\-_]", "_", cleaned)
            project = re.sub(r"_+", "_", project).strip("_")
            if project:
                return project

        return "untitled"

    def _extract_source_type(self, metadata: dict[str, Any]) -> str:
        """Extract AI source type from metadata."""
        # Check if AI source was detected
        if metadata.get("ai_source"):
            source = metadata["ai_source"]
            if isinstance(source, SourceType):
                return source.value
            return str(source)

        return "unknown"

    def _get_quality_folder(self, rating: QualityRating) -> str:
        """Get quality folder name from rating."""
        return f"{rating.value}-star"

    async def _get_next_sequence_number(
        self, date_folder: str, project_name: str, source_type: str, quality_folder: str | None
    ) -> int:
        """Get next sequence number for the project.

        Note: In the actual service, this would query a database or
        coordinate with the main service to ensure unique numbering.
        """
        # For now, return a placeholder
        # In production, this would check existing files or use a counter service
        return 1

    def _generate_filename(self, project_name: str, sequence_number: int, extension: str) -> str:
        """Generate organized filename."""
        # Format: project-00001.ext
        return f"{project_name}-{sequence_number:05d}{extension.lower()}"
