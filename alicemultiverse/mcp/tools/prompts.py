"""Prompt management MCP tools."""


from ...prompts.mcp_tools import PromptMCPTools


def register_prompt_tools(server) -> None:
    """Register prompt management tools with MCP server.

    Args:
        server: MCP server instance
    """
    # Initialize prompt tools
    prompt_tools = PromptMCPTools()

    # Register each prompt tool
    server.tool()(prompt_tools.add_prompt)
    server.tool()(prompt_tools.search_prompts)
    server.tool()(prompt_tools.record_prompt_usage)
    server.tool()(prompt_tools.get_effective_prompts)
    server.tool()(prompt_tools.get_prompt_details)
    server.tool()(prompt_tools.update_prompt_rating)
    server.tool()(prompt_tools.find_similar_prompts)
    server.tool()(prompt_tools.analyze_prompt_patterns)
    server.tool()(prompt_tools.get_project_prompts)
    server.tool()(prompt_tools.sync_project_prompts)
