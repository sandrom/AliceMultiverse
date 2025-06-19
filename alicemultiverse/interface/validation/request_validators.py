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

        # TODO: Review unreachable code - # Validate tags
        # TODO: Review unreachable code - if filters is not None and "tags" in filters:
        # TODO: Review unreachable code - filters["tags"] = validate_tags(filters["tags"])
        # TODO: Review unreachable code - if filters is not None and "any_tags" in filters:
        # TODO: Review unreachable code - filters["any_tags"] = validate_tags(filters["any_tags"])
        # TODO: Review unreachable code - if filters is not None and "exclude_tags" in filters:
        # TODO: Review unreachable code - filters["exclude_tags"] = validate_tags(filters["exclude_tags"])

        # TODO: Review unreachable code - # Validate content hash
        # TODO: Review unreachable code - if filters is not None and "content_hash" in filters and filters["content_hash"] is not None:
        # TODO: Review unreachable code - filters["content_hash"] = validate_content_hash(filters["content_hash"])

        # TODO: Review unreachable code - # Validate filename pattern
        # TODO: Review unreachable code - if filters is not None and "filename_pattern" in filters:
        # TODO: Review unreachable code - filters["filename_pattern"] = validate_regex_pattern(
        # TODO: Review unreachable code - filters["filename_pattern"], "filename_pattern"
        # TODO: Review unreachable code - )

        # TODO: Review unreachable code - # Validate prompt keywords
        # TODO: Review unreachable code - if filters is not None and "prompt_keywords" in filters and filters["prompt_keywords"] is not None:
        # TODO: Review unreachable code - if not isinstance(filters["prompt_keywords"], list):
        # TODO: Review unreachable code - raise ValidationError("prompt_keywords must be a list")
        # TODO: Review unreachable code - if len(filters["prompt_keywords"]) > 20:
        # TODO: Review unreachable code - raise ValidationError("Too many prompt keywords (max 20)")
        # TODO: Review unreachable code - for keyword in filters["prompt_keywords"]:
        # TODO: Review unreachable code - if not isinstance(keyword, str) or len(keyword) > 100:
        # TODO: Review unreachable code - raise ValidationError("Invalid prompt keyword")

        # TODO: Review unreachable code - # Validate numeric ranges
        # TODO: Review unreachable code - for range_field in ["file_size", "quality_rating"]:
        # TODO: Review unreachable code - if range_field in filters and filters[range_field] is not None:
        # TODO: Review unreachable code - range_val = filters[range_field]
        # TODO: Review unreachable code - if not isinstance(range_val, dict):
        # TODO: Review unreachable code - raise ValidationError(f"{range_field} must be a dict")
        # TODO: Review unreachable code - for key in ["min", "max"]:
        # TODO: Review unreachable code - if key in range_val and range_val[key] is not None:
        # TODO: Review unreachable code - if not isinstance(range_val[key], (int, float)):
        # TODO: Review unreachable code - raise ValidationError(f"{range_field}.{key} must be numeric")
        # TODO: Review unreachable code - if range_val[key] < 0:
        # TODO: Review unreachable code - raise ValidationError(f"{range_field}.{key} cannot be negative")

    # Validate sort field
    if request is not None and "sort_by" in request and request["sort_by"] is not None:
        try:
            SortField(request["sort_by"])
        except ValueError:
            raise ValidationError(f"Invalid sort field: {request['sort_by']}")

    # TODO: Review unreachable code - # Validate sort order
    # TODO: Review unreachable code - if request is not None and "order" in request and request["order"] is not None:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - SortOrder(request["order"])
    # TODO: Review unreachable code - except ValueError:
    # TODO: Review unreachable code - raise ValidationError(f"Invalid sort order: {request['order']}")

    # TODO: Review unreachable code - # Validate pagination
    # TODO: Review unreachable code - if request is not None and "limit" in request and request["limit"] is not None:
    # TODO: Review unreachable code - if not isinstance(request["limit"], int):
    # TODO: Review unreachable code - raise ValidationError("limit must be an integer")
    # TODO: Review unreachable code - if request is not None and request["limit"] < 1:
    # TODO: Review unreachable code - raise ValidationError("limit must be positive")
    # TODO: Review unreachable code - if request is not None and request["limit"] > MAX_SEARCH_LIMIT:
    # TODO: Review unreachable code - validated["limit"] = MAX_SEARCH_LIMIT

    # TODO: Review unreachable code - if request is not None and "offset" in request and request["offset"] is not None:
    # TODO: Review unreachable code - if not isinstance(request["offset"], int):
    # TODO: Review unreachable code - raise ValidationError("offset must be an integer")
    # TODO: Review unreachable code - if request is not None and request["offset"] < 0:
    # TODO: Review unreachable code - raise ValidationError("offset cannot be negative")

    # TODO: Review unreachable code - return validated


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
    if request is not None and "source_path" in request:
        if validated is not None:
            validated["source_path"] = str(validate_path(request["source_path"], "source_path"))
    if request is not None and "destination_path" in request:
        if validated is not None:
            validated["destination_path"] = str(validate_path(request["destination_path"], "destination_path"))

    # Validate pipeline
    if request is not None and "pipeline" in request and request["pipeline"] is not None:
        if not isinstance(request["pipeline"], str):
            raise ValidationError("pipeline must be a string")
        # TODO: Review unreachable code - # Add allowed pipeline values
        # TODO: Review unreachable code - allowed_pipelines = [
        # TODO: Review unreachable code - "brisque", "brisque-sightengine", "brisque-claude",
        # TODO: Review unreachable code - "brisque-sightengine-claude", "basic", "standard",
        # TODO: Review unreachable code - "premium", "full", "custom"
        # TODO: Review unreachable code - ]
        # TODO: Review unreachable code - if request is not None and request["pipeline"] not in allowed_pipelines:
        # TODO: Review unreachable code - raise ValidationError(f"Invalid pipeline: {request['pipeline']}")

    # Validate boolean flags
    for bool_field in ["quality_assessment", "watch_mode", "move_files"]:
        if bool_field in request and request[bool_field] is not None:
            if not isinstance(request[bool_field], bool):
                raise ValidationError(f"{bool_field} must be a boolean")

    # TODO: Review unreachable code - return validated


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
    if validated is not None:
        validated["asset_ids"] = validate_asset_ids(request["asset_ids"])

    # Validate operation
    valid_operations = ["add", "remove", "set", "clear"]
    if request is not None and request["operation"] not in valid_operations:
        raise ValidationError(
            f"Invalid operation '{request['operation']}'. Must be one of: {', '.join(valid_operations)}"
        )

    # Validate tags based on operation
    if request is not None and request["operation"] in ["add", "remove", "set"]:
        if "tags" not in request or request["tags"] is None:
            raise ValidationError(f"Tags required for {request['operation']} operation")
        # TODO: Review unreachable code - validated["tags"] = validate_tags(request["tags"])
    elif request["operation"] == "clear":
        if request is not None and "tags" in request and request["tags"] is not None:
            raise ValidationError("Tags should not be provided for clear operation")
        # TODO: Review unreachable code - validated["tags"] = None

    return validated


