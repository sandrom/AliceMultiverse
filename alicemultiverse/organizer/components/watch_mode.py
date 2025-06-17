"""Watch mode functionality for media organizer."""

import signal
import time
from pathlib import Path

from tqdm import tqdm

from ...core.logging import get_logger

logger = get_logger(__name__)


class WatchModeMixin:
    """Mixin for continuous monitoring of new media files."""
    
    def _watch_and_organize(self) -> bool:
        """Watch for new files and organize them continuously."""
        logger.info(f"Watching {self.source_dir} for new files...")
        logger.info("Press Ctrl+C to stop")

        # Set up signal handler for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)

        # Process existing files first
        self._organize_once()

        # Track processed files
        self.processed_files = set(self._find_media_files())

        # Watch for new files
        while not self.stop_watching:
            try:
                time.sleep(self.watch_interval)

                # Find new files
                current_files = set(self._find_media_files())
                new_files = current_files - self.processed_files

                if new_files:
                    logger.info(f"Found {len(new_files)} new files")
                    for media_file in new_files:
                        result = self._process_file(media_file)
                        self._update_statistics(result)
                        self.processed_files.add(media_file)

                    # Clean up duplicates after processing batch
                    if self.output_dir.exists():
                        self._cleanup_duplicates()

            except Exception as e:
                logger.error(f"Error in watch mode: {e}")

        logger.info("\nStopped watching")
        self._log_statistics()
        return True

    def _signal_handler(self, signum, frame):
        """Handle interrupt signal."""
        _ = signum, frame  # Unused but required by signal interface
        self.stop_watching = True

    def _organize_once(self) -> bool:
        """Organize files once and return."""
        logger.info(f"Organizing files from {self.source_dir} to {self.output_dir}")

        if not self.source_dir.exists():
            logger.error(f"Source directory does not exist: {self.source_dir}")
            return False

        # Find all media files
        media_files = self._find_media_files()
        if not media_files:
            logger.info("No media files found to organize")
            return True

        logger.info(f"Found {len(media_files)} media files to process")

        # Process files with progress bar
        with tqdm(total=len(media_files), desc="Organizing files") as pbar:
            for media_file in media_files:
                result = self._process_file(media_file)
                self._update_statistics(result)
                pbar.update(1)

        # Clean up duplicates in organized folder
        if self.output_dir.exists():
            self._cleanup_duplicates()

        # Log statistics
        self._log_statistics()

        # Log cache statistics
        self._log_cache_statistics()

        return True

    def organize(self) -> bool:
        """Main entry point for organizing media files.
        
        Returns:
            True if successful, False otherwise
        """
        try:
            # Show cost warnings if understanding is enabled
            if self.metadata_cache.enable_understanding:
                self._show_cost_warning()

            if self.watch_mode:
                return self._watch_and_organize()
            else:
                return self._organize_once()
        except KeyboardInterrupt:
            logger.info("\nOrganization cancelled by user")
            raise  # Re-raise to let CLI handle the exit code
        except Exception as e:
            logger.error(f"Organization failed: {e}")
            return False