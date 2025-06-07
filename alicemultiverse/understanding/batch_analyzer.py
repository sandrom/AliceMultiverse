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
    
    @property
    def elapsed_time(self) -> timedelta:
        """Get elapsed time."""
        return datetime.now() - self.start_time
    
    @property
    def estimated_time_remaining(self) -> Optional[timedelta]:
        """Estimate remaining time based on current rate."""
        if self.processed == 0:
            return None
        
        rate = self.processed / self.elapsed_time.total_seconds()
        remaining = self.total_images - self.processed
        
        if rate > 0:
            return timedelta(seconds=remaining / rate)
        return None
    
    @property
    def average_cost_per_image(self) -> float:
        """Get average cost per processed image."""
        return self.total_cost / self.succeeded if self.succeeded > 0 else 0
    
    def save_checkpoint(self):
        """Save progress checkpoint for resumption."""
        if self.checkpoint_file:
            checkpoint_data = {
                "processed_hashes": list(self.processed_hashes),
                "failed_hashes": self.failed_hashes,
                "total_cost": self.total_cost,
                "processed": self.processed,
                "succeeded": self.succeeded,
                "failed": self.failed,
                "skipped": self.skipped,
                "timestamp": datetime.now().isoformat()
            }
            
            with open(self.checkpoint_file, 'w') as f:
                json.dump(checkpoint_data, f, indent=2)
    
    @classmethod
    def load_checkpoint(cls, checkpoint_file: Path, total_images: int) -> 'BatchProgress':
        """Load progress from checkpoint file."""
        progress = cls(total_images=total_images, checkpoint_file=checkpoint_file)
        
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, 'r') as f:
                    data = json.load(f)
                
                progress.processed_hashes = set(data.get("processed_hashes", []))
                progress.failed_hashes = data.get("failed_hashes", {})
                progress.total_cost = data.get("total_cost", 0.0)
                progress.processed = data.get("processed", 0)
                progress.succeeded = data.get("succeeded", 0)
                progress.failed = data.get("failed", 0)
                progress.skipped = data.get("skipped", 0)
                
                logger.info(f"Resumed from checkpoint: {progress.processed}/{total_images} processed")
                
            except Exception as e:
                logger.warning(f"Failed to load checkpoint: {e}")
        
        return progress


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
        
        if self.max_concurrent < 1:
            raise ValueError("max_concurrent must be at least 1")
        
        if self.max_cost is not None and self.max_cost <= 0:
            raise ValueError("max_cost must be positive")


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
        
        # Check cost estimate
        estimated_cost, cost_details = await self.estimate_cost(request)
        if estimated_cost > request.cost_warning_threshold:
            logger.warning(f"Estimated cost ${estimated_cost:.2f} exceeds warning threshold")
        
        if request.max_cost and estimated_cost > request.max_cost:
            raise ValueError(f"Estimated cost ${estimated_cost:.2f} exceeds maximum ${request.max_cost:.2f}")
        
        # Set up progress tracking
        checkpoint_file = Path(f".batch_analysis_{int(time.time())}.checkpoint")
        progress = BatchProgress.load_checkpoint(checkpoint_file, len(images)) if request.resume_from_checkpoint else BatchProgress(len(images), checkpoint_file=checkpoint_file)
        
        # Filter out already processed
        if request.skip_existing:
            images = [img for img in images if self._get_content_hash(img) not in progress.processed_hashes]
            progress.skipped = len(progress.processed_hashes)
        
        # Process images
        results = []
        semaphore = asyncio.Semaphore(request.max_concurrent)
        
        async def process_with_retry(image_path: Path) -> Tuple[Path, Optional[ImageAnalysisResult]]:
            """Process a single image with retry logic."""
            content_hash = self._get_content_hash(image_path)
            
            # Skip if already processed
            if content_hash in progress.processed_hashes:
                return image_path, None
            
            # Skip if failed and not retrying
            if content_hash in progress.failed_hashes and not request.reanalyze_failed:
                return image_path, None
            
            async with semaphore:
                # Rate limiting
                async with self._rate_limiter:
                    await asyncio.sleep(request.rate_limit_delay)
                
                # Retry logic
                last_error = None
                for attempt in range(request.retry_attempts):
                    try:
                        # Check cost limit
                        if request.max_cost and progress.total_cost >= request.max_cost:
                            logger.warning("Reached cost limit, stopping batch")
                            return image_path, None
                        
                        # Analyze image
                        result = await self.analyzer.analyze(
                            image_path,
                            provider=request.provider,
                            generate_prompt=request.generate_prompt,
                            extract_tags=request.extract_tags,
                            detailed=request.detailed,
                            custom_instructions=request.custom_instructions
                        )
                        
                        # Update progress
                        progress.processed += 1
                        progress.succeeded += 1
                        progress.total_cost += result.cost
                        progress.processed_hashes.add(content_hash)
                        
                        # Database saving removed with PostgreSQL
                        
                        # Checkpoint periodically
                        if progress.processed % request.checkpoint_interval == 0:
                            progress.save_checkpoint()
                        
                        return image_path, result
                        
                    except Exception as e:
                        last_error = str(e)
                        logger.warning(f"Attempt {attempt + 1} failed for {image_path}: {e}")
                        if attempt < request.retry_attempts - 1:
                            await asyncio.sleep(request.retry_delay * (attempt + 1))
                
                # All retries failed
                progress.processed += 1
                progress.failed += 1
                progress.failed_hashes[content_hash] = last_error
                return image_path, None
        
        # Process with progress bar
        if request.show_progress:
            tasks = [process_with_retry(img) for img in images]
            with tqdm(total=len(images), desc="Analyzing images") as pbar:
                for coro in asyncio.as_completed(tasks):
                    result = await coro
                    results.append(result)
                    pbar.update(1)
                    pbar.set_postfix({
                        "succeeded": progress.succeeded,
                        "failed": progress.failed,
                        "cost": f"${progress.total_cost:.2f}"
                    })
        else:
            # Process without progress bar
            tasks = [process_with_retry(img) for img in images]
            results = await asyncio.gather(*tasks)
        
        # Final checkpoint
        progress.save_checkpoint()
        
        # Clean up checkpoint if fully successful
        if progress.failed == 0 and checkpoint_file.exists():
            checkpoint_file.unlink()
        
        # Log summary
        logger.info(f"Batch analysis complete: {progress.succeeded} succeeded, "
                   f"{progress.failed} failed, ${progress.total_cost:.2f} total cost")
        
        return results
    
    async def _get_images_to_process(self, request: BatchAnalysisRequest) -> List[Path]:
        """Get list of images to process based on request."""
        images = []
        
        if request.image_paths:
            images = request.image_paths
        
        elif request.project_id:
            # PostgreSQL removed - project queries not supported
            logger.warning("Project-based batch analysis not available without PostgreSQL")
            raise ValueError("Project-based batch analysis requires database integration")
        
        elif request.content_hashes:
            # PostgreSQL removed - content hash queries not supported
            logger.warning("Content hash-based batch analysis not available without PostgreSQL")
            raise ValueError("Content hash-based batch analysis requires database integration")
        
        # Filter by media type
        valid_extensions = {
            "image": {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"},
            "video": {".mp4", ".mov", ".avi", ".mkv"}
        }
        
        allowed_extensions = set()
        for media_type in request.media_types:
            allowed_extensions.update(valid_extensions.get(media_type, set()))
        
        return [img for img in images if img.suffix.lower() in allowed_extensions]
    
    def _get_content_hash(self, image_path: Path) -> str:
        """Get content hash for an image."""
        # Simple hash based on path and size for now
        # In production, would use actual content hash
        import hashlib
        
        stat = image_path.stat()
        hash_input = f"{image_path}:{stat.st_size}:{stat.st_mtime}"
        return hashlib.sha256(hash_input.encode()).hexdigest()
    
