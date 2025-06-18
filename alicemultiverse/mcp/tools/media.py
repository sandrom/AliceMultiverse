"""Media-related MCP tools (composition, deduplication, variations)."""


from ...interface.broll_suggestions_mcp import register_broll_tools
from ...interface.composition_mcp import (
    analyze_image_composition,
    analyze_timeline_compositions,
    analyze_timeline_flow,
    detect_composition_patterns,
    optimize_timeline,
    suggest_clip_order,
)
from ...interface.deduplication_mcp import register_deduplication_tools
from ...interface.variation_mcp import (
    analyze_variation_success,
    create_variation_group,
    export_variation_analytics,
    find_top_variations,
    generate_content_variations,
    get_variation_insights,
    get_variation_recommendations,
    track_variation_performance,
)


def register_media_tools(server) -> None:
    """Register media processing tools with MCP server.

    Args:
        server: MCP server instance
    """
    # B-roll suggestions
    register_broll_tools(server)

    # Composition analysis
    server.tool()(analyze_image_composition)
    server.tool()(analyze_timeline_compositions)
    server.tool()(analyze_timeline_flow)
    server.tool()(detect_composition_patterns)
    server.tool()(optimize_timeline)
    server.tool()(suggest_clip_order)

    # Deduplication
    register_deduplication_tools(server)

    # Variations
    server.tool()(generate_content_variations)
    server.tool()(create_variation_group)
    server.tool()(analyze_variation_success)
    server.tool()(get_variation_insights)
    server.tool()(track_variation_performance)
    server.tool()(find_top_variations)
    server.tool()(get_variation_recommendations)
    server.tool()(export_variation_analytics)
