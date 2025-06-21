"""Tests for input validation module."""

import pytest

from alicemultiverse.core.exceptions import ValidationError
from alicemultiverse.interface.structured_models import (
    AssetRole,
    MediaType,
    SearchRequest,
    SortField,
    TagUpdateRequest,
)
from alicemultiverse.interface.validation import (
    validate_asset_ids,
    validate_asset_role,
    validate_content_hash,
    validate_generation_request,
    validate_grouping_request,
    validate_organize_request,
    validate_path,
    validate_regex_pattern,
    validate_search_request,
    validate_tag,
    validate_tag_update_request,
    validate_tags,
)


class TestPathValidation:
    """Test path validation."""

    def test_valid_path(self):
        """Test valid path validation."""
        result = validate_path("/Users/test/documents")
        assert result is not None
        assert str(result).startswith("/")

    def test_none_path(self):
        """Test None path returns None."""
        assert validate_path(None) is None

    def test_path_traversal_attack(self):
        """Test path traversal prevention."""
        with pytest.raises(ValidationError, match="path traversal"):
            validate_path("/Users/test/../../../etc/passwd")

    def test_null_byte_in_path(self):
        """Test null byte prevention."""
        with pytest.raises(ValidationError, match="null bytes"):
            validate_path("/Users/test/file\x00.txt")

    def test_path_too_long(self):
        """Test path length limit."""
        long_path = "/" + "a" * 5000
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            validate_path(long_path)


class TestTagValidation:
    """Test tag validation."""

    def test_valid_tag(self):
        """Test valid tag validation."""
        assert validate_tag("cyberpunk") == "cyberpunk"
        assert validate_tag("  fantasy  ") == "fantasy"
        assert validate_tag("sci-fi_2024") == "sci-fi_2024"

    def test_empty_tag(self):
        """Test empty tag rejection."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_tag("")

    def test_tag_too_long(self):
        """Test tag length limit."""
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            validate_tag("a" * 150)

    def test_tag_with_invalid_chars(self):
        """Test tag with invalid characters."""
        with pytest.raises(ValidationError, match="invalid characters"):
            validate_tag("tag@with#special")

    def test_tag_with_sql_injection(self):
        """Test SQL injection prevention."""
        with pytest.raises(ValidationError, match="invalid characters|malicious patterns"):
            validate_tag("'; DROP TABLE assets; --")

    def test_validate_tags_list(self):
        """Test tag list validation."""
        tags = ["cyberpunk", "fantasy", "  dark  ", "cyberpunk"]
        result = validate_tags(tags)
        assert result == ["cyberpunk", "fantasy", "dark"]  # Trimmed and deduplicated

    def test_validate_tags_none(self):
        """Test None tags returns None."""
        assert validate_tags(None) is None

    def test_too_many_tags(self):
        """Test tag count limit."""
        tags = [f"tag{i}" for i in range(150)]
        with pytest.raises(ValidationError, match="Too many tags"):
            validate_tags(tags)


class TestContentHashValidation:
    """Test content hash validation."""

    def test_valid_hash(self):
        """Test valid SHA256 hash."""
        hash_value = "a" * 64
        assert validate_content_hash(hash_value) == hash_value

    def test_uppercase_hash(self):
        """Test uppercase hash is converted to lowercase."""
        hash_value = "A" * 64
        assert validate_content_hash(hash_value) == "a" * 64

    def test_invalid_hash_length(self):
        """Test invalid hash length."""
        with pytest.raises(ValidationError, match="Invalid content hash"):
            validate_content_hash("abc123")

    def test_invalid_hash_chars(self):
        """Test invalid hash characters."""
        with pytest.raises(ValidationError, match="Invalid content hash"):
            validate_content_hash("g" * 64)  # 'g' is not valid hex


class TestAssetIDValidation:
    """Test asset ID validation."""

    def test_valid_asset_ids(self):
        """Test valid asset ID list."""
        ids = ["a" * 64, "b" * 64]
        result = validate_asset_ids(ids)
        assert result == ids

    def test_empty_asset_ids(self):
        """Test empty asset ID list."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_asset_ids([])

    def test_too_many_asset_ids(self):
        """Test asset ID count limit."""
        ids = ["a" * 64 for _ in range(1500)]
        with pytest.raises(ValidationError, match="Too many asset IDs"):
            validate_asset_ids(ids)


class TestRegexPatternValidation:
    """Test regex pattern validation."""

    def test_valid_regex(self):
        """Test valid regex pattern."""
        assert validate_regex_pattern(r"\.jpg$") == r"\.jpg$"
        assert validate_regex_pattern(r"[0-9]+") == r"[0-9]+"

    def test_none_regex(self):
        """Test None regex returns None."""
        assert validate_regex_pattern(None) is None

    def test_invalid_regex(self):
        """Test invalid regex pattern."""
        with pytest.raises(ValidationError, match="Invalid regex"):
            validate_regex_pattern(r"[unclosed")

    def test_regex_too_long(self):
        """Test regex length limit."""
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            validate_regex_pattern("a" * 600)


