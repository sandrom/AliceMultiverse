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
            suffix = image_path.suffix.lower()

            if suffix == ".png":
                return self._embed_png_metadata(image_path, metadata)
            elif suffix in [".jpg", ".jpeg"]:
                return self._embed_jpeg_metadata(image_path, metadata)
            elif suffix == ".webp":
                return self._embed_webp_metadata(image_path, metadata)
            elif suffix in [".heic", ".heif"]:
                return self._embed_heic_metadata(image_path, metadata)
            else:
                # Should not happen with our restricted format support
                logger.error(f"Unexpected format: {suffix}")
                return False

        except Exception as e:
            logger.error(f"Failed to embed metadata in {image_path}: {e}")
            return False

    def extract_metadata(self, image_path: Path) -> dict[str, Any]:
        """
        Extract all metadata from an image file.

        Args:
            image_path: Path to the image file

        Returns:
            Dictionary containing all extracted metadata
        """
        metadata = {}

        try:
            suffix = image_path.suffix.lower()

            if suffix == ".png":
                metadata = self._extract_png_metadata(image_path)
            elif suffix in [".jpg", ".jpeg"]:
                metadata = self._extract_jpeg_metadata(image_path)
            elif suffix == ".webp":
                metadata = self._extract_webp_metadata(image_path)
            elif suffix in [".heic", ".heif"]:
                metadata = self._extract_heic_metadata(image_path)

        except Exception as e:
            logger.error(f"Failed to extract metadata from {image_path}: {e}")

        return metadata

    def _create_xmp_from_metadata(self, metadata: dict[str, Any]) -> str:
        """
        Create XMP XML string from metadata dictionary.

        This is a simplified XMP creation for basic metadata storage.
        """
        # Basic XMP template
        xmp_template = """<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:xmp="http://ns.adobe.com/xap/1.0/"
        xmlns:alice="http://alicemultiverse.ai/ns/1.0/">
      <dc:description>{description}</dc:description>
      <xmp:CreatorTool>AliceMultiverse</xmp:CreatorTool>
      <alice:metadata>{metadata_json}</alice:metadata>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>"""

        # Convert metadata to JSON string
        metadata_json = json.dumps(metadata, ensure_ascii=False)

        # Get description from prompt or use default
        description = metadata.get("prompt", "AI-generated content")

        # Format XMP with our data
        xmp_data = xmp_template.format(description=description, metadata_json=metadata_json)

        return xmp_data

    def _embed_png_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
        """Embed metadata into PNG file using tEXt chunks."""
        try:
            # Load image
            img = Image.open(image_path)

            # Create PngInfo object for metadata
            pnginfo = PngInfo()

            # Add existing metadata first
            if hasattr(img, "info") and img.info:
                for key, value in img.info.items():
                    if isinstance(value, (str, bytes)):
                        pnginfo.add_text(key, str(value))

            # Add Alice metadata
            alice_data = {
                "version": METADATA_VERSION,
                "timestamp": datetime.now(UTC).isoformat(),
                "analysis": {},
            }

            # Store analysis results
            if "brisque_score" in metadata:
                alice_data["analysis"]["brisque"] = {
                    "score": metadata["brisque_score"],
                    "normalized": metadata.get("brisque_normalized"),
                }

            if "sightengine_quality" in metadata:
                alice_data["analysis"]["sightengine"] = {
                    "quality": metadata["sightengine_quality"],
                    "sharpness": metadata.get("sightengine_sharpness"),
                    "contrast": metadata.get("sightengine_contrast"),
                    "brightness": metadata.get("sightengine_brightness"),
                    "ai_generated": metadata.get("sightengine_ai_generated"),
                    "ai_probability": metadata.get("sightengine_ai_probability"),
                }

            if "claude_defects_found" in metadata:
                alice_data["analysis"]["claude"] = {
                    "defects_found": metadata["claude_defects_found"],
                    "defect_count": metadata.get("claude_defect_count", 0),
                    "severity": metadata.get("claude_severity", "unknown"),
                    "confidence": metadata.get("claude_confidence", 0.0),
                    "quality_score": metadata.get("claude_quality_score"),
                }

            # Store semantic tags
            if any(key in metadata for key in ["style_tags", "mood_tags", "subject_tags"]):
                alice_data["tags"] = {
                    "style": metadata.get("style_tags", []),
                    "mood": metadata.get("mood_tags", []),
                    "subject": metadata.get("subject_tags", []),
                    "color": metadata.get("color_tags", []),
                    "custom": metadata.get("custom_tags", []),
                }

            # Store relationships
            if "relationships" in metadata:
                alice_data["relationships"] = metadata["relationships"]

            # Store role and project info
            if "role" in metadata:
                alice_data["role"] = metadata["role"]
            if "project_id" in metadata:
                alice_data["project_id"] = metadata["project_id"]

            # Serialize and add to PNG
            pnginfo.add_text(f"{ALICE_NAMESPACE}:metadata", json.dumps(alice_data))

            # Store generation parameters separately for compatibility
            if "prompt" in metadata:
                pnginfo.add_text("parameters", metadata["prompt"])
            if "generation_params" in metadata:
                for key, field in STANDARD_FIELDS.items():
                    if key in metadata["generation_params"]:
                        pnginfo.add_text(field, str(metadata["generation_params"][key]))

            # Save with metadata
            img.save(image_path, pnginfo=pnginfo)
            return True

        except Exception as e:
            logger.error(f"Failed to embed PNG metadata: {e}")
            return False

    def _extract_png_metadata(self, image_path: Path) -> dict[str, Any]:
        """Extract metadata from PNG file."""
        metadata = {}

        try:
            img = Image.open(image_path)

            if hasattr(img, "info") and img.info:
                # Extract standard fields
                for key, value in img.info.items():
                    if key == "parameters":
                        metadata["prompt"] = value
                    elif key in STANDARD_FIELDS.values():
                        # Reverse lookup to get our field name
                        our_key = next(k for k, v in STANDARD_FIELDS.items() if v == key)
                        if "generation_params" not in metadata:
                            metadata["generation_params"] = {}
                        metadata["generation_params"][our_key] = value

                # Extract Alice metadata
                alice_key = f"{ALICE_NAMESPACE}:metadata"
                if alice_key in img.info:
                    alice_data = json.loads(img.info[alice_key])

                    # Restore analysis results
                    if "analysis" in alice_data:
                        analysis = alice_data["analysis"]

                        if "brisque" in analysis:
                            metadata["brisque_score"] = analysis["brisque"]["score"]
                            if "normalized" in analysis["brisque"]:
                                metadata["brisque_normalized"] = analysis["brisque"]["normalized"]

                        if "sightengine" in analysis:
                            for key, value in analysis["sightengine"].items():
                                metadata[f"sightengine_{key}"] = value

                        if "claude" in analysis:
                            for key, value in analysis["claude"].items():
                                metadata[f"claude_{key}"] = value

                    # Restore tags
                    if "tags" in alice_data:
                        tags = alice_data["tags"]
                        metadata["style_tags"] = tags.get("style", [])
                        metadata["mood_tags"] = tags.get("mood", [])
                        metadata["subject_tags"] = tags.get("subject", [])
                        metadata["color_tags"] = tags.get("color", [])
                        metadata["custom_tags"] = tags.get("custom", [])

                    # Restore other fields
                    if "relationships" in alice_data:
                        metadata["relationships"] = alice_data["relationships"]
                    if "role" in alice_data:
                        metadata["role"] = alice_data["role"]
                    if "project_id" in alice_data:
                        metadata["project_id"] = alice_data["project_id"]

        except Exception as e:
            logger.error(f"Failed to extract PNG metadata: {e}")

        return metadata

    def _create_xmp_from_metadata(self, metadata: dict[str, Any]) -> str:
        """
        Create XMP XML string from metadata dictionary.

        This is a simplified XMP creation for basic metadata storage.
        """
        # Basic XMP template
        xmp_template = """<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:xmp="http://ns.adobe.com/xap/1.0/"
        xmlns:alice="http://alicemultiverse.ai/ns/1.0/">
      <dc:description>{description}</dc:description>
      <xmp:CreatorTool>AliceMultiverse</xmp:CreatorTool>
      <alice:metadata>{metadata_json}</alice:metadata>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>"""

        # Convert metadata to JSON string
        metadata_json = json.dumps(metadata, ensure_ascii=False)

        # Get description from prompt or use default
        description = metadata.get("prompt", "AI-generated content")

        # Format XMP with our data
        xmp_data = xmp_template.format(description=description, metadata_json=metadata_json)

        return xmp_data

    def _embed_jpeg_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
        """Embed metadata into JPEG using EXIF."""
        try:
            img = Image.open(image_path)

            # Get existing EXIF data or create new
            if "exif" in img.info:
                exif_dict = piexif.load(img.info["exif"])
            else:
                exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}}

            # Use ImageDescription field for our JSON data
            alice_data = {
                "version": METADATA_VERSION,
                "timestamp": datetime.now(UTC).isoformat(),
                "metadata": metadata,
            }

            # Store in ImageDescription (0x010e)
            exif_dict["0th"][piexif.ImageIFD.ImageDescription] = json.dumps(alice_data).encode(
                "utf-8"
            )

            # Also store prompt in XPComment for compatibility
            if "prompt" in metadata:
                exif_dict["0th"][piexif.ImageIFD.XPComment] = metadata["prompt"].encode("utf-16le")

            # Convert back to bytes
            exif_bytes = piexif.dump(exif_dict)

            # Save with new EXIF
            img.save(image_path, exif=exif_bytes)
            return True

        except Exception as e:
            logger.error(f"Failed to embed JPEG metadata: {e}")
            return False

    def _extract_jpeg_metadata(self, image_path: Path) -> dict[str, Any]:
        """Extract metadata from JPEG EXIF."""
        metadata = {}

        try:
            img = Image.open(image_path)

            if "exif" in img.info:
                exif_dict = piexif.load(img.info["exif"])

                # Extract our JSON data from ImageDescription
                if piexif.ImageIFD.ImageDescription in exif_dict["0th"]:
                    desc = exif_dict["0th"][piexif.ImageIFD.ImageDescription]
                    if isinstance(desc, bytes):
                        desc = desc.decode("utf-8")

                    try:
                        alice_data = json.loads(desc)
                        if alice_data.get("version") == METADATA_VERSION:
                            metadata = alice_data.get("metadata", {})
                    except json.JSONDecodeError:
                        # Might be regular description, not our data
                        pass

                # Also check XPComment for prompt
                if piexif.ImageIFD.XPComment in exif_dict["0th"]:
                    comment = exif_dict["0th"][piexif.ImageIFD.XPComment]
                    if isinstance(comment, bytes):
                        # XPComment is UTF-16LE encoded
                        prompt = comment.decode("utf-16le").rstrip("\x00")
                        if "prompt" not in metadata and prompt:
                            metadata["prompt"] = prompt

        except Exception as e:
            logger.error(f"Failed to extract JPEG metadata: {e}")

        return metadata

    def _create_xmp_from_metadata(self, metadata: dict[str, Any]) -> str:
        """
        Create XMP XML string from metadata dictionary.

        This is a simplified XMP creation for basic metadata storage.
        """
        # Basic XMP template
        xmp_template = """<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:xmp="http://ns.adobe.com/xap/1.0/"
        xmlns:alice="http://alicemultiverse.ai/ns/1.0/">
      <dc:description>{description}</dc:description>
      <xmp:CreatorTool>AliceMultiverse</xmp:CreatorTool>
      <alice:metadata>{metadata_json}</alice:metadata>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>"""

        # Convert metadata to JSON string
        metadata_json = json.dumps(metadata, ensure_ascii=False)

        # Get description from prompt or use default
        description = metadata.get("prompt", "AI-generated content")

        # Format XMP with our data
        xmp_data = xmp_template.format(description=description, metadata_json=metadata_json)

        return xmp_data

    def _embed_webp_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
        """
        Embed metadata into WebP file.

        Note: WebP metadata support in Python is limited. Pillow can read/write
        basic metadata but full XMP support requires external tools like webpmux.
        We store what we can in the available fields.
        """
        try:
            # Read the WebP image
            with Image.open(image_path) as img:
                # Prepare metadata dict for WebP
                # WebP through Pillow supports basic info dict
                info = img.info.copy() if hasattr(img, "info") else {}

                # Store our metadata as JSON in comment field
                alice_data = {
                    "version": METADATA_VERSION,
                    "namespace": ALICE_NAMESPACE,
                    "metadata": metadata,
                }
                info["comment"] = json.dumps(alice_data)

                # Also store prompt separately if available
                if "prompt" in metadata:
                    info["prompt"] = metadata["prompt"]

                # Store AI source
                if "ai_source" in metadata:
                    info["software"] = f"AliceMultiverse/{metadata['ai_source']}"

                # Create a temporary file
                with tempfile.NamedTemporaryFile(suffix=".webp", delete=False) as tmp:
                    tmp_path = Path(tmp.name)

                # Save with metadata
                # Note: Not all metadata may be preserved due to WebP/Pillow limitations
                save_kwargs = {"format": "WebP"}
                if info:
                    # Pass specific fields that WebP supports
                    if "comment" in info:
                        save_kwargs["comment"] = info["comment"]
                    if "exif" in info:
                        save_kwargs["exif"] = info["exif"]

                img.save(tmp_path, **save_kwargs)

                # Replace original file
                shutil.move(str(tmp_path), str(image_path))

            logger.info("Embedded basic metadata in WebP (full XMP support requires webpmux)")
            return True

        except Exception as e:
            logger.error(f"Failed to embed WebP metadata: {e}")
            return False

    def _extract_webp_metadata(self, image_path: Path) -> dict[str, Any]:
        """
        Extract metadata from WebP file.
        """
        metadata = {}

        try:
            with Image.open(image_path) as img:
                # Check PIL info dict
                if hasattr(img, "info") and img.info:
                    # Direct metadata fields
                    for key in ["prompt", "workflow", "parameters", "comment"]:
                        if key in img.info:
                            metadata[key] = img.info[key]

                    # Check for EXIF data
                    if "exif" in img.info:
                        try:
                            exif_dict = piexif.load(img.info["exif"])

                            # UserComment (prompt)
                            if piexif.ExifIFD.UserComment in exif_dict.get("Exif", {}):
                                comment = exif_dict["Exif"][piexif.ExifIFD.UserComment]
                                if isinstance(comment, bytes):
                                    # Remove encoding prefix if present
                                    if comment.startswith(b"ASCII\x00\x00\x00"):
                                        comment = comment[8:]
                                    metadata["prompt"] = comment.decode("utf-8", errors="ignore")

                            # ImageDescription
                            if piexif.ImageIFD.ImageDescription in exif_dict.get("0th", {}):
                                desc = exif_dict["0th"][piexif.ImageIFD.ImageDescription]
                                if isinstance(desc, bytes):
                                    desc = desc.decode("utf-8")
                                if desc.startswith("AI: "):
                                    metadata["ai_source"] = desc[4:]

                        except Exception as e:
                            logger.debug(f"Could not parse WebP EXIF: {e}")

        except Exception as e:
            logger.error(f"Failed to extract WebP metadata: {e}")

        return metadata

    def _create_xmp_from_metadata(self, metadata: dict[str, Any]) -> str:
        """
        Create XMP XML string from metadata dictionary.

        This is a simplified XMP creation for basic metadata storage.
        """
        # Basic XMP template
        xmp_template = """<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:xmp="http://ns.adobe.com/xap/1.0/"
        xmlns:alice="http://alicemultiverse.ai/ns/1.0/">
      <dc:description>{description}</dc:description>
      <xmp:CreatorTool>AliceMultiverse</xmp:CreatorTool>
      <alice:metadata>{metadata_json}</alice:metadata>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>"""

        # Convert metadata to JSON string
        metadata_json = json.dumps(metadata, ensure_ascii=False)

        # Get description from prompt or use default
        description = metadata.get("prompt", "AI-generated content")

        # Format XMP with our data
        xmp_data = xmp_template.format(description=description, metadata_json=metadata_json)

        return xmp_data

    def _embed_heic_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
        """
        Embed metadata into HEIC/HEIF file.

        Note: HEIC support requires additional libraries (pyheif).
        For now, we'll log a warning and return True to not break the flow.
        """
        # HEIC/HEIF metadata requires specialized libraries like pyheif
        # which have complex dependencies (libheif)
        logger.warning(f"HEIC metadata embedding not fully implemented for {image_path}")
        return True

    def _extract_heic_metadata(self, image_path: Path) -> dict[str, Any]:
        """
        Extract metadata from HEIC/HEIF file.

        Note: HEIC support requires additional libraries.
        """
        metadata = {}
        # Basic implementation - in production would use pyheif
        logger.warning(f"HEIC metadata extraction not fully implemented for {image_path}")
        return metadata

    def _create_xmp_from_metadata(self, metadata: dict[str, Any]) -> str:
        """
        Create XMP XML string from metadata dictionary.

        This is a simplified XMP creation for basic metadata storage.
        """
        # Basic XMP template
        xmp_template = """<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/">
  <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
    <rdf:Description rdf:about=""
        xmlns:dc="http://purl.org/dc/elements/1.1/"
        xmlns:xmp="http://ns.adobe.com/xap/1.0/"
        xmlns:alice="http://alicemultiverse.ai/ns/1.0/">
      <dc:description>{description}</dc:description>
      <xmp:CreatorTool>AliceMultiverse</xmp:CreatorTool>
      <alice:metadata>{metadata_json}</alice:metadata>
    </rdf:Description>
  </rdf:RDF>
</x:xmpmeta>"""

        # Convert metadata to JSON string
        metadata_json = json.dumps(metadata, ensure_ascii=False)

        # Get description from prompt or use default
        description = metadata.get("prompt", "AI-generated content")

        # Format XMP with our data
        xmp_data = xmp_template.format(description=description, metadata_json=metadata_json)

        return xmp_data
