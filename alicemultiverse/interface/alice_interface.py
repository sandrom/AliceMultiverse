"""Alice Interface - The intelligent orchestration layer for AI assistants."""

import logging
from typing import List, Dict, Optional, Any
from datetime import datetime, timedelta
from pathlib import Path

from ..organizer.enhanced_organizer import EnhancedMediaOrganizer
from ..core.config import load_config
from ..metadata.models import SearchQuery, AssetRole
from .models import (
    AliceResponse, SearchRequest, GenerateRequest, 
    OrganizeRequest, TagRequest, GroupRequest,
    ProjectContextRequest, AssetInfo
)


logger = logging.getLogger(__name__)


class AliceInterface:
    """Primary interface for AI assistants to interact with AliceMultiverse.
    
    This class provides high-level functions that AI can call using natural
    language concepts, while Alice handles all technical complexity.
    """
    
    def __init__(self, config_path: Optional[Path] = None):
        """Initialize Alice interface.
        
        Args:
            config_path: Optional path to configuration file
        """
        self.config = load_config(config_path)
        self.config.enhanced_metadata = True  # Always use enhanced metadata
        self.organizer = None
        self._ensure_organizer()
    
    def _ensure_organizer(self):
        """Ensure organizer is initialized."""
        if not self.organizer:
            self.organizer = EnhancedMediaOrganizer(self.config)
    
    def _parse_time_reference(self, time_ref: str) -> Optional[datetime]:
        """Parse natural language time references.
        
        Args:
            time_ref: Natural language time like "last week", "yesterday"
            
        Returns:
            Datetime object or None
        """
        now = datetime.now()
        time_ref = time_ref.lower()
        
        if "yesterday" in time_ref:
            return now - timedelta(days=1)
        elif "last week" in time_ref:
            return now - timedelta(weeks=1)
        elif "last month" in time_ref:
            return now - timedelta(days=30)
        elif "today" in time_ref:
            return now.replace(hour=0, minute=0, second=0)
        
        # Try to parse month names
        months = ["january", "february", "march", "april", "may", "june",
                 "july", "august", "september", "october", "november", "december"]
        for i, month in enumerate(months):
            if month in time_ref:
                # Assume current year
                return datetime(now.year, i+1, 1)
        
        return None
    
    def _simplify_asset_info(self, asset: Dict) -> AssetInfo:
        """Convert full metadata to simplified info for AI.
        
        Args:
            asset: Full asset metadata
            
        Returns:
            Simplified asset information
        """
        # Combine all tags
        all_tags = (
            asset.get('style_tags', []) +
            asset.get('mood_tags', []) +
            asset.get('subject_tags', []) +
            asset.get('custom_tags', [])
        )
        
        # Build relationships
        relationships = {}
        if asset.get('parent_id'):
            relationships['parent'] = [asset['parent_id']]
        if asset.get('similar_to'):
            relationships['similar'] = asset['similar_to']
        if asset.get('grouped_with'):
            relationships['grouped'] = asset['grouped_with']
        
        return AssetInfo(
            id=asset['asset_id'],
            filename=asset['file_name'],
            prompt=asset.get('prompt'),
            tags=all_tags,
            quality_stars=asset.get('quality_stars'),
            role=asset.get('role', AssetRole.WIP).value if hasattr(asset.get('role'), 'value') else str(asset.get('role', 'wip')),
            created=asset.get('created_at', datetime.now()).isoformat(),
            source=asset.get('source_type', 'unknown'),
            relationships=relationships
        )
    
    # === Core Functions for AI ===
    
    def search_assets(self, request: SearchRequest) -> AliceResponse:
        """Search for assets based on creative criteria.
        
        This is the primary way AI finds existing assets.
        
        Args:
            request: Search request with criteria
            
        Returns:
            Response with matching assets
        """
        try:
            self._ensure_organizer()
            
            # Build search query
            query_params = {}
            
            # Handle natural language description
            if request.get('description'):
                # Use description search first
                results = self.organizer.search_engine.search_by_description(
                    request['description'], 
                    limit=request.get('limit', 20)
                )
            else:
                # Build structured query
                if request.get('time_reference'):
                    start_time = self._parse_time_reference(request['time_reference'])
                    if start_time:
                        query_params['timeframe_start'] = start_time
                
                # Add tag filters
                if request.get('style_tags'):
                    query_params['style_tags'] = request['style_tags']
                if request.get('mood_tags'):
                    query_params['mood_tags'] = request['mood_tags']
                if request.get('subject_tags'):
                    query_params['subject_tags'] = request['subject_tags']
                
                # Add other filters
                if request.get('source_types'):
                    query_params['source_types'] = request['source_types']
                if request.get('min_quality_stars'):
                    query_params['min_stars'] = request['min_quality_stars']
                if request.get('roles'):
                    query_params['roles'] = [AssetRole(r) for r in request['roles']]
                
                # Add options
                query_params['sort_by'] = request.get('sort_by', 'relevance')
                query_params['limit'] = request.get('limit', 20)
                
                # Execute search
                results = self.organizer.search_assets(**query_params)
            
            # Simplify results for AI
            simplified_results = [self._simplify_asset_info(asset) for asset in results]
            
            return AliceResponse(
                success=True,
                message=f"Found {len(results)} assets",
                data=simplified_results,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return AliceResponse(
                success=False,
                message="Search failed",
                data=None,
                error=str(e)
            )
    
    def generate_content(self, request: GenerateRequest) -> AliceResponse:
        """Generate new content based on prompt and references.
        
        This is a placeholder for future implementation when generation
        capabilities are added.
        
        Args:
            request: Generation request
            
        Returns:
            Response with generation result
        """
        try:
            # This would integrate with fal.ai, ComfyUI, etc.
            # For now, return a placeholder response
            
            return AliceResponse(
                success=False,
                message="Content generation not yet implemented",
                data=None,
                error="This feature will be implemented when generation services are integrated"
            )
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return AliceResponse(
                success=False,
                message="Generation failed",
                data=None,
                error=str(e)
            )
    
    def organize_media(self, request: OrganizeRequest) -> AliceResponse:
        """Organize media files with optional enhancements.
        
        Args:
            request: Organization request
            
        Returns:
            Response with organization results
        """
        try:
            # Update config based on request
            if request.get('source_path'):
                self.config.paths.inbox = request['source_path']
            if request.get('quality_assessment'):
                self.config.processing.quality = True
            if request.get('pipeline'):
                self.config.pipeline.mode = request['pipeline']
            if request.get('watch_mode'):
                self.config.processing.watch = True
            
            # Recreate organizer with updated config
            self.organizer = EnhancedMediaOrganizer(self.config)
            
            # Run organization
            success = self.organizer.organize()
            
            # Get summary
            summary = self.organizer.get_organization_summary()
            
            return AliceResponse(
                success=success,
                message=summary,
                data={
                    'stats': self.organizer.stats,
                    'metadata_count': len(self.organizer.metadata_cache.get_all_metadata())
                },
                error=None
            )
            
        except Exception as e:
            logger.error(f"Organization failed: {e}")
            return AliceResponse(
                success=False,
                message="Organization failed",
                data=None,
                error=str(e)
            )
    
    def tag_assets(self, request: TagRequest) -> AliceResponse:
        """Add tags to assets.
        
        Args:
            request: Tagging request
            
        Returns:
            Response indicating success
        """
        try:
            self._ensure_organizer()
            
            tag_type = request.get('tag_type', 'custom_tags')
            success_count = 0
            
            for asset_id in request['asset_ids']:
                if self.organizer.tag_asset(asset_id, request['tags'], tag_type):
                    success_count += 1
            
            return AliceResponse(
                success=success_count > 0,
                message=f"Tagged {success_count}/{len(request['asset_ids'])} assets",
                data={'tagged_count': success_count},
                error=None
            )
            
        except Exception as e:
            logger.error(f"Tagging failed: {e}")
            return AliceResponse(
                success=False,
                message="Tagging failed",
                data=None,
                error=str(e)
            )
    
    def group_assets(self, request: GroupRequest) -> AliceResponse:
        """Group assets together.
        
        Args:
            request: Grouping request
            
        Returns:
            Response indicating success
        """
        try:
            self._ensure_organizer()
            
            success = self.organizer.group_assets(
                request['asset_ids'],
                request['group_name']
            )
            
            return AliceResponse(
                success=success,
                message=f"Grouped {len(request['asset_ids'])} assets as '{request['group_name']}'",
                data={'group_name': request['group_name']},
                error=None
            )
            
        except Exception as e:
            logger.error(f"Grouping failed: {e}")
            return AliceResponse(
                success=False,
                message="Grouping failed",
                data=None,
                error=str(e)
            )
    
    def get_project_context(self, request: ProjectContextRequest) -> AliceResponse:
        """Get project context and statistics.
        
        Args:
            request: Context request
            
        Returns:
            Response with project context
        """
        try:
            self._ensure_organizer()
            
            context = self.organizer.get_project_context()
            
            # Add recent assets if requested
            if request.get('include_recent_assets'):
                recent = self.organizer.search_assets(
                    sort_by='created',
                    limit=10
                )
                context['recent_assets'] = [
                    self._simplify_asset_info(asset) for asset in recent
                ]
            
            return AliceResponse(
                success=True,
                message="Project context retrieved",
                data=context,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Context retrieval failed: {e}")
            return AliceResponse(
                success=False,
                message="Context retrieval failed",
                data=None,
                error=str(e)
            )
    
    def find_similar_assets(self, asset_id: str, threshold: float = 0.7) -> AliceResponse:
        """Find assets similar to a reference.
        
        Args:
            asset_id: Reference asset ID
            threshold: Similarity threshold (0-1)
            
        Returns:
            Response with similar assets
        """
        try:
            self._ensure_organizer()
            
            similar = self.organizer.find_similar(asset_id, threshold)
            simplified = [self._simplify_asset_info(asset) for asset in similar]
            
            return AliceResponse(
                success=True,
                message=f"Found {len(similar)} similar assets",
                data=simplified,
                error=None
            )
            
        except Exception as e:
            logger.error(f"Similarity search failed: {e}")
            return AliceResponse(
                success=False,
                message="Similarity search failed",
                data=None,
                error=str(e)
            )
    
    def set_asset_role(self, asset_id: str, role: str) -> AliceResponse:
        """Set the creative role of an asset.
        
        Args:
            asset_id: Asset ID
            role: Role name (hero, b_roll, reference, etc.)
            
        Returns:
            Response indicating success
        """
        try:
            self._ensure_organizer()
            
            role_enum = AssetRole(role)
            success = self.organizer.set_asset_role(asset_id, role_enum)
            
            return AliceResponse(
                success=success,
                message=f"Set role to '{role}'" if success else "Failed to set role",
                data={'asset_id': asset_id, 'role': role},
                error=None
            )
            
        except Exception as e:
            logger.error(f"Role setting failed: {e}")
            return AliceResponse(
                success=False,
                message="Role setting failed",
                data=None,
                error=str(e)
            )