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


async def run_server(
    server: Server | None = None,
    transport: str = "stdio"
) -> None:
    """Run the MCP server.
    
    Args:
        server: Server instance (creates default if not provided)
        transport: Transport type (stdio, websocket, etc.)
    """
    if server is None:
        server = create_server()

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("Starting AliceMultiverse MCP server...")

    if transport == "stdio":
        # Run with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            init_options = InitializationOptions(
                server_name="alice-mcp",
                server_version="2.0.0"
            )

            await server.run(
                read_stream,
                write_stream,
                init_options
            )
    else:
        raise ValueError(f"Unsupported transport: {transport}")


def main():
    """Main entry point for MCP server."""
    try:
        asyncio.run(run_server())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.exception(f"Server error: {e}")
        raise


if __name__ == "__main__":
    main()
