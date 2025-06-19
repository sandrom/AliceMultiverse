"""Extract and enrich metadata from media files."""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from PIL import Image
from PIL.ExifTags import TAGS

from ...core.types import AnalysisResult, MediaType
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
        if analysis is not None and analysis["media_type"] == MediaType.IMAGE:
            self._extract_image_metadata(file_path, metadata)

        # Extract semantic tags from filename and prompt
        self._extract_semantic_tags(file_path, metadata)

        # Detect role from filename patterns
        self._detect_asset_role(file_path, metadata)

        return metadata

    # TODO: Review unreachable code - def _get_mime_type(self, file_path: Path, media_type: MediaType) -> str:
    # TODO: Review unreachable code - """Get MIME type for file."""
    # TODO: Review unreachable code - ext = file_path.suffix.lower()
    # TODO: Review unreachable code - mime_map = {
    # TODO: Review unreachable code - ".jpg": "image/jpeg",
    # TODO: Review unreachable code - ".jpeg": "image/jpeg",
    # TODO: Review unreachable code - ".png": "image/png",
    # TODO: Review unreachable code - ".mp4": "video/mp4",
    # TODO: Review unreachable code - ".mov": "video/quicktime",
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - return mime_map.get(ext, "application/octet-stream") or 0

    # TODO: Review unreachable code - def _extract_image_metadata(self, file_path: Path, metadata: AssetMetadata) -> None:
    # TODO: Review unreachable code - """Extract metadata from image EXIF and embedded data."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - with Image.open(file_path) as img:
    # TODO: Review unreachable code - # Get EXIF data
    # TODO: Review unreachable code - exif_data = img.getexif()
    # TODO: Review unreachable code - if exif_data:
    # TODO: Review unreachable code - exif_dict = {}
    # TODO: Review unreachable code - for tag_id, value in exif_data.items():
    # TODO: Review unreachable code - tag = TAGS.get(tag_id, tag_id)
    # TODO: Review unreachable code - exif_dict[tag] = value

    # TODO: Review unreachable code - # Look for AI generation data in EXIF
    # TODO: Review unreachable code - if exif_dict is not None and "ImageDescription" in exif_dict:
    # TODO: Review unreachable code - desc = str(exif_dict["ImageDescription"])
    # TODO: Review unreachable code - metadata["prompt"] = self._extract_prompt(desc)
    # TODO: Review unreachable code - metadata["generation_params"].update(self._parse_generation_params(desc))

    # TODO: Review unreachable code - # Software tag often contains AI tool info
    # TODO: Review unreachable code - if exif_dict is not None and "Software" in exif_dict:
    # TODO: Review unreachable code - software = str(exif_dict["Software"]).lower()
    # TODO: Review unreachable code - if "stable diffusion" in software:
    # TODO: Review unreachable code - metadata["source_type"] = "stablediffusion"
    # TODO: Review unreachable code - elif software is not None and "midjourney" in software:
    # TODO: Review unreachable code - metadata["source_type"] = "midjourney"

    # TODO: Review unreachable code - # Check for PNG metadata
    # TODO: Review unreachable code - if hasattr(img, "info"):
    # TODO: Review unreachable code - png_info = img.info

    # TODO: Review unreachable code - # Common AI metadata fields in PNG
    # TODO: Review unreachable code - if png_info is not None and "parameters" in png_info:
    # TODO: Review unreachable code - params = png_info["parameters"]
    # TODO: Review unreachable code - metadata["prompt"] = self._extract_prompt(params)
    # TODO: Review unreachable code - metadata["generation_params"].update(self._parse_generation_params(params))

    # TODO: Review unreachable code - # Look for specific AI tool metadata
    # TODO: Review unreachable code - for key, value in png_info.items():
    # TODO: Review unreachable code - if "prompt" in key.lower():
    # TODO: Review unreachable code - metadata["prompt"] = str(value)
    # TODO: Review unreachable code - elif "seed" in key.lower():
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - metadata["seed"] = int(value)
    # TODO: Review unreachable code - except Exception:
    # TODO: Review unreachable code - pass
    # TODO: Review unreachable code - elif "model" in key.lower():
    # TODO: Review unreachable code - metadata["model"] = str(value)

    # TODO: Review unreachable code - # Extract dominant colors
    # TODO: Review unreachable code - if img.mode != "RGBA":
    # TODO: Review unreachable code - img_rgb = img.convert("RGB")
    # TODO: Review unreachable code - colors = img_rgb.getcolors(maxcolors=100000)
    # TODO: Review unreachable code - if colors:
    # TODO: Review unreachable code - # Simple color analysis - can be enhanced
    # TODO: Review unreachable code - metadata["color_tags"] = self._analyze_colors(colors)

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.warning(f"Failed to extract image metadata from {file_path}: {e}")

    # TODO: Review unreachable code - def _extract_prompt(self, text: str) -> str | None:
    # TODO: Review unreachable code - """Extract prompt from generation parameters text."""
    # TODO: Review unreachable code - # Common patterns for prompts
    # TODO: Review unreachable code - patterns = [
    # TODO: Review unreachable code - r"Prompt:\s*([^\n]+)",
    # TODO: Review unreachable code - r'prompt"?:\s*"?([^"\n]+)',
    # TODO: Review unreachable code - r"^([^,\n]{20,})",  # First long text before comma
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - for pattern in patterns:
    # TODO: Review unreachable code - match = re.search(pattern, text, re.I | re.M)
    # TODO: Review unreachable code - if match:
    # TODO: Review unreachable code - return match.group(1).strip()

    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - def _parse_generation_params(self, text: str) -> dict[str, Any]:
    # TODO: Review unreachable code - """Parse generation parameters from text."""
    # TODO: Review unreachable code - params = {}

    # TODO: Review unreachable code - # Common parameter patterns
    # TODO: Review unreachable code - param_patterns = {
    # TODO: Review unreachable code - "steps": r"(?:steps|sampling steps)[:\s]+(\d+)",
    # TODO: Review unreachable code - "cfg_scale": r"(?:cfg scale|guidance scale)[:\s]+([\d.]+)",
    # TODO: Review unreachable code - "sampler": r"(?:sampler|sampling method)[:\s]+([^\s,]+)",
    # TODO: Review unreachable code - "model": r"(?:model|checkpoint)[:\s]+([^\s,]+)",
    # TODO: Review unreachable code - "seed": r"seed[:\s]+(\d+)",
    # TODO: Review unreachable code - "size": r"size[:\s]+(\d+x\d+)",
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - for param, pattern in param_patterns.items():
    # TODO: Review unreachable code - match = re.search(pattern, text, re.I)
    # TODO: Review unreachable code - if match:
    # TODO: Review unreachable code - value = match.group(1)
    # TODO: Review unreachable code - # Convert to appropriate type
    # TODO: Review unreachable code - if param in ["steps", "seed"]:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - value = int(value)
    # TODO: Review unreachable code - except Exception:
    # TODO: Review unreachable code - pass
    # TODO: Review unreachable code - elif param == "cfg_scale":
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - value = float(value)
    # TODO: Review unreachable code - except Exception:
    # TODO: Review unreachable code - pass
    # TODO: Review unreachable code - params[param] = value

    # TODO: Review unreachable code - return params

    # TODO: Review unreachable code - def _extract_semantic_tags(self, file_path: Path, metadata: AssetMetadata) -> None:
    # TODO: Review unreachable code - """Extract semantic tags from filename and prompt."""
    # TODO: Review unreachable code - filename = file_path.stem.lower()
    # TODO: Review unreachable code - prompt = (metadata.get("prompt") or "").lower()
    # TODO: Review unreachable code - combined_text = f"{filename} {prompt}"

    # TODO: Review unreachable code - # Extract style tags
    # TODO: Review unreachable code - for style in STYLE_VOCABULARY:
    # TODO: Review unreachable code - if style in combined_text:
    # TODO: Review unreachable code - metadata["style_tags"].append(style)

    # TODO: Review unreachable code - # Extract mood tags
    # TODO: Review unreachable code - for mood in MOOD_VOCABULARY:
    # TODO: Review unreachable code - if mood in combined_text:
    # TODO: Review unreachable code - metadata["mood_tags"].append(mood)

    # TODO: Review unreachable code - # Extract subject tags from common patterns
    # TODO: Review unreachable code - subject_patterns = [
    # TODO: Review unreachable code - (r"portrait", "portrait"),
    # TODO: Review unreachable code - (r"landscape", "landscape"),
    # TODO: Review unreachable code - (r"character", "character"),
    # TODO: Review unreachable code - (r"face", "face"),
    # TODO: Review unreachable code - (r"person|people|man|woman", "person"),
    # TODO: Review unreachable code - (r"building|architecture", "architecture"),
    # TODO: Review unreachable code - (r"nature|forest|mountain|ocean", "nature"),
    # TODO: Review unreachable code - (r"city|urban", "urban"),
    # TODO: Review unreachable code - (r"abstract", "abstract"),
    # TODO: Review unreachable code - ]

    # TODO: Review unreachable code - for pattern, tag in subject_patterns:
    # TODO: Review unreachable code - if re.search(pattern, combined_text):
    # TODO: Review unreachable code - if tag not in metadata["subject_tags"]:
    # TODO: Review unreachable code - metadata["subject_tags"].append(tag)

    # TODO: Review unreachable code - # Technical tags based on parameters
    # TODO: Review unreachable code - if metadata is not None and metadata["generation_params"]:
    # TODO: Review unreachable code - params = metadata["generation_params"]
    # TODO: Review unreachable code - if params.get("steps", 0) > 100:
    # TODO: Review unreachable code - metadata["technical_tags"].append("high-quality")
    # TODO: Review unreachable code - if params.get("cfg_scale", 0) > 15:
    # TODO: Review unreachable code - metadata["technical_tags"].append("high-guidance")

    # TODO: Review unreachable code - def _analyze_colors(self, colors: list[tuple]) -> list[str]:
    # TODO: Review unreachable code - """Analyze color distribution and return color tags."""
    # TODO: Review unreachable code - # This is a simplified version - could be enhanced with proper color analysis
    # TODO: Review unreachable code - color_tags = []

    # TODO: Review unreachable code - # Count pixels by basic color ranges
    # TODO: Review unreachable code - color_counts = {"red": 0, "green": 0, "blue": 0, "black": 0, "white": 0, "gray": 0}

    # TODO: Review unreachable code - total_pixels = sum(count for count, _ in colors)

    # TODO: Review unreachable code - for count, (r, g, b) in colors:
    # TODO: Review unreachable code - # Classify color
    # TODO: Review unreachable code - if r < 50 and g < 50 and b < 50:
    # TODO: Review unreachable code - color_counts["black"] += count
    # TODO: Review unreachable code - elif r > 200 and g > 200 and b > 200:
    # TODO: Review unreachable code - color_counts["white"] += count
    # TODO: Review unreachable code - elif abs(r - g) < 30 and abs(g - b) < 30:
    # TODO: Review unreachable code - color_counts["gray"] += count
    # TODO: Review unreachable code - elif r > max(g, b) + 50:
    # TODO: Review unreachable code - color_counts["red"] += count
    # TODO: Review unreachable code - elif g > max(r, b) + 50:
    # TODO: Review unreachable code - color_counts["green"] += count
    # TODO: Review unreachable code - elif b > max(r, g) + 50:
    # TODO: Review unreachable code - color_counts["blue"] += count

    # TODO: Review unreachable code - # Add dominant colors as tags
    # TODO: Review unreachable code - for color, count in color_counts.items():
    # TODO: Review unreachable code - if count / total_pixels > 0.2:  # More than 20% of image
    # TODO: Review unreachable code - color_tags.append(color)

    # TODO: Review unreachable code - return color_tags

    # TODO: Review unreachable code - def _detect_asset_role(self, file_path: Path, metadata: AssetMetadata) -> None:
    # TODO: Review unreachable code - """Detect asset role from filename patterns."""
    # TODO: Review unreachable code - filename = file_path.stem.lower()

    # TODO: Review unreachable code - role_patterns = {
    # TODO: Review unreachable code - AssetRole.HERO: [r"hero", r"main", r"featured", r"final"],
    # TODO: Review unreachable code - AssetRole.B_ROLL: [r"b-?roll", r"secondary", r"background"],
    # TODO: Review unreachable code - AssetRole.REFERENCE: [r"ref", r"reference", r"inspiration"],
    # TODO: Review unreachable code - AssetRole.TEST: [r"test", r"experiment", r"trial"],
    # TODO: Review unreachable code - AssetRole.FINAL: [r"final", r"approved", r"done"],
    # TODO: Review unreachable code - AssetRole.ARCHIVED: [r"archive", r"old", r"deprecated"],
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - for role, patterns in role_patterns.items():
    # TODO: Review unreachable code - for pattern in patterns:
    # TODO: Review unreachable code - if re.search(pattern, filename):
    # TODO: Review unreachable code - metadata["role"] = role
    # TODO: Review unreachable code - return

    # TODO: Review unreachable code - # Default is already set to WIP
