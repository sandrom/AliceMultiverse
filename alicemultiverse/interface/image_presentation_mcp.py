"""MCP tool wrappers for Image Presentation API."""

import json
from datetime import datetime
from typing import Any

from mcp.server import Server

from alicemultiverse.core.structured_logging import get_logger
from alicemultiverse.interface.image_presentation import ImagePresentationAPI, SoftDeleteCategory
from alicemultiverse.storage.unified_duckdb import DuckDBSearchCache

logger = get_logger(__name__)


def register_image_presentation_tools(server: Server, api: ImagePresentationAPI) -> None:
    """Register image presentation tools with MCP server.

    Args:
        server: MCP server instance
        api: Image Presentation API instance
    """

    @server.tool()
    async def search_images(
        query: str | None = None,
        tags: list[str] | None = None,
        similar_to: list[str] | None = None,
        exclude_tags: list[str] | None = None,
        exclude_folders: list[str] | None = None,
        limit: int = 20,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """Search and display images for user selection.

        Args:
            query: Natural language search query
            tags: Tags to search for
            similar_to: Image hashes to find similar images
            exclude_tags: Tags to exclude
            exclude_folders: Folders to exclude from search
            limit: Maximum results to return
            offset: Pagination offset

        Returns:
            List of images formatted for chat display
        """
        try:
            result = await api.search_images(
                query=query,
                tags=tags,
                similar_to=similar_to,
                exclude_tags=exclude_tags,
                exclude_folders=exclude_folders,
                limit=limit,
                offset=offset
            )

            # Convert to chat-friendly format
            response = result.to_chat_response()

            # Add metadata for Claude
            response["_metadata"] = {
                "tool": "search_images",
                "timestamp": datetime.now().isoformat(),
                "query": query or "all images",
                "total_results": result.total_count
            }

            return response

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return {
                "error": str(e),
                "images": [],
                "total": 0,
                "has_more": False
            }

    @server.tool()
    async def track_selection(
        image_hash: str,
        selected: bool,
        reason: str | None = None,
        session_id: str | None = None
    ) -> dict[str, Any]:
        """Track user's selection decision and reasoning.

        Args:
            image_hash: Hash of the selected/rejected image
            selected: Whether image was selected
            reason: User's reason for selection/rejection
            session_id: Optional session identifier

        Returns:
            Confirmation of tracking
        """
        try:
            await api.track_selection(
                image_hash=image_hash,
                selected=selected,
                reason=reason,
                session_id=session_id
            )

            return {
                "success": True,
                "message": f"Tracked {'selection' if selected else 'rejection'} for {image_hash}",
                "reason": reason
            }

        except Exception as e:
            logger.error(f"Failed to track selection: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @server.tool()
    async def soft_delete_image(
        image_hash: str,
        reason: str,
        category: str = "rejected"
    ) -> dict[str, Any]:
        """Move image to sorted-out folder.

        Args:
            image_hash: Hash of image to soft delete
            reason: Reason for deletion
            category: Category - rejected, broken, or maybe-later

        Returns:
            New path and confirmation
        """
        try:
            # Convert string to enum
            category_enum = SoftDeleteCategory(category)

            new_path = await api.soft_delete_image(
                image_hash=image_hash,
                reason=reason,
                category=category_enum
            )

            return {
                "success": True,
                "message": f"Moved image to {category} folder",
                "new_path": new_path,
                "reason": reason
            }

        except FileNotFoundError:
            return {
                "success": False,
                "error": f"Image not found: {image_hash}"
            }
        except Exception as e:
            logger.error(f"Failed to soft delete: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    @server.tool()
    async def get_selection_summary(
        session_id: str | None = None,
        selected_only: bool = True
    ) -> dict[str, Any]:
        """Get summary of selected images for the session.

        Args:
            session_id: Optional session identifier
            selected_only: Whether to include only selected images

        Returns:
            Summary of selections
        """
        try:
            # Read selection history
            selections = []

            if api.feedback_file.exists():
                with open(api.feedback_file) as f:
                    for line in f:
                        try:
                            record = json.loads(line.strip())
                            if session_id and record.get("session_id") != session_id:
                                continue
                            if selected_only and not record.get("selected"):
                                continue
                            selections.append(record)
                        except Exception:
                            continue

            # Group by selection status
            selected = [s for s in selections if s.get("selected")]
            rejected = [s for s in selections if not s.get("selected")]

            return {
                "session_id": session_id,
                "total_reviewed": len(selections),
                "selected_count": len(selected),
                "rejected_count": len(rejected),
                "selected_images": selected[:10],  # Limit to avoid huge responses
                "common_reasons": _get_common_reasons(selections)
            }

        except Exception as e:
            logger.error(f"Failed to get selection summary: {e}")
            return {
                "error": str(e),
                "total_reviewed": 0,
                "selected_count": 0,
                "rejected_count": 0
            }


def _get_common_reasons(selections: list[dict[str, Any]]) -> dict[str, int]:
    """Extract common reasons from selections."""
    reasons = {}
    for sel in selections:
        reason = sel.get("reason")
        if reason:
            # Simple keyword extraction
            keywords = reason.lower().split()
            for keyword in keywords:
                if len(keyword) > 3:  # Skip short words
                    reasons[keyword] = reasons.get(keyword, 0) + 1

    # Return top 5 reasons
    sorted_reasons = sorted(reasons.items(), key=lambda x: x[1], reverse=True)
    return dict(sorted_reasons[:5])


# Create default API instance for MCP server
def create_default_api() -> ImagePresentationAPI:
    """Create default Image Presentation API instance."""
    storage = DuckDBSearchCache()
    return ImagePresentationAPI(storage=storage)
