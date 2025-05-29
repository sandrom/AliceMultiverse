"""Alice Interface V2 - Migration layer that translates legacy calls to structured API."""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .alice_structured import AliceStructuredInterface
from .models import (
    AliceResponse,
    AssetInfo,
    GenerateRequest,
    GroupRequest,
    OrganizeRequest,
    ProjectContextRequest,
    SearchRequest,
    TagRequest,
)
from .structured_models import (
    AssetRole,
    DateRange,
    GenerationRequest as StructuredGenerationRequest,
    GroupingRequest,
    MediaType,
    OrganizeRequest as StructuredOrganizeRequest,
    SearchFilters,
    SearchRequest as StructuredSearchRequest,
    SortField,
    TagUpdateRequest,
)

logger = logging.getLogger(__name__)


class AliceInterface:
    """Legacy interface maintained for backward compatibility.
    
    This class translates natural language and legacy requests into
    structured API calls. New code should use AliceStructuredInterface directly.
    
    DEPRECATED: This interface will be removed in the next major version.
    Use AliceStructuredInterface for new implementations.
    """

    def __init__(self, config_path: Path | None = None):
        """Initialize Alice interface with structured backend.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.structured = AliceStructuredInterface(config_path)
        logger.warning(
            "AliceInterface is deprecated. Please migrate to AliceStructuredInterface "
            "for better performance and reliability."
        )

    def _parse_time_reference(self, time_ref: str) -> DateRange:
        """Parse natural language time references into date range.
        
        Args:
            time_ref: Natural language time like "last week", "yesterday"
            
        Returns:
            DateRange with start and optionally end dates
        """
        now = datetime.now()
        time_ref = time_ref.lower()
        
        if "yesterday" in time_ref:
            start = now - timedelta(days=1)
            return DateRange(
                start=start.replace(hour=0, minute=0, second=0).isoformat(),
                end=start.replace(hour=23, minute=59, second=59).isoformat()
            )
        elif "last week" in time_ref:
            start = now - timedelta(weeks=1)
            return DateRange(start=start.isoformat())
        elif "last month" in time_ref:
            start = now - timedelta(days=30)
            return DateRange(start=start.isoformat())
        elif "today" in time_ref:
            start = now.replace(hour=0, minute=0, second=0)
            return DateRange(
                start=start.isoformat(),
                end=now.replace(hour=23, minute=59, second=59).isoformat()
            )
        
        # Try to parse month names
        months = [
            "january", "february", "march", "april", "may", "june",
            "july", "august", "september", "october", "november", "december"
        ]
        for i, month in enumerate(months):
            if month in time_ref:
                # Assume current year
                month_start = datetime(now.year, i + 1, 1)
                # Calculate last day of month
                if i == 11:  # December
                    month_end = datetime(now.year + 1, 1, 1) - timedelta(days=1)
                else:
                    month_end = datetime(now.year, i + 2, 1) - timedelta(days=1)
                
                return DateRange(
                    start=month_start.isoformat(),
                    end=month_end.replace(hour=23, minute=59, second=59).isoformat()
                )
        
        # Default to last 7 days if we can't parse
        return DateRange(start=(now - timedelta(days=7)).isoformat())

    def _parse_description_to_filters(self, description: str) -> SearchFilters:
        """Attempt to extract structured filters from natural language.
        
        This is a simple implementation. In production, this would be
        handled by the AI assistant layer with proper NLP.
        
        Args:
            description: Natural language description
            
        Returns:
            Extracted search filters
        """
        filters = SearchFilters()
        desc_lower = description.lower()
        
        # Extract common style tags
        style_keywords = {
            "cyberpunk": ["cyberpunk", "cyber", "neon"],
            "fantasy": ["fantasy", "magical", "wizard", "elf"],
            "portrait": ["portrait", "face", "headshot"],
            "landscape": ["landscape", "scenery", "nature"],
            "anime": ["anime", "manga"],
            "photorealistic": ["photorealistic", "realistic", "photo"],
            "abstract": ["abstract"],
            "dark": ["dark", "noir", "gothic"],
            "bright": ["bright", "colorful", "vibrant"],
        }
        
        tags = []
        for tag, keywords in style_keywords.items():
            if any(keyword in desc_lower for keyword in keywords):
                tags.append(tag)
        
        if tags:
            filters["tags"] = tags
        
        # Extract quality references
        if any(word in desc_lower for word in ["high quality", "best", "excellent"]):
            filters["quality_rating"] = {"min": 4}
        elif any(word in desc_lower for word in ["low quality", "poor", "bad"]):
            filters["quality_rating"] = {"max": 2}
        
        # Extract media type
        if any(word in desc_lower for word in ["image", "picture", "photo"]):
            filters["media_type"] = MediaType.IMAGE
        elif any(word in desc_lower for word in ["video", "clip", "movie"]):
            filters["media_type"] = MediaType.VIDEO
        
        return filters

    def _simplify_asset_info(self, asset: Dict[str, Any]) -> AssetInfo:
        """Convert structured asset to legacy AssetInfo format.
        
        Args:
            asset: Structured asset data
            
        Returns:
            Legacy AssetInfo format
        """
        # Extract relationships from metadata
        relationships = {}
        metadata = asset.get("metadata", {})
        
        return AssetInfo(
            id=asset.get("content_hash", ""),
            filename=Path(asset.get("file_path", "")).name,
            prompt=metadata.get("prompt"),
            tags=asset.get("tags", []),
            quality_stars=int(asset.get("quality_rating", 0)) if asset.get("quality_rating") else None,
            role="wip",  # Default role
            created=asset.get("created_at", datetime.now().isoformat()),
            source=asset.get("ai_source", "unknown"),
            relationships=relationships,
        )

    def search_assets(self, request: SearchRequest, client_id: str = "default") -> AliceResponse:
        """Search for assets with legacy request format.
        
        Args:
            request: Legacy search request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with matching assets
        """
        try:
            # Build structured search request
            filters = SearchFilters()
            
            # Handle natural language description
            if request.get("description"):
                filters.update(self._parse_description_to_filters(request["description"]))
            
            # Handle time reference
            if request.get("time_reference"):
                filters["date_range"] = self._parse_time_reference(request["time_reference"])
            
            # Map legacy tag fields
            all_tags = []
            if request.get("style_tags"):
                all_tags.extend(request["style_tags"])
            if request.get("mood_tags"):
                all_tags.extend(request["mood_tags"])
            if request.get("subject_tags"):
                all_tags.extend(request["subject_tags"])
            
            if all_tags:
                # Merge with any tags from description parsing
                existing_tags = filters.get("tags", [])
                filters["tags"] = list(set(existing_tags + all_tags))
            
            # Map other filters
            if request.get("source_types"):
                filters["ai_source"] = request["source_types"]
            
            if request.get("min_quality_stars"):
                filters["quality_rating"] = {"min": float(request["min_quality_stars"])}
            
            # Map sort options
            sort_map = {
                "created": SortField.CREATED_DATE,
                "quality": SortField.QUALITY_RATING,
                "relevance": SortField.CREATED_DATE,  # Default to created date
            }
            sort_by = sort_map.get(request.get("sort_by", "created"), SortField.CREATED_DATE)
            
            # Create structured request
            structured_request = StructuredSearchRequest(
                filters=filters,
                sort_by=sort_by,
                limit=request.get("limit", 20),
            )
            
            # Execute structured search
            response = self.structured.search_assets(structured_request, client_id)
            
            # Convert response format if successful
            if response["success"] and response["data"]:
                search_data = response["data"]
                simplified_results = [
                    self._simplify_asset_info(asset) 
                    for asset in search_data.get("results", [])
                ]
                
                return AliceResponse(
                    success=True,
                    message=f"Found {len(simplified_results)} assets",
                    data=simplified_results,
                    error=None,
                )
            
            return response
            
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Search failed",
                data=None,
                error=str(e)
            )

    def organize_media(self, request: OrganizeRequest, client_id: str = "default") -> AliceResponse:
        """Organize media with legacy request format.
        
        Args:
            request: Legacy organization request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with organization results
        """
        try:
            # Convert to structured request
            structured_request = StructuredOrganizeRequest(
                source_path=request.get("source_path"),
                quality_assessment=request.get("quality_assessment"),
                pipeline=request.get("pipeline"),
                watch_mode=request.get("watch_mode"),
            )
            
            # Use structured interface
            return self.structured.organize_media(structured_request, client_id)
            
        except Exception as e:
            logger.error(f"Organization failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Organization failed",
                data=None,
                error=str(e)
            )

    def tag_assets(self, request: TagRequest, client_id: str = "default") -> AliceResponse:
        """Add tags to assets with legacy request format.
        
        Args:
            request: Legacy tagging request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response indicating success
        """
        try:
            # Collect all tags to add
            tags_to_add = []
            
            # The legacy interface uses a deprecated tag_type parameter
            # We'll just add all tags as custom tags
            tag_type = request.get("tag_type", "custom_tags")
            
            if tag_type == "style_tags" and request.get("style_tags"):
                tags_to_add.extend(request["style_tags"])
            elif tag_type == "mood_tags" and request.get("mood_tags"):
                tags_to_add.extend(request["mood_tags"])
            elif tag_type == "subject_tags" and request.get("subject_tags"):
                tags_to_add.extend(request["subject_tags"])
            elif tag_type == "custom_tags" and request.get("custom_tags"):
                tags_to_add.extend(request["custom_tags"])
            else:
                # Default: use any provided tags
                tags_to_add = request.get("tags", [])
            
            # Create structured request
            structured_request = TagUpdateRequest(
                asset_ids=request["asset_ids"],
                add_tags=tags_to_add,
            )
            
            # Use structured interface
            return self.structured.update_tags(structured_request, client_id)
            
        except Exception as e:
            logger.error(f"Tagging failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Tagging failed",
                data=None,
                error=str(e)
            )

    def group_assets(self, request: GroupRequest, client_id: str = "default") -> AliceResponse:
        """Group assets with legacy request format.
        
        Args:
            request: Legacy grouping request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response indicating success
        """
        try:
            # Convert to structured request
            structured_request = GroupingRequest(
                asset_ids=request["asset_ids"],
                group_name=request["group_name"],
            )
            
            # Use structured interface
            return self.structured.group_assets(structured_request, client_id)
            
        except Exception as e:
            logger.error(f"Grouping failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Grouping failed",
                data=None,
                error=str(e)
            )

    def generate_content(self, request: GenerateRequest, client_id: str = "default") -> AliceResponse:
        """Generate content with legacy request format.
        
        Args:
            request: Legacy generation request
            client_id: Client identifier for rate limiting
            
        Returns:
            Response with generation result
        """
        try:
            # Convert to structured request
            structured_request = StructuredGenerationRequest(
                prompt=request["prompt"],
                model=request.get("model"),
                parameters=request.get("parameters"),
                reference_assets=[request["style_reference"]] if request.get("style_reference") else None,
                project=request.get("project_id"),
                tags=request.get("tags"),
            )
            
            # Use structured interface
            return self.structured.generate_content(structured_request, client_id)
            
        except Exception as e:
            logger.error(f"Generation failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Generation failed",
                data=None,
                error=str(e)
            )

    def get_project_context(self, request: ProjectContextRequest) -> AliceResponse:
        """Get project context with legacy request format.
        
        This method is deprecated and returns minimal data.
        """
        return AliceResponse(
            success=True,
            message="Project context retrieved",
            data={
                "total_assets": 0,
                "recent_assets": [],
                "message": "This method is deprecated. Use structured API for project management."
            },
            error=None
        )

    def find_similar_assets(self, asset_id: str, threshold: float = 0.7) -> AliceResponse:
        """Find similar assets with legacy interface.
        
        This method is deprecated. Use search with appropriate filters instead.
        """
        return AliceResponse(
            success=False,
            message="Similarity search is deprecated",
            data=None,
            error="Use structured search with appropriate tag filters instead"
        )

    def set_asset_role(self, asset_id: str, role: str, client_id: str = "default") -> AliceResponse:
        """Set asset role with legacy string role.
        
        Args:
            asset_id: Asset identifier
            role: Role name as string
            client_id: Client identifier for rate limiting
            
        Returns:
            Response indicating success
        """
        try:
            # Convert string role to enum
            role_enum = AssetRole(role)
            
            # Use structured interface
            return self.structured.set_asset_role(asset_id, role_enum, client_id)
            
        except ValueError:
            return AliceResponse(
                success=False,
                message="Invalid role",
                data=None,
                error=f"Invalid role '{role}'. Valid roles: {[r.value for r in AssetRole]}"
            )
        except Exception as e:
            logger.error(f"Role setting failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Role setting failed",
                data=None,
                error=str(e)
            )