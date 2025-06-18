"""Memory and style learning MCP tools."""


from ...memory.style_memory_mcp import (
    analyze_style_patterns,
    end_style_workflow,
    export_style_profile,
    get_style_evolution,
    get_style_recommendations,
    import_style_profile,
    start_style_workflow,
    suggest_next_action,
    track_style_preference,
)


def register_memory_tools(server) -> None:
    """Register memory and style learning tools with MCP server.

    Args:
        server: MCP server instance
    """
    # Style memory tools
    server.tool()(start_style_workflow)
    server.tool()(end_style_workflow)
    server.tool()(track_style_preference)
    server.tool()(get_style_recommendations)
    server.tool()(analyze_style_patterns)
    server.tool()(get_style_evolution)
    server.tool()(suggest_next_action)
    server.tool()(export_style_profile)
    server.tool()(import_style_profile)
