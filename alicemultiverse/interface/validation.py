"""Input validation for Alice interface to prevent security issues and ensure data integrity."""

import re
from pathlib import Path

from ..core.exceptions import ValidationError
from .structured_models import (
    AssetRole,
    GenerationRequest,
    GroupingRequest,
    MediaType,
    OrganizeRequest,
    ProjectRequest,
    SearchRequest,
    SelectionCreateRequest,
    SelectionExportRequest,
    SelectionPurpose,
    SelectionSearchRequest,
    SelectionStatus,
    SelectionUpdateRequest,
    SoftDeleteRequest,
    SortField,
    SortOrder,
    TagUpdateRequest,
    WorkflowRequest,
)

# Security constants
MAX_PATH_LENGTH = 4096
MAX_TAG_LENGTH = 100
MAX_TAGS_PER_REQUEST = 100
MAX_ASSET_IDS = 1000
MAX_SEARCH_LIMIT = 1000
MAX_FILENAME_PATTERN_LENGTH = 500
MAX_PROMPT_LENGTH = 10000
MAX_GROUP_NAME_LENGTH = 255
MAX_PROJECT_NAME_LENGTH = 255
MAX_WORKFLOW_NAME_LENGTH = 255

# Regex patterns for validation
SAFE_TAG_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\s]+$')
SAFE_NAME_PATTERN = re.compile(r'^[a-zA-Z0-9_\-\s\.]+$')
CONTENT_HASH_PATTERN = re.compile(r'^[a-fA-F0-9]{64}$')  # SHA256 hash (case-insensitive)
SQL_INJECTION_PATTERNS = [
    re.compile(r'(union|select|insert|update|delete|drop|create|alter|exec|execute)', re.IGNORECASE),
    re.compile(r'(-{2}|/\*|\*/|;|\||\'|")', re.IGNORECASE),
]


def validate_path(path: str | None, param_name: str = "path") -> Path | None:
    """Validate and sanitize file system paths.
    
    Args:
        path: Path string to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated Path object or None
        
    Raises:
        ValidationError: If path is invalid or potentially malicious
    """
    if path is None:
        return None

    if not isinstance(path, str):
        raise ValidationError(f"{param_name} must be a string")

    if len(path) > MAX_PATH_LENGTH:
        raise ValidationError(f"{param_name} exceeds maximum length of {MAX_PATH_LENGTH}")

    # Check for null bytes before Path resolution
    if "\x00" in path:
        raise ValidationError(f"{param_name} contains null bytes")

    # Convert to Path object for validation
    try:
        path_obj = Path(path).resolve()
    except (ValueError, OSError) as e:
        raise ValidationError(f"Invalid {param_name}: {e}")

    # Prevent path traversal attacks
    if ".." in str(path):
        raise ValidationError(f"{param_name} contains path traversal sequence")

    return path_obj


def validate_tag(tag: str) -> str:
    """Validate a single tag.
    
    Args:
        tag: Tag string to validate
        
    Returns:
        Validated tag
        
    Raises:
        ValidationError: If tag is invalid
    """
    if not isinstance(tag, str):
        raise ValidationError("Tag must be a string")

    if len(tag) == 0:
        raise ValidationError("Tag cannot be empty")

    if len(tag) > MAX_TAG_LENGTH:
        raise ValidationError(f"Tag exceeds maximum length of {MAX_TAG_LENGTH}")

    # Check for SQL injection patterns first
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(tag):
            raise ValidationError("Tag contains potentially malicious content")

    if not SAFE_TAG_PATTERN.match(tag):
        raise ValidationError("Tag contains invalid characters")

    return tag.strip()


def validate_tags(tags: list[str] | None) -> list[str] | None:
    """Validate a list of tags.
    
    Args:
        tags: List of tags to validate
        
    Returns:
        Validated list of tags or None
        
    Raises:
        ValidationError: If any tag is invalid
    """
    if tags is None:
        return None

    if not isinstance(tags, list):
        raise ValidationError("Tags must be a list")

    if len(tags) > MAX_TAGS_PER_REQUEST:
        raise ValidationError(f"Too many tags (max {MAX_TAGS_PER_REQUEST})")

    validated_tags = []
    for tag in tags:
        validated_tags.append(validate_tag(tag))

    # Remove duplicates while preserving order
    seen = set()
    unique_tags = []
    for tag in validated_tags:
        if tag not in seen:
            seen.add(tag)
            unique_tags.append(tag)

    return unique_tags


def validate_content_hash(content_hash: str) -> str:
    """Validate content hash format.
    
    Args:
        content_hash: Content hash to validate
        
    Returns:
        Validated content hash
        
    Raises:
        ValidationError: If hash is invalid
    """
    if not isinstance(content_hash, str):
        raise ValidationError("Content hash must be a string")

    if not CONTENT_HASH_PATTERN.match(content_hash):
        raise ValidationError("Invalid content hash format (expected SHA256)")

    return content_hash.lower()


def validate_asset_ids(asset_ids: list[str]) -> list[str]:
    """Validate a list of asset IDs.
    
    Args:
        asset_ids: List of asset IDs to validate
        
    Returns:
        Validated list of asset IDs
        
    Raises:
        ValidationError: If any asset ID is invalid
    """
    if not isinstance(asset_ids, list):
        raise ValidationError("Asset IDs must be a list")

    if len(asset_ids) == 0:
        raise ValidationError("Asset IDs list cannot be empty")

    if len(asset_ids) > MAX_ASSET_IDS:
        raise ValidationError(f"Too many asset IDs (max {MAX_ASSET_IDS})")

    validated_ids = []
    for asset_id in asset_ids:
        validated_ids.append(validate_content_hash(asset_id))

    return validated_ids


