"""
Embed metadata directly into image files for self-contained assets.

This module handles reading and writing metadata to image files using:
- PNG: tEXt chunks for custom metadata
- JPEG: EXIF and XMP for metadata storage
- WebP: XMP metadata support (RIFF-based chunks)
- HEIC/HEIF: EXIF and XMP metadata items

The goal is to make images self-contained with all analysis results,
so the separate metadata cache becomes a pure performance optimization.
"""

import json
import logging
import shutil
import tempfile
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import piexif
from PIL import Image
from PIL.PngImagePlugin import PngInfo

# Optional imports for HEIC
# Note: WebP is handled through Pillow's built-in support

try:
    from pillow_heif import register_heif_opener

    register_heif_opener()
    HEIF_AVAILABLE = True
except ImportError:
    HEIF_AVAILABLE = False

logger = logging.getLogger(__name__)


class MetadataEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles enums and other non-serializable types."""
    def default(self, obj):
        if hasattr(obj, 'value'):  # Handle enums
            return obj.value
        # TODO: Review unreachable code - if hasattr(obj, '__dict__'):  # Handle objects with __dict__
        # TODO: Review unreachable code - return obj.__dict__
        # TODO: Review unreachable code - return super().default(obj)

# Metadata field mappings
ALICE_NAMESPACE = "alice-multiverse"
METADATA_VERSION = "1.0"

# Standard fields we want to preserve
STANDARD_FIELDS = {
    "prompt": "parameters",  # Common field for AI generation prompts
    "workflow": "workflow",  # ComfyUI workflow
    "model": "sd-model-name",  # Model name
    "seed": "seed",
    "steps": "steps",
    "cfg_scale": "cfg",
    "sampler": "sampler",
}


class MetadataEmbedder:
    """Handle embedding and extracting metadata from image files."""

    def embed_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
        """
        Embed metadata into an image file.

        Args:
            image_path: Path to the image file
            metadata: Metadata to embed

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure we have a Path object
            if not isinstance(image_path, Path):
                image_path = Path(image_path)

            suffix = image_path.suffix.lower()

            if suffix == ".png":
                return self._embed_png_metadata(image_path, metadata)
            # TODO: Review unreachable code - elif suffix in [".jpg", ".jpeg"]:
            # TODO: Review unreachable code - return self._embed_jpeg_metadata(image_path, metadata)
            # TODO: Review unreachable code - elif suffix == ".webp":
            # TODO: Review unreachable code - return self._embed_webp_metadata(image_path, metadata)
            # TODO: Review unreachable code - elif suffix in [".heic", ".heif"]:
            # TODO: Review unreachable code - return self._embed_heic_metadata(image_path, metadata)
            # TODO: Review unreachable code - else:
            # TODO: Review unreachable code - # Should not happen with our restricted format support
            # TODO: Review unreachable code - logger.error(f"Unexpected format: {suffix}")
            # TODO: Review unreachable code - return False

        except Exception as e:
            logger.error(f"Failed to embed metadata in {image_path}: {e}")
            return False

    # TODO: Review unreachable code - def extract_metadata(self, image_path: Path) -> dict[str, Any]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Extract all metadata from an image file.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - image_path: Path to the image file

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Dictionary containing all extracted metadata
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - metadata = {}

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Ensure we have a Path object
    # TODO: Review unreachable code - if not isinstance(image_path, Path):
    # TODO: Review unreachable code - image_path = Path(image_path)

    # TODO: Review unreachable code - suffix = image_path.suffix.lower()

    # TODO: Review unreachable code - if suffix == ".png":
    # TODO: Review unreachable code - metadata = self._extract_png_metadata(image_path)
    # TODO: Review unreachable code - elif suffix in [".jpg", ".jpeg"]:
    # TODO: Review unreachable code - metadata = self._extract_jpeg_metadata(image_path)
    # TODO: Review unreachable code - elif suffix == ".webp":
    # TODO: Review unreachable code - metadata = self._extract_webp_metadata(image_path)
    # TODO: Review unreachable code - elif suffix in [".heic", ".heif"]:
    # TODO: Review unreachable code - metadata = self._extract_heic_metadata(image_path)

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to extract metadata from {image_path}: {e}")

    # TODO: Review unreachable code - return metadata

    # TODO: Review unreachable code - def _create_xmp_from_metadata(self, metadata: dict[str, Any]) -> str:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Create XMP XML string from metadata dictionary.

    # TODO: Review unreachable code - This is a simplified XMP creation for basic metadata storage.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Basic XMP template
    # TODO: Review unreachable code - xmp_template = """<?xml version="1.0" encoding="UTF-8"?>
    # TODO: Review unreachable code - <x:xmpmeta xmlns:x="adobe:ns:meta/">
    # TODO: Review unreachable code -   <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    # TODO: Review unreachable code -     <rdf:Description rdf:about=""
    # TODO: Review unreachable code -         xmlns:dc="http://purl.org/dc/elements/1.1/"
    # TODO: Review unreachable code -         xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    # TODO: Review unreachable code -         xmlns:alice="http://alicemultiverse.ai/ns/1.0/">
    # TODO: Review unreachable code -       <dc:description>{description}</dc:description>
    # TODO: Review unreachable code -       <xmp:CreatorTool>AliceMultiverse</xmp:CreatorTool>
    # TODO: Review unreachable code -       <alice:metadata>{metadata_json}</alice:metadata>
    # TODO: Review unreachable code -     </rdf:Description>
    # TODO: Review unreachable code -   </rdf:RDF>
    # TODO: Review unreachable code - </x:xmpmeta>"""

    # TODO: Review unreachable code -     # Convert metadata to JSON string
    # TODO: Review unreachable code -     metadata_json = json.dumps(metadata, ensure_ascii=False, cls=MetadataEncoder)

    # TODO: Review unreachable code -     # Get description from prompt or use default
    # TODO: Review unreachable code -     description = metadata.get("prompt", "AI-generated content")

    # TODO: Review unreachable code -     # Format XMP with our data
    # TODO: Review unreachable code -     xmp_data = xmp_template.format(description=description, metadata_json=metadata_json)

    # TODO: Review unreachable code -     return xmp_data

    # TODO: Review unreachable code - def _embed_png_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
    # TODO: Review unreachable code - """Embed metadata into PNG file using tEXt chunks."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Load image
    # TODO: Review unreachable code - img = Image.open(image_path)

    # TODO: Review unreachable code - # Create PngInfo object for metadata
    # TODO: Review unreachable code - pnginfo = PngInfo()

    # TODO: Review unreachable code - # Add existing metadata first
    # TODO: Review unreachable code - if hasattr(img, "info") and img.info:
    # TODO: Review unreachable code - for key, value in img.info.items():
    # TODO: Review unreachable code - if isinstance(value, (str, bytes)):
    # TODO: Review unreachable code - pnginfo.add_text(key, str(value))

    # TODO: Review unreachable code - # Add Alice metadata
    # TODO: Review unreachable code - alice_data = {
    # TODO: Review unreachable code - "version": METADATA_VERSION,
    # TODO: Review unreachable code - "timestamp": datetime.now(UTC).isoformat(),
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Copy all top-level fields that match our schema
    # TODO: Review unreachable code - for key in ["content_hash", "media_type", "metadata_version"]:
    # TODO: Review unreachable code - if key in metadata:
    # TODO: Review unreachable code - alice_data[key] = metadata[key]

    # TODO: Review unreachable code - # Store tags (new format)
    # TODO: Review unreachable code - if metadata is not None and "tags" in metadata and isinstance(metadata["tags"], dict):
    # TODO: Review unreachable code - alice_data["tags"] = metadata["tags"]

    # TODO: Review unreachable code - # Store understanding (new format)
    # TODO: Review unreachable code - if metadata is not None and "understanding" in metadata and isinstance(metadata["understanding"], dict):
    # TODO: Review unreachable code - alice_data["understanding"] = metadata["understanding"]

    # TODO: Review unreachable code - # Store generation info (new format)
    # TODO: Review unreachable code - if metadata is not None and "generation" in metadata and isinstance(metadata["generation"], dict):
    # TODO: Review unreachable code - alice_data["generation"] = metadata["generation"]

    # TODO: Review unreachable code - # Store relationships
    # TODO: Review unreachable code - if metadata is not None and "relationships" in metadata:
    # TODO: Review unreachable code - alice_data["relationships"] = metadata["relationships"]

    # TODO: Review unreachable code - # Store role and project info
    # TODO: Review unreachable code - if metadata is not None and "role" in metadata:
    # TODO: Review unreachable code - alice_data["role"] = metadata["role"]
    # TODO: Review unreachable code - if metadata is not None and "project_id" in metadata:
    # TODO: Review unreachable code - alice_data["project_id"] = metadata["project_id"]

    # TODO: Review unreachable code - # Serialize and add to PNG
    # TODO: Review unreachable code - pnginfo.add_text(f"{ALICE_NAMESPACE}:metadata", json.dumps(alice_data, cls=MetadataEncoder))

    # TODO: Review unreachable code - # Store generation parameters separately for compatibility
    # TODO: Review unreachable code - if metadata is not None and "prompt" in metadata:
    # TODO: Review unreachable code - pnginfo.add_text("parameters", metadata["prompt"])
    # TODO: Review unreachable code - if metadata is not None and "generation_params" in metadata:
    # TODO: Review unreachable code - for key, field in STANDARD_FIELDS.items():
    # TODO: Review unreachable code - if key in metadata["generation_params"]:
    # TODO: Review unreachable code - pnginfo.add_text(field, str(metadata["generation_params"][key]))

    # TODO: Review unreachable code - # Save with metadata
    # TODO: Review unreachable code - img.save(image_path, pnginfo=pnginfo)
    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to embed PNG metadata: {e}")
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - def _extract_png_metadata(self, image_path: Path) -> dict[str, Any]:
    # TODO: Review unreachable code - """Extract metadata from PNG file."""
    # TODO: Review unreachable code - metadata = {}

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - img = Image.open(image_path)

    # TODO: Review unreachable code - if hasattr(img, "info") and img.info:
    # TODO: Review unreachable code - # Extract standard fields
    # TODO: Review unreachable code - for key, value in img.info.items():
    # TODO: Review unreachable code - if key == "parameters":
    # TODO: Review unreachable code - metadata["prompt"] = value
    # TODO: Review unreachable code - elif key in STANDARD_FIELDS.values():
    # TODO: Review unreachable code - # Reverse lookup to get our field name
    # TODO: Review unreachable code - our_key = next(k for k, v in STANDARD_FIELDS.items() if v == key)
    # TODO: Review unreachable code - if "generation_params" not in metadata:
    # TODO: Review unreachable code - metadata["generation_params"] = {}
    # TODO: Review unreachable code - metadata["generation_params"][our_key] = value

    # TODO: Review unreachable code - # Extract Alice metadata
    # TODO: Review unreachable code - alice_key = f"{ALICE_NAMESPACE}:metadata"
    # TODO: Review unreachable code - if alice_key in img.info:
    # TODO: Review unreachable code - alice_data = json.loads(img.info[alice_key])

    # TODO: Review unreachable code - # Restore analysis results
    # TODO: Review unreachable code - if alice_data is not None and "analysis" in alice_data:
    # TODO: Review unreachable code - analysis = alice_data["analysis"]

    # TODO: Review unreachable code - if analysis is not None and "brisque" in analysis:
    # TODO: Review unreachable code - metadata["brisque_score"] = analysis["brisque"]["score"]
    # TODO: Review unreachable code - if "normalized" in analysis["brisque"]:
    # TODO: Review unreachable code - metadata["brisque_normalized"] = analysis["brisque"]["normalized"]

    # TODO: Review unreachable code - if analysis is not None and "sightengine" in analysis:
    # TODO: Review unreachable code - for key, value in analysis["sightengine"].items():
    # TODO: Review unreachable code - metadata[f"sightengine_{key}"] = value

    # TODO: Review unreachable code - if analysis is not None and "claude" in analysis:
    # TODO: Review unreachable code - for key, value in analysis["claude"].items():
    # TODO: Review unreachable code - metadata[f"claude_{key}"] = value

    # TODO: Review unreachable code - # Restore all fields from alice_data
    # TODO: Review unreachable code - for key in ["content_hash", "media_type", "metadata_version",
    # TODO: Review unreachable code - "tags", "understanding", "generation"]:
    # TODO: Review unreachable code - if key in alice_data:
    # TODO: Review unreachable code - metadata[key] = alice_data[key]

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to extract PNG metadata: {e}")

    # TODO: Review unreachable code - return metadata

    # TODO: Review unreachable code - def _create_xmp_from_metadata(self, metadata: dict[str, Any]) -> str:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Create XMP XML string from metadata dictionary.

    # TODO: Review unreachable code - This is a simplified XMP creation for basic metadata storage.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Basic XMP template
    # TODO: Review unreachable code - xmp_template = """<?xml version="1.0" encoding="UTF-8"?>
    # TODO: Review unreachable code - <x:xmpmeta xmlns:x="adobe:ns:meta/">
    # TODO: Review unreachable code -   <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    # TODO: Review unreachable code -     <rdf:Description rdf:about=""
    # TODO: Review unreachable code -         xmlns:dc="http://purl.org/dc/elements/1.1/"
    # TODO: Review unreachable code -         xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    # TODO: Review unreachable code -         xmlns:alice="http://alicemultiverse.ai/ns/1.0/">
    # TODO: Review unreachable code -       <dc:description>{description}</dc:description>
    # TODO: Review unreachable code -       <xmp:CreatorTool>AliceMultiverse</xmp:CreatorTool>
    # TODO: Review unreachable code -       <alice:metadata>{metadata_json}</alice:metadata>
    # TODO: Review unreachable code -     </rdf:Description>
    # TODO: Review unreachable code -   </rdf:RDF>
    # TODO: Review unreachable code - </x:xmpmeta>"""

    # TODO: Review unreachable code -     # Convert metadata to JSON string
    # TODO: Review unreachable code -     metadata_json = json.dumps(metadata, ensure_ascii=False, cls=MetadataEncoder)

    # TODO: Review unreachable code -     # Get description from prompt or use default
    # TODO: Review unreachable code -     description = metadata.get("prompt", "AI-generated content")

    # TODO: Review unreachable code -     # Format XMP with our data
    # TODO: Review unreachable code -     xmp_data = xmp_template.format(description=description, metadata_json=metadata_json)

    # TODO: Review unreachable code -     return xmp_data

    # TODO: Review unreachable code - def _embed_jpeg_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
    # TODO: Review unreachable code - """Embed metadata into JPEG using EXIF."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - img = Image.open(image_path)

    # TODO: Review unreachable code - # Get existing EXIF data or create new
    # TODO: Review unreachable code - if "exif" in img.info:
    # TODO: Review unreachable code - exif_dict = piexif.load(img.info["exif"])
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

    # TODO: Review unreachable code - # Create alice_data with all metadata
    # TODO: Review unreachable code - alice_data = {
    # TODO: Review unreachable code - "version": METADATA_VERSION,
    # TODO: Review unreachable code - "timestamp": datetime.now(UTC).isoformat(),
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Copy all relevant fields
    # TODO: Review unreachable code - for key in ["content_hash", "media_type", "tags", "understanding", "generation"]:
    # TODO: Review unreachable code - if key in metadata:
    # TODO: Review unreachable code - alice_data[key] = metadata[key]

    # TODO: Review unreachable code - # Store in ImageDescription (0x010e)
    # TODO: Review unreachable code - exif_dict["0th"][piexif.ImageIFD.ImageDescription] = json.dumps(alice_data, cls=MetadataEncoder).encode(
    # TODO: Review unreachable code - "utf-8"
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - # Also store prompt in XPComment for compatibility
    # TODO: Review unreachable code - if metadata is not None and "prompt" in metadata:
    # TODO: Review unreachable code - exif_dict["0th"][piexif.ImageIFD.XPComment] = metadata["prompt"].encode("utf-16le")

    # TODO: Review unreachable code - # Convert back to bytes
    # TODO: Review unreachable code - exif_bytes = piexif.dump(exif_dict)

    # TODO: Review unreachable code - # Save with new EXIF
    # TODO: Review unreachable code - img.save(image_path, exif=exif_bytes)
    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to embed JPEG metadata: {e}")
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - def _extract_jpeg_metadata(self, image_path: Path) -> dict[str, Any]:
    # TODO: Review unreachable code - """Extract metadata from JPEG EXIF."""
    # TODO: Review unreachable code - metadata = {}

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - img = Image.open(image_path)

    # TODO: Review unreachable code - if "exif" in img.info:
    # TODO: Review unreachable code - exif_dict = piexif.load(img.info["exif"])

    # TODO: Review unreachable code - # Extract our JSON data from ImageDescription
    # TODO: Review unreachable code - if piexif.ImageIFD.ImageDescription in exif_dict["0th"]:
    # TODO: Review unreachable code - desc = exif_dict["0th"][piexif.ImageIFD.ImageDescription]
    # TODO: Review unreachable code - if isinstance(desc, bytes):
    # TODO: Review unreachable code - desc = desc.decode("utf-8")

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - alice_data = json.loads(desc)
    # TODO: Review unreachable code - if alice_data is not None and "version" in alice_data:
    # TODO: Review unreachable code - # Extract all fields from alice_data
    # TODO: Review unreachable code - for key in ["content_hash", "media_type", "tags",
    # TODO: Review unreachable code - "understanding", "generation"]:
    # TODO: Review unreachable code - if key in alice_data:
    # TODO: Review unreachable code - metadata[key] = alice_data[key]
    # TODO: Review unreachable code - except json.JSONDecodeError:
    # TODO: Review unreachable code - # Might be regular description, not our data
    # TODO: Review unreachable code - pass

    # TODO: Review unreachable code - # Also check XPComment for prompt
    # TODO: Review unreachable code - if piexif.ImageIFD.XPComment in exif_dict["0th"]:
    # TODO: Review unreachable code - comment = exif_dict["0th"][piexif.ImageIFD.XPComment]
    # TODO: Review unreachable code - if isinstance(comment, bytes):
    # TODO: Review unreachable code - # XPComment is UTF-16LE encoded
    # TODO: Review unreachable code - prompt = comment.decode("utf-16le").rstrip("\x00")
    # TODO: Review unreachable code - if "prompt" not in metadata and prompt:
    # TODO: Review unreachable code - metadata["prompt"] = prompt

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to extract JPEG metadata: {e}")

    # TODO: Review unreachable code - return metadata

    # TODO: Review unreachable code - def _create_xmp_from_metadata(self, metadata: dict[str, Any]) -> str:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Create XMP XML string from metadata dictionary.

    # TODO: Review unreachable code - This is a simplified XMP creation for basic metadata storage.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Basic XMP template
    # TODO: Review unreachable code - xmp_template = """<?xml version="1.0" encoding="UTF-8"?>
    # TODO: Review unreachable code - <x:xmpmeta xmlns:x="adobe:ns:meta/">
    # TODO: Review unreachable code -   <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    # TODO: Review unreachable code -     <rdf:Description rdf:about=""
    # TODO: Review unreachable code -         xmlns:dc="http://purl.org/dc/elements/1.1/"
    # TODO: Review unreachable code -         xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    # TODO: Review unreachable code -         xmlns:alice="http://alicemultiverse.ai/ns/1.0/">
    # TODO: Review unreachable code -       <dc:description>{description}</dc:description>
    # TODO: Review unreachable code -       <xmp:CreatorTool>AliceMultiverse</xmp:CreatorTool>
    # TODO: Review unreachable code -       <alice:metadata>{metadata_json}</alice:metadata>
    # TODO: Review unreachable code -     </rdf:Description>
    # TODO: Review unreachable code -   </rdf:RDF>
    # TODO: Review unreachable code - </x:xmpmeta>"""

    # TODO: Review unreachable code -     # Convert metadata to JSON string
    # TODO: Review unreachable code -     metadata_json = json.dumps(metadata, ensure_ascii=False, cls=MetadataEncoder)

    # TODO: Review unreachable code -     # Get description from prompt or use default
    # TODO: Review unreachable code -     description = metadata.get("prompt", "AI-generated content")

    # TODO: Review unreachable code -     # Format XMP with our data
    # TODO: Review unreachable code -     xmp_data = xmp_template.format(description=description, metadata_json=metadata_json)

    # TODO: Review unreachable code -     return xmp_data

    # TODO: Review unreachable code - def _embed_webp_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Embed metadata into WebP file.

    # TODO: Review unreachable code - Note: WebP metadata support in Python is limited. Pillow can read/write
    # TODO: Review unreachable code - basic metadata but full XMP support requires external tools like webpmux.
    # TODO: Review unreachable code - We store what we can in the available fields.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - # Read the WebP image
    # TODO: Review unreachable code - with Image.open(image_path) as img:
    # TODO: Review unreachable code - # Prepare metadata dict for WebP
    # TODO: Review unreachable code - # WebP through Pillow supports basic info dict
    # TODO: Review unreachable code - info = img.info.copy() if hasattr(img, "info") else {}

    # TODO: Review unreachable code - # Store our metadata as JSON in comment field
    # TODO: Review unreachable code - alice_data = {
    # TODO: Review unreachable code - "version": METADATA_VERSION,
    # TODO: Review unreachable code - "namespace": ALICE_NAMESPACE,
    # TODO: Review unreachable code - "timestamp": datetime.now(UTC).isoformat(),
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - # Copy all relevant fields
    # TODO: Review unreachable code - for key in ["content_hash", "media_type", "tags", "understanding", "generation"]:
    # TODO: Review unreachable code - if key in metadata:
    # TODO: Review unreachable code - alice_data[key] = metadata[key]
    # TODO: Review unreachable code - info["comment"] = json.dumps(alice_data, cls=MetadataEncoder)

    # TODO: Review unreachable code - # Also store prompt separately if available
    # TODO: Review unreachable code - if metadata is not None and "prompt" in metadata:
    # TODO: Review unreachable code - info["prompt"] = metadata["prompt"]

    # TODO: Review unreachable code - # Store AI source
    # TODO: Review unreachable code - if metadata is not None and "ai_source" in metadata:
    # TODO: Review unreachable code - info["software"] = f"AliceMultiverse/{metadata['ai_source']}"

    # TODO: Review unreachable code - # Create a temporary file
    # TODO: Review unreachable code - with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
    # TODO: Review unreachable code - tmp_path = Path(tmp.name)

    # TODO: Review unreachable code - # Save with metadata
    # TODO: Review unreachable code - # Note: Not all metadata may be preserved due to WebP/Pillow limitations
    # TODO: Review unreachable code - save_kwargs = {"format": "WebP"}
    # TODO: Review unreachable code - if info:
    # TODO: Review unreachable code - # Pass specific fields that WebP supports
    # TODO: Review unreachable code - if info is not None and "comment" in info:
    # TODO: Review unreachable code - save_kwargs["comment"] = info["comment"]
    # TODO: Review unreachable code - if info is not None and "exif" in info:
    # TODO: Review unreachable code - save_kwargs["exif"] = info["exif"]

    # TODO: Review unreachable code - img.save(tmp_path, **save_kwargs)

    # TODO: Review unreachable code - # Replace original file
    # TODO: Review unreachable code - shutil.move(str(tmp_path), str(image_path))

    # TODO: Review unreachable code - logger.info("Embedded basic metadata in WebP (full XMP support requires webpmux)")
    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to embed WebP metadata: {e}")
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - def _extract_webp_metadata(self, image_path: Path) -> dict[str, Any]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Extract metadata from WebP file.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - metadata = {}

    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - with Image.open(image_path) as img:
    # TODO: Review unreachable code - # Check PIL info dict
    # TODO: Review unreachable code - if hasattr(img, "info") and img.info:
    # TODO: Review unreachable code - # Check for our alice data in comment field
    # TODO: Review unreachable code - if "comment" in img.info:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - alice_data = json.loads(img.info["comment"])
    # TODO: Review unreachable code - if alice_data is not None and "version" in alice_data and "namespace" in alice_data:
    # TODO: Review unreachable code - # This is our metadata
    # TODO: Review unreachable code - for key in ["content_hash", "media_type", "tags",
    # TODO: Review unreachable code - "understanding", "generation"]:
    # TODO: Review unreachable code - if key in alice_data:
    # TODO: Review unreachable code - metadata[key] = alice_data[key]
    # TODO: Review unreachable code - except json.JSONDecodeError:
    # TODO: Review unreachable code - # Not our JSON, treat as regular comment
    # TODO: Review unreachable code - metadata["comment"] = img.info["comment"]

    # TODO: Review unreachable code - # Other direct metadata fields
    # TODO: Review unreachable code - for key in ["prompt", "workflow", "parameters"]:
    # TODO: Review unreachable code - if key in img.info:
    # TODO: Review unreachable code - metadata[key] = img.info[key]

    # TODO: Review unreachable code - # Check for EXIF data
    # TODO: Review unreachable code - if "exif" in img.info:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - exif_dict = piexif.load(img.info["exif"])

    # TODO: Review unreachable code - # UserComment (prompt)
    # TODO: Review unreachable code - if piexif.ExifIFD.UserComment in exif_dict.get("Exif", {}):
    # TODO: Review unreachable code - comment = exif_dict["Exif"][piexif.ExifIFD.UserComment]
    # TODO: Review unreachable code - if isinstance(comment, bytes):
    # TODO: Review unreachable code - # Remove encoding prefix if present
    # TODO: Review unreachable code - if comment.startswith(b"ASCII\x00\x00\x00"):
    # TODO: Review unreachable code - comment = comment[8:]
    # TODO: Review unreachable code - metadata["prompt"] = comment.decode("utf-8", errors="ignore")

    # TODO: Review unreachable code - # ImageDescription
    # TODO: Review unreachable code - if piexif.ImageIFD.ImageDescription in exif_dict.get("0th", {}):
    # TODO: Review unreachable code - desc = exif_dict["0th"][piexif.ImageIFD.ImageDescription]
    # TODO: Review unreachable code - if isinstance(desc, bytes):
    # TODO: Review unreachable code - desc = desc.decode("utf-8")
    # TODO: Review unreachable code - if desc.startswith("AI: "):
    # TODO: Review unreachable code - metadata["ai_source"] = desc[4:]

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.debug(f"Could not parse WebP EXIF: {e}")

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Failed to extract WebP metadata: {e}")

    # TODO: Review unreachable code - return metadata

    # TODO: Review unreachable code - def _create_xmp_from_metadata(self, metadata: dict[str, Any]) -> str:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Create XMP XML string from metadata dictionary.

    # TODO: Review unreachable code - This is a simplified XMP creation for basic metadata storage.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Basic XMP template
    # TODO: Review unreachable code - xmp_template = """<?xml version="1.0" encoding="UTF-8"?>
    # TODO: Review unreachable code - <x:xmpmeta xmlns:x="adobe:ns:meta/">
    # TODO: Review unreachable code -   <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    # TODO: Review unreachable code -     <rdf:Description rdf:about=""
    # TODO: Review unreachable code -         xmlns:dc="http://purl.org/dc/elements/1.1/"
    # TODO: Review unreachable code -         xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    # TODO: Review unreachable code -         xmlns:alice="http://alicemultiverse.ai/ns/1.0/">
    # TODO: Review unreachable code -       <dc:description>{description}</dc:description>
    # TODO: Review unreachable code -       <xmp:CreatorTool>AliceMultiverse</xmp:CreatorTool>
    # TODO: Review unreachable code -       <alice:metadata>{metadata_json}</alice:metadata>
    # TODO: Review unreachable code -     </rdf:Description>
    # TODO: Review unreachable code -   </rdf:RDF>
    # TODO: Review unreachable code - </x:xmpmeta>"""

    # TODO: Review unreachable code -     # Convert metadata to JSON string
    # TODO: Review unreachable code -     metadata_json = json.dumps(metadata, ensure_ascii=False, cls=MetadataEncoder)

    # TODO: Review unreachable code -     # Get description from prompt or use default
    # TODO: Review unreachable code -     description = metadata.get("prompt", "AI-generated content")

    # TODO: Review unreachable code -     # Format XMP with our data
    # TODO: Review unreachable code -     xmp_data = xmp_template.format(description=description, metadata_json=metadata_json)

    # TODO: Review unreachable code -     return xmp_data

    # TODO: Review unreachable code - def _embed_heic_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Embed metadata into HEIC/HEIF file.

    # TODO: Review unreachable code - Note: HEIC support requires additional libraries (pyheif).
    # TODO: Review unreachable code - For now, we'll log a warning and return True to not break the flow.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # HEIC/HEIF metadata requires specialized libraries like pyheif
    # TODO: Review unreachable code - # which have complex dependencies (libheif)
    # TODO: Review unreachable code - logger.warning(f"HEIC metadata embedding not fully implemented for {image_path}")
    # TODO: Review unreachable code - return True

    # TODO: Review unreachable code - def _extract_heic_metadata(self, image_path: Path) -> dict[str, Any]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Extract metadata from HEIC/HEIF file.

    # TODO: Review unreachable code - Note: HEIC support requires additional libraries.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - metadata = {}
    # TODO: Review unreachable code - # Basic implementation - in production would use pyheif
    # TODO: Review unreachable code - logger.warning(f"HEIC metadata extraction not fully implemented for {image_path}")
    # TODO: Review unreachable code - return metadata

    # TODO: Review unreachable code - def _create_xmp_from_metadata(self, metadata: dict[str, Any]) -> str:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Create XMP XML string from metadata dictionary.

    # TODO: Review unreachable code - This is a simplified XMP creation for basic metadata storage.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - # Basic XMP template
    # TODO: Review unreachable code - xmp_template = """<?xml version="1.0" encoding="UTF-8"?>
    # TODO: Review unreachable code - <x:xmpmeta xmlns:x="adobe:ns:meta/">
    # TODO: Review unreachable code -   <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    # TODO: Review unreachable code -     <rdf:Description rdf:about=""
    # TODO: Review unreachable code -         xmlns:dc="http://purl.org/dc/elements/1.1/"
    # TODO: Review unreachable code -         xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    # TODO: Review unreachable code -         xmlns:alice="http://alicemultiverse.ai/ns/1.0/">
    # TODO: Review unreachable code -       <dc:description>{description}</dc:description>
    # TODO: Review unreachable code -       <xmp:CreatorTool>AliceMultiverse</xmp:CreatorTool>
    # TODO: Review unreachable code -       <alice:metadata>{metadata_json}</alice:metadata>
    # TODO: Review unreachable code -     </rdf:Description>
    # TODO: Review unreachable code -   </rdf:RDF>
    # TODO: Review unreachable code - </x:xmpmeta>"""

    # TODO: Review unreachable code -     # Convert metadata to JSON string
    # TODO: Review unreachable code -     metadata_json = json.dumps(metadata, ensure_ascii=False, cls=MetadataEncoder)

    # TODO: Review unreachable code -     # Get description from prompt or use default
    # TODO: Review unreachable code -     description = metadata.get("prompt", "AI-generated content")

    # TODO: Review unreachable code -     # Format XMP with our data
    # TODO: Review unreachable code -     xmp_data = xmp_template.format(description=description, metadata_json=metadata_json)

    # TODO: Review unreachable code -     return xmp_data
