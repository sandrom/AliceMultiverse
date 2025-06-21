#!/usr/bin/env python3
"""MCP (Model Context Protocol) server for AliceMultiverse.

This server provides AI assistants with tools to interact with Alice's
media organization and creative workflow capabilities.
"""

import asyncio
import json
import logging
import sys
from typing import Any, Dict, List, Optional

try:
    from mcp import Server, Tool, Resource
    from mcp.server.stdio import stdio_server
    MCP_AVAILABLE = True
except ImportError:
    MCP_AVAILABLE = False
    Server = None
    Tool = None
    Resource = None
    stdio_server = None

from .interface import AliceInterface
from .interface.models import (
    OrganizeRequest,
    SearchRequest,
    SearchResponse,
    TagUpdateRequest,
)

logger = logging.getLogger(__name__)

# Global Alice instance
alice: Optional[AliceInterface] = None


def get_alice() -> AliceInterface:
    """Get or create Alice interface instance."""
    global alice
    if alice is None:
        alice = AliceInterface()
    return alice


async def search_assets(query: str, **kwargs) -> Dict[str, Any]:
    """Search for assets using natural language or structured queries."""
    interface = get_alice()
    
    request = SearchRequest(
        query=query,
        media_types=kwargs.get("media_types"),
        tags=kwargs.get("tags"),
        date_range=kwargs.get("date_range"),
        limit=kwargs.get("limit", 20),
    )
    
    response = await interface.search_assets(request)
    return response.model_dump()


async def organize_media(inbox_path: Optional[str] = None, **kwargs) -> Dict[str, Any]:
    """Organize media files from inbox to organized structure."""
    interface = get_alice()
    
    request = OrganizeRequest(
        inbox_path=inbox_path,
        dry_run=kwargs.get("dry_run", False),
        watch_mode=kwargs.get("watch_mode", False),
        understanding_enabled=kwargs.get("understanding_enabled", False),
    )
    
    stats = await interface.organize_media(request)
    return stats


async def update_tags(content_hash: str, **kwargs) -> Dict[str, Any]:
    """Update tags for an asset."""
    interface = get_alice()
    
    request = TagUpdateRequest(
        content_hash=content_hash,
        add_tags=kwargs.get("add_tags", []),
        remove_tags=kwargs.get("remove_tags", []),
        set_tags=kwargs.get("set_tags"),
    )
    
    success = await interface.update_tags(request)
    return {"success": success}


def create_mcp_server() -> Optional[Server]:
    """Create and configure the MCP server."""
    if not MCP_AVAILABLE:
        logger.error("MCP package not available. Install with: pip install mcp")
        return None
    
    server = Server("alice-multiverse")
    
    # Register tools
    server.add_tool(Tool(
        name="search_assets",
        description="Search for media assets using natural language or structured queries",
        input_schema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Natural language search query or structured query"
                },
                "media_types": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by media types (image, video)"
                },
                "tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Filter by tags"
                },
                "limit": {
                    "type": "integer",
                    "description": "Maximum number of results",
                    "default": 20
                }
            },
            "required": ["query"]
        },
        handler=search_assets
    ))
    
    server.add_tool(Tool(
        name="organize_media",
        description="Organize media files from inbox to structured folders",
        input_schema={
            "type": "object",
            "properties": {
                "inbox_path": {
                    "type": "string",
                    "description": "Path to inbox folder (uses default if not specified)"
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview changes without moving files",
                    "default": False
                },
                "understanding_enabled": {
                    "type": "boolean",
                    "description": "Enable AI understanding for content analysis",
                    "default": False
                }
            }
        },
        handler=organize_media
    ))
    
    server.add_tool(Tool(
        name="update_tags",
        description="Update tags for a media asset",
        input_schema={
            "type": "object",
            "properties": {
                "content_hash": {
                    "type": "string",
                    "description": "Content hash of the asset"
                },
                "add_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to add"
                },
                "remove_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Tags to remove"
                },
                "set_tags": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Replace all tags with these"
                }
            },
            "required": ["content_hash"]
        },
        handler=update_tags
    ))
    
    return server


def run_mcp_server_sync(**kwargs) -> int:
    """Run the MCP server (synchronous wrapper)."""
    return asyncio.run(run_mcp_server_async(**kwargs))


async def run_mcp_server_async(**kwargs) -> int:
    """Run the MCP server asynchronously."""
    if not MCP_AVAILABLE:
        print("Error: MCP package not available. Install with: pip install mcp", file=sys.stderr)
        return 1
    
    server = create_mcp_server()
    if server is None:
        return 1
    
    # Run with stdio transport by default
    transport = kwargs.get("transport", "stdio")
    
    if transport == "stdio":
        async with stdio_server() as (read_stream, write_stream):
            await server.run(read_stream, write_stream)
    else:
        print(f"Error: Unsupported transport: {transport}", file=sys.stderr)
        return 1
    
    return 0


# For backward compatibility
def run_mcp_server(**kwargs) -> int:
    """Run the MCP server."""
    return run_mcp_server_sync(**kwargs)