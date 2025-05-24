"""Event-aware media organizer wrapper.

This module wraps the MediaOrganizer to publish events for all significant
operations, enabling monitoring, debugging, and future service extraction.
"""

import asyncio
import time
from pathlib import Path
from typing import Dict, Any

from omegaconf import DictConfig

from .media_organizer import MediaOrganizer
from ..core.types import OrganizeResult
from ..core.logging import get_logger
from ..events import (
    AssetDiscoveredEvent, AssetProcessedEvent, AssetOrganizedEvent,
    QualityAssessedEvent, publish_event
)

logger = get_logger(__name__)


class EventAwareMediaOrganizer(MediaOrganizer):
    """Media organizer that publishes events for all operations."""
    
    def __init__(self, config: DictConfig):
        """Initialize with event publishing support."""
        super().__init__(config)
        self.source = "MediaOrganizer"
        
        # Track event loop for async operations
        try:
            self.loop = asyncio.get_event_loop()
        except RuntimeError:
            self.loop = asyncio.new_event_loop()
            asyncio.set_event_loop(self.loop)
    
    def _publish_event_sync(self, event):
        """Publish event synchronously by running async code."""
        # If we're already in an event loop, schedule it
        try:
            asyncio.get_running_loop()
            # We're in an async context, create a task
            asyncio.create_task(publish_event(event))
        except RuntimeError:
            # No running loop, run it directly
            self.loop.run_until_complete(publish_event(event))
    
    def _process_file(self, media_path: Path) -> OrganizeResult:
        """Process file with event publishing."""
        # Publish discovery event
        try:
            project_folder = self.extract_project_folder(media_path, self.source_dir)
            media_type = self._get_media_type(media_path)
            
            discovery_event = AssetDiscoveredEvent(
                source=self.source,
                file_path=str(media_path),
                content_hash="",  # Will be computed later
                file_size=media_path.stat().st_size,
                media_type=media_type.value,
                project_name=project_folder,
                inbox_path=str(self.source_dir),
                discovery_source="file_scan" if not hasattr(self, 'stop_watching') else "watch_mode"
            )
            self._publish_event_sync(discovery_event)
        except Exception as e:
            logger.error(f"Failed to publish discovery event: {e}")
        
        # Process the file
        result = super()._process_file(media_path)
        
        # Publish organized event if successful
        if result.status == "success" and result.destination:
            try:
                organized_event = AssetOrganizedEvent(
                    source=self.source,
                    content_hash=self.metadata_cache.get_content_hash(media_path),
                    source_path=str(media_path),
                    destination_path=result.destination,
                    project_name=result.project_folder,
                    source_type=result.source_type or "unknown",
                    date_folder=result.date or "",
                    quality_folder=f"{result.quality_stars}-star" if result.quality_stars else None,
                    operation="copy" if self.config.processing.copy_mode else "move",
                    sequence_number=result.file_number
                )
                self._publish_event_sync(organized_event)
            except Exception as e:
                logger.error(f"Failed to publish organized event: {e}")
        
        return result
    
    def _analyze_media(self, media_path: Path, project_folder: str) -> Dict[str, Any]:
        """Analyze media with event publishing."""
        start_time = time.time()
        
        # Perform analysis
        analysis = super()._analyze_media(media_path, project_folder)
        
        # Publish processed event
        try:
            processed_event = AssetProcessedEvent(
                source=self.source,
                content_hash=self.metadata_cache.get_content_hash(media_path),
                file_path=str(media_path),
                metadata=analysis,
                extracted_metadata=analysis.get('metadata', {}),
                generation_params=analysis.get('generation_params', {}),
                processing_duration_ms=int((time.time() - start_time) * 1000),
                processor_version="1.0.0"
            )
            self._publish_event_sync(processed_event)
        except Exception as e:
            logger.error(f"Failed to publish processed event: {e}")
        
        # Publish quality event if assessed
        if 'quality_stars' in analysis and analysis['quality_stars'] is not None:
            try:
                quality_event = QualityAssessedEvent(
                    source=self.source,
                    content_hash=self.metadata_cache.get_content_hash(media_path),
                    file_path=str(media_path),
                    brisque_score=analysis.get('brisque_score'),
                    star_rating=analysis['quality_stars'],
                    combined_score=0.0,  # TODO: Calculate from pipeline
                    pipeline_mode=self.config.pipeline.get('mode', 'basic'),
                    assessment_duration_ms=int(analysis.get('quality_assessment_time', 0) * 1000),
                    stages_completed=['brisque'] if analysis.get('brisque_score') else []
                )
                
                # Add pipeline results if available
                if 'pipeline_result' in analysis and analysis['pipeline_result']:
                    pipeline = analysis['pipeline_result']
                    if 'sightengine' in pipeline:
                        quality_event.sightengine_score = pipeline['sightengine'].get('quality_score')
                        quality_event.stages_completed.append('sightengine')
                    if 'claude' in pipeline:
                        quality_event.claude_assessment = pipeline['claude']
                        quality_event.stages_completed.append('claude')
                    if 'combined_score' in pipeline:
                        quality_event.combined_score = pipeline['combined_score']
                        
                self._publish_event_sync(quality_event)
            except Exception as e:
                logger.error(f"Failed to publish quality event: {e}")
        
        return analysis
    
    def extract_project_folder(self, media_path: Path, source_dir: Path) -> str:
        """Extract project folder name from path.
        
        Made public for event publishing needs.
        """
        try:
            # Get the path relative to source directory
            relative_path = media_path.relative_to(source_dir)
            # The first part is the project folder
            return relative_path.parts[0] if relative_path.parts else "unknown"
        except ValueError:
            # Path is not relative to source_dir
            return "unknown"