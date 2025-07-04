"""Validators for various request types."""

from ...core.exceptions import ValidationError
from ..structured_models import (
    GenerationRequest,
    GroupingRequest,
    MediaType,
    OrganizeRequest,
    ProjectRequest,
    SearchRequest,
    SoftDeleteRequest,
    SortField,
    SortOrder,
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
    SQL_INJECTION_PATTERNS,
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
    if request is not None and "filters" in request:
        filters = request["filters"]

        # Validate media type
        if filters is not None and "media_type" in filters and filters["media_type"] is not None:
            try:
                MediaType(filters["media_type"])
            except ValueError:
                raise ValidationError(f"Invalid media type: {filters['media_type']}")

        # Validate tags
        if filters is not None and "tags" in filters:
            filters["tags"] = validate_tags(filters["tags"])
        if filters is not None and "any_tags" in filters:
            filters["any_tags"] = validate_tags(filters["any_tags"])
        if filters is not None and "not_tags" in filters: # Changed from exclude_tags
            filters["not_tags"] = validate_tags(filters["not_tags"]) # Changed from exclude_tags

        # Validate content hash
        if filters is not None and "content_hash" in filters and filters["content_hash"] is not None:
            filters["content_hash"] = validate_content_hash(filters["content_hash"])

        # Validate filename pattern
        if filters is not None and "filename_pattern" in filters:
            filters["filename_pattern"] = validate_regex_pattern(
                filters["filename_pattern"], "filename_pattern"
            )

        # Validate prompt keywords
        if filters is not None and "prompt_keywords" in filters and filters["prompt_keywords"] is not None:
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
    if request is not None and "sort_by" in request and request["sort_by"] is not None:
        try:
            SortField(request["sort_by"])
        except ValueError:
            raise ValidationError(f"Invalid sort field: {request['sort_by']}")

    # Validate sort order
    if request is not None and "order" in request and request["order"] is not None:
        try:
            SortOrder(request["order"])
        except ValueError:
            raise ValidationError(f"Invalid sort order: {request['order']}")

    # Validate pagination
    if request is not None and "limit" in request and request["limit"] is not None:
        if not isinstance(request["limit"], int):
            raise ValidationError("limit must be an integer")
        if request is not None and request["limit"] < 1:
            raise ValidationError("limit must be positive")
        if request is not None and request["limit"] > MAX_SEARCH_LIMIT:
            validated["limit"] = MAX_SEARCH_LIMIT

    if request is not None and "offset" in request and request["offset"] is not None:
        if not isinstance(request["offset"], int):
            raise ValidationError("offset must be an integer")
        if request is not None and request["offset"] < 0:
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
        if request["source_path"] is not None:
            validated["source_path"] = str(validate_path(request["source_path"], "source_path"))
        else:
            validated["source_path"] = None # Preserve explicit None

    if "destination_path" in request:
        if request["destination_path"] is not None:
            validated["destination_path"] = str(validate_path(request["destination_path"], "destination_path"))
        else:
            validated["destination_path"] = None # Preserve explicit None

    # Validate pipeline
    # Assuming pipeline is Optional[str] in OrganizeRequest based on total=False
    # The original check `request["pipeline"] is not None` was good.
    pipeline_val = request.get("pipeline")
    if pipeline_val is not None:
        if not isinstance(pipeline_val, str):
            raise ValidationError("pipeline must be a string")
        allowed_pipelines = [
            "brisque", "brisque-sightengine", "brisque-claude",
            "brisque-sightengine-claude", "basic", "standard",
            "premium", "full", "custom"
        ]
        if pipeline_val not in allowed_pipelines:
            raise ValidationError(f"Invalid pipeline: {pipeline_val}")

    # Validate boolean flags
    for bool_field in ["quality_assessment", "watch_mode", "move_files", "understanding"]: # Added understanding
        field_val = request.get(bool_field)
        if field_val is not None:
            if not isinstance(field_val, bool):
                raise ValidationError(f"{bool_field} must be a boolean")
            # No change needed for validated[bool_field] as it's already copied
            # and type is correct if present and not None.

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

    # Validate asset IDs (assuming asset_ids is always present as per current direct access)
    # If asset_ids could be missing, this would need request.get("asset_ids")
    validated["asset_ids"] = validate_asset_ids(request["asset_ids"])

    # Validate tag operations
    operations_count = 0
    add_tags_val = request.get("add_tags")
    if add_tags_val is not None:
        operations_count += 1
        validated["add_tags"] = validate_tags(add_tags_val)

    remove_tags_val = request.get("remove_tags")
    if remove_tags_val is not None:
        operations_count += 1
        validated["remove_tags"] = validate_tags(remove_tags_val)

    set_tags_val = request.get("set_tags")
    if set_tags_val is not None:
        operations_count += 1
        validated["set_tags"] = validate_tags(set_tags_val)
    
    # Ensure at least one operation is specified
    if operations_count == 0:
        raise ValidationError("At least one tag operation (add_tags, remove_tags, or set_tags) must be specified")
    
    # Ensure set_tags is not used with other operations
    if request.get("set_tags") is not None and operations_count > 1:
        raise ValidationError("set_tags cannot be used with add_tags or remove_tags")

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
    if request is not None and "tags" in request:
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
    if request is not None and "metadata" in request and request["metadata"] is not None:
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
    if request is not None and "parameters" in request and request["parameters"] is not None:
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

    # Validate prompt (required)
    if "prompt" not in request:
        raise ValidationError("prompt is required")
    
    if not isinstance(request["prompt"], str):
        raise ValidationError("prompt must be a string")

    if len(request["prompt"]) == 0:
        raise ValidationError("prompt cannot be empty")

    if len(request["prompt"]) > MAX_PROMPT_LENGTH:
        raise ValidationError(f"prompt exceeds maximum length of {MAX_PROMPT_LENGTH}")
    
    # Check for malicious content in prompt
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(request["prompt"]):
            raise ValidationError("prompt contains potentially malicious content")

    # Validate model if present
    if "model" in request and request["model"] is not None:
        if not isinstance(request["model"], str):
            raise ValidationError("model must be a string")

        if len(request["model"]) == 0:
            raise ValidationError("model cannot be empty")

    # Validate reference assets if present
    if request is not None and "reference_assets" in request and request["reference_assets"] is not None:
        validated["reference_assets"] = validate_asset_ids(request["reference_assets"])

    # Validate parameters if present
    if request is not None and "parameters" in request and request["parameters"] is not None:
        if not isinstance(request["parameters"], dict):
            raise ValidationError("parameters must be a dictionary")

        # Validate specific parameters
        params = request["parameters"]

        # Validate steps
        if params is not None and "steps" in params and params["steps"] is not None:
            if not isinstance(params["steps"], int):
                raise ValidationError("steps must be an integer")
            if params is not None and params["steps"] < 1 or params["steps"] > 1000:
                raise ValidationError("steps must be between 1 and 1000")

        # Validate guidance scale
        if params is not None and "guidance_scale" in params and params["guidance_scale"] is not None:
            if not isinstance(params["guidance_scale"], (int, float)):
                raise ValidationError("guidance_scale must be numeric")
            if params is not None and params["guidance_scale"] < 0 or params["guidance_scale"] > 50:
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
    if request is not None and "reason" in request and request["reason"] is not None:
        if not isinstance(request["reason"], str):
            raise ValidationError("reason must be a string")

        if len(request["reason"]) > 500:
            raise ValidationError("reason exceeds maximum length of 500")

    # Validate permanent flag
    if request is not None and "permanent" in request and request["permanent"] is not None:
        if not isinstance(request["permanent"], bool):
            raise ValidationError("permanent must be a boolean")
    
    return validated
