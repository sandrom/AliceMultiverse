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


# TODO: Review unreachable code - # Convenience functions for even simpler usage


# TODO: Review unreachable code - async def ask_alice(message: str, project: str | None = None) -> dict[str, Any]:
# TODO: Review unreachable code - """One-line helper to ask Alice anything.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - message: What you want to ask
# TODO: Review unreachable code - project: Optional project context

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Alice's response

# TODO: Review unreachable code - Example:
# TODO: Review unreachable code - result = await ask_alice("Find all the cyberpunk images from last week")
# TODO: Review unreachable code - """
# TODO: Review unreachable code - api = AliceAPI(project)
# TODO: Review unreachable code - return await api.request(message)


# TODO: Review unreachable code - def ask_alice_sync(message: str, project: str | None = None) -> dict[str, Any]:
# TODO: Review unreachable code - """Synchronous version for non-async contexts.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - message: What you want to ask
# TODO: Review unreachable code - project: Optional project context

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Alice's response

# TODO: Review unreachable code - Example:
# TODO: Review unreachable code - result = ask_alice_sync("Create a variation of the last image")
# TODO: Review unreachable code - """
# TODO: Review unreachable code - loop = asyncio.new_event_loop()
# TODO: Review unreachable code - asyncio.set_event_loop(loop)
# TODO: Review unreachable code - result = loop.run_until_complete(ask_alice(message, project))
# TODO: Review unreachable code - loop.close()
# TODO: Review unreachable code - return result


# TODO: Review unreachable code - # MCP (Model Context Protocol) Integration Helper


# TODO: Review unreachable code - class AliceMCP:
# TODO: Review unreachable code - """Helper for MCP integration.

# TODO: Review unreachable code - This class provides MCP-compatible methods that can be exposed
# TODO: Review unreachable code - as tools to AI assistants like Claude.
# TODO: Review unreachable code - """

# TODO: Review unreachable code - def __init__(self, project_id: str | None = None) -> None:
# TODO: Review unreachable code - self.api = AliceAPI(project_id)

# TODO: Review unreachable code - def search(self, query: str) -> dict[str, Any]:
# TODO: Review unreachable code - """Search for assets using natural language.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - query: Natural language search query

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Search results with assets and suggestions
# TODO: Review unreachable code - """
# TODO: Review unreachable code - return ask_alice_sync(f"Find {query}")

# TODO: Review unreachable code - def create(self, description: str) -> dict[str, Any]:
# TODO: Review unreachable code - """Create new content from description.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - description: What to create

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Creation status and workflow information
# TODO: Review unreachable code - """
# TODO: Review unreachable code - return ask_alice_sync(f"Create {description}")

# TODO: Review unreachable code - def remember(self, topic: str = "recent work") -> dict[str, Any]:
# TODO: Review unreachable code - """Remember past work and context.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - topic: What to remember about

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Memory and context information
# TODO: Review unreachable code - """
# TODO: Review unreachable code - return ask_alice_sync(f"Remember our {topic}")

# TODO: Review unreachable code - def organize(self, instruction: str = "media files") -> dict[str, Any]:
# TODO: Review unreachable code - """Organize assets based on instruction.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - instruction: Organization instruction

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Organization status
# TODO: Review unreachable code - """
# TODO: Review unreachable code - return ask_alice_sync(f"Organize {instruction}")

# TODO: Review unreachable code - def explore(self, starting_point: str) -> dict[str, Any]:
# TODO: Review unreachable code - """Explore variations and related content.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - starting_point: What to explore from

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Exploration results and suggestions
# TODO: Review unreachable code - """
# TODO: Review unreachable code - return ask_alice_sync(f"Explore variations of {starting_point}")
