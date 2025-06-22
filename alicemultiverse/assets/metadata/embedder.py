"""
Temporary stub for embedder module while fixing syntax issues.
"""

from pathlib import Path
from typing import Any


class MetadataEmbedder:
    """Temporary stub for metadata embedder."""
    
    def embed_metadata(self, image_path: Path, metadata: dict[str, Any]) -> bool:
        """Stub method."""
        return True
    
    def extract_metadata(self, image_path: Path) -> dict[str, Any]:
        """Stub method."""
        return {}