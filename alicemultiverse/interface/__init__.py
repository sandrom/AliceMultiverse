"""Alice Interface - The primary interface for AI assistants."""

from .alice_api import AliceAPI, AliceMCP, ask_alice, ask_alice_sync
from .alice_interface import AliceInterface
from .alice_orchestrator import AliceOrchestrator, CreativeIntent, CreativeResponse
from .alice_structured import AliceStructuredInterface
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
from .structured_models import (
    AssetRole,
    DimensionFilter,
    GenerationRequest as StructuredGenerationRequest,
    GroupingRequest,
    MediaType,
    OrganizeRequest as StructuredOrganizeRequest,
    ProjectRequest,
    RangeFilter,
    SearchFilters,
    SearchRequest as StructuredSearchRequest,
    SearchResponse,
    SortField,
    SortOrder,
    TagUpdateRequest,
    WorkflowRequest,
)

__all__ = [
    # Legacy interface (deprecated)
    "AliceInterface",
    "AliceResponse",
    "SearchRequest",
    "GenerateRequest",
    "OrganizeRequest",
    "TagRequest",
    "GroupRequest",
    # Structured interface (recommended)
    "AliceStructuredInterface",
    "AssetRole",
    "DimensionFilter",
    "GroupingRequest",
    "MediaType",
    "ProjectRequest",
    "RangeFilter",
    "SearchFilters",
    "SearchResponse",
    "SortField",
    "SortOrder",
    "StructuredGenerationRequest",
    "StructuredOrganizeRequest",
    "StructuredSearchRequest",
    "TagUpdateRequest",
    "WorkflowRequest",
    # New orchestrator
    "AliceOrchestrator",
    "CreativeIntent",
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
