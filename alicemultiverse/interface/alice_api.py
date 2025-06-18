"""Alice API - Simple interface for AI assistants.

This provides a clean, simple API that AI assistants can call.
All complexity is hidden behind natural language understanding.
"""

import asyncio
from typing import Any

from ..core.logging import get_logger
from .alice_orchestrator import AliceOrchestrator

logger = get_logger(__name__)


class AliceAPI:
    """Simple API for AI assistants to interact with Alice.

    Example usage:
        alice = AliceAPI()

        # Natural language requests
        response = await alice.request("Find that cyberpunk character we made last month")
        response = await alice.request("Create a neon city scene in the same style")
        response = await alice.request("Remember what styles we've been using")
    """

    def __init__(self, project_id: str | None = None) -> None:
        """Initialize Alice API.

        Args:
            project_id: Optional project context to load
        """
        self.orchestrator = AliceOrchestrator(project_id)
        self.project_id = project_id

    async def request(self, message: str) -> dict[str, Any]:
        """Send a natural language request to Alice.

        This is the primary endpoint - just describe what you want.

        Args:
            message: Natural language request

        Returns:
            Dictionary with:
                - success: Whether request succeeded
                - message: Human-readable response
                - data: Any returned data (assets, context, etc.)
                - suggestions: Helpful next steps
        """
        try:
            # Let Alice understand and handle the request
            response = await self.orchestrator.understand(message)

            # Convert to simple dictionary
            return {
                "success": response.success,
                "message": response.message,
                "data": {"assets": response.assets, "context": response.context},
                "suggestions": response.suggestions,
            }

        except Exception as e:
            logger.error(f"Request failed: {e}")
            return {
                "success": False,
                "message": f"I encountered an error: {e!s}",
                "data": None,
                "suggestions": ["Try rephrasing your request"],
            }

    async def remember(self) -> dict[str, Any]:
        """Get Alice's memory of recent work.

        Returns:
            Dictionary with recent searches, creations, and patterns
        """
        response = await self.orchestrator.understand("What do you remember about our recent work?")
        return {
            "success": response.success,
            "message": response.message,
            "memory": response.context,
        }

    async def suggest(self) -> dict[str, Any]:
        """Get creative suggestions based on patterns.

        Returns:
            Dictionary with creative suggestions
        """
        response = await self.orchestrator.understand("What should we explore next?")
        return {
            "success": response.success,
            "message": response.message,
            "suggestions": response.suggestions,
        }

    def save_context(self) -> bool:
        """Save current context for future sessions.

        Returns:
            Whether save was successful
        """
        # Run async method in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(self.orchestrator.save_context())
        loop.close()
        return result


# Convenience functions for even simpler usage


async def ask_alice(message: str, project: str | None = None) -> dict[str, Any]:
    """One-line helper to ask Alice anything.

    Args:
        message: What you want to ask
        project: Optional project context

    Returns:
        Alice's response

    Example:
        result = await ask_alice("Find all the cyberpunk images from last week")
    """
    api = AliceAPI(project)
    return await api.request(message)


def ask_alice_sync(message: str, project: str | None = None) -> dict[str, Any]:
    """Synchronous version for non-async contexts.

    Args:
        message: What you want to ask
        project: Optional project context

    Returns:
        Alice's response

    Example:
        result = ask_alice_sync("Create a variation of the last image")
    """
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    result = loop.run_until_complete(ask_alice(message, project))
    loop.close()
    return result


# MCP (Model Context Protocol) Integration Helper


class AliceMCP:
    """Helper for MCP integration.

    This class provides MCP-compatible methods that can be exposed
    as tools to AI assistants like Claude.
    """

    def __init__(self, project_id: str | None = None) -> None:
        self.api = AliceAPI(project_id)

    def search(self, query: str) -> dict[str, Any]:
        """Search for assets using natural language.

        Args:
            query: Natural language search query

        Returns:
            Search results with assets and suggestions
        """
        return ask_alice_sync(f"Find {query}")

    def create(self, description: str) -> dict[str, Any]:
        """Create new content from description.

        Args:
            description: What to create

        Returns:
            Creation status and workflow information
        """
        return ask_alice_sync(f"Create {description}")

    def remember(self, topic: str = "recent work") -> dict[str, Any]:
        """Remember past work and context.

        Args:
            topic: What to remember about

        Returns:
            Memory and context information
        """
        return ask_alice_sync(f"Remember our {topic}")

    def organize(self, instruction: str = "media files") -> dict[str, Any]:
        """Organize assets based on instruction.

        Args:
            instruction: Organization instruction

        Returns:
            Organization status
        """
        return ask_alice_sync(f"Organize {instruction}")

    def explore(self, starting_point: str) -> dict[str, Any]:
        """Explore variations and related content.

        Args:
            starting_point: What to explore from

        Returns:
            Exploration results and suggestions
        """
        return ask_alice_sync(f"Explore variations of {starting_point}")
