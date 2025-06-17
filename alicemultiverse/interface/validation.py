"""Input validation - Compatibility layer for the refactored modular validation.

This module maintains backward compatibility while the implementation
has been refactored into modular components in the validation/ directory.
"""

from .validation import (
    CONTENT_HASH_PATTERN,
    MAX_ASSET_IDS,
    MAX_FILENAME_PATTERN_LENGTH,
    MAX_GROUP_NAME_LENGTH,
    # Constants
    MAX_PATH_LENGTH,
    MAX_PROJECT_NAME_LENGTH,
    MAX_PROMPT_LENGTH,
    MAX_SEARCH_LIMIT,
    MAX_TAG_LENGTH,
    MAX_TAGS_PER_REQUEST,
    MAX_WORKFLOW_NAME_LENGTH,
    SAFE_NAME_PATTERN,
    SAFE_TAG_PATTERN,
    SQL_INJECTION_PATTERNS,
    validate_asset_ids,
    validate_asset_role,
    validate_content_hash,
    validate_generation_request,
    validate_grouping_request,
    validate_organize_request,
    # Basic validators
    validate_path,
    validate_project_request,
    validate_regex_pattern,
    # Request validators
    validate_search_request,
    # Selection validators
    validate_selection_create_request,
    validate_selection_export_request,
    validate_selection_search_request,
    validate_selection_update_request,
    validate_soft_delete_request,
    validate_tag,
    validate_tag_update_request,
    validate_tags,
    validate_workflow_request,
)

__all__ = [
    # Constants
    "MAX_PATH_LENGTH",
    "MAX_TAG_LENGTH",
    "MAX_TAGS_PER_REQUEST",
    "MAX_ASSET_IDS",
    "MAX_SEARCH_LIMIT",
    "MAX_FILENAME_PATTERN_LENGTH",
    "MAX_PROMPT_LENGTH",
    "MAX_GROUP_NAME_LENGTH",
    "MAX_PROJECT_NAME_LENGTH",
    "MAX_WORKFLOW_NAME_LENGTH",
    "SAFE_TAG_PATTERN",
    "SAFE_NAME_PATTERN",
    "CONTENT_HASH_PATTERN",
    "SQL_INJECTION_PATTERNS",
    # Basic validators
    "validate_path",
    "validate_tag",
    "validate_tags",
    "validate_content_hash",
    "validate_asset_ids",
    "validate_regex_pattern",
    "validate_asset_role",
    # Request validators
    "validate_search_request",
    "validate_organize_request",
    "validate_tag_update_request",
    "validate_grouping_request",
    "validate_project_request",
    "validate_workflow_request",
    "validate_generation_request",
    "validate_soft_delete_request",
    # Selection validators
    "validate_selection_create_request",
    "validate_selection_update_request",
    "validate_selection_export_request",
    "validate_selection_search_request",
]
