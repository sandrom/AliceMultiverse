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
    if len(request["project_id"]) == 0:
        raise ValidationError("project_id cannot be empty")
    validated["project_id"] = request["project_id"].strip()

    # Validate name
    if not isinstance(request["name"], str):
        raise ValidationError("name must be a string")
    if len(request["name"]) == 0:
        raise ValidationError("name cannot be empty")
    if len(request["name"]) > MAX_PROJECT_NAME_LENGTH:
        raise ValidationError(f"name exceeds maximum length of {MAX_PROJECT_NAME_LENGTH}")
    if not SAFE_NAME_PATTERN.match(request["name"]):
        raise ValidationError("name contains invalid characters")
    validated["name"] = request["name"].strip()

    # Validate purpose if provided
    if "purpose" in request and request["purpose"] is not None:
        if isinstance(request["purpose"], SelectionPurpose):
            validated["purpose"] = request["purpose"]
        else:
            try:
                validated["purpose"] = SelectionPurpose(request["purpose"])
            except ValueError:
                valid_purposes = [p.value for p in SelectionPurpose]
                raise ValidationError(f"Invalid purpose '{request['purpose']}'. Valid purposes: {valid_purposes}")

    # Validate description if provided
    if "description" in request and request["description"] is not None:
        if not isinstance(request["description"], str):
            raise ValidationError("description must be a string")
        if len(request["description"]) > 1000:
            raise ValidationError("description exceeds maximum length of 1000 characters")
        validated["description"] = request["description"].strip()

    # Validate tags if provided
    if "tags" in request and request["tags"] is not None:
        validated["tags"] = validate_tags(request["tags"])

    return validated


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
    if len(request["selection_id"]) == 0:
        raise ValidationError("selection_id cannot be empty")
    validated["selection_id"] = request["selection_id"].strip()

    # Validate add_items if provided
    if "add_items" in request and request["add_items"] is not None:
        if not isinstance(request["add_items"], list):
            raise ValidationError("add_items must be a list")
        for i, item in enumerate(request["add_items"]):
            if not isinstance(item, dict):
                raise ValidationError(f"add_items[{i}] must be a dictionary")
            if "asset_hash" not in item:
                raise ValidationError(f"add_items[{i}] must have an asset_hash")
            try:
                item["asset_hash"] = validate_content_hash(item["asset_hash"])
            except ValidationError as e:
                raise ValidationError(f"add_items[{i}].asset_hash: {e}")
            if "file_path" not in item or not isinstance(item["file_path"], str):
                raise ValidationError(f"add_items[{i}] must have a valid file_path")

    # Validate remove_items if provided
    if "remove_items" in request and request["remove_items"] is not None:
        validated["remove_items"] = validate_asset_ids(request["remove_items"])

    # Validate update_status if provided
    if "update_status" in request and request["update_status"] is not None:
        if isinstance(request["update_status"], SelectionStatus):
            validated["update_status"] = request["update_status"]
        else:
            try:
                validated["update_status"] = SelectionStatus(request["update_status"])
            except ValueError:
                valid_statuses = [s.value for s in SelectionStatus]
                raise ValidationError(f"Invalid status '{request['update_status']}'. Valid statuses: {valid_statuses}")

    # Validate notes if provided
    if "notes" in request and request["notes"] is not None:
        if not isinstance(request["notes"], str):
            raise ValidationError("notes must be a string")
        if len(request["notes"]) > 1000:
            raise ValidationError("notes exceeds maximum length of 1000 characters")
        # Check for SQL injection patterns
        for pattern in SQL_INJECTION_PATTERNS:
            if pattern.search(request["notes"]):
                raise ValidationError("notes contains potentially malicious content")
        validated["notes"] = request["notes"].strip()

    return validated


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
    if len(request["selection_id"]) == 0:
        raise ValidationError("selection_id cannot be empty")
    validated["selection_id"] = request["selection_id"].strip()

    # Validate export path
    validated["export_path"] = str(validate_path(request["export_path"], "export_path"))

    return validated


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
    if len(request["project_id"]) == 0:
        raise ValidationError("project_id cannot be empty")
    validated["project_id"] = request["project_id"].strip()

    # Validate status if provided
    if "status" in request and request["status"] is not None:
        if isinstance(request["status"], SelectionStatus):
            validated["status"] = request["status"]
        else:
            try:
                validated["status"] = SelectionStatus(request["status"])
            except ValueError:
                valid_statuses = [s.value for s in SelectionStatus]
                raise ValidationError(f"Invalid status '{request['status']}'. Valid statuses: {valid_statuses}")

    # Validate purpose if provided
    if "purpose" in request and request["purpose"] is not None:
        if isinstance(request["purpose"], SelectionPurpose):
            validated["purpose"] = request["purpose"]
        else:
            try:
                validated["purpose"] = SelectionPurpose(request["purpose"])
            except ValueError:
                valid_purposes = [p.value for p in SelectionPurpose]
                raise ValidationError(f"Invalid purpose '{request['purpose']}'. Valid purposes: {valid_purposes}")

    # Validate containing_asset if provided
    if "containing_asset" in request and request["containing_asset"] is not None:
        validated["containing_asset"] = validate_content_hash(request["containing_asset"])

    return validated