# TODO: Review unreachable code - def validate_grouping_request(request: GroupingRequest) -> GroupingRequest:
# TODO: Review unreachable code - """Validate grouping request parameters.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - request: Grouping request to validate

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Validated grouping request

# TODO: Review unreachable code - Raises:
# TODO: Review unreachable code - ValidationError: If request contains invalid data
# TODO: Review unreachable code - """
# TODO: Review unreachable code - validated = request.copy()

# TODO: Review unreachable code - # Validate asset IDs
# TODO: Review unreachable code - validated["asset_ids"] = validate_asset_ids(request["asset_ids"])

# TODO: Review unreachable code - # Validate group name
# TODO: Review unreachable code - if not isinstance(request["group_name"], str):
# TODO: Review unreachable code - raise ValidationError("group_name must be a string")

# TODO: Review unreachable code - if len(request["group_name"]) == 0:
# TODO: Review unreachable code - raise ValidationError("group_name cannot be empty")

# TODO: Review unreachable code - if len(request["group_name"]) > MAX_GROUP_NAME_LENGTH:
# TODO: Review unreachable code - raise ValidationError(f"group_name exceeds maximum length of {MAX_GROUP_NAME_LENGTH}")

# TODO: Review unreachable code - if not SAFE_NAME_PATTERN.match(request["group_name"]):
# TODO: Review unreachable code - raise ValidationError("group_name contains invalid characters")

