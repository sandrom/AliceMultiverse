# alice-utils

Common utilities for AliceMultiverse services.

## Installation

```bash
pip install -e packages/alice-utils
```

## Usage

```python
from alice_utils import (
    hash_file_content,
    extract_image_metadata,
    detect_media_type,
    normalize_path
)

# Hash file content
content_hash = hash_file_content("/path/to/file.jpg")

# Extract metadata
metadata = extract_image_metadata("/path/to/image.jpg")

# Detect media type
media_type = detect_media_type("/path/to/file")  # Returns MediaType.IMAGE

# Normalize paths
normalized = normalize_path("~/Documents/../Pictures/photo.jpg")
```

## Utilities

### File Operations
- `hash_file_content()` - SHA256 content hashing
- `copy_with_metadata()` - Preserve metadata during copy
- `atomic_write()` - Atomic file writing

### Image Processing
- `extract_image_metadata()` - EXIF and technical metadata
- `generate_thumbnail()` - Create thumbnails
- `detect_image_format()` - Identify image formats

### Media Detection
- `detect_media_type()` - Identify media type from file
- `is_supported_format()` - Check if format is supported
- `get_file_info()` - Get size, modified time, etc.

### Path Utilities  
- `normalize_path()` - Expand and normalize paths
- `ensure_directory()` - Create directory if needed
- `safe_filename()` - Sanitize filenames