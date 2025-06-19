"""Batch analysis system for processing multiple images efficiently."""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from tqdm.asyncio import tqdm

# PostgreSQL removed - Asset and AssetRepository no longer available
from .analyzer import ImageAnalyzer
from .base import ImageAnalysisResult

logger = logging.getLogger(__name__)


@dataclass
class BatchProgress:
    """Track progress of batch analysis."""

    total_images: int
    processed: int = 0
    succeeded: int = 0
    failed: int = 0
    skipped: int = 0
    start_time: datetime = field(default_factory=datetime.now)

    # Cost tracking
    total_cost: float = 0.0
    estimated_remaining_cost: float = 0.0

    # Resumption support
    checkpoint_file: Optional[Path] = None
    processed_hashes: Set[str] = field(default_factory=set)
    failed_hashes: Dict[str, str] = field(default_factory=dict)  # hash -> error

    @property
    def completion_percentage(self) -> float:
        """Get completion percentage."""
        return (self.processed / self.total_images * 100) if self.total_images > 0 else 0

    # TODO: Review unreachable code - @property
    # TODO: Review unreachable code - def elapsed_time(self) -> timedelta:
    # TODO: Review unreachable code - """Get elapsed time."""
    # TODO: Review unreachable code - return datetime.now() - self.start_time

    # TODO: Review unreachable code - @property
    # TODO: Review unreachable code - def estimated_time_remaining(self) -> Optional[timedelta]:
    # TODO: Review unreachable code - """Estimate remaining time based on current rate."""
    # TODO: Review unreachable code - if self.processed == 0:
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - rate = self.processed / self.elapsed_time.total_seconds()
    # TODO: Review unreachable code - remaining = self.total_images - self.processed

    # TODO: Review unreachable code - if rate > 0:
    # TODO: Review unreachable code - return timedelta(seconds=remaining / rate)
    # TODO: Review unreachable code - return None

    # TODO: Review unreachable code - @property
    # TODO: Review unreachable code - def average_cost_per_image(self) -> float:
    # TODO: Review unreachable code - """Get average cost per processed image."""
    # TODO: Review unreachable code - return float(self.total_cost) / self.succeeded if self.succeeded > 0 else 0

    # TODO: Review unreachable code - def save_checkpoint(self):
    # TODO: Review unreachable code - """Save progress checkpoint for resumption."""
    # TODO: Review unreachable code - if self.checkpoint_file:
    # TODO: Review unreachable code - checkpoint_data = {
    # TODO: Review unreachable code - "processed_hashes": list(self.processed_hashes),
    # TODO: Review unreachable code - "failed_hashes": self.failed_hashes,
    # TODO: Review unreachable code - "total_cost": self.total_cost,
    # TODO: Review unreachable code - "processed": self.processed,
    # TODO: Review unreachable code - "succeeded": self.succeeded,
    # TODO: Review unreachable code - "failed": self.failed,
    # TODO: Review unreachable code - "skipped": self.skipped,
    # TODO: Review unreachable code - "timestamp": datetime.now().isoformat()
    # TODO: Review unreachable code - }

    # TODO: Review unreachable code - with open(self.checkpoint_file, 'w') as f:
    # TODO: Review unreachable code - json.dump(checkpoint_data, f, indent=2)

    # TODO: Review unreachable code - @classmethod
    # TODO: Review unreachable code - def load_checkpoint(cls, checkpoint_file: Path, total_images: int) -> 'BatchProgress':
    # TODO: Review unreachable code - """Load progress from checkpoint file."""
    # TODO: Review unreachable code - progress = cls(total_images=total_images, checkpoint_file=checkpoint_file)

    # TODO: Review unreachable code - if checkpoint_file.exists():
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - with open(checkpoint_file, 'r') as f:
    # TODO: Review unreachable code - data = json.load(f)

    # TODO: Review unreachable code - progress.processed_hashes = set(data.get("processed_hashes", []))
    # TODO: Review unreachable code - progress.failed_hashes = data.get("failed_hashes", {})
    # TODO: Review unreachable code - progress.total_cost = data.get("total_cost", 0.0)
    # TODO: Review unreachable code - progress.processed = data.get("processed", 0)
    # TODO: Review unreachable code - progress.succeeded = data.get("succeeded", 0)
    # TODO: Review unreachable code - progress.failed = data.get("failed", 0)
    # TODO: Review unreachable code - progress.skipped = data.get("skipped", 0)

    # TODO: Review unreachable code - logger.info(f"Resumed from checkpoint: {progress.processed}/{total_images} processed")

    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.warning(f"Failed to load checkpoint: {e}")

    # TODO: Review unreachable code - return progress


