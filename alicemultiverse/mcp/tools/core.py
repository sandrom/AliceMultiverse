"""Core MCP tools for search and organization."""

from typing import Any

from ...interface import AliceInterface
from ...interface.models import OrganizeRequest, SearchRequest, TagRequest


def register_core_tools(server) -> None:
    """Register core Alice tools with MCP server.

    Args:
        server: MCP server instance
    """
    alice = AliceInterface()

    @server.tool()
    async def search_assets(
        description: str | None = None,
        style_tags: list[str] | None = None,
        mood_tags: list[str] | None = None,
        subject_tags: list[str] | None = None,
        time_reference: str | None = None,
        min_quality_stars: int | None = None,
        media_type: str | None = None,
        ai_source: str | None = None,
        limit: int = 50
    ) -> dict[str, Any]:
        """
        Search for AI-generated assets using natural language or structured queries.

        Parameters:
        - description: Natural language description of what you're looking for
        - style_tags: Specific style tags (e.g., ["cyberpunk", "minimalist"])
        - mood_tags: Mood/emotion tags (e.g., ["dramatic", "peaceful"])
        - subject_tags: Subject matter tags (e.g., ["portrait", "landscape"])
        - time_reference: Time reference (e.g., "today", "last week", "2024-01")
        - min_quality_stars: Minimum quality rating (1-5)
        - media_type: Filter by type ("image", "video", "document")
        - ai_source: Filter by AI source (e.g., "midjourney", "flux")
        - limit: Maximum number of results (default: 50)

        Returns dictionary with:
        - assets: List of matching assets
        - total_count: Total number of matches
        - facets: Available filter options
        """
        # Convert parameters to SearchRequest
        request = SearchRequest(
            query=description,
            filters={
                "style_tags": style_tags,
                "mood_tags": mood_tags,
                "subject_tags": subject_tags,
                "min_quality": min_quality_stars,
                "media_type": media_type,
                "ai_source": ai_source,
            },
            time_filter=time_reference,
            limit=limit
        )

        result = alice.search(request)
        return result.model_dump()

    # TODO: Review unreachable code - @server.tool()
    # TODO: Review unreachable code - async def organize_media(
    # TODO: Review unreachable code - source_path: str | None = None,
    # TODO: Review unreachable code - output_path: str | None = None,
    # TODO: Review unreachable code - quality_assessment: bool = False,
    # TODO: Review unreachable code - auto_tag: bool = True,
    # TODO: Review unreachable code - understanding: bool = True
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Organize AI-generated media files into a structured directory layout.

    # TODO: Review unreachable code - Parameters:
    # TODO: Review unreachable code - - source_path: Source directory (uses configured inbox if not specified)
    # TODO: Review unreachable code - - output_path: Output directory (uses configured organized if not specified)
    # TODO: Review unreachable code - - quality_assessment: Enable quality assessment
    # TODO: Review unreachable code - - auto_tag: Enable automatic tagging
    # TODO: Review unreachable code - - understanding: Enable AI-powered image understanding

    # TODO: Review unreachable code - Returns dictionary with:
    # TODO: Review unreachable code - - processed: Number of files processed
    # TODO: Review unreachable code - - organized: Number of files organized
    # TODO: Review unreachable code - - errors: Any errors encountered
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - request = OrganizeRequest(
    # TODO: Review unreachable code - source_path=source_path,
    # TODO: Review unreachable code - quality_assessment=quality_assessment,
    # TODO: Review unreachable code - understanding=understanding
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - result = alice.organize(request)
    # TODO: Review unreachable code - return result.model_dump()

    # TODO: Review unreachable code - @server.tool()
    # TODO: Review unreachable code - async def update_tags(
    # TODO: Review unreachable code - asset_ids: list[str],
    # TODO: Review unreachable code - add_tags: list[str] | None = None,
    # TODO: Review unreachable code - remove_tags: list[str] | None = None,
    # TODO: Review unreachable code - set_tags: list[str] | None = None
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Update tags for one or more assets.

    # TODO: Review unreachable code - Parameters:
    # TODO: Review unreachable code - - asset_ids: List of asset content hashes
    # TODO: Review unreachable code - - add_tags: Tags to add
    # TODO: Review unreachable code - - remove_tags: Tags to remove
    # TODO: Review unreachable code - - set_tags: Replace all tags with these (overrides add/remove)

    # TODO: Review unreachable code - Returns success status and updated asset count.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - request = TagRequest(
    # TODO: Review unreachable code - asset_ids=asset_ids,
    # TODO: Review unreachable code - add_tags=add_tags,
    # TODO: Review unreachable code - remove_tags=remove_tags,
    # TODO: Review unreachable code - set_tags=set_tags
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - result = alice.update_tags(request)
    # TODO: Review unreachable code - return result.model_dump()

    # TODO: Review unreachable code - @server.tool()
    # TODO: Review unreachable code - async def get_asset_details(asset_id: str) -> dict[str, Any]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Get detailed information about a specific asset.

    # TODO: Review unreachable code - Parameters:
    # TODO: Review unreachable code - - asset_id: Asset content hash

    # TODO: Review unreachable code - Returns complete asset metadata including:
    # TODO: Review unreachable code - - Basic info (path, size, type)
    # TODO: Review unreachable code - - AI generation details
    # TODO: Review unreachable code - - Tags and quality ratings
    # TODO: Review unreachable code - - Understanding/analysis results
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - result = alice.get_asset(asset_id)
    # TODO: Review unreachable code - return result.model_dump()

    # TODO: Review unreachable code - @server.tool()
    # TODO: Review unreachable code - async def soft_delete_assets(
    # TODO: Review unreachable code - asset_ids: list[str],
    # TODO: Review unreachable code - category: str = "general",
    # TODO: Review unreachable code - reason: str | None = None
    # TODO: Review unreachable code - ) -> dict[str, Any]:
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - Soft delete assets by moving them to sorted-out folder.

    # TODO: Review unreachable code - Parameters:
    # TODO: Review unreachable code - - asset_ids: List of asset content hashes to delete
    # TODO: Review unreachable code - - category: Category for organization (e.g., "duplicates", "low_quality")
    # TODO: Review unreachable code - - reason: Optional reason for deletion

    # TODO: Review unreachable code - Returns status and moved file count.
    # TODO: Review unreachable code - """
    # TODO: Review unreachable code - from ...interface.models import SoftDeleteRequest

    # TODO: Review unreachable code - request = SoftDeleteRequest(
    # TODO: Review unreachable code - asset_ids=asset_ids,
    # TODO: Review unreachable code - category=category,
    # TODO: Review unreachable code - reason=reason
    # TODO: Review unreachable code - )

    # TODO: Review unreachable code - result = alice.soft_delete(request)
    # TODO: Review unreachable code - return result.model_dump()
