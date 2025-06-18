"""Selection operations for structured interface."""
from typing import TYPE_CHECKING

import logging

from ...core.exceptions import ValidationError
from ..structured_models import (
    AliceResponse,
    SelectionCreateRequest,
    SelectionExportRequest,
    SelectionPurpose,
    SelectionSearchRequest,
    SelectionUpdateRequest,
)
from ..validation import (
    validate_selection_create_request,
    validate_selection_export_request,
    validate_selection_search_request,
    validate_selection_update_request,
)

logger = logging.getLogger(__name__)


if TYPE_CHECKING:
    from ...core.protocols import HasProjectService, HasSelectionService

class SelectionOperationsMixin:
    """Mixin for selection-related operations."""

    if TYPE_CHECKING:
        # Type hints for mypy
        selection_service: Any
        project_service: Any


    def create_selection(self, request: SelectionCreateRequest, client_id: str = "default") -> AliceResponse:
        """Create a new selection for a project.

        Args:
            request: Selection creation request
            client_id: Client identifier for rate limiting

        Returns:
            Response with created selection
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "create_selection")

            # Validate request
            request = validate_selection_create_request(request)

            # Create selection
            selection = self.selection_service.create_selection(
                project_id=request["project_id"],
                name=request["name"],
                purpose=request.get("purpose", SelectionPurpose.CURATION),
                description=request.get("description"),
                criteria=request.get("criteria"),
                constraints=request.get("constraints"),
                tags=request.get("tags"),
                metadata=request.get("metadata"),
            )

            if selection:
                return AliceResponse(
                    success=True,
                    message=f"Created selection '{selection.name}'",
                    data={
                        "selection_id": selection.id,
                        "name": selection.name,
                        "purpose": selection.purpose.value,
                        "status": selection.status.value,
                        "created_at": selection.created_at.isoformat(),
                    },
                    error=None
                )
            else:
                return AliceResponse(
                    success=False,
                    message="Failed to create selection",
                    data=None,
                    error="Project not found or creation failed"
                )

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Selection creation failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Selection creation failed",
                data=None,
                error=str(e)
            )

    def update_selection(self, request: SelectionUpdateRequest, client_id: str = "default") -> AliceResponse:
        """Update a selection (add/remove items, change status, etc).

        Args:
            request: Selection update request
            client_id: Client identifier for rate limiting

        Returns:
            Response with updated selection
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "update_selection")

            # Validate request
            request = validate_selection_update_request(request)

            # Get project ID from selection
            selection = None
            project_id = None

            # First, find the selection to get project ID
            for project in self.project_service.list_projects():
                test_selection = self.selection_service.get_selection(
                    project["id"], request["selection_id"]
                )
                if test_selection:
                    selection = test_selection
                    project_id = project["id"]
                    break

            if not selection:
                return AliceResponse(
                    success=False,
                    message="Selection not found",
                    data=None,
                    error=f"No selection found with ID: {request['selection_id']}"
                )

            # Handle different update operations
            result = None

            if "add_items" in request:
                result = self.selection_service.add_items_to_selection(
                    project_id, request["selection_id"], request["add_items"]
                )

            if "remove_items" in request:
                result = self.selection_service.remove_items_from_selection(
                    project_id, request["selection_id"], request["remove_items"]
                )

            if "status" in request:
                result = self.selection_service.update_selection_status(
                    project_id, request["selection_id"], request["status"]
                )

            if "metadata" in request:
                result = self.selection_service.update_selection_metadata(
                    project_id, request["selection_id"], request["metadata"]
                )

            if result:
                # Get updated selection
                updated_selection = self.selection_service.get_selection(
                    project_id, request["selection_id"]
                )

                return AliceResponse(
                    success=True,
                    message="Selection updated",
                    data={
                        "selection_id": updated_selection.id,
                        "name": updated_selection.name,
                        "status": updated_selection.status.value,
                        "item_count": len(updated_selection.items),
                        "modified_at": updated_selection.modified_at.isoformat(),
                    },
                    error=None
                )
            else:
                return AliceResponse(
                    success=False,
                    message="Failed to update selection",
                    data=None,
                    error="Update operation failed"
                )

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Selection update failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Selection update failed",
                data=None,
                error=str(e)
            )

    def search_selections(self, request: SelectionSearchRequest, client_id: str = "default") -> AliceResponse:
        """Search for selections across projects.

        Args:
            request: Selection search request
            client_id: Client identifier for rate limiting

        Returns:
            Response with search results
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "search_selections")

            # Validate request
            request = validate_selection_search_request(request)

            # Search selections
            results = self.selection_service.search_selections(
                project_id=request.get("project_id"),
                name_pattern=request.get("name_pattern"),
                purpose=request.get("purpose"),
                status=request.get("status"),
                tags=request.get("tags"),
                created_after=request.get("created_after"),
                created_before=request.get("created_before"),
                limit=request.get("limit", 50)
            )

            # Format results
            selections_data = []
            for selection in results:
                selections_data.append({
                    "selection_id": selection.id,
                    "project_id": selection.project_id,
                    "name": selection.name,
                    "purpose": selection.purpose.value,
                    "status": selection.status.value,
                    "item_count": len(selection.items),
                    "created_at": selection.created_at.isoformat(),
                    "modified_at": selection.modified_at.isoformat(),
                })

            return AliceResponse(
                success=True,
                message=f"Found {len(results)} selections",
                data={
                    "selections": selections_data,
                    "total_count": len(results)
                },
                error=None
            )

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Selection search failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Selection search failed",
                data=None,
                error=str(e)
            )

    def export_selection(self, request: SelectionExportRequest, client_id: str = "default") -> AliceResponse:
        """Export a selection in various formats.

        Args:
            request: Selection export request
            client_id: Client identifier for rate limiting

        Returns:
            Response with export result
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "export_selection")

            # Validate request
            request = validate_selection_export_request(request)

            # Find selection
            selection = None
            project_id = None

            for project in self.project_service.list_projects():
                test_selection = self.selection_service.get_selection(
                    project["id"], request["selection_id"]
                )
                if test_selection:
                    selection = test_selection
                    project_id = project["id"]
                    break

            if not selection:
                return AliceResponse(
                    success=False,
                    message="Selection not found",
                    data=None,
                    error=f"No selection found with ID: {request['selection_id']}"
                )

            # Export selection
            export_result = self.selection_service.export_selection(
                project_id,
                request["selection_id"],
                format=request["format"],
                output_path=request.get("output_path"),
                include_metadata=request.get("include_metadata", True),
                include_assets=request.get("include_assets", False)
            )

            if export_result:
                return AliceResponse(
                    success=True,
                    message=f"Exported selection to {export_result['path']}",
                    data={
                        "export_path": export_result["path"],
                        "format": request["format"],
                        "item_count": export_result.get("item_count", 0),
                        "file_size": export_result.get("file_size", 0)
                    },
                    error=None
                )
            else:
                return AliceResponse(
                    success=False,
                    message="Export failed",
                    data=None,
                    error="Failed to export selection"
                )

        except ValidationError as e:
            logger.error(f"Validation error: {e}")
            return AliceResponse(
                success=False,
                message="Invalid request",
                data=None,
                error=str(e)
            )
        except Exception as e:
            logger.error(f"Selection export failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Selection export failed",
                data=None,
                error=str(e)
            )

    def get_selection(self, project_id: str, selection_id: str, client_id: str = "default") -> AliceResponse:
        """Get details of a specific selection.

        Args:
            project_id: Project identifier
            selection_id: Selection identifier
            client_id: Client identifier for rate limiting

        Returns:
            Response with selection details
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "get_selection")

            # Get selection
            selection = self.selection_service.get_selection(project_id, selection_id)

            if not selection:
                return AliceResponse(
                    success=False,
                    message="Selection not found",
                    data=None,
                    error=f"No selection found with ID: {selection_id} in project: {project_id}"
                )

            # Format selection data
            selection_data = {
                "selection_id": selection.id,
                "project_id": selection.project_id,
                "name": selection.name,
                "purpose": selection.purpose.value,
                "status": selection.status.value,
                "description": selection.description,
                "criteria": selection.criteria,
                "constraints": selection.constraints,
                "tags": selection.tags,
                "items": selection.items,
                "item_count": len(selection.items),
                "metadata": selection.metadata,
                "created_at": selection.created_at.isoformat(),
                "modified_at": selection.modified_at.isoformat(),
                "created_by": selection.created_by,
                "modified_by": selection.modified_by,
            }

            return AliceResponse(
                success=True,
                message="Selection retrieved",
                data=selection_data,
                error=None
            )

        except Exception as e:
            logger.error(f"Selection retrieval failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Selection retrieval failed",
                data=None,
                error=str(e)
            )

    def find_similar_to_selection(
        self,
        project_id: str,
        selection_id: str,
        limit: int = 20,
        client_id: str = "default"
    ) -> AliceResponse:
        """Find assets similar to those in a selection.

        Args:
            project_id: Project identifier
            selection_id: Selection identifier
            limit: Maximum number of similar assets to return
            client_id: Client identifier for rate limiting

        Returns:
            Response with similar assets
        """
        try:
            # Rate limiting
            self.rate_limiter.check_request(client_id, "find_similar")

            # Get selection
            selection = self.selection_service.get_selection(project_id, selection_id)

            if not selection:
                return AliceResponse(
                    success=False,
                    message="Selection not found",
                    data=None,
                    error=f"No selection found with ID: {selection_id}"
                )

            # Find similar assets
            similar_assets = self.selection_service.find_similar_assets(
                project_id,
                selection_id,
                limit=limit
            )

            return AliceResponse(
                success=True,
                message=f"Found {len(similar_assets)} similar assets",
                data={
                    "similar_assets": similar_assets,
                    "total_count": len(similar_assets)
                },
                error=None
            )

        except Exception as e:
            logger.error(f"Similar asset search failed: {e}", exc_info=True)
            return AliceResponse(
                success=False,
                message="Similar asset search failed",
                data=None,
                error=str(e)
            )
