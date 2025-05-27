"""Workflow-related events for AliceMultiverse (v2).

These events track the lifecycle of creative workflows, from initiation
through completion or failure, enabling monitoring and orchestration.
"""

from dataclasses import dataclass, field
from typing import Any

from .base import BaseEvent


@dataclass
class WorkflowStartedEvent(BaseEvent):
    """Fired when a creative workflow begins execution."""

    # Workflow identification
    workflow_id: str
    workflow_type: str  # 'image_generation', 'video_generation', 'style_transfer'
    workflow_name: str

    # Workflow context
    project_id: str | None = None
    initiated_by: str = ""  # 'user', 'ai_assistant', 'scheduled'

    # Workflow parameters
    input_parameters: dict[str, Any] = field(default_factory=dict)
    provider: str | None = None  # 'fal.ai', 'comfyui', 'local'
    estimated_duration_ms: int | None = None
    estimated_cost: float | None = None

    @property
    def event_type(self) -> str:
        return "workflow.started"


@dataclass
class WorkflowStepCompletedEvent(BaseEvent):
    """Fired when a step within a workflow completes."""

    # Workflow identification
    workflow_id: str
    step_id: str
    step_name: str

    # Step details
    step_number: int
    total_steps: int

    # Step results
    status: str  # 'completed', 'skipped', 'failed'
    output_data: dict[str, Any] = field(default_factory=dict)
    duration_ms: int = 0

    # Resource usage
    resource_usage: dict[str, Any] = field(default_factory=dict)  # GPU, memory, etc.

    @property
    def event_type(self) -> str:
        return "workflow.step_completed"


@dataclass
class WorkflowCompletedEvent(BaseEvent):
    """Fired when a workflow completes successfully."""

    # Workflow identification
    workflow_id: str
    workflow_type: str

    # Completion details
    total_duration_ms: int
    steps_completed: int

    # Results
    output_assets: list[str] = field(default_factory=list)  # Content hashes
    output_metadata: dict[str, Any] = field(default_factory=dict)

    # Resource usage summary
    total_cost: float | None = None
    provider_used: str | None = None
    resource_usage: dict[str, Any] = field(default_factory=dict)

    @property
    def event_type(self) -> str:
        return "workflow.completed"


@dataclass
class WorkflowFailedEvent(BaseEvent):
    """Fired when a workflow fails to complete."""

    # Workflow identification
    workflow_id: str
    workflow_type: str

    # Failure details
    error_type: str  # 'provider_error', 'validation_error', 'resource_limit'
    error_message: str
    failed_at_step: str | None = None
    error_details: dict[str, Any] = field(default_factory=dict)

    # Recovery information
    is_retryable: bool = False
    retry_count: int = 0
    max_retries: int = 3

    # Context
    duration_before_failure_ms: int = 0
    partial_outputs: list[str] = field(default_factory=list)

    @property
    def event_type(self) -> str:
        return "workflow.failed"
