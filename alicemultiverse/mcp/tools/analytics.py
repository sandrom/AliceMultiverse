"""Analytics MCP tools."""


from ...interface.analytics_mcp import (
    end_analytics_session,
    get_export_analytics,
    get_improvement_suggestions,
    get_performance_insights,
    start_analytics_session,
    track_export_event,
    track_user_action,
    track_workflow_event,
)


def register_analytics_tools(server) -> None:
    """Register analytics tools with MCP server.
    
    Args:
        server: MCP server instance
    """
    # Register each analytics function as a tool
    server.tool()(start_analytics_session)
    server.tool()(end_analytics_session)
    server.tool()(track_user_action)
    server.tool()(track_workflow_event)
    server.tool()(track_export_event)
    server.tool()(get_performance_insights)
    server.tool()(get_improvement_suggestions)
    server.tool()(get_export_analytics)
