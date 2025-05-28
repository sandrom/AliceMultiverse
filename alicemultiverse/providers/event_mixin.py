"""Event publishing mixin for providers."""

import asyncio
import logging
from typing import Optional

from ..events.base import EventBus
from .types import GenerationRequest, GenerationResult

logger = logging.getLogger(__name__)


class ProviderEventMixin:
    """Mixin for publishing provider events."""
    
    event_bus: Optional[EventBus]
    name: str  # Provider name
    
    def _publish_success(self, request: GenerationRequest, result: GenerationResult):
        """Publish success event."""
        if self.event_bus and result.file_path:
            # Import here to avoid circular dependencies
            from ..events.asset_events import AssetGeneratedEvent
            from ..events.base import create_event
            
            event = create_event(
                AssetGeneratedEvent,
                source=f"provider:{self.name}",
                asset_id=result.asset_id or "",
                file_path=str(result.file_path),
                generation_type=request.generation_type.value,
                provider=self.name,
                model=result.model or request.model or "default",
                prompt=request.prompt,
                parameters=request.parameters or {},
                cost=result.cost,
                generation_time=result.generation_time,
            )
            self._sync_publish(event)

    def _publish_failure(self, request: GenerationRequest, error: str):
        """Publish failure event."""
        if self.event_bus:
            # Import here to avoid circular dependencies
            from ..events.asset_events import GenerationFailedEvent
            from ..events.base import create_event
            
            event = create_event(
                GenerationFailedEvent,
                source=f"provider:{self.name}",
                generation_type=request.generation_type.value,
                provider=self.name,
                model=request.model or "default",
                prompt=request.prompt,
                error=error,
                parameters=request.parameters or {},
            )
            self._sync_publish(event)
    
    def _publish_started(self, request: GenerationRequest):
        """Publish generation started event."""
        if self.event_bus:
            # Import here to avoid circular dependencies
            from ..events.asset_events import GenerationStartedEvent
            from ..events.base import create_event
            
            event = create_event(
                GenerationStartedEvent,
                source=f"provider:{self.name}",
                generation_type=request.generation_type.value,
                provider=self.name,
                model=request.model or "default",
                prompt=request.prompt,
                parameters=request.parameters or {},
            )
            self._sync_publish(event)
    
    def _sync_publish(self, event):
        """Publish event synchronously."""
        if not self.event_bus:
            return
            
        # Check if we have an event loop running
        try:
            loop = asyncio.get_running_loop()
            # We're in an async context, create a task
            asyncio.create_task(self.event_bus.publish(event))
        except RuntimeError:
            # No event loop, run sync
            try:
                asyncio.run(self.event_bus.publish(event))
            except Exception as e:
                logger.warning(f"Failed to publish event: {e}")