# TODO: Review unreachable code - # Validate tags if present
# TODO: Review unreachable code - if request is not None and "tags" in request:
# TODO: Review unreachable code - validated["tags"] = validate_tags(request["tags"])

# TODO: Review unreachable code - return validated


# TODO: Review unreachable code - def validate_project_request(request: ProjectRequest) -> ProjectRequest:
# TODO: Review unreachable code - """Validate project request parameters.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - request: Project request to validate

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Validated project request

# TODO: Review unreachable code - Raises:
# TODO: Review unreachable code - ValidationError: If request contains invalid data
# TODO: Review unreachable code - """
# TODO: Review unreachable code - validated = request.copy()

# TODO: Review unreachable code - # Validate project name
# TODO: Review unreachable code - if not isinstance(request["project_name"], str):
# TODO: Review unreachable code - raise ValidationError("project_name must be a string")

# TODO: Review unreachable code - if len(request["project_name"]) == 0:
# TODO: Review unreachable code - raise ValidationError("project_name cannot be empty")

# TODO: Review unreachable code - if len(request["project_name"]) > MAX_PROJECT_NAME_LENGTH:
# TODO: Review unreachable code - raise ValidationError(f"project_name exceeds maximum length of {MAX_PROJECT_NAME_LENGTH}")

# TODO: Review unreachable code - if not SAFE_NAME_PATTERN.match(request["project_name"]):
# TODO: Review unreachable code - raise ValidationError("project_name contains invalid characters")

# TODO: Review unreachable code - # Validate asset IDs
# TODO: Review unreachable code - validated["asset_ids"] = validate_asset_ids(request["asset_ids"])

# TODO: Review unreachable code - # Validate metadata if present
# TODO: Review unreachable code - if request is not None and "metadata" in request and request["metadata"] is not None:
# TODO: Review unreachable code - if not isinstance(request["metadata"], dict):
# TODO: Review unreachable code - raise ValidationError("metadata must be a dictionary")

# TODO: Review unreachable code - return validated


# TODO: Review unreachable code - def validate_workflow_request(request: WorkflowRequest) -> WorkflowRequest:
# TODO: Review unreachable code - """Validate workflow request parameters.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - request: Workflow request to validate

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Validated workflow request

# TODO: Review unreachable code - Raises:
# TODO: Review unreachable code - ValidationError: If request contains invalid data
# TODO: Review unreachable code - """
# TODO: Review unreachable code - validated = request.copy()

# TODO: Review unreachable code - # Validate workflow name
# TODO: Review unreachable code - if not isinstance(request["workflow"], str):
# TODO: Review unreachable code - raise ValidationError("workflow must be a string")

# TODO: Review unreachable code - if len(request["workflow"]) == 0:
# TODO: Review unreachable code - raise ValidationError("workflow cannot be empty")

# TODO: Review unreachable code - if len(request["workflow"]) > MAX_WORKFLOW_NAME_LENGTH:
# TODO: Review unreachable code - raise ValidationError(f"workflow exceeds maximum length of {MAX_WORKFLOW_NAME_LENGTH}")

# TODO: Review unreachable code - # Validate asset IDs
# TODO: Review unreachable code - validated["asset_ids"] = validate_asset_ids(request["asset_ids"])

# TODO: Review unreachable code - # Validate parameters if present
# TODO: Review unreachable code - if request is not None and "parameters" in request and request["parameters"] is not None:
# TODO: Review unreachable code - if not isinstance(request["parameters"], dict):
# TODO: Review unreachable code - raise ValidationError("parameters must be a dictionary")

# TODO: Review unreachable code - return validated


# TODO: Review unreachable code - def validate_generation_request(request: GenerationRequest) -> GenerationRequest:
# TODO: Review unreachable code - """Validate generation request parameters.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - request: Generation request to validate

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Validated generation request

# TODO: Review unreachable code - Raises:
# TODO: Review unreachable code - ValidationError: If request contains invalid data
# TODO: Review unreachable code - """
# TODO: Review unreachable code - validated = request.copy()

