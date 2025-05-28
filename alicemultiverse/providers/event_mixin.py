"""Event publishing mixin for providers."""

import logging
from typing import Any, Optional

from ..events.postgres_events import publish_event
from .types import GenerationRequest, GenerationResult

logger = logging.getLogger(__name__)


class ProviderEventMixin:
    """Mixin for publishing provider events."""
    
    event_bus: Optional[Any]  # Kept for compatibility but not used
    name: str  # Provider name
    
    def _publish_success(self, request: GenerationRequest, result: GenerationResult):
        """Publish success event."""
        if result.file_path:
            publish_event(
                "asset.generated",
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

    def _publish_failure(self, request: GenerationRequest, error: str):
        """Publish failure event."""
        publish_event(
            "generation.failed",
            source=f"provider:{self.name}",
            generation_type=request.generation_type.value,
            provider=self.name,
            model=request.model or "default",
            prompt=request.prompt,
            error=error,
            parameters=request.parameters or {},
        )
    
    def _publish_started(self, request: GenerationRequest):
        """Publish generation started event."""
        publish_event(
            "generation.started",
            source=f"provider:{self.name}",
            generation_type=request.generation_type.value,
            provider=self.name,
            model=request.model or "default",
            prompt=request.prompt,
            parameters=request.parameters or {},
        )