def validate_regex_pattern(pattern: str | None, param_name: str = "pattern") -> str | None:
    """Validate a regex pattern.
    
    Args:
        pattern: Regex pattern to validate
        param_name: Parameter name for error messages
        
    Returns:
        Validated pattern or None
        
    Raises:
        ValidationError: If pattern is invalid
    """
    if pattern is None:
        return None

    if not isinstance(pattern, str):
        raise ValidationError(f"{param_name} must be a string")

    if len(pattern) > MAX_FILENAME_PATTERN_LENGTH:
        raise ValidationError(f"{param_name} exceeds maximum length")

    try:
        re.compile(pattern)
    except re.error as e:
        raise ValidationError(f"Invalid regex {param_name}: {e}")

    return pattern


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

    # Validate tag operations
    operation_count = 0
    if "add_tags" in request and request["add_tags"] is not None:
        validated["add_tags"] = validate_tags(request["add_tags"])
        operation_count += 1

    if "remove_tags" in request and request["remove_tags"] is not None:
        validated["remove_tags"] = validate_tags(request["remove_tags"])
        operation_count += 1

    if "set_tags" in request and request["set_tags"] is not None:
        validated["set_tags"] = validate_tags(request["set_tags"])
        operation_count += 1

    # Ensure at least one operation is specified
    if operation_count == 0:
        raise ValidationError("At least one tag operation must be specified")

    # Ensure set_tags is not used with other operations
    if "set_tags" in validated and validated["set_tags"] is not None and operation_count > 1:
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

    validated["group_name"] = request["group_name"].strip()

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
    if "project_name" in request:
        if not isinstance(request["project_name"], str):
            raise ValidationError("project_name must be a string")
        if len(request["project_name"]) == 0:
            raise ValidationError("project_name cannot be empty")
        if len(request["project_name"]) > MAX_PROJECT_NAME_LENGTH:
            raise ValidationError(f"project_name exceeds maximum length of {MAX_PROJECT_NAME_LENGTH}")
        if not SAFE_NAME_PATTERN.match(request["project_name"]):
            raise ValidationError("project_name contains invalid characters")
        validated["project_name"] = request["project_name"].strip()

    # Validate action
    if "action" in request and request["action"] is not None:
        if request["action"] not in ["create", "update", "delete"]:
            raise ValidationError(f"Invalid action: {request['action']}")

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
    if not isinstance(request["workflow_name"], str):
        raise ValidationError("workflow_name must be a string")
    if len(request["workflow_name"]) == 0:
        raise ValidationError("workflow_name cannot be empty")
    if len(request["workflow_name"]) > MAX_WORKFLOW_NAME_LENGTH:
        raise ValidationError(f"workflow_name exceeds maximum length of {MAX_WORKFLOW_NAME_LENGTH}")
    if not SAFE_NAME_PATTERN.match(request["workflow_name"]):
        raise ValidationError("workflow_name contains invalid characters")
    validated["workflow_name"] = request["workflow_name"].strip()

    # Validate dry_run flag
    if "dry_run" in request and request["dry_run"] is not None:
        if not isinstance(request["dry_run"], bool):
            raise ValidationError("dry_run must be a boolean")

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

    # Basic sanitization of prompt (allow more characters than tags)
    # But still check for obvious injection attempts
    for pattern in SQL_INJECTION_PATTERNS:
        if pattern.search(request["prompt"]):
            raise ValidationError("prompt contains potentially malicious content")

    validated["prompt"] = request["prompt"].strip()

    # Validate model
    if "model" in request and request["model"] is not None:
        if not isinstance(request["model"], str):
            raise ValidationError("model must be a string")
        if not SAFE_NAME_PATTERN.match(request["model"]):
            raise ValidationError("model contains invalid characters")

    # Validate reference assets
    if "reference_assets" in request and request["reference_assets"] is not None:
        validated["reference_assets"] = validate_asset_ids(request["reference_assets"])

    # Validate tags
    if "tags" in request:
        validated["tags"] = validate_tags(request["tags"])

    return validated


def validate_asset_role(role: str | AssetRole) -> AssetRole:
    """Validate asset role.
    
    Args:
        role: Role to validate
        
    Returns:
        Validated AssetRole enum
        
    Raises:
        ValidationError: If role is invalid
    """
    if isinstance(role, AssetRole):
        return role

    if not isinstance(role, str):
        raise ValidationError("role must be a string or AssetRole enum")

    try:
        return AssetRole(role)
    except ValueError:
        valid_roles = [r.value for r in AssetRole]
        raise ValidationError(f"Invalid role '{role}'. Valid roles: {valid_roles}")


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

    # Validate category
    valid_categories = ["broken", "duplicate", "maybe-later", "rejected", "archive"]
    if request["category"] not in valid_categories:
        raise ValidationError(f"Invalid category '{request['category']}'. Valid categories: {valid_categories}")

    # Validate reason if provided
    if "reason" in request and request["reason"] is not None:
        if not isinstance(request["reason"], str):
            raise ValidationError("reason must be a string")
        if len(request["reason"]) > 500:
            raise ValidationError("reason exceeds maximum length of 500 characters")
        # Check for malicious content
        for pattern in SQL_INJECTION_PATTERNS:
            if pattern.search(request["reason"]):
                raise ValidationError("reason contains potentially malicious content")
        validated["reason"] = request["reason"].strip()

    return validated


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
            if "asset_hash" not in item or not validate_content_hash(item["asset_hash"]):
                raise ValidationError(f"add_items[{i}] must have a valid asset_hash")
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
        if not validate_content_hash(request["containing_asset"]):
            raise ValidationError("containing_asset must be a valid content hash")
        validated["containing_asset"] = request["containing_asset"]

    return validated