@dataclass
class BatchAnalysisRequest:
    """Configuration for batch analysis."""

    # Input specification
    image_paths: Optional[List[Path]] = None
    project_id: Optional[str] = None
    content_hashes: Optional[List[str]] = None

    # Analysis options
    provider: Optional[str] = None  # None = auto-select
    generate_prompt: bool = True
    extract_tags: bool = True
    detailed: bool = False
    custom_instructions: Optional[str] = None

    # Processing options
    max_concurrent: int = 5
    rate_limit_delay: float = 0.1  # Seconds between requests
    retry_attempts: int = 3
    retry_delay: float = 1.0

    # Cost controls
    max_cost: Optional[float] = None
    cost_warning_threshold: float = 10.0  # Warn if estimated > this

    # Progress tracking
    show_progress: bool = True
    checkpoint_interval: int = 10  # Save checkpoint every N images
    resume_from_checkpoint: bool = True

    # Filtering
    skip_existing: bool = True  # Skip if already analyzed
    reanalyze_failed: bool = True  # Retry previously failed
    media_types: List[str] = field(default_factory=lambda: ["image"])

    def validate(self) -> None:
        """Validate the request configuration."""
        if not any([self.image_paths, self.project_id, self.content_hashes]):
            raise ValueError("Must specify either image_paths, project_id, or content_hashes")

        # TODO: Review unreachable code - if self.max_concurrent < 1:
        # TODO: Review unreachable code - raise ValueError("max_concurrent must be at least 1")

        # TODO: Review unreachable code - if self.max_cost is not None and self.max_cost <= 0:
        # TODO: Review unreachable code - raise ValueError("max_cost must be positive")


