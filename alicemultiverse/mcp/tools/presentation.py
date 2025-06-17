"""Presentation and timeline preview MCP tools."""


from ...interface.image_presentation_mcp import register_image_presentation_tools
from ...interface.multi_version_export_mcp import register_multi_version_export_tools
from ...interface.timeline_nlp_mcp import register_timeline_nlp_tools
from ...interface.timeline_preview_mcp import register_timeline_preview_tools


def register_presentation_tools(server) -> None:
    """Register presentation and preview tools with MCP server.
    
    Args:
        server: MCP server instance
    """
    # Image presentation
    register_image_presentation_tools(server)

    # Multi-version export
    register_multi_version_export_tools(server)

    # Timeline NLP
    register_timeline_nlp_tools(server)

    # Timeline preview
    register_timeline_preview_tools(server)