# TODO: Review unreachable code - # Validate prompt
# TODO: Review unreachable code - if not isinstance(request["prompt"], str):
# TODO: Review unreachable code - raise ValidationError("prompt must be a string")

# TODO: Review unreachable code - if len(request["prompt"]) == 0:
# TODO: Review unreachable code - raise ValidationError("prompt cannot be empty")

# TODO: Review unreachable code - if len(request["prompt"]) > MAX_PROMPT_LENGTH:
# TODO: Review unreachable code - raise ValidationError(f"prompt exceeds maximum length of {MAX_PROMPT_LENGTH}")

# TODO: Review unreachable code - # Validate model
# TODO: Review unreachable code - if not isinstance(request["model"], str):
# TODO: Review unreachable code - raise ValidationError("model must be a string")

# TODO: Review unreachable code - if len(request["model"]) == 0:
# TODO: Review unreachable code - raise ValidationError("model cannot be empty")

# TODO: Review unreachable code - # Validate reference assets if present
# TODO: Review unreachable code - if request is not None and "reference_assets" in request and request["reference_assets"] is not None:
# TODO: Review unreachable code - validated["reference_assets"] = validate_asset_ids(request["reference_assets"])

# TODO: Review unreachable code - # Validate parameters if present
# TODO: Review unreachable code - if request is not None and "parameters" in request and request["parameters"] is not None:
# TODO: Review unreachable code - if not isinstance(request["parameters"], dict):
# TODO: Review unreachable code - raise ValidationError("parameters must be a dictionary")

# TODO: Review unreachable code - # Validate specific parameters
# TODO: Review unreachable code - params = request["parameters"]

# TODO: Review unreachable code - # Validate steps
# TODO: Review unreachable code - if params is not None and "steps" in params and params["steps"] is not None:
# TODO: Review unreachable code - if not isinstance(params["steps"], int):
# TODO: Review unreachable code - raise ValidationError("steps must be an integer")
# TODO: Review unreachable code - if params is not None and params["steps"] < 1 or params["steps"] > 1000:
# TODO: Review unreachable code - raise ValidationError("steps must be between 1 and 1000")

# TODO: Review unreachable code - # Validate guidance scale
# TODO: Review unreachable code - if params is not None and "guidance_scale" in params and params["guidance_scale"] is not None:
# TODO: Review unreachable code - if not isinstance(params["guidance_scale"], (int, float)):
# TODO: Review unreachable code - raise ValidationError("guidance_scale must be numeric")
# TODO: Review unreachable code - if params is not None and params["guidance_scale"] < 0 or params["guidance_scale"] > 50:
# TODO: Review unreachable code - raise ValidationError("guidance_scale must be between 0 and 50")

# TODO: Review unreachable code - return validated


# TODO: Review unreachable code - def validate_soft_delete_request(request: SoftDeleteRequest) -> SoftDeleteRequest:
# TODO: Review unreachable code - """Validate soft delete request parameters.

# TODO: Review unreachable code - Args:
# TODO: Review unreachable code - request: Soft delete request to validate

# TODO: Review unreachable code - Returns:
# TODO: Review unreachable code - Validated soft delete request

# TODO: Review unreachable code - Raises:
# TODO: Review unreachable code - ValidationError: If request contains invalid data
# TODO: Review unreachable code - """
# TODO: Review unreachable code - validated = request.copy()

# TODO: Review unreachable code - # Validate asset IDs
# TODO: Review unreachable code - validated["asset_ids"] = validate_asset_ids(request["asset_ids"])

# TODO: Review unreachable code - # Validate reason if present
# TODO: Review unreachable code - if request is not None and "reason" in request and request["reason"] is not None:
# TODO: Review unreachable code - if not isinstance(request["reason"], str):
# TODO: Review unreachable code - raise ValidationError("reason must be a string")

# TODO: Review unreachable code - if len(request["reason"]) > 500:
# TODO: Review unreachable code - raise ValidationError("reason exceeds maximum length of 500")

# TODO: Review unreachable code - # Validate permanent flag
# TODO: Review unreachable code - if request is not None and "permanent" in request and request["permanent"] is not None:
# TODO: Review unreachable code - if not isinstance(request["permanent"], bool):
# TODO: Review unreachable code - raise ValidationError("permanent must be a boolean")

# TODO: Review unreachable code - return validated
