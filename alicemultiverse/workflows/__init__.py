"""Multi-modal workflow support for AliceMultiverse.

This module provides workflow templates for chaining AI operations like:
- Image generation → upscaling → variation
- Video generation → audio addition → enhancement
- Style transfer pipelines
- Multi-provider optimization
"""

from .base import (
    WorkflowTemplate,
    WorkflowStep,
    WorkflowContext,
    WorkflowResult,
    WorkflowStatus,
)
from .executor import WorkflowExecutor
from .registry import (
    WorkflowRegistry,
    get_workflow,
    list_workflows,
    register_workflow,
)

__all__ = [
    # Base classes
    "WorkflowTemplate",
    "WorkflowStep", 
    "WorkflowContext",
    "WorkflowResult",
    "WorkflowStatus",
    # Executor
    "WorkflowExecutor",
    # Registry
    "WorkflowRegistry",
    "get_workflow",
    "list_workflows",
    "register_workflow",
]