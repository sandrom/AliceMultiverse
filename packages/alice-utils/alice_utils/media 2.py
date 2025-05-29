"""Media handling utilities."""

import mimetypes
from pathlib import Path
from typing import Union, Dict, Any, Optional, Tuple
from datetime import datetime

try:
    from PIL import Image
    from PIL.ExifTags import TAGS
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# Import MediaType enum - this creates a circular dependency
# In real implementation, this would be defined here or imported differently
class MediaType:
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"
    DOCUMENT = "document"
    UNKNOWN = "unknown"


# Supported formats
IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp', '.heic', '.heif'}
VIDEO_EXTENSIONS = {'.mp4', '.avi', '.mov', '.mkv', '.webm', '.flv', '.wmv'}
AUDIO_EXTENSIONS = {'.mp3', '.wav', '.flac', '.aac', '.ogg', '.wma', '.m4a'}


def detect_media_type(file_path: Union[str, Path]) -> str:
    """Detect media type from file."""
    path = Path(file_path)
    ext = path.suffix.lower()
    
    if ext in IMAGE_EXTENSIONS:
        return MediaType.IMAGE
    elif ext in VIDEO_EXTENSIONS:
        return MediaType.VIDEO
    elif ext in AUDIO_EXTENSIONS:
        return MediaType.AUDIO
    else:
        # Try mime type detection
        mime_type, _ = mimetypes.guess_type(str(path))
        if mime_type:
            if mime_type.startswith('image/'):
                return MediaType.IMAGE
            elif mime_type.startswith('video/'):
                return MediaType.VIDEO
            elif mime_type.startswith('audio/'):
                return MediaType.AUDIO
    
    return MediaType.UNKNOWN


def is_supported_format(file_path: Union[str, Path]) -> bool:
    """Check if file format is supported."""
    media_type = detect_media_type(file_path)
    return media_type != MediaType.UNKNOWN


def get_file_info(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Get basic file information."""
    path = Path(file_path)
    stat = path.stat()
    
    return {
        "path": str(path),
        "name": path.name,
        "size": stat.st_size,
        "created": datetime.fromtimestamp(stat.st_ctime),
        "modified": datetime.fromtimestamp(stat.st_mtime),
        "media_type": detect_media_type(path),
        "extension": path.suffix.lower()
    }


def extract_image_metadata(file_path: Union[str, Path]) -> Dict[str, Any]:
    """Extract metadata from image file."""
    if not PIL_AVAILABLE:
        return {"error": "PIL not available"}
    
    metadata = {}
    
    try:
        with Image.open(file_path) as img:
            # Basic properties
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["format"] = img.format
            metadata["mode"] = img.mode
            
            # EXIF data
            exif_data = img.getexif()
            if exif_data:
                exif = {}
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    exif[tag] = value
                metadata["exif"] = exif
            
            # Image info (may contain AI generation parameters)
            if hasattr(img, 'info'):
                metadata["info"] = dict(img.info)
                
    except Exception as e:
        metadata["error"] = str(e)
    
    return metadata


def generate_thumbnail(file_path: Union[str, Path],
                      output_path: Union[str, Path],
                      size: Tuple[int, int] = (256, 256)) -> bool:
    """Generate thumbnail for image."""
    if not PIL_AVAILABLE:
        return False
    
    try:
        with Image.open(file_path) as img:
            # Convert to RGB if necessary
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Generate thumbnail
            img.thumbnail(size, Image.Resampling.LANCZOS)
            img.save(output_path, quality=85, optimize=True)
            return True
            
    except Exception:
        return False