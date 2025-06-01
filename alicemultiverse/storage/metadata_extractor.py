"""Extract metadata from media files.

This module extracts embedded metadata from various file types:
- Images: EXIF, XMP, IPTC
- Videos: MP4 metadata
- Audio: ID3 tags
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from PIL import Image
from PIL.ExifTags import TAGS
import piexif

from ..core.structured_logging import get_logger

logger = get_logger(__name__)


class MetadataExtractor:
    """Extract embedded metadata from media files."""
    
    # Alice-specific XMP namespace
    ALICE_XMP_NAMESPACE = "http://alicemultiverse.ai/xmp/1.0/"
    ALICE_XMP_PREFIX = "alice"
    
    def extract_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract all metadata from a file.
        
        Args:
            file_path: Path to the media file
            
        Returns:
            Dictionary containing all extracted metadata
        """
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        # Determine file type and extract accordingly
        suffix = file_path.suffix.lower()
        
        if suffix in [".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"]:
            return self._extract_image_metadata(file_path)
        elif suffix in [".mp4", ".mov"]:
            return self._extract_video_metadata(file_path)
        elif suffix in [".mp3", ".wav", ".m4a"]:
            return self._extract_audio_metadata(file_path)
        else:
            logger.warning(f"Unsupported file type: {suffix}")
            return {"media_type": "unknown"}
    
    def _extract_image_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from image files."""
        metadata = {
            "media_type": "image",
            "file_path": str(file_path)
        }
        
        try:
            # Open image with PIL
            with Image.open(file_path) as img:
                # Basic image info
                metadata["dimensions"] = {
                    "width": img.width,
                    "height": img.height
                }
                metadata["format"] = img.format
                metadata["mode"] = img.mode
                
                # Extract EXIF data
                exif_data = img.getexif()
                if exif_data:
                    metadata.update(self._parse_exif_data(exif_data))
                
                # Extract XMP data (where we store Alice metadata)
                if hasattr(img, 'info') and 'XML:com.adobe.xmp' in img.info:
                    xmp_data = img.info['XML:com.adobe.xmp']
                    metadata.update(self._parse_xmp_data(xmp_data))
        
        except Exception as e:
            logger.error(f"Error extracting image metadata: {e}", exc_info=True)
        
        return metadata
    
    def _parse_exif_data(self, exif_data) -> Dict[str, Any]:
        """Parse EXIF data from image."""
        parsed = {}
        
        for tag_id, value in exif_data.items():
            tag = TAGS.get(tag_id, tag_id)
            
            # Handle special tags
            if tag == "ImageDescription":
                parsed["description"] = value
            elif tag == "UserComment":
                # Try to parse as JSON (for structured data)
                try:
                    parsed["user_data"] = json.loads(value)
                except:
                    parsed["user_comment"] = value
            elif tag == "Software":
                parsed["software"] = value
            elif tag == "DateTime":
                parsed["datetime"] = value
        
        return parsed
    
    def _parse_xmp_data(self, xmp_data) -> Dict[str, Any]:
        """Parse XMP metadata containing Alice-specific data."""
        parsed = {}
        
        try:
            # Handle both bytes and string input
            if isinstance(xmp_data, bytes):
                xmp_str = xmp_data.decode('utf-8')
            else:
                xmp_str = xmp_data
            
            # Extract Alice namespace data
            # This is a simplified parser - in production we'd use python-xmp-toolkit
            import re
            
            # Extract content hash
            hash_match = re.search(r'alice:content_hash="([^"]+)"', xmp_str)
            if hash_match:
                parsed["content_hash"] = hash_match.group(1)
            
            # Extract understanding data (stored as JSON)
            understanding_match = re.search(r'alice:understanding="([^"]+)"', xmp_str)
            if understanding_match:
                try:
                    # Unescape and parse JSON
                    json_str = understanding_match.group(1).replace('&quot;', '"')
                    parsed["understanding"] = json.loads(json_str)
                except:
                    logger.warning("Failed to parse understanding metadata")
            
            # Extract generation data
            generation_match = re.search(r'alice:generation="([^"]+)"', xmp_str)
            if generation_match:
                try:
                    json_str = generation_match.group(1).replace('&quot;', '"')
                    parsed["generation"] = json.loads(json_str)
                except:
                    logger.warning("Failed to parse generation metadata")
            
            # Extract tags
            tags_match = re.search(r'alice:tags="([^"]+)"', xmp_str)
            if tags_match:
                try:
                    json_str = tags_match.group(1).replace('&quot;', '"')
                    parsed["tags"] = json.loads(json_str)
                except:
                    logger.warning("Failed to parse tags metadata")
            
            # Extract metadata version
            version_match = re.search(r'alice:metadata_version="([^"]+)"', xmp_str)
            if version_match:
                parsed["metadata_version"] = version_match.group(1)
        
        except Exception as e:
            logger.error(f"Error parsing XMP data: {e}")
        
        return parsed
    
    def _extract_video_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from video files."""
        metadata = {
            "media_type": "video",
            "file_path": str(file_path)
        }
        
        try:
            # For MP4 files, we can extract metadata using mutagen
            from mutagen.mp4 import MP4
            
            video = MP4(str(file_path))
            
            # Extract standard tags
            if "\xa9cmt" in video:  # Comment tag
                comment = video["\xa9cmt"][0]
                # Try to parse as JSON (Alice metadata)
                try:
                    alice_data = json.loads(comment)
                    metadata.update(alice_data)
                except:
                    metadata["comment"] = comment
            
            # Extract other useful tags
            if "\xa9nam" in video:
                metadata["title"] = video["\xa9nam"][0]
            if "\xa9ART" in video:
                metadata["artist"] = video["\xa9ART"][0]
            if "\xa9day" in video:
                metadata["date"] = video["\xa9day"][0]
            
            # Duration
            if video.info.length:
                metadata["duration"] = video.info.length
            
        except ImportError:
            logger.warning("mutagen not available for video metadata extraction")
        except Exception as e:
            logger.error(f"Error extracting video metadata: {e}")
        
        return metadata
    
    def _extract_audio_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Extract metadata from audio files."""
        metadata = {
            "media_type": "audio",
            "file_path": str(file_path)
        }
        
        try:
            from mutagen import File
            
            audio = File(str(file_path))
            if audio is None:
                return metadata
            
            # Extract ID3 tags for MP3
            if hasattr(audio, "tags") and audio.tags:
                # Look for comment tag (where we store Alice metadata)
                for key in ["COMM::eng", "COMM"]:
                    if key in audio.tags:
                        comment = str(audio.tags[key])
                        try:
                            alice_data = json.loads(comment)
                            metadata.update(alice_data)
                        except:
                            metadata["comment"] = comment
                        break
                
                # Extract other standard tags
                if "TIT2" in audio.tags:  # Title
                    metadata["title"] = str(audio.tags["TIT2"])
                if "TPE1" in audio.tags:  # Artist
                    metadata["artist"] = str(audio.tags["TPE1"])
                if "TALB" in audio.tags:  # Album
                    metadata["album"] = str(audio.tags["TALB"])
            
            # Duration
            if hasattr(audio.info, "length") and audio.info.length:
                metadata["duration"] = audio.info.length
            
        except ImportError:
            logger.warning("mutagen not available for audio metadata extraction")
        except Exception as e:
            logger.error(f"Error extracting audio metadata: {e}")
        
        return metadata
    
    def has_alice_metadata(self, file_path: Path) -> bool:
        """Check if a file has Alice metadata embedded.
        
        Args:
            file_path: Path to check
            
        Returns:
            True if file has Alice metadata
        """
        try:
            metadata = self.extract_metadata(file_path)
            
            # Check for Alice-specific fields
            alice_fields = ["content_hash", "understanding", "generation", "tags"]
            return any(field in metadata for field in alice_fields)
            
        except Exception:
            return False