"""Tests for cloud storage scanners."""

from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from alicemultiverse.storage.cloud_scanners import GCSScanner, S3Scanner, create_cloud_scanner
from alicemultiverse.storage.location_registry import StorageLocation, StorageType


class TestS3Scanner:
    """Test S3 scanner functionality."""

    def test_init(self):
        """Test S3 scanner initialization."""
        location = StorageLocation(
            location_id=None,
            name="S3 Test",
            type=StorageType.S3,
            path="test-bucket",
            priority=50,
            config={"prefix": "test/"}
        )

        scanner = S3Scanner(location)
        assert scanner.bucket_name == "test-bucket"
        assert scanner.prefix == "test/"

    @pytest.mark.asyncio
    async def test_scan_with_mock(self):
        """Test S3 scanning with mocked boto3."""
        location = StorageLocation(
            location_id=None,
            name="S3 Test",
            type=StorageType.S3,
            path="test-bucket",
            priority=50
        )

        # Mock boto3
        with patch('boto3.client') as mock_boto3_client:
            # Setup mock client
            mock_client = MagicMock()
            mock_boto3_client.return_value = mock_client

            # Mock paginator
            mock_paginator = MagicMock()
            mock_client.get_paginator.return_value = mock_paginator

            # Mock page iterator with test data
            mock_pages = [
                {
                    'Contents': [
                        {
                            'Key': 'project1/image1.png',
                            'Size': 1024,
                            'ETag': '"abc123"',
                            'LastModified': datetime.now()
                        },
                        {
                            'Key': 'project1/image2.jpg',
                            'Size': 2048,
                            'ETag': '"def456"',
                            'LastModified': datetime.now()
                        },
                        {
                            'Key': 'project1/document.pdf',  # Non-media file
                            'Size': 512,
                            'ETag': '"ghi789"',
                            'LastModified': datetime.now()
                        }
                    ]
                }
            ]
            mock_paginator.paginate.return_value = mock_pages

            scanner = S3Scanner(location)
            results = await scanner.scan(show_progress=False)

            # Verify results
            assert results["files_found"] == 2  # Only media files
            assert results["total_size"] == 3072  # 1024 + 2048
            assert len(results["media_files"]) == 2

            # Check first file
            first_file = results["media_files"][0]
            assert first_file["key"] == "project1/image1.png"
            assert first_file["size"] == 1024
            assert first_file["content_hash"] == "abc123"

    @pytest.mark.asyncio
    async def test_upload_file(self):
        """Test S3 file upload."""
        location = StorageLocation(
            location_id=None,
            name="S3 Test",
            type=StorageType.S3,
            path="test-bucket",
            priority=50
        )

        with patch('boto3.client') as mock_boto3_client:
            mock_client = MagicMock()
            mock_boto3_client.return_value = mock_client

            scanner = S3Scanner(location)

            # Create a fake local file path
            local_path = Path("/tmp/test.png")

            await scanner.upload_file(local_path, "uploads/test.png")

            # Verify upload was called
            mock_client.upload_file.assert_called_once_with(
                str(local_path),
                "test-bucket",
                "uploads/test.png"
            )


class TestGCSScanner:
    """Test GCS scanner functionality."""

    def test_init(self):
        """Test GCS scanner initialization."""
        location = StorageLocation(
            location_id=None,
            name="GCS Test",
            type=StorageType.GCS,
            path="test-bucket",
            priority=50,
            config={"prefix": "test/"}
        )

        scanner = GCSScanner(location)
        assert scanner.bucket_name == "test-bucket"
        assert scanner.prefix == "test/"

    @pytest.mark.asyncio
    async def test_scan_with_mock(self):
        """Test GCS scanning with mocked google-cloud-storage."""
        location = StorageLocation(
            location_id=None,
            name="GCS Test",
            type=StorageType.GCS,
            path="test-bucket",
            priority=50
        )

        # Mock google.cloud.storage
        with patch('google.cloud.storage.Client') as mock_storage_client:
            # Setup mock client and bucket
            mock_client = MagicMock()
            mock_bucket = MagicMock()
            mock_storage_client.return_value = mock_client
            mock_client.bucket.return_value = mock_bucket

            # Mock blob list
            mock_blob1 = MagicMock()
            mock_blob1.name = "project1/image1.png"
            mock_blob1.size = 1024
            mock_blob1.md5_hash = "abc123"
            mock_blob1.time_created = datetime.now()

            mock_blob2 = MagicMock()
            mock_blob2.name = "project1/video.mp4"
            mock_blob2.size = 4096
            mock_blob2.md5_hash = "def456"
            mock_blob2.time_created = datetime.now()

            mock_blob3 = MagicMock()
            mock_blob3.name = "project1/readme.txt"  # Non-media
            mock_blob3.size = 256
            mock_blob3.md5_hash = "ghi789"
            mock_blob3.time_created = datetime.now()

            mock_bucket.list_blobs.return_value = [mock_blob1, mock_blob2, mock_blob3]

            scanner = GCSScanner(location)
            results = await scanner.scan(show_progress=False)

            # Verify results
            assert results["files_found"] == 2  # Only media files
            assert results["total_size"] == 5120  # 1024 + 4096
            assert len(results["media_files"]) == 2


class TestCloudScannerFactory:
    """Test cloud scanner factory function."""

    def test_create_s3_scanner(self):
        """Test creating S3 scanner."""
        location = StorageLocation(
            location_id=None,
            name="S3",
            type=StorageType.S3,
            path="bucket",
            priority=50
        )

        scanner = create_cloud_scanner(location)
        assert isinstance(scanner, S3Scanner)

    def test_create_gcs_scanner(self):
        """Test creating GCS scanner."""
        location = StorageLocation(
            location_id=None,
            name="GCS",
            type=StorageType.GCS,
            path="bucket",
            priority=50
        )

        scanner = create_cloud_scanner(location)
        assert isinstance(scanner, GCSScanner)

    def test_unsupported_type(self):
        """Test error on unsupported storage type."""
        location = StorageLocation(
            location_id=None,
            name="Local",
            type=StorageType.LOCAL,
            path="/tmp",
            priority=50
        )

        with pytest.raises(ValueError, match="Unsupported cloud storage type"):
            create_cloud_scanner(location)
