"""Alice API - Simple interface for AI assistants.

This provides a clean, simple API that AI assistants can call.
All complexity is hidden behind natural language understanding.
"""

import asyncio
from typing import Any

from ..core.logging import get_logger
# from .alice_orchestrator import AliceOrchestrator  # Temporarily disabled

logger = get_logger(__name__)


# Stub implementations for backwards compatibility
async def ask_alice(message: str, project: str | None = None) -> dict[str, Any]:
    """Ask Alice a question - stub implementation."""
    return {"response": "Alice is not yet implemented", "status": "stub"}


def ask_alice_sync(message: str, project: str | None = None) -> dict[str, Any]:
    """Ask Alice a question synchronously - stub implementation."""
    return {"response": "Alice is not yet implemented", "status": "stub"}


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
        # self.orchestrator = AliceOrchestrator(project_id)  # Temporarily disabled
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
        # Temporarily return stub response
        return {
            "success": False,
            "message": "Alice orchestrator is temporarily disabled during restoration",
            "data": None,
            "suggestions": ["Use the structured interface or CLI instead"],
        }

    async def remember(self) -> dict[str, Any]:
        """Get Alice's memory of recent work.

        Returns:
            Dictionary with recent searches, creations, and patterns
        """
        return {
            "success": False,
            "message": "Alice orchestrator is temporarily disabled during restoration",
            "memory": {},
        }

    async def suggest(self) -> dict[str, Any]:
        """Get creative suggestions based on patterns.

        Returns:
            Dictionary with creative suggestions
        """
        return {
            "success": False,
            "message": "Alice orchestrator is temporarily disabled during restoration",
            "suggestions": [],
        }

    def save_context(self) -> bool:
        """Save current context for future sessions.

        Returns:
            Whether save was successful
        """
        # Temporarily return false
        return False


# Additional helper functions and MCP integration are temporarily disabled
# during the restoration process. The existing stub functions at the top
# of this file provide basic compatibility.
