"""Statistics tracking for media organizer."""

from collections import defaultdict

from ...core.logging import get_logger
from ...core.types import MediaType, OrganizeResult, Statistics

logger = get_logger(__name__)


class StatisticsMixin:
    """Mixin for statistics tracking and reporting."""
    
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

        if result["status"] == "success":
            self.stats["organized"] += 1
        elif result["status"] == "moved_existing":
            self.stats["moved_existing"] += 1
            self.stats["organized"] += 1  # Count as organized too
        elif result["status"] == "duplicate":
            self.stats["duplicates"] += 1
        elif result["status"] == "error":
            self.stats["errors"] += 1

        if result["date"]:
            self.stats["by_date"][result["date"]] += 1

        if result["source_type"]:
            self.stats["by_source"][result["source_type"]] += 1

        if result["project_folder"]:
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

        # Simple cost estimates per image
        provider = self.metadata_cache.understanding_provider or "anthropic"
        cost_estimates = {
            "openai": 0.01,
            "anthropic": 0.004,  # Claude Haiku
            "google": 0.002,
            "deepseek": 0.0003,
            "ollama": 0.0,  # Free local
        }
        
        cost_per_image = cost_estimates.get(provider, 0.01)
        total_cost = cost_per_image * len(media_files)

        # Show warning
        print("\n" + "="*70)
        print("💸 COST ESTIMATE FOR AI UNDERSTANDING")
        print("="*70)
        print(f"\nProvider: {provider}")
        print(f"Images to analyze: {len(media_files)}")
        print(f"Cost per image: ${cost_per_image:.4f}")
        print(f"Estimated total: ${total_cost:.2f}")

        # Show cheaper alternatives if available
        if cost_per_image > 0.001:
            print("\n💡 Cheaper alternatives:")
            if provider != "deepseek":
                print("  • DeepSeek: ~$0.0003 per image")
            if provider != "google":
                print("  • Google AI: ~$0.002 per image")
            if provider != "ollama":
                print("  • Ollama: FREE (local models)")

        if not self.config.processing.dry_run:
            print("\n🔍 This is a preview. Add --dry-run to see what would happen without cost.")
            response = input("\nProceed with analysis? (y/N): ").strip().lower()
            if response != 'y':
                print("Analysis cancelled.")
                raise KeyboardInterrupt("User cancelled due to cost")
        else:
            print("\n✅ DRY RUN - No actual API calls will be made")

        print("="*70 + "\n")

    def _log_cache_statistics(self) -> None:
        """Log cache performance statistics."""
        cache_stats = self.metadata_cache.get_stats()
        if cache_stats["total_processed"] > 0:
            logger.info(
                f"Cache performance: {cache_stats['cache_hits']} hits, "
                f"{cache_stats['cache_misses']} misses "
                f"({cache_stats['hit_rate']:.1f}% hit rate)"
            )
            if cache_stats["time_saved"] > 0:
                logger.info(f"Time saved by cache: {cache_stats['time_saved']:.1f} seconds")