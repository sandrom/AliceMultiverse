"""Constants and patterns for validation."""

import re

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