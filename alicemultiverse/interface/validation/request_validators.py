"""Validators for various request types."""

from ...core.exceptions import ValidationError
from ..structured_models import (
    GenerationRequest,
    GroupingRequest,
    MediaType,
    OrganizeRequest,
    ProjectRequest,
    SoftDeleteRequest,
    SortField,
    SortOrder,
    SearchRequest,
    TagUpdateRequest,
    WorkflowRequest,
)
from .basic import (
    validate_asset_ids,
    validate_content_hash,
    validate_path,
    validate_regex_pattern,
    validate_tags,
)
from .constants import (
    MAX_GROUP_NAME_LENGTH,
    MAX_PROJECT_NAME_LENGTH,
    MAX_PROMPT_LENGTH,
    MAX_SEARCH_LIMIT,
    MAX_WORKFLOW_NAME_LENGTH,
    SAFE_NAME_PATTERN,
)


def validate_search_request(request: SearchRequest) -> SearchRequest:
    """Validate search request parameters.
    
    Args:
        request: Search request to validate
        
    Returns:
        Validated search request
        
    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate filters if present
    if "filters" in request:
        filters = request["filters"]

        # Validate media type
        if "media_type" in filters and filters["media_type"] is not None:
            try:
                MediaType(filters["media_type"])
            except ValueError:
                raise ValidationError(f"Invalid media type: {filters['media_type']}")

        # Validate tags
        if "tags" in filters:
            filters["tags"] = validate_tags(filters["tags"])
        if "any_tags" in filters:
            filters["any_tags"] = validate_tags(filters["any_tags"])
        if "exclude_tags" in filters:
            filters["exclude_tags"] = validate_tags(filters["exclude_tags"])

        # Validate content hash
        if "content_hash" in filters and filters["content_hash"] is not None:
            filters["content_hash"] = validate_content_hash(filters["content_hash"])

        # Validate filename pattern
        if "filename_pattern" in filters:
            filters["filename_pattern"] = validate_regex_pattern(
                filters["filename_pattern"], "filename_pattern"
            )

        # Validate prompt keywords
        if "prompt_keywords" in filters and filters["prompt_keywords"] is not None:
            if not isinstance(filters["prompt_keywords"], list):
                raise ValidationError("prompt_keywords must be a list")
            if len(filters["prompt_keywords"]) > 20:
                raise ValidationError("Too many prompt keywords (max 20)")
            for keyword in filters["prompt_keywords"]:
                if not isinstance(keyword, str) or len(keyword) > 100:
                    raise ValidationError("Invalid prompt keyword")

        # Validate numeric ranges
        for range_field in ["file_size", "quality_rating"]:
            if range_field in filters and filters[range_field] is not None:
                range_val = filters[range_field]
                if not isinstance(range_val, dict):
                    raise ValidationError(f"{range_field} must be a dict")
                for key in ["min", "max"]:
                    if key in range_val and range_val[key] is not None:
                        if not isinstance(range_val[key], (int, float)):
                            raise ValidationError(f"{range_field}.{key} must be numeric")
                        if range_val[key] < 0:
                            raise ValidationError(f"{range_field}.{key} cannot be negative")

    # Validate sort field
    if "sort_by" in request and request["sort_by"] is not None:
        try:
            SortField(request["sort_by"])
        except ValueError:
            raise ValidationError(f"Invalid sort field: {request['sort_by']}")

    # Validate sort order
    if "order" in request and request["order"] is not None:
        try:
            SortOrder(request["order"])
        except ValueError:
            raise ValidationError(f"Invalid sort order: {request['order']}")

    # Validate pagination
    if "limit" in request and request["limit"] is not None:
        if not isinstance(request["limit"], int):
            raise ValidationError("limit must be an integer")
        if request["limit"] < 1:
            raise ValidationError("limit must be positive")
        if request["limit"] > MAX_SEARCH_LIMIT:
            validated["limit"] = MAX_SEARCH_LIMIT

    if "offset" in request and request["offset"] is not None:
        if not isinstance(request["offset"], int):
            raise ValidationError("offset must be an integer")
        if request["offset"] < 0:
            raise ValidationError("offset cannot be negative")

    return validated


def validate_organize_request(request: OrganizeRequest) -> OrganizeRequest:
    """Validate organize request parameters.
    
    Args:
        request: Organize request to validate
        
    Returns:
        Validated organize request
        
    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate paths
    if "source_path" in request:
        validated["source_path"] = str(validate_path(request["source_path"], "source_path"))
    if "destination_path" in request:
        validated["destination_path"] = str(validate_path(request["destination_path"], "destination_path"))

    # Validate pipeline
    if "pipeline" in request and request["pipeline"] is not None:
        if not isinstance(request["pipeline"], str):
            raise ValidationError("pipeline must be a string")
        # Add allowed pipeline values
        allowed_pipelines = [
            "brisque", "brisque-sightengine", "brisque-claude",
            "brisque-sightengine-claude", "basic", "standard",
            "premium", "full", "custom"
        ]
        if request["pipeline"] not in allowed_pipelines:
            raise ValidationError(f"Invalid pipeline: {request['pipeline']}")

    # Validate boolean flags
    for bool_field in ["quality_assessment", "watch_mode", "move_files"]:
        if bool_field in request and request[bool_field] is not None:
            if not isinstance(request[bool_field], bool):
                raise ValidationError(f"{bool_field} must be a boolean")

    return validated


def validate_tag_update_request(request: TagUpdateRequest) -> TagUpdateRequest:
    """Validate tag update request parameters.
    
    Args:
        request: Tag update request to validate
        
    Returns:
        Validated tag update request
        
    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate asset IDs
    validated["asset_ids"] = validate_asset_ids(request["asset_ids"])

    # Validate operation
    valid_operations = ["add", "remove", "set", "clear"]
    if request["operation"] not in valid_operations:
        raise ValidationError(
            f"Invalid operation '{request['operation']}'. Must be one of: {', '.join(valid_operations)}"
        )

    # Validate tags based on operation
    if request["operation"] in ["add", "remove", "set"]:
        if "tags" not in request or request["tags"] is None:
            raise ValidationError(f"Tags required for {request['operation']} operation")
        validated["tags"] = validate_tags(request["tags"])
    elif request["operation"] == "clear":
        if "tags" in request and request["tags"] is not None:
            raise ValidationError("Tags should not be provided for clear operation")
        validated["tags"] = None

    return validated


def validate_grouping_request(request: GroupingRequest) -> GroupingRequest:
    """Validate grouping request parameters.
    
    Args:
        request: Grouping request to validate
        
    Returns:
        Validated grouping request
        
    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate asset IDs
    validated["asset_ids"] = validate_asset_ids(request["asset_ids"])

    # Validate group name
    if not isinstance(request["group_name"], str):
        raise ValidationError("group_name must be a string")
    
    if len(request["group_name"]) == 0:
        raise ValidationError("group_name cannot be empty")
    
    if len(request["group_name"]) > MAX_GROUP_NAME_LENGTH:
        raise ValidationError(f"group_name exceeds maximum length of {MAX_GROUP_NAME_LENGTH}")
    
    if not SAFE_NAME_PATTERN.match(request["group_name"]):
        raise ValidationError("group_name contains invalid characters")

    # Validate tags if present
    if "tags" in request:
        validated["tags"] = validate_tags(request["tags"])

    return validated


