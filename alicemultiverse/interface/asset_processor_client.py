"""Client for Asset Processor service."""

import logging
from pathlib import Path
from typing import Any

import aiohttp
from alice_config import get_config

logger = logging.getLogger(__name__)


class AssetProcessorClient:
    """Client for communicating with Asset Processor service."""

    def __init__(self, base_url: str | None = None):
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

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        """Exit async context."""
        if self.session:
            await self.session.close()

    async def analyze(self, file_path: Path) -> dict[str, Any]:
        """Analyze a media file.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Analysis results
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/analyze"
        data = {"file_path": str(file_path)}

        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()

    async def assess_quality(
        self, file_path: Path, content_hash: str, pipeline_mode: str = "basic"
    ) -> dict[str, Any]:
        """Assess quality of a media file.

        Args:
            file_path: Path to the file
            content_hash: Content hash for caching
            pipeline_mode: Pipeline mode (basic, standard, premium)

        Returns:
            Quality assessment results
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/quality/assess"
        data = {
            "file_path": str(file_path),
            "content_hash": content_hash,
            "pipeline_mode": pipeline_mode,
        }

        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()

    async def plan_organization(
        self,
        file_path: Path,
        content_hash: str,
        metadata: dict[str, Any],
        quality_rating: int | None = None,
    ) -> dict[str, Any]:
        """Plan organization for a file.

        Args:
            file_path: Path to the file
            content_hash: Content hash
            metadata: File metadata
            quality_rating: Quality rating (1-5)

        Returns:
            Organization plan
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/organize/plan"
        data = {
            "file_path": str(file_path),
            "content_hash": content_hash,
            "metadata": metadata,
            "quality_rating": quality_rating,
        }

        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()

    async def process_batch(
        self, file_paths: list[Path], pipeline_mode: str = "basic"
    ) -> dict[str, Any]:
        """Process multiple files in batch.

        Args:
            file_paths: List of file paths
            pipeline_mode: Pipeline mode for quality assessment

        Returns:
            Batch processing results
        """
        if not self.session:
            self.session = aiohttp.ClientSession()

        url = f"{self.base_url}/process/batch"
        data = {"file_paths": [str(p) for p in file_paths], "pipeline_mode": pipeline_mode}

        async with self.session.post(url, json=data) as response:
            response.raise_for_status()
            return await response.json()

    async def health_check(self) -> bool:
        """Check if service is healthy.

        Returns:
            True if service is healthy
        """
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()

            url = f"{self.base_url}/health"
            async with self.session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                return data.get("status") == "healthy"
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False


# Convenience function
async def get_asset_processor_client(base_url: str | None = None) -> AssetProcessorClient:
    """Get an asset processor client instance."""
    return AssetProcessorClient(base_url)
