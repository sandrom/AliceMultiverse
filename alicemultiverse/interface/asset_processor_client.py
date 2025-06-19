"""Client for Asset Processor service."""

import logging
from pathlib import Path
from typing import Any

import aiohttp
from alice_config import get_config  # type: ignore[import-untyped]

logger = logging.getLogger(__name__)


class AssetProcessorClient:
    """Client for communicating with Asset Processor service."""

    def __init__(self, base_url: str | None = None) -> None:
        """Initialize client.

        Args:
            base_url: Base URL for the service. If None, uses config.
        """
        self.config = get_config()

        if base_url:
            self.base_url = base_url.rstrip("/")
        else:
            # Get from config
            host = self.config.get("services.asset_processor.host", "localhost")
            port = self.config.get("services.asset_processor.port", 8001)
            self.base_url = f"http://{host}:{port}"

        self.session = None

    async def __aenter__(self) -> "AssetProcessorClient":
        """Enter async context."""
        self.session = aiohttp.ClientSession()
        return self

    # TODO: Review unreachable code - async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
    # TODO: Review unreachable code - """Exit async context."""
    # TODO: Review unreachable code - if self.session:
    # TODO: Review unreachable code - await self.session.close()

    # TODO: Review unreachable code - async def analyze(self, file_path: Path) -> dict[str, Any]:
    # TODO: Review unreachable code - """Analyze a media file.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_path: Path to the file to analyze

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Analysis results
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not self.session:
    # TODO: Review unreachable code - self.session = aiohttp.ClientSession()

    # TODO: Review unreachable code - url = f"{self.base_url}/analyze"
    # TODO: Review unreachable code - data = {"file_path": str(file_path)}

    # TODO: Review unreachable code - async with self.session.post(url, json=data) as response:
    # TODO: Review unreachable code - response.raise_for_status()
    # TODO: Review unreachable code - return await response.json()

    # TODO: Review unreachable code - async def assess_quality(
    # TODO: Review unreachable code - self, file_path: Path, content_hash: str, provider: str | None = None
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """Assess quality of a media file.

    # TODO: Review unreachable code - DEPRECATED: Quality assessment replaced with understanding system.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_path: Path to the file
    # TODO: Review unreachable code - content_hash: Content hash for caching
    # TODO: Review unreachable code - provider: Understanding provider to use

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Quality assessment results (empty for compatibility)
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not self.session:
    # TODO: Review unreachable code - self.session = aiohttp.ClientSession()

    # TODO: Review unreachable code - url = f"{self.base_url}/quality/assess"
    # TODO: Review unreachable code - data = {
    # TODO: Review unreachable code - "file_path": str(file_path),
    # TODO: Review unreachable code - "content_hash": content_hash,
    # TODO: Review unreachable code - "provider": provider,
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - async with self.session.post(url, json=data) as response:
    # TODO: Review unreachable code - response.raise_for_status()
    # TODO: Review unreachable code - return await response.json()

    # TODO: Review unreachable code - async def plan_organization(
    # TODO: Review unreachable code - self,
    # TODO: Review unreachable code - file_path: Path,
    # TODO: Review unreachable code - content_hash: str,
    # TODO: Review unreachable code - metadata: dict[str, Any],
    # TODO: Review unreachable code - quality_rating: int | None = None,
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """Plan organization for a file.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_path: Path to the file
    # TODO: Review unreachable code - content_hash: Content hash
    # TODO: Review unreachable code - metadata: File metadata
    # TODO: Review unreachable code - quality_rating: Quality rating (1-5)

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Organization plan
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not self.session:
    # TODO: Review unreachable code - self.session = aiohttp.ClientSession()

    # TODO: Review unreachable code - url = f"{self.base_url}/organize/plan"
    # TODO: Review unreachable code - data = {
    # TODO: Review unreachable code - "file_path": str(file_path),
    # TODO: Review unreachable code - "content_hash": content_hash,
    # TODO: Review unreachable code - "metadata": metadata,
    # TODO: Review unreachable code - "quality_rating": quality_rating,
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - async with self.session.post(url, json=data) as response:
    # TODO: Review unreachable code - response.raise_for_status()
    # TODO: Review unreachable code - return await response.json()

    # TODO: Review unreachable code - async def process_batch(
    # TODO: Review unreachable code - self, file_paths: list[Path], understanding: bool = True
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """Process multiple files in batch.

    # TODO: Review unreachable code - Args:
    # TODO: Review unreachable code - file_paths: List of file paths
    # TODO: Review unreachable code - understanding: Enable AI-powered understanding

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - Batch processing results
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - if not self.session:
    # TODO: Review unreachable code - self.session = aiohttp.ClientSession()

    # TODO: Review unreachable code - url = f"{self.base_url}/process/batch"
    # TODO: Review unreachable code - data = {"file_paths": [str(p) for p in file_paths], "understanding": understanding}

    # TODO: Review unreachable code - async with self.session.post(url, json=data) as response:
    # TODO: Review unreachable code - response.raise_for_status()
    # TODO: Review unreachable code - return await response.json()

    # TODO: Review unreachable code - async def health_check(self) -> bool:
    # TODO: Review unreachable code - """Check if service is healthy.

    # TODO: Review unreachable code - Returns:
    # TODO: Review unreachable code - True if service is healthy
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - if not self.session:
    # TODO: Review unreachable code - self.session = aiohttp.ClientSession()

    # TODO: Review unreachable code - url = f"{self.base_url}/health"
    # TODO: Review unreachable code - async with self.session.get(url) as response:
    # TODO: Review unreachable code - response.raise_for_status()
    # TODO: Review unreachable code - data = await response.json()
    # TODO: Review unreachable code - return data.get("status") == "healthy"
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.error(f"Health check failed: {e}")
    # TODO: Review unreachable code - return False


# Convenience function
async def get_asset_processor_client(base_url: str | None = None) -> AssetProcessorClient:
    """Get an asset processor client instance."""
    return AssetProcessorClient(base_url)