def validate_project_request(request: ProjectRequest) -> ProjectRequest:
    """Validate project request parameters.
    
    Args:
        request: Project request to validate
        
    Returns:
        Validated project request
        
    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate project name
    if not isinstance(request["project_name"], str):
        raise ValidationError("project_name must be a string")
    
    if len(request["project_name"]) == 0:
        raise ValidationError("project_name cannot be empty")
    
    if len(request["project_name"]) > MAX_PROJECT_NAME_LENGTH:
        raise ValidationError(f"project_name exceeds maximum length of {MAX_PROJECT_NAME_LENGTH}")
    
    if not SAFE_NAME_PATTERN.match(request["project_name"]):
        raise ValidationError("project_name contains invalid characters")

    # Validate asset IDs
    validated["asset_ids"] = validate_asset_ids(request["asset_ids"])

    # Validate metadata if present
    if "metadata" in request and request["metadata"] is not None:
        if not isinstance(request["metadata"], dict):
            raise ValidationError("metadata must be a dictionary")

    return validated


def validate_workflow_request(request: WorkflowRequest) -> WorkflowRequest:
    """Validate workflow request parameters.
    
    Args:
        request: Workflow request to validate
        
    Returns:
        Validated workflow request
        
    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate workflow name
    if not isinstance(request["workflow"], str):
        raise ValidationError("workflow must be a string")
    
    if len(request["workflow"]) == 0:
        raise ValidationError("workflow cannot be empty")
    
    if len(request["workflow"]) > MAX_WORKFLOW_NAME_LENGTH:
        raise ValidationError(f"workflow exceeds maximum length of {MAX_WORKFLOW_NAME_LENGTH}")

    # Validate asset IDs
    validated["asset_ids"] = validate_asset_ids(request["asset_ids"])

    # Validate parameters if present
    if "parameters" in request and request["parameters"] is not None:
        if not isinstance(request["parameters"], dict):
            raise ValidationError("parameters must be a dictionary")

    return validated


def validate_generation_request(request: GenerationRequest) -> GenerationRequest:
    """Validate generation request parameters.
    
    Args:
        request: Generation request to validate
        
    Returns:
        Validated generation request
        
    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate prompt
    if not isinstance(request["prompt"], str):
        raise ValidationError("prompt must be a string")
    
    if len(request["prompt"]) == 0:
        raise ValidationError("prompt cannot be empty")
    
    if len(request["prompt"]) > MAX_PROMPT_LENGTH:
        raise ValidationError(f"prompt exceeds maximum length of {MAX_PROMPT_LENGTH}")

    # Validate model
    if not isinstance(request["model"], str):
        raise ValidationError("model must be a string")
    
    if len(request["model"]) == 0:
        raise ValidationError("model cannot be empty")

    # Validate reference assets if present
    if "reference_assets" in request and request["reference_assets"] is not None:
        validated["reference_assets"] = validate_asset_ids(request["reference_assets"])

    # Validate parameters if present
    if "parameters" in request and request["parameters"] is not None:
        if not isinstance(request["parameters"], dict):
            raise ValidationError("parameters must be a dictionary")
        
        # Validate specific parameters
        params = request["parameters"]
        
        # Validate steps
        if "steps" in params and params["steps"] is not None:
            if not isinstance(params["steps"], int):
                raise ValidationError("steps must be an integer")
            if params["steps"] < 1 or params["steps"] > 1000:
                raise ValidationError("steps must be between 1 and 1000")
        
        # Validate guidance scale
        if "guidance_scale" in params and params["guidance_scale"] is not None:
            if not isinstance(params["guidance_scale"], (int, float)):
                raise ValidationError("guidance_scale must be numeric")
            if params["guidance_scale"] < 0 or params["guidance_scale"] > 50:
                raise ValidationError("guidance_scale must be between 0 and 50")

    return validated


def validate_soft_delete_request(request: SoftDeleteRequest) -> SoftDeleteRequest:
    """Validate soft delete request parameters.
    
    Args:
        request: Soft delete request to validate
        
    Returns:
        Validated soft delete request
        
    Raises:
        ValidationError: If request contains invalid data
    """
    validated = request.copy()

    # Validate asset IDs
    validated["asset_ids"] = validate_asset_ids(request["asset_ids"])

    # Validate reason if present
    if "reason" in request and request["reason"] is not None:
        if not isinstance(request["reason"], str):
            raise ValidationError("reason must be a string")
        
        if len(request["reason"]) > 500:
            raise ValidationError("reason exceeds maximum length of 500")

    # Validate permanent flag
    if "permanent" in request and request["permanent"] is not None:
        if not isinstance(request["permanent"], bool):
            raise ValidationError("permanent must be a boolean")

    return validated