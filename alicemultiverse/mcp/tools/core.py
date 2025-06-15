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
    
    @server.tool()
    async def organize_media(
        source_path: str | None = None,
        output_path: str | None = None,
        quality_assessment: bool = False,
        auto_tag: bool = True,
        understanding: bool = True
    ) -> dict[str, Any]:
        """
        Organize AI-generated media files into a structured directory layout.
        
        Parameters:
        - source_path: Source directory (uses configured inbox if not specified)
        - output_path: Output directory (uses configured organized if not specified)
        - quality_assessment: Enable quality assessment
        - auto_tag: Enable automatic tagging
        - understanding: Enable AI-powered image understanding
        
        Returns dictionary with:
        - processed: Number of files processed
        - organized: Number of files organized
        - errors: Any errors encountered
        """
        request = OrganizeRequest(
            source_path=source_path,
            output_path=output_path,
            quality_assessment=quality_assessment,
            auto_tag=auto_tag,
            pipeline=pipeline
        )
        
        result = alice.organize(request)
        return result.model_dump()
    
    @server.tool()
    async def update_tags(
        asset_ids: list[str],
        add_tags: list[str] | None = None,
        remove_tags: list[str] | None = None,
        set_tags: list[str] | None = None
    ) -> dict[str, Any]:
        """
        Update tags for one or more assets.
        
        Parameters:
        - asset_ids: List of asset content hashes
        - add_tags: Tags to add
        - remove_tags: Tags to remove
        - set_tags: Replace all tags with these (overrides add/remove)
        
        Returns success status and updated asset count.
        """
        request = TagRequest(
            asset_ids=asset_ids,
            add_tags=add_tags,
            remove_tags=remove_tags,
            set_tags=set_tags
        )
        
        result = alice.update_tags(request)
        return result.model_dump()
    
    @server.tool()
    async def get_asset_details(asset_id: str) -> dict[str, Any]:
        """
        Get detailed information about a specific asset.
        
        Parameters:
        - asset_id: Asset content hash
        
        Returns complete asset metadata including:
        - Basic info (path, size, type)
        - AI generation details
        - Tags and quality ratings
        - Understanding/analysis results
        """
        result = alice.get_asset(asset_id)
        return result.model_dump()
    
    @server.tool()
    async def soft_delete_assets(
        asset_ids: list[str],
        category: str = "general",
        reason: str | None = None
    ) -> dict[str, Any]:
        """
        Soft delete assets by moving them to sorted-out folder.
        
        Parameters:
        - asset_ids: List of asset content hashes to delete
        - category: Category for organization (e.g., "duplicates", "low_quality")
        - reason: Optional reason for deletion
        
        Returns status and moved file count.
        """
        from ...interface.models import SoftDeleteRequest
        
        request = SoftDeleteRequest(
            asset_ids=asset_ids,
            category=category,
            reason=reason
        )
        
        result = alice.soft_delete(request)
        return result.model_dump()