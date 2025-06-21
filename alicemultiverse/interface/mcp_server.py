"""MCP server interface for AliceMultiverse."""

from ..mcp_server import run_mcp_server as _run_mcp_server

# Re-export the main function
run_mcp_server = _run_mcp_server

__all__ = ["run_mcp_server"]