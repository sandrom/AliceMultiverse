"""Alice Interface - The primary interface for AI assistants."""

from .alice_api import AliceAPI, AliceMCP, ask_alice, ask_alice_sync
from .alice_interface import AliceInterface
from .alice_orchestrator import AliceOrchestrator, CreativeResponse
from .creative_models import (
    CreativeAsset,
    CreativeContext,
    CreativeMood,
    CreativeRole,
    CreativeWorkflow,
    WorkflowPhase,
)
from .models import (
    AliceResponse,
    GenerateRequest,
    GroupRequest,
    OrganizeRequest,
    SearchRequest,
    TagRequest,
)

__all__ = [
    # Legacy interface
    "AliceInterface",
    "AliceResponse",
    "SearchRequest",
    "GenerateRequest",
    "OrganizeRequest",
    "TagRequest",
    "GroupRequest",
    # New orchestrator
    "AliceOrchestrator",
    "CreativeResponse",
    "AliceAPI",
    "ask_alice",
    "ask_alice_sync",
    "AliceMCP",
    # Creative models
    "CreativeContext",
    "CreativeAsset",
    "CreativeWorkflow",
    "CreativeRole",
    "CreativeMood",
    "WorkflowPhase",
]
