"""Extract and enrich metadata from media files."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image
from PIL.ExifTags import TAGS

from ..core.types import AnalysisResult, MediaType
from .models import MOOD_VOCABULARY, STYLE_VOCABULARY, AssetMetadata, AssetRole

logger = logging.getLogger(__name__)


class MetadataExtractor:
    """Extract rich metadata from media files for AI navigation."""

    def __init__(self):
        """Initialize metadata extractor."""
        self.prompt_patterns = {
            # Common prompt patterns to extract
            "style": re.compile(r"(?:style|aesthetic)[:\s]+([^,\n]+)", re.I),
            "mood": re.compile(r"(?:mood|atmosphere|feeling)[:\s]+([^,\n]+)", re.I),
            "subject": re.compile(r"(?:subject|featuring|portrait of)[:\s]+([^,\n]+)", re.I),
        }

    def extract_metadata(
        self, file_path: Path, analysis: AnalysisResult, project_id: str, content_hash: str
    ) -> AssetMetadata:
        """Extract complete metadata from a media file.

        Args:
            file_path: Path to the media file
            analysis: Basic analysis result
            project_id: Project identifier
            content_hash: Content-based hash

        Returns:
            Complete asset metadata
        """
        # Start with basic metadata
        metadata = AssetMetadata(
            asset_id=content_hash,
            file_path=str(file_path),
            file_name=file_path.name,
            file_size=file_path.stat().st_size,
            mime_type=self._get_mime_type(file_path, analysis["media_type"]),
            created_at=datetime.fromtimestamp(file_path.stat().st_ctime),
            modified_at=datetime.fromtimestamp(file_path.stat().st_mtime),
            imported_at=datetime.now(),
            project_id=project_id,
            project_phase=None,  # Will be set based on project state
            session_id=None,  # Will be set by session manager
            source_type=analysis["source_type"],
            generation_params={},
            prompt=None,
            model=None,
            seed=None,
            style_tags=[],
            mood_tags=[],
            subject_tags=[],
            color_tags=[],
            technical_tags=[],
            custom_tags=[],
            parent_id=None,
            variation_of=None,
            similar_to=[],
            referenced_by=[],
            grouped_with=[],
            quality_score=analysis.get("brisque_score"),
            quality_stars=analysis.get("quality_stars"),
            technical_scores={},
            ai_defects=[],
            role=AssetRole.WIP,  # Default role
            description=None,
            notes=None,
            approved=False,
            flagged=False,
            timecode=None,
            beat_aligned=None,
            scene_number=None,
            lyrics_line=None,
        )

        # Extract generation parameters from EXIF/metadata
        if analysis["media_type"] == MediaType.IMAGE:
            self._extract_image_metadata(file_path, metadata)

        # Extract semantic tags from filename and prompt
        self._extract_semantic_tags(file_path, metadata)

        # Detect role from filename patterns
        self._detect_asset_role(file_path, metadata)

        return metadata

    def _get_mime_type(self, file_path: Path, media_type: MediaType) -> str:
        """Get MIME type for file."""
        ext = file_path.suffix.lower()
        mime_map = {
            ".jpg": "image/jpeg",
            ".jpeg": "image/jpeg",
            ".png": "image/png",
            ".mp4": "video/mp4",
            ".mov": "video/quicktime",
        }
        return mime_map.get(ext, "application/octet-stream")

    def _extract_image_metadata(self, file_path: Path, metadata: AssetMetadata) -> None:
        """Extract metadata from image EXIF and embedded data."""
        try:
            with Image.open(file_path) as img:
                # Get EXIF data
                exif_data = img.getexif()
                if exif_data:
                    exif_dict = {}
                    for tag_id, value in exif_data.items():
                        tag = TAGS.get(tag_id, tag_id)
                        exif_dict[tag] = value

                    # Look for AI generation data in EXIF
                    if "ImageDescription" in exif_dict:
                        desc = str(exif_dict["ImageDescription"])
                        metadata["prompt"] = self._extract_prompt(desc)
                        metadata["generation_params"].update(self._parse_generation_params(desc))

                    # Software tag often contains AI tool info
                    if "Software" in exif_dict:
                        software = str(exif_dict["Software"]).lower()
                        if "stable diffusion" in software:
                            metadata["source_type"] = "stablediffusion"
                        elif "midjourney" in software:
                            metadata["source_type"] = "midjourney"

                # Check for PNG metadata
                if hasattr(img, "info"):
                    png_info = img.info

                    # Common AI metadata fields in PNG
                    if "parameters" in png_info:
                        params = png_info["parameters"]
                        metadata["prompt"] = self._extract_prompt(params)
                        metadata["generation_params"].update(self._parse_generation_params(params))

                    # Look for specific AI tool metadata
                    for key, value in png_info.items():
                        if "prompt" in key.lower():
                            metadata["prompt"] = str(value)
                        elif "seed" in key.lower():
                            try:
                                metadata["seed"] = int(value)
                            except Exception:
                                pass
                        elif "model" in key.lower():
                            metadata["model"] = str(value)

                # Extract dominant colors
                if img.mode != "RGBA":
                    img_rgb = img.convert("RGB")
                    colors = img_rgb.getcolors(maxcolors=100000)
                    if colors:
                        # Simple color analysis - can be enhanced
                        metadata["color_tags"] = self._analyze_colors(colors)

        except Exception as e:
            logger.warning(f"Failed to extract image metadata from {file_path}: {e}")

    def _extract_prompt(self, text: str) -> str | None:
        """Extract prompt from generation parameters text."""
        # Common patterns for prompts
        patterns = [
            r"Prompt:\s*([^\n]+)",
            r'prompt"?:\s*"?([^"\n]+)',
            r"^([^,\n]{20,})",  # First long text before comma
        ]

        for pattern in patterns:
            match = re.search(pattern, text, re.I | re.M)
            if match:
                return match.group(1).strip()

        return None

    def _parse_generation_params(self, text: str) -> dict[str, Any]:
        """Parse generation parameters from text."""
        params = {}

        # Common parameter patterns
        param_patterns = {
            "steps": r"(?:steps|sampling steps)[:\s]+(\d+)",
            "cfg_scale": r"(?:cfg scale|guidance scale)[:\s]+([\d.]+)",
            "sampler": r"(?:sampler|sampling method)[:\s]+([^\s,]+)",
            "model": r"(?:model|checkpoint)[:\s]+([^\s,]+)",
            "seed": r"seed[:\s]+(\d+)",
            "size": r"size[:\s]+(\d+x\d+)",
        }

        for param, pattern in param_patterns.items():
            match = re.search(pattern, text, re.I)
            if match:
                value = match.group(1)
                # Convert to appropriate type
                if param in ["steps", "seed"]:
                    try:
                        value = int(value)
                    except Exception:
                        pass
                elif param == "cfg_scale":
                    try:
                        value = float(value)
                    except Exception:
                        pass
                params[param] = value

        return params

    def _extract_semantic_tags(self, file_path: Path, metadata: AssetMetadata) -> None:
        """Extract semantic tags from filename and prompt."""
        filename = file_path.stem.lower()
        prompt = (metadata.get("prompt") or "").lower()
        combined_text = f"{filename} {prompt}"

        # Extract style tags
        for style in STYLE_VOCABULARY:
            if style in combined_text:
                metadata["style_tags"].append(style)

        # Extract mood tags
        for mood in MOOD_VOCABULARY:
            if mood in combined_text:
                metadata["mood_tags"].append(mood)

        # Extract subject tags from common patterns
        subject_patterns = [
            (r"portrait", "portrait"),
            (r"landscape", "landscape"),
            (r"character", "character"),
            (r"face", "face"),
            (r"person|people|man|woman", "person"),
            (r"building|architecture", "architecture"),
            (r"nature|forest|mountain|ocean", "nature"),
            (r"city|urban", "urban"),
            (r"abstract", "abstract"),
        ]

        for pattern, tag in subject_patterns:
            if re.search(pattern, combined_text):
                if tag not in metadata["subject_tags"]:
                    metadata["subject_tags"].append(tag)

        # Technical tags based on parameters
        if metadata["generation_params"]:
            params = metadata["generation_params"]
            if params.get("steps", 0) > 100:
                metadata["technical_tags"].append("high-quality")
            if params.get("cfg_scale", 0) > 15:
                metadata["technical_tags"].append("high-guidance")

    def _analyze_colors(self, colors: list[tuple]) -> list[str]:
        """Analyze color distribution and return color tags."""
        # This is a simplified version - could be enhanced with proper color analysis
        color_tags = []

        # Count pixels by basic color ranges
        color_counts = {"red": 0, "green": 0, "blue": 0, "black": 0, "white": 0, "gray": 0}

        total_pixels = sum(count for count, _ in colors)

        for count, (r, g, b) in colors:
            # Classify color
            if r < 50 and g < 50 and b < 50:
                color_counts["black"] += count
            elif r > 200 and g > 200 and b > 200:
                color_counts["white"] += count
            elif abs(r - g) < 30 and abs(g - b) < 30:
                color_counts["gray"] += count
            elif r > max(g, b) + 50:
                color_counts["red"] += count
            elif g > max(r, b) + 50:
                color_counts["green"] += count
            elif b > max(r, g) + 50:
                color_counts["blue"] += count

        # Add dominant colors as tags
        for color, count in color_counts.items():
            if count / total_pixels > 0.2:  # More than 20% of image
                color_tags.append(color)

        return color_tags

    def _detect_asset_role(self, file_path: Path, metadata: AssetMetadata) -> None:
        """Detect asset role from filename patterns."""
        filename = file_path.stem.lower()

        role_patterns = {
            AssetRole.HERO: [r"hero", r"main", r"featured", r"final"],
            AssetRole.B_ROLL: [r"b-?roll", r"secondary", r"background"],
            AssetRole.REFERENCE: [r"ref", r"reference", r"inspiration"],
            AssetRole.TEST: [r"test", r"experiment", r"trial"],
            AssetRole.FINAL: [r"final", r"approved", r"done"],
            AssetRole.ARCHIVED: [r"archive", r"old", r"deprecated"],
        }

        for role, patterns in role_patterns.items():
            for pattern in patterns:
                if re.search(pattern, filename):
                    metadata["role"] = role
                    return

        # Default is already set to WIP
