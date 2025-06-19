"""Main MCP server implementation."""

import asyncio
import logging

from mcp import Resource
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.server.stdio import stdio_server

from .tools import register_all_tools

logger = logging.getLogger(__name__)


def create_server(name: str = "alice-mcp") -> Server:
    """Create and configure the MCP server.

    Args:
        name: Server name

    Returns:
        Configured MCP server instance
    """
    # Create server
    server = Server(name)

    # Register all tool groups
    logger.info("Registering MCP tools...")
    register_all_tools(server)

    logger.info(f"Registered {len(server._tools)} tools")

    # Set up initialization handler
    @server.list_resources()
    async def handle_list_resources() -> list[Resource]:
        """List available resources."""
        return [
            Resource(
                uri="alice://projects",
                name="Alice Projects",
                description="Access to Alice project management"
            ),
            Resource(
                uri="alice://selections",
                name="Quick Selections",
                description="Access to quick marks and selections"
            ),
            Resource(
                uri="alice://costs",
                name="Cost Tracking",
                description="API cost tracking and budgets"
            )
        ]

    return server


# TODO: Review unreachable code - async def run_server(
# TODO: Review unreachable code - server: Server | None = None,
# TODO: Review unreachable code - transport: str = "stdio"
# TODO: Review unreachable code - ) -> None:
# TODO: Review unreachable code - """Run the MCP server.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - server: Server instance (creates default if not provided)
# TODO: Review unreachable code - transport: Transport type (stdio, websocket, etc.)
# TODO: Review unreachable code - """
# TODO: Review unreachable code - if server is None:
# TODO: Review unreachable code - server = create_server()

# TODO: Review unreachable code - # Configure logging
# TODO: Review unreachable code - logging.basicConfig(
# TODO: Review unreachable code - level=logging.INFO,
# TODO: Review unreachable code - format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
# TODO: Review unreachable code - )

# TODO: Review unreachable code - logger.info("Starting AliceMultiverse MCP server...")

# TODO: Review unreachable code - if transport == "stdio":
# TODO: Review unreachable code - # Run with stdio transport
# TODO: Review unreachable code - async with stdio_server() as (read_stream, write_stream):
# TODO: Review unreachable code - init_options = InitializationOptions(
# TODO: Review unreachable code - server_name="alice-mcp",
# TODO: Review unreachable code - server_version="2.0.0"
# TODO: Review unreachable code - )

# TODO: Review unreachable code - await server.run(
# TODO: Review unreachable code - read_stream,
# TODO: Review unreachable code - write_stream,
# TODO: Review unreachable code - init_options
# TODO: Review unreachable code - )
# TODO: Review unreachable code - else:
# TODO: Review unreachable code - raise ValueError(f"Unsupported transport: {transport}")


# TODO: Review unreachable code - def main():
# TODO: Review unreachable code - """Main entry point for MCP server."""
# TODO: Review unreachable code - try:
# TODO: Review unreachable code - asyncio.run(run_server())
# TODO: Review unreachable code - except KeyboardInterrupt:
# TODO: Review unreachable code - logger.info("Server stopped by user")
# TODO: Review unreachable code - except Exception as e:
# TODO: Review unreachable code - logger.exception(f"Server error: {e}")
# TODO: Review unreachable code - raise


# TODO: Review unreachable code - if __name__ == "__main__":
# TODO: Review unreachable code - main()
