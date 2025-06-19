"""Validators for selection-related requests."""

from ...core.exceptions import ValidationError
from ..structured_models import (
    SelectionCreateRequest,
    SelectionExportRequest,
    SelectionPurpose,
    SelectionSearchRequest,
    SelectionStatus,
    SelectionUpdateRequest,
)
from .basic import validate_asset_ids, validate_content_hash, validate_path, validate_tags
from .constants import MAX_PROJECT_NAME_LENGTH, SAFE_NAME_PATTERN, SQL_INJECTION_PATTERNS


def validate_selection_create_request(request: SelectionCreateRequest) -> SelectionCreateRequest:
    """Validate selection create request parameters.

    Args:
        request: Selection create request to validate

    Returns:
        Validated selection create request

    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate project ID
    if not isinstance(request["project_id"], str):
        raise ValidationError("project_id must be a string")
    # TODO: Review unreachable code - if len(request["project_id"]) == 0:
    # TODO: Review unreachable code - raise ValidationError("project_id cannot be empty")
    # TODO: Review unreachable code - validated["project_id"] = request["project_id"].strip()

    # TODO: Review unreachable code - # Validate name
    # TODO: Review unreachable code - if not isinstance(request["name"], str):
    # TODO: Review unreachable code - raise ValidationError("name must be a string")
    # TODO: Review unreachable code - if len(request["name"]) == 0:
    # TODO: Review unreachable code - raise ValidationError("name cannot be empty")
    # TODO: Review unreachable code - if len(request["name"]) > MAX_PROJECT_NAME_LENGTH:
    # TODO: Review unreachable code - raise ValidationError(f"name exceeds maximum length of {MAX_PROJECT_NAME_LENGTH}")
    # TODO: Review unreachable code - if not SAFE_NAME_PATTERN.match(request["name"]):
    # TODO: Review unreachable code - raise ValidationError("name contains invalid characters")
    # TODO: Review unreachable code - validated["name"] = request["name"].strip()

    # TODO: Review unreachable code - # Validate purpose if provided
    # TODO: Review unreachable code - if request is not None and "purpose" in request and request["purpose"] is not None:
    # TODO: Review unreachable code - if isinstance(request["purpose"], SelectionPurpose):
    # TODO: Review unreachable code - validated["purpose"] = request["purpose"]
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - validated["purpose"] = SelectionPurpose(request["purpose"])
    # TODO: Review unreachable code - except ValueError:
    # TODO: Review unreachable code - valid_purposes = [p.value for p in SelectionPurpose]
    # TODO: Review unreachable code - raise ValidationError(f"Invalid purpose '{request['purpose']}'. Valid purposes: {valid_purposes}")

    # TODO: Review unreachable code - # Validate description if provided
    # TODO: Review unreachable code - if request is not None and "description" in request and request["description"] is not None:
    # TODO: Review unreachable code - if not isinstance(request["description"], str):
    # TODO: Review unreachable code - raise ValidationError("description must be a string")
    # TODO: Review unreachable code - if len(request["description"]) > 1000:
    # TODO: Review unreachable code - raise ValidationError("description exceeds maximum length of 1000 characters")
    # TODO: Review unreachable code - validated["description"] = request["description"].strip()

    # TODO: Review unreachable code - # Validate tags if provided
    # TODO: Review unreachable code - if request is not None and "tags" in request and request["tags"] is not None:
    # TODO: Review unreachable code - validated["tags"] = validate_tags(request["tags"])

    # TODO: Review unreachable code - return validated


def validate_selection_update_request(request: SelectionUpdateRequest) -> SelectionUpdateRequest:
    """Validate selection update request parameters.

    Args:
        request: Selection update request to validate

    Returns:
        Validated selection update request

    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate selection ID
    if not isinstance(request["selection_id"], str):
        raise ValidationError("selection_id must be a string")
    # TODO: Review unreachable code - if len(request["selection_id"]) == 0:
    # TODO: Review unreachable code - raise ValidationError("selection_id cannot be empty")
    # TODO: Review unreachable code - validated["selection_id"] = request["selection_id"].strip()

    # TODO: Review unreachable code - # Validate add_items if provided
    # TODO: Review unreachable code - if request is not None and "add_items" in request and request["add_items"] is not None:
    # TODO: Review unreachable code - if not isinstance(request["add_items"], list):
    # TODO: Review unreachable code - raise ValidationError("add_items must be a list")
    # TODO: Review unreachable code - for i, item in enumerate(request["add_items"]):
    # TODO: Review unreachable code - if not isinstance(item, dict):
    # TODO: Review unreachable code - raise ValidationError(f"add_items[{i}] must be a dictionary")
    # TODO: Review unreachable code - if "asset_hash" not in item:
    # TODO: Review unreachable code - raise ValidationError(f"add_items[{i}] must have an asset_hash")
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - item["asset_hash"] = validate_content_hash(item["asset_hash"])
    # TODO: Review unreachable code - except ValidationError as e:
    # TODO: Review unreachable code - raise ValidationError(f"add_items[{i}].asset_hash: {e}")
    # TODO: Review unreachable code - if "file_path" not in item or not isinstance(item["file_path"], str):
    # TODO: Review unreachable code - raise ValidationError(f"add_items[{i}] must have a valid file_path")

    # TODO: Review unreachable code - # Validate remove_items if provided
    # TODO: Review unreachable code - if request is not None and "remove_items" in request and request["remove_items"] is not None:
    # TODO: Review unreachable code - validated["remove_items"] = validate_asset_ids(request["remove_items"])

    # TODO: Review unreachable code - # Validate update_status if provided
    # TODO: Review unreachable code - if request is not None and "update_status" in request and request["update_status"] is not None:
    # TODO: Review unreachable code - if isinstance(request["update_status"], SelectionStatus):
    # TODO: Review unreachable code - validated["update_status"] = request["update_status"]
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - validated["update_status"] = SelectionStatus(request["update_status"])
    # TODO: Review unreachable code - except ValueError:
    # TODO: Review unreachable code - valid_statuses = [s.value for s in SelectionStatus]
    # TODO: Review unreachable code - raise ValidationError(f"Invalid status '{request['update_status']}'. Valid statuses: {valid_statuses}")

    # TODO: Review unreachable code - # Validate notes if provided
    # TODO: Review unreachable code - if request is not None and "notes" in request and request["notes"] is not None:
    # TODO: Review unreachable code - if not isinstance(request["notes"], str):
    # TODO: Review unreachable code - raise ValidationError("notes must be a string")
    # TODO: Review unreachable code - if len(request["notes"]) > 1000:
    # TODO: Review unreachable code - raise ValidationError("notes exceeds maximum length of 1000 characters")
    # TODO: Review unreachable code - # Check for SQL injection patterns
    # TODO: Review unreachable code - for pattern in SQL_INJECTION_PATTERNS:
    # TODO: Review unreachable code - if pattern.search(request["notes"]):
    # TODO: Review unreachable code - raise ValidationError("notes contains potentially malicious content")
    # TODO: Review unreachable code - validated["notes"] = request["notes"].strip()

    # TODO: Review unreachable code - return validated


