"""MCP tool modules."""

# Import all tool registration functions
from .analytics import register_analytics_tools
from .core import register_core_tools
from .cost import register_cost_tools
from .media import register_media_tools
from .memory import register_memory_tools
from .presentation import register_presentation_tools
from .projects import register_project_tools
from .prompts import register_prompt_tools
from .selections import register_selection_tools
from .video import register_video_tools
from .workflows import register_workflow_tools


def register_all_tools(server) -> None:
    """Register all MCP tools with the server.

    Args:
        server: MCP server instance
    """
    # Register each category of tools
    register_core_tools(server)
    register_analytics_tools(server)
    register_media_tools(server)
    register_video_tools(server)
    register_cost_tools(server)
    register_project_tools(server)
    register_selection_tools(server)
    register_memory_tools(server)
    register_presentation_tools(server)
    register_workflow_tools(server)
    register_prompt_tools(server)


__all__ = [
    "register_all_tools",
    "register_core_tools",
    "register_analytics_tools",
    "register_media_tools",
    "register_video_tools",
    "register_cost_tools",
    "register_project_tools",
    "register_selection_tools",
    "register_memory_tools",
    "register_presentation_tools",
    "register_workflow_tools",
    "register_prompt_tools",
]
