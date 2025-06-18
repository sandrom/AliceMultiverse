"""Base classes for workflow templates."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

from alicemultiverse.providers.provider_types import GenerationResult

logger = logging.getLogger(__name__)


class WorkflowStatus(str, Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    PAUSED = "paused"


class StepStatus(str, Enum):
    """Individual step status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class WorkflowStep:
    """Individual step in a workflow.

    Attributes:
        name: Step name for identification
        provider: Provider name (e.g., "leonardo", "magnific")
        operation: Operation type (e.g., "generate", "upscale")
        parameters: Parameters for the operation
        condition: Optional condition for execution
        retry_count: Number of retries on failure
        timeout: Timeout in seconds
        cost_limit: Maximum cost for this step
    """
    name: str
    provider: str
    operation: str = "generate"
    parameters: dict[str, Any] = field(default_factory=dict)
    condition: str | None = None  # Simple condition like "previous.success"
    retry_count: int = 3
    timeout: float = 300.0  # 5 minutes default
    cost_limit: float | None = None

    # Runtime fields
    status: StepStatus = StepStatus.PENDING
    result: GenerationResult | None = None
    error: str | None = None
    start_time: datetime | None = None
    end_time: datetime | None = None
    cost: float = 0.0


@dataclass
class WorkflowContext:
    """Shared context between workflow steps.

    Stores intermediate results and allows data passing between steps.
    """
    # Input data
    initial_prompt: str
    initial_params: dict[str, Any] = field(default_factory=dict)

    # Step results
    steps: dict[str, WorkflowStep] = field(default_factory=dict)
    results: dict[str, GenerationResult] = field(default_factory=dict)

    # File management
    files: dict[str, Path] = field(default_factory=dict)
    temp_files: list[Path] = field(default_factory=list)

    # Metadata
    metadata: dict[str, Any] = field(default_factory=dict)
    total_cost: float = 0.0
    start_time: datetime | None = None
    end_time: datetime | None = None

    def get_previous_result(self, step_name: str | None = None) -> GenerationResult | None:
        """Get result from a previous step."""
        if not step_name:
            # Get the last completed step
            for name in reversed(list(self.steps.keys())):
                if name in self.results:
                    return self.results[name]
            return None
        return self.results.get(step_name)

    def get_file(self, key: str) -> Path | None:
        """Get a file path by key."""
        return self.files.get(key)

    def set_file(self, key: str, path: Path):
        """Store a file path with a key."""
        self.files[key] = path

    def add_temp_file(self, path: Path):
        """Add a temporary file for cleanup."""
        self.temp_files.append(path)

    def evaluate_condition(self, condition: str) -> bool:
        """Evaluate a simple condition.

        Supports:
        - "previous.success": Last step was successful
        - "step_name.success": Specific step was successful
        - "cost < 10": Total cost under threshold
        """
        if not condition:
            return True

        if condition == "previous.success":
            prev = self.get_previous_result()
            return prev is not None and prev.success

        if ".success" in condition:
            step_name = condition.replace(".success", "")
            step = self.steps.get(step_name)
            return step is not None and step.status == StepStatus.COMPLETED

        if "cost" in condition:
            # Simple cost comparison
            try:
                if "<" in condition:
                    threshold = float(condition.split("<")[1].strip())
                    return self.total_cost < threshold
                elif ">" in condition:
                    threshold = float(condition.split(">")[1].strip())
                    return self.total_cost > threshold
            except (ValueError, IndexError):
                logger.warning(f"Invalid cost condition: {condition}")

        return True


@dataclass
class WorkflowResult:
    """Result of workflow execution."""
    workflow_name: str
    status: WorkflowStatus
    context: WorkflowContext
    total_cost: float
    execution_time: float
    completed_steps: int
    total_steps: int
    final_outputs: list[Path] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)

    @property
    def success(self) -> bool:
        """Check if workflow completed successfully."""
        return self.status == WorkflowStatus.COMPLETED


class WorkflowTemplate(ABC):
    """Abstract base class for workflow templates.

    Subclasses define specific workflows like:
    - ImageEnhancementWorkflow
    - VideoProductionWorkflow
    - StyleTransferWorkflow
    """

    def __init__(self, name: str | None = None):
        """Initialize workflow template.

        Args:
            name: Workflow name (defaults to class name)
        """
        self.name = name or self.__class__.__name__
        self._steps: list[WorkflowStep] = []

    @abstractmethod
    def define_steps(self, context: WorkflowContext) -> list[WorkflowStep]:
        """Define the workflow steps.

        Args:
            context: Workflow context with initial parameters

        Returns:
            List of workflow steps to execute
        """

    def validate(self, context: WorkflowContext) -> list[str]:
        """Validate the workflow can execute.

        Args:
            context: Workflow context

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Check required parameters
        if not context.initial_prompt:
            errors.append("Initial prompt is required")

        # Subclasses can add more validation
        return errors

    def estimate_cost(self, context: WorkflowContext) -> float:
        """Estimate total workflow cost.

        Args:
            context: Workflow context

        Returns:
            Estimated total cost in USD
        """
        # This is a simple estimate - executor will refine it
        steps = self.define_steps(context)
        total = 0.0

        for step in steps:
            # Basic estimation - providers will give more accurate costs
            if step.provider in ["leonardo", "firefly", "ideogram"]:
                total += 0.02  # ~$0.02 per image
            elif step.provider in ["magnific", "freepik"]:
                total += 0.05  # Upscaling typically costs more
            elif step.provider in ["google", "veo"]:
                total += 0.10  # Video generation costs more

        return total

    def get_description(self) -> str:
        """Get workflow description."""
        return self.__doc__ or f"{self.name} workflow"

    def get_required_providers(self) -> list[str]:
        """Get list of required providers."""
        # Extract from a sample run
        context = WorkflowContext(initial_prompt="test")
        steps = self.define_steps(context)
        return list(set(step.provider for step in steps))

    def cleanup(self, context: WorkflowContext):
        """Clean up temporary files.

        Args:
            context: Workflow context with temp files
        """
        for temp_file in context.temp_files:
            try:
                if temp_file.exists():
                    temp_file.unlink()
                    logger.debug(f"Cleaned up temp file: {temp_file}")
            except Exception as e:
                logger.warning(f"Failed to clean up {temp_file}: {e}")
