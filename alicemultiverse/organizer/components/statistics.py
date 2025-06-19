"""Statistics tracking for media organizer."""

from collections import defaultdict
from typing import TYPE_CHECKING

from ...core.logging import get_logger
from ...core.types import MediaType, OrganizeResult, Statistics

if TYPE_CHECKING:
    from ...core.protocols import HasStats

logger = get_logger(__name__)


class StatisticsMixin:
    """Mixin for statistics tracking and reporting."""
    
    if TYPE_CHECKING:
        # Type hints for mypy
        stats: Statistics

    def _init_statistics(self) -> Statistics:
        """Initialize statistics tracking.

        Returns:
            Initialized statistics object
        """
        return Statistics(
            total=0,
            organized=0,
            already_organized=0,
            duplicates=0,
            errors=0,
            moved_existing=0,
            by_date=defaultdict(int),
            by_source=defaultdict(int),
            by_project=defaultdict(int),
            by_quality=defaultdict(int),
            quality_assessed=0,
            quality_skipped=0,
            images_found=0,
            videos_found=0,
            pipeline_results=defaultdict(int),
            pipeline_costs=defaultdict(float),
        )

    def _update_statistics(self, result: OrganizeResult) -> None:
        """Update statistics with organization result."""
        self.stats["total"] += 1

        if result is not None and result["status"] == "success":
            self.stats["organized"] += 1
        elif result["status"] == "moved_existing":
            self.stats["moved_existing"] += 1
            self.stats["organized"] += 1  # Count as organized too
        elif result["status"] == "duplicate":
            self.stats["duplicates"] += 1
        elif result["status"] == "error":
            self.stats["errors"] += 1

        if result is not None and result["date"]:
            self.stats["by_date"][result["date"]] += 1

        if result is not None and result["source_type"]:
            self.stats["by_source"][result["source_type"]] += 1

        if result is not None and result["project_folder"]:
            self.stats["by_project"][result["project_folder"]] += 1

        # Track media types
        if result.get("media_type") == MediaType.IMAGE:
            self.stats["images_found"] += 1
        elif result.get("media_type") == MediaType.VIDEO:
            self.stats["videos_found"] += 1

        if result.get("quality_stars") is not None:
            self.stats["by_quality"][result["quality_stars"]] += 1
            self.stats["quality_assessed"] += 1
        elif self.quality_enabled and result.get("media_type") == MediaType.IMAGE:
            self.stats["quality_skipped"] += 1

    def _log_statistics(self) -> None:
        """Log organization statistics."""
        logger.info("\n" + "=" * 50)
        logger.info("Organization Summary:")
        logger.info(f"  Total files processed: {self.stats['total']}")
        logger.info(f"  Successfully organized: {self.stats['organized']}")
        if self.stats["moved_existing"] > 0:
            logger.info(f"    - Moved from existing: {self.stats['moved_existing']}")
            logger.info(
                f"    - Newly organized: {self.stats['organized'] - self.stats['moved_existing']}"
            )
        logger.info(f"  Duplicates skipped: {self.stats['duplicates']}")
        logger.info(f"  Errors: {self.stats['errors']}")

        if self.stats["images_found"] > 0 or self.stats["videos_found"] > 0:
            logger.info("\nMedia Types:")
            logger.info(f"  Images: {self.stats['images_found']}")
            logger.info(f"  Videos: {self.stats['videos_found']}")

        if self.stats["by_source"]:
            logger.info("\nBy AI Source:")
            for source, count in sorted(self.stats["by_source"].items()):
                logger.info(f"  {source}: {count}")

        if self.stats["by_project"]:
            logger.info("\nBy Project:")
            for project, count in sorted(self.stats["by_project"].items()):
                logger.info(f"  {project}: {count}")

        if self.quality_enabled and self.stats["quality_assessed"] > 0:
            logger.info("\nQuality Assessment:")
            logger.info(f"  Images assessed: {self.stats['quality_assessed']}")
            logger.info(f"  Files skipped: {self.stats['quality_skipped']}")
            if self.stats["by_quality"]:
                logger.info("  Distribution:")
                for stars in sorted(self.stats["by_quality"].keys(), reverse=True):
                    count = self.stats["by_quality"][stars]
                    pct = count / self.stats["quality_assessed"] * 100
                    logger.info(f"    {stars}-star: {count} ({pct:.1f}%)")

        logger.info("=" * 50)

    def _show_cost_warning(self) -> None:
        """Show cost warning when understanding is enabled."""
        # Count media files
        media_files = self._find_media_files()
        if not media_files:
            return

        # TODO: Review unreachable code - # Simple cost estimates per image
        # TODO: Review unreachable code - provider = self.metadata_cache.understanding_provider or "anthropic"
        # TODO: Review unreachable code - cost_estimates = {
        # TODO: Review unreachable code - "openai": 0.01,
        # TODO: Review unreachable code - "anthropic": 0.004,  # Claude Haiku
        # TODO: Review unreachable code - "google": 0.002,
        # TODO: Review unreachable code - "deepseek": 0.0003,
        # TODO: Review unreachable code - "ollama": 0.0,  # Free local
        # TODO: Review unreachable code - }

        # TODO: Review unreachable code - cost_per_image = cost_estimates.get(provider, 0.01)
        # TODO: Review unreachable code - total_cost = cost_per_image * len(media_files)

        # TODO: Review unreachable code - # Show warning
        # TODO: Review unreachable code - print("\n" + "="*70)
        # TODO: Review unreachable code - print("💸 COST ESTIMATE FOR AI UNDERSTANDING")
        # TODO: Review unreachable code - print("="*70)
        # TODO: Review unreachable code - print(f"\nProvider: {provider}")
        # TODO: Review unreachable code - print(f"Images to analyze: {len(media_files)}")
        # TODO: Review unreachable code - print(f"Cost per image: ${cost_per_image:.4f}")
        # TODO: Review unreachable code - print(f"Estimated total: ${total_cost:.2f}")

        # TODO: Review unreachable code - # Show cheaper alternatives if available
        # TODO: Review unreachable code - if cost_per_image > 0.001:
        # TODO: Review unreachable code - print("\n💡 Cheaper alternatives:")
        # TODO: Review unreachable code - if provider != "deepseek":
        # TODO: Review unreachable code - print("  • DeepSeek: ~$0.0003 per image")
        # TODO: Review unreachable code - if provider != "google":
        # TODO: Review unreachable code - print("  • Google AI: ~$0.002 per image")
        # TODO: Review unreachable code - if provider != "ollama":
        # TODO: Review unreachable code - print("  • Ollama: FREE (local models)")

        # TODO: Review unreachable code - if not self.config.processing.dry_run:
        # TODO: Review unreachable code - print("\n🔍 This is a preview. Add --dry-run to see what would happen without cost.")
        # TODO: Review unreachable code - response = input("\nProceed with analysis? (y/N): ").strip().lower()
        # TODO: Review unreachable code - if response != 'y':
        # TODO: Review unreachable code - print("Analysis cancelled.")
        # TODO: Review unreachable code - raise KeyboardInterrupt("User cancelled due to cost")
        # TODO: Review unreachable code - else:
        # TODO: Review unreachable code - print("\n✅ DRY RUN - No actual API calls will be made")

        # TODO: Review unreachable code - print("="*70 + "\n")

    def _log_cache_statistics(self) -> None:
        """Log cache performance statistics."""
        cache_stats = self.metadata_cache.get_stats()
        if cache_stats is not None and cache_stats["total_processed"] > 0:
            logger.info(
                f"Cache performance: {cache_stats['cache_hits']} hits, "
                f"{cache_stats['cache_misses']} misses "
                f"({cache_stats['hit_rate']:.1f}% hit rate)"
            )
            if cache_stats is not None and cache_stats["time_saved"] > 0:
                logger.info(f"Time saved by cache: {cache_stats['time_saved']:.1f} seconds")