class TestSearchRequestValidation:
    """Test search request validation."""

    def test_minimal_search_request(self):
        """Test minimal valid search request."""
        request: SearchRequest = {
            "filters": {},
            "sort_by": None,
            "order": None,
            "limit": None,
            "offset": None,
        }
        result = validate_search_request(request)
        assert result == request

    def test_search_with_filters(self):
        """Test search with various filters."""
        request: SearchRequest = {
            "filters": {
                "media_type": MediaType.IMAGE,
                "tags": ["cyberpunk", "fantasy"],
                "content_hash": "a" * 64,
                "filename_pattern": r"\.jpg$",
                "quality_rating": {"min": 0, "max": 5},
            },
            "sort_by": SortField.CREATED_DATE,
            "order": "desc",
            "limit": 50,
            "offset": 0,
        }
        result = validate_search_request(request)
        assert result["filters"]["tags"] == ["cyberpunk", "fantasy"]

    def test_invalid_media_type(self):
        """Test invalid media type."""
        request: SearchRequest = {
            "filters": {"media_type": "invalid"},
            "sort_by": None,
            "order": None,
            "limit": None,
            "offset": None,
        }
        with pytest.raises(ValidationError, match="Invalid media type"):
            validate_search_request(request)

    def test_search_limit_capped(self):
        """Test search limit is capped."""
        request: SearchRequest = {
            "filters": {},
            "sort_by": None,
            "order": None,
            "limit": 5000,
            "offset": None,
        }
        result = validate_search_request(request)
        assert result["limit"] == 1000  # Capped to MAX_SEARCH_LIMIT

    def test_negative_offset(self):
        """Test negative offset rejection."""
        request: SearchRequest = {
            "filters": {},
            "sort_by": None,
            "order": None,
            "limit": None,
            "offset": -1,
        }
        with pytest.raises(ValidationError, match="offset cannot be negative"):
            validate_search_request(request)


class TestOrganizeRequestValidation:
    """Test organize request validation."""

    def test_valid_organize_request(self):
        """Test valid organize request."""
        request = {
            "source_path": "/Users/test/inbox",
            "destination_path": "/Users/test/organized",
            "pipeline": "standard",
            "quality_assessment": True,
            "watch_mode": False,
        }
        result = validate_organize_request(request)
        assert result["source_path"].startswith("/")

    def test_invalid_pipeline(self):
        """Test invalid pipeline name."""
        request = {"pipeline": "invalid-pipeline"}
        with pytest.raises(ValidationError, match="Invalid pipeline"):
            validate_organize_request(request)

    def test_non_boolean_flags(self):
        """Test non-boolean flag rejection."""
        request = {"quality_assessment": "yes"}
        with pytest.raises(ValidationError, match="must be a boolean"):
            validate_organize_request(request)


class TestTagUpdateRequestValidation:
    """Test tag update request validation."""

    def test_add_tags_request(self):
        """Test adding tags request."""
        request: TagUpdateRequest = {
            "asset_ids": ["a" * 64],
            "add_tags": ["cyberpunk", "fantasy"],
            "remove_tags": None,
            "set_tags": None,
        }
        result = validate_tag_update_request(request)
        assert result["add_tags"] == ["cyberpunk", "fantasy"]

    def test_set_tags_exclusive(self):
        """Test set_tags cannot be used with other operations."""
        request: TagUpdateRequest = {
            "asset_ids": ["a" * 64],
            "add_tags": ["tag1"],
            "set_tags": ["tag2"],
            "remove_tags": None,
        }
        with pytest.raises(ValidationError, match="cannot be used with"):
            validate_tag_update_request(request)

    def test_no_operations(self):
        """Test at least one operation required."""
        request: TagUpdateRequest = {
            "asset_ids": ["a" * 64],
            "add_tags": None,
            "remove_tags": None,
            "set_tags": None,
        }
        with pytest.raises(ValidationError, match="At least one"):
            validate_tag_update_request(request)


class TestGroupingRequestValidation:
    """Test grouping request validation."""

    def test_valid_grouping_request(self):
        """Test valid grouping request."""
        request = {
            "asset_ids": ["a" * 64, "b" * 64],
            "group_name": "My Collection",
        }
        result = validate_grouping_request(request)
        assert result["group_name"] == "My Collection"

    def test_empty_group_name(self):
        """Test empty group name rejection."""
        request = {
            "asset_ids": ["a" * 64],
            "group_name": "",
        }
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_grouping_request(request)

    def test_group_name_too_long(self):
        """Test group name length limit."""
        request = {
            "asset_ids": ["a" * 64],
            "group_name": "a" * 300,
        }
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            validate_grouping_request(request)


class TestGenerationRequestValidation:
    """Test generation request validation."""

    def test_valid_generation_request(self):
        """Test valid generation request."""
        request = {
            "prompt": "A cyberpunk city at night",
            "model": "flux-dev",
            "tags": ["cyberpunk", "city"],
        }
        result = validate_generation_request(request)
        assert result["prompt"] == "A cyberpunk city at night"

    def test_empty_prompt(self):
        """Test empty prompt rejection."""
        request = {"prompt": ""}
        with pytest.raises(ValidationError, match="cannot be empty"):
            validate_generation_request(request)

    def test_prompt_too_long(self):
        """Test prompt length limit."""
        request = {"prompt": "a" * 15000}
        with pytest.raises(ValidationError, match="exceeds maximum length"):
            validate_generation_request(request)

    def test_prompt_with_sql_injection(self):
        """Test SQL injection in prompt."""
        request = {"prompt": "Generate '; DROP TABLE assets; --"}
        with pytest.raises(ValidationError, match="malicious content"):
            validate_generation_request(request)


class TestAssetRoleValidation:
    """Test asset role validation."""

    def test_valid_role_string(self):
        """Test valid role string."""
        assert validate_asset_role("hero") == AssetRole.HERO
        assert validate_asset_role("b_roll") == AssetRole.B_ROLL

    def test_valid_role_enum(self):
        """Test valid role enum."""
        assert validate_asset_role(AssetRole.FINAL) == AssetRole.FINAL

    def test_invalid_role(self):
        """Test invalid role."""
        with pytest.raises(ValidationError, match="Invalid asset role"):
            validate_asset_role("invalid_role")