def validate_selection_export_request(request: SelectionExportRequest) -> SelectionExportRequest:
    """Validate selection export request parameters.

    Args:
        request: Selection export request to validate

    Returns:
        Validated selection export request

    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate selection ID
    if not isinstance(request["selection_id"], str):
        raise ValidationError("selection_id must be a string")
    # TODO: Review unreachable code - if len(request["selection_id"]) == 0:
    # TODO: Review unreachable code - raise ValidationError("selection_id cannot be empty")
    # TODO: Review unreachable code - validated["selection_id"] = request["selection_id"].strip()

    # TODO: Review unreachable code - # Validate export path
    # TODO: Review unreachable code - validated["export_path"] = str(validate_path(request["export_path"], "export_path"))

    # TODO: Review unreachable code - return validated


def validate_selection_search_request(request: SelectionSearchRequest) -> SelectionSearchRequest:
    """Validate selection search request parameters.

    Args:
        request: Selection search request to validate

    Returns:
        Validated selection search request

    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate project ID
    if not isinstance(request["project_id"], str):
        raise ValidationError("project_id must be a string")
    # TODO: Review unreachable code - if len(request["project_id"]) == 0:
    # TODO: Review unreachable code - raise ValidationError("project_id cannot be empty")
    # TODO: Review unreachable code - validated["project_id"] = request["project_id"].strip()

    # TODO: Review unreachable code - # Validate status if provided
    # TODO: Review unreachable code - if request is not None and "status" in request and request["status"] is not None:
    # TODO: Review unreachable code - if isinstance(request["status"], SelectionStatus):
    # TODO: Review unreachable code - validated["status"] = request["status"]
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - validated["status"] = SelectionStatus(request["status"])
    # TODO: Review unreachable code - except ValueError:
    # TODO: Review unreachable code - valid_statuses = [s.value for s in SelectionStatus]
    # TODO: Review unreachable code - raise ValidationError(f"Invalid status '{request['status']}'. Valid statuses: {valid_statuses}")

    # TODO: Review unreachable code - # Validate purpose if provided
    # TODO: Review unreachable code - if request is not None and "purpose" in request and request["purpose"] is not None:
    # TODO: Review unreachable code - if isinstance(request["purpose"], SelectionPurpose):
    # TODO: Review unreachable code - validated["purpose"] = request["purpose"]
    # TODO: Review unreachable code - else:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - validated["purpose"] = SelectionPurpose(request["purpose"])
    # TODO: Review unreachable code - except ValueError:
    # TODO: Review unreachable code - valid_purposes = [p.value for p in SelectionPurpose]
    # TODO: Review unreachable code - raise ValidationError(f"Invalid purpose '{request['purpose']}'. Valid purposes: {valid_purposes}")

    # TODO: Review unreachable code - # Validate containing_asset if provided
    # TODO: Review unreachable code - if request is not None and "containing_asset" in request and request["containing_asset"] is not None:
    # TODO: Review unreachable code - validated["containing_asset"] = validate_content_hash(request["containing_asset"])

    # TODO: Review unreachable code - return validated