class BatchAnalyzer:
    """Handles batch analysis of images with progress tracking and cost management."""

    def __init__(self, analyzer: ImageAnalyzer):
        """Initialize batch analyzer.

        Args:
            analyzer: Image analyzer instance
        """
        self.analyzer = analyzer
        self._rate_limiter = asyncio.Semaphore(1)  # For rate limiting

    async def estimate_cost(self, request: BatchAnalysisRequest) -> Tuple[float, Dict[str, Any]]:
        """Estimate the cost of batch analysis.

        Args:
            request: Batch analysis request

        Returns:
            Tuple of (total_cost, details_dict)
        """
        # Get images to process
        images = await self._get_images_to_process(request)

        # Get provider costs
        if request.provider:
            providers = [request.provider]
        else:
            providers = self.analyzer.get_available_providers()

        estimates = {}
        for provider in providers:
            if provider in self.analyzer.analyzers:
                cost_per_image = self.analyzer.analyzers[provider].estimate_cost(request.detailed)
                total_cost = cost_per_image * len(images)
                estimates[provider] = {
                    "cost_per_image": cost_per_image,
                    "total_cost": total_cost,
                    "image_count": len(images)
                }

        # Find cheapest if auto-selecting
        if not request.provider and estimates:
            cheapest = min(estimates.items(), key=lambda x: x[1]["total_cost"])
            selected_provider = cheapest[0]
            selected_cost = cheapest[1]["total_cost"]
        elif request.provider in estimates:
            selected_provider = request.provider
            selected_cost = estimates[request.provider]["total_cost"]
        else:
            selected_provider = None
            selected_cost = 0

        return selected_cost, {
            "estimates": estimates,
            "selected_provider": selected_provider,
            "image_count": len(images),
            "detailed": request.detailed
        }

    async def analyze_batch(self, request: BatchAnalysisRequest) -> List[Tuple[Path, Optional[ImageAnalysisResult]]]:
        """Analyze a batch of images.

        Args:
            request: Batch analysis request

        Returns:
            List of (image_path, result) tuples
        """
        request.validate()

        # Get images to process
        images = await self._get_images_to_process(request)
        logger.info(f"Found {len(images)} images to process")

        if not images:
            return []

        # TODO: Review unreachable code - # Check cost estimate
        # TODO: Review unreachable code - estimated_cost, cost_details = await self.estimate_cost(request)
        # TODO: Review unreachable code - if estimated_cost > request.cost_warning_threshold:
        # TODO: Review unreachable code - logger.warning(f"Estimated cost ${estimated_cost:.2f} exceeds warning threshold")

        # TODO: Review unreachable code - if request.max_cost and estimated_cost > request.max_cost:
        # TODO: Review unreachable code - raise ValueError(f"Estimated cost ${estimated_cost:.2f} exceeds maximum ${request.max_cost:.2f}")

        # TODO: Review unreachable code - # Set up progress tracking
        # TODO: Review unreachable code - checkpoint_file = Path(f".batch_analysis_{int(time.time())}.checkpoint")
        # TODO: Review unreachable code - progress = BatchProgress.load_checkpoint(checkpoint_file, len(images)) if request.resume_from_checkpoint else BatchProgress(len(images), checkpoint_file=checkpoint_file)

        # TODO: Review unreachable code - # Filter out already processed
        # TODO: Review unreachable code - if request.skip_existing:
        # TODO: Review unreachable code - images = [img for img in images if self._get_content_hash(img) not in progress.processed_hashes]
        # TODO: Review unreachable code - progress.skipped = len(progress.processed_hashes)

        # TODO: Review unreachable code - # Process images
        # TODO: Review unreachable code - results = []
        # TODO: Review unreachable code - semaphore = asyncio.Semaphore(request.max_concurrent)

        # TODO: Review unreachable code - async def process_with_retry(image_path: Path) -> Tuple[Path, Optional[ImageAnalysisResult]]:
        # TODO: Review unreachable code - """Process a single image with retry logic."""
        # TODO: Review unreachable code - content_hash = self._get_content_hash(image_path)

        # TODO: Review unreachable code - # Skip if already processed
        # TODO: Review unreachable code - if content_hash in progress.processed_hashes:
        # TODO: Review unreachable code - return image_path, None

        # TODO: Review unreachable code - # Skip if failed and not retrying
        # TODO: Review unreachable code - if content_hash in progress.failed_hashes and not request.reanalyze_failed:
        # TODO: Review unreachable code - return image_path, None

        # TODO: Review unreachable code - async with semaphore:
        # TODO: Review unreachable code - # Rate limiting
        # TODO: Review unreachable code - async with self._rate_limiter:
        # TODO: Review unreachable code - await asyncio.sleep(request.rate_limit_delay)

        # TODO: Review unreachable code - # Retry logic
        # TODO: Review unreachable code - last_error = None
        # TODO: Review unreachable code - for attempt in range(request.retry_attempts):
        # TODO: Review unreachable code - try:
        # TODO: Review unreachable code - # Check cost limit
        # TODO: Review unreachable code - if request.max_cost and progress.total_cost >= request.max_cost:
        # TODO: Review unreachable code - logger.warning("Reached cost limit, stopping batch")
        # TODO: Review unreachable code - return image_path, None

        # TODO: Review unreachable code - # Analyze image
        # TODO: Review unreachable code - result = await self.analyzer.analyze(
        # TODO: Review unreachable code - image_path,
        # TODO: Review unreachable code - provider=request.provider,
        # TODO: Review unreachable code - generate_prompt=request.generate_prompt,
        # TODO: Review unreachable code - extract_tags=request.extract_tags,
        # TODO: Review unreachable code - detailed=request.detailed,
        # TODO: Review unreachable code - custom_instructions=request.custom_instructions
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - # Update progress
        # TODO: Review unreachable code - progress.processed += 1
        # TODO: Review unreachable code - progress.succeeded += 1
        # TODO: Review unreachable code - progress.total_cost += result.cost
        # TODO: Review unreachable code - progress.processed_hashes.add(content_hash)

        # TODO: Review unreachable code - # Database saving removed with PostgreSQL

        # TODO: Review unreachable code - # Checkpoint periodically
        # TODO: Review unreachable code - if progress.processed % request.checkpoint_interval == 0:
        # TODO: Review unreachable code - progress.save_checkpoint()

        # TODO: Review unreachable code - return image_path, result

        # TODO: Review unreachable code - except Exception as e:
        # TODO: Review unreachable code - last_error = str(e)
        # TODO: Review unreachable code - logger.warning(f"Attempt {attempt + 1} failed for {image_path}: {e}")
        # TODO: Review unreachable code - if attempt < request.retry_attempts - 1:
        # TODO: Review unreachable code - await asyncio.sleep(request.retry_delay * (attempt + 1))

        # TODO: Review unreachable code - # All retries failed
        # TODO: Review unreachable code - progress.processed += 1
        # TODO: Review unreachable code - progress.failed += 1
        # TODO: Review unreachable code - progress.failed_hashes[content_hash] = last_error
        # TODO: Review unreachable code - return image_path, None

        # TODO: Review unreachable code - # Process with progress bar
        # TODO: Review unreachable code - if request.show_progress:
        # TODO: Review unreachable code - tasks = [process_with_retry(img) for img in images]
        # TODO: Review unreachable code - with tqdm(total=len(images), desc="Analyzing images") as pbar:
        # TODO: Review unreachable code - for coro in asyncio.as_completed(tasks):
        # TODO: Review unreachable code - result = await coro
        # TODO: Review unreachable code - results.append(result)
        # TODO: Review unreachable code - pbar.update(1)
        # TODO: Review unreachable code - pbar.set_postfix({
        # TODO: Review unreachable code - "succeeded": progress.succeeded,
        # TODO: Review unreachable code - "failed": progress.failed,
        # TODO: Review unreachable code - "cost": f"${progress.total_cost:.2f}"
        # TODO: Review unreachable code - })
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - # Process without progress bar
        # TODO: Review unreachable code - tasks = [process_with_retry(img) for img in images]
        # TODO: Review unreachable code - results = await asyncio.gather(*tasks)

        # TODO: Review unreachable code - # Final checkpoint
        # TODO: Review unreachable code - progress.save_checkpoint()

        # TODO: Review unreachable code - # Clean up checkpoint if fully successful
        # TODO: Review unreachable code - if progress.failed == 0 and checkpoint_file.exists():
        # TODO: Review unreachable code - checkpoint_file.unlink()

        # TODO: Review unreachable code - # Log summary
        # TODO: Review unreachable code - logger.info(f"Batch analysis complete: {progress.succeeded} succeeded, "
        # TODO: Review unreachable code - f"{progress.failed} failed, ${progress.total_cost:.2f} total cost")

        # TODO: Review unreachable code - return results

    async def _get_images_to_process(self, request: BatchAnalysisRequest) -> List[Path]:
        """Get list of images to process based on request."""
        images = []

        if request.image_paths:
            images = request.image_paths

        elif request.project_id:
            # PostgreSQL removed - project queries not supported
            logger.warning("Project-based batch analysis not available without PostgreSQL")
            raise ValueError("Project-based batch analysis requires database integration")

        # TODO: Review unreachable code - elif request.content_hashes:
        # TODO: Review unreachable code - # PostgreSQL removed - content hash queries not supported
        # TODO: Review unreachable code - logger.warning("Content hash-based batch analysis not available without PostgreSQL")
        # TODO: Review unreachable code - raise ValueError("Content hash-based batch analysis requires database integration")

        # TODO: Review unreachable code - # Filter by media type
        # TODO: Review unreachable code - valid_extensions = {
        # TODO: Review unreachable code - "image": {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"},
        # TODO: Review unreachable code - "video": {".mp4", ".mov", ".avi", ".mkv"}
        # TODO: Review unreachable code - }

        # TODO: Review unreachable code - allowed_extensions = set()
        # TODO: Review unreachable code - for media_type in request.media_types:
        # TODO: Review unreachable code - allowed_extensions.update(valid_extensions.get(media_type, set()))

        # TODO: Review unreachable code - return [img for img in images if img.suffix.lower() in allowed_extensions]

    def _get_content_hash(self, image_path: Path) -> str:
        """Get content hash for an image."""
        # Simple hash based on path and size for now
        # In production, would use actual content hash
        import hashlib

        stat = image_path.stat()
        hash_input = f"{image_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.sha256(hash_input.encode()).hexdigest()

