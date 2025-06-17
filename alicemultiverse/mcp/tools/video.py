"""Video-related MCP tools."""


from ...interface.video_creation_mcp import register_video_creation_tools
from ...interface.video_providers_mcp import register_video_providers_tools
from ...workflows.templates.template_mcp import (
    create_documentary_video,
    create_instagram_reel,
    create_social_media_video,
    create_story_arc_video,
    create_tiktok_video,
    get_platform_specifications,
    suggest_story_structure,
)


def register_video_tools(server) -> None:
    """Register video creation and processing tools with MCP server.
    
    Args:
        server: MCP server instance
    """
    # Video creation tools
    register_video_creation_tools(server)

    # Video provider tools
    register_video_providers_tools(server)

    # Template-based video creation
    server.tool()(create_social_media_video)
    server.tool()(create_instagram_reel)
    server.tool()(create_tiktok_video)
    server.tool()(create_documentary_video)
    server.tool()(create_story_arc_video)
    server.tool()(get_platform_specifications)
    server.tool()(suggest_story_structure)
