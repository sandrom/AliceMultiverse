"""Cloud storage scanner implementations for S3 and GCS.

This module provides scanning capabilities for cloud storage locations,
enabling multi-path storage across local and cloud infrastructure.
"""

import hashlib
from pathlib import Path

from ..core.structured_logging import get_logger
from .location_registry import StorageLocation, StorageType
from typing import Any

logger = get_logger(__name__)


class S3Scanner:
    """Scanner for Amazon S3 storage locations."""

    def __init__(self, location: StorageLocation):
        """Initialize S3 scanner.

        Args:
            location: Storage location configuration
        """
        self.location = location
        self.bucket_name = location.path
        self.prefix = location.config.get("prefix", "")
        self._client = None

    def _get_client(self):
        """Get or create S3 client."""
        if self._client is None:
            try:
                import boto3
                from botocore.exceptions import NoCredentialsError

                # Get credentials from location config or environment
                config = self.location.config
                if "aws_access_key_id" in config and "aws_secret_access_key" in config:
                    self._client = boto3.client(
                        's3',
                        aws_access_key_id=config["aws_access_key_id"],
                        aws_secret_access_key=config["aws_secret_access_key"],
                        region_name=config.get("region", "us-east-1")
                    )
                else:
                    # Use default credentials (IAM role, ~/.aws/credentials, etc.)
                    self._client = boto3.client('s3')

            except ImportError:
                raise ImportError(
                    "boto3 is required for S3 storage. "
                    "Install with: pip install boto3"
                )
            except NoCredentialsError:
                raise ValueError(
                    "No AWS credentials found. Either configure them in the "
                    "storage location or set up AWS credentials in your environment."
                )

        return self._client

    async def scan(self, show_progress: bool = True) -> dict[str, Any]:
        """Scan S3 bucket for media files.

        Args:
            show_progress: Whether to show progress

        Returns:
            Scan statistics
        """
        logger.info(f"Scanning S3 bucket: {self.bucket_name}")

        stats = {
            "files_found": 0,
            "total_size": 0,
            "media_files": []
        }

        try:
            client = self._get_client()

            # List objects in bucket
            paginator = client.get_paginator('list_objects_v2')
            page_iterator = paginator.paginate(
                Bucket=self.bucket_name,
                Prefix=self.prefix
            )

            media_extensions = {
                '.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif',
                '.mp4', '.mov', '.avi', '.mkv'
            }

            for page in page_iterator:
                if 'Contents' not in page:
                    continue

                for obj in page['Contents']:
                    key = obj['Key']
                    size = obj['Size']

                    # Check if it's a media file
                    if any(key.lower().endswith(ext) for ext in media_extensions):
                        stats["files_found"] += 1
                        stats["total_size"] += size

                        # Calculate content hash (would need to download file)
                        # For now, use S3 ETag as a placeholder
                        content_hash = obj['ETag'].strip('"')

                        stats["media_files"].append({
                            "path": f"s3://{self.bucket_name}/{key}",
                            "key": key,
                            "size": size,
                            "content_hash": content_hash,
                            "last_modified": obj['LastModified']
                        })

                        if show_progress and stats["files_found"] % 100 == 0:
                            logger.info(f"Scanned {stats['files_found']} files...")

            logger.info(
                f"S3 scan complete: {stats['files_found']} files, "
                f"{stats['total_size'] / (1024**3):.2f} GB"
            )

        except Exception as e:
            logger.error(f"Error scanning S3 bucket {self.bucket_name}: {e}")
            raise

        return stats

    async def download_file(self, key: str, local_path: Path) -> None:
        """Download a file from S3.

        Args:
            key: S3 object key
            local_path: Local path to save file
        """
        client = self._get_client()

        # Ensure parent directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Download file
        logger.info(f"Downloading s3://{self.bucket_name}/{key} to {local_path}")
        client.download_file(self.bucket_name, key, str(local_path))

    async def upload_file(self, local_path: Path, key: str) -> None:
        """Upload a file to S3.

        Args:
            local_path: Local file path
            key: S3 object key
        """
        client = self._get_client()

        # Upload file
        logger.info(f"Uploading {local_path} to s3://{self.bucket_name}/{key}")
        client.upload_file(str(local_path), self.bucket_name, key)

    async def calculate_content_hash(self, key: str) -> str:
        """Calculate SHA-256 hash of an S3 object.

        Args:
            key: S3 object key

        Returns:
            SHA-256 hash hex string
        """
        client = self._get_client()

        # Stream object and calculate hash
        hasher = hashlib.sha256()

        response = client.get_object(Bucket=self.bucket_name, Key=key)
        for chunk in response['Body'].iter_chunks(chunk_size=8192):
            hasher.update(chunk)

        return hasher.hexdigest()


class GCSScanner:
    """Scanner for Google Cloud Storage locations."""

    def __init__(self, location: StorageLocation):
        """Initialize GCS scanner.

        Args:
            location: Storage location configuration
        """
        self.location = location
        self.bucket_name = location.path
        self.prefix = location.config.get("prefix", "")
        self._client = None
        self._bucket = None

    def _get_client(self):
        """Get or create GCS client."""
        if self._client is None:
            try:
                from google.auth.exceptions import DefaultCredentialsError
                from google.cloud import storage

                # Get credentials from location config or environment
                config = self.location.config
                if "credentials_path" in config:
                    # Use service account key file
                    import os
                    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = config["credentials_path"]

                self._client = storage.Client()
                self._bucket = self._client.bucket(self.bucket_name)

            except ImportError:
                raise ImportError(
                    "google-cloud-storage is required for GCS storage. "
                    "Install with: pip install google-cloud-storage"
                )
            except DefaultCredentialsError:
                raise ValueError(
                    "No GCS credentials found. Either configure a credentials_path "
                    "in the storage location or set up Application Default Credentials."
                )

        return self._client, self._bucket

    async def scan(self, show_progress: bool = True) -> dict[str, Any]:
        """Scan GCS bucket for media files.

        Args:
            show_progress: Whether to show progress

        Returns:
            Scan statistics
        """
        logger.info(f"Scanning GCS bucket: {self.bucket_name}")

        stats = {
            "files_found": 0,
            "total_size": 0,
            "media_files": []
        }

        try:
            _, bucket = self._get_client()

            # List objects in bucket
            media_extensions = {
                '.png', '.jpg', '.jpeg', '.webp', '.heic', '.heif',
                '.mp4', '.mov', '.avi', '.mkv'
            }

            blobs = bucket.list_blobs(prefix=self.prefix)

            for blob in blobs:
                name = blob.name

                # Check if it's a media file
                if any(name.lower().endswith(ext) for ext in media_extensions):
                    stats["files_found"] += 1
                    stats["total_size"] += blob.size

                    # GCS provides MD5 hash, but we need SHA-256
                    # For now, use MD5 as a placeholder
                    content_hash = blob.md5_hash

                    stats["media_files"].append({
                        "path": f"gs://{self.bucket_name}/{name}",
                        "name": name,
                        "size": blob.size,
                        "content_hash": content_hash,
                        "last_modified": blob.time_created
                    })

                    if show_progress and stats["files_found"] % 100 == 0:
                        logger.info(f"Scanned {stats['files_found']} files...")

            logger.info(
                f"GCS scan complete: {stats['files_found']} files, "
                f"{stats['total_size'] / (1024**3):.2f} GB"
            )

        except Exception as e:
            logger.error(f"Error scanning GCS bucket {self.bucket_name}: {e}")
            raise

        return stats

    async def download_file(self, blob_name: str, local_path: Path) -> None:
        """Download a file from GCS.

        Args:
            blob_name: GCS blob name
            local_path: Local path to save file
        """
        _, bucket = self._get_client()

        # Ensure parent directory exists
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Download file
        logger.info(f"Downloading gs://{self.bucket_name}/{blob_name} to {local_path}")
        blob = bucket.blob(blob_name)
        blob.download_to_filename(str(local_path))

    async def upload_file(self, local_path: Path, blob_name: str) -> None:
        """Upload a file to GCS.

        Args:
            local_path: Local file path
            blob_name: GCS blob name
        """
        _, bucket = self._get_client()

        # Upload file
        logger.info(f"Uploading {local_path} to gs://{self.bucket_name}/{blob_name}")
        blob = bucket.blob(blob_name)
        blob.upload_from_filename(str(local_path))

    async def calculate_content_hash(self, blob_name: str) -> str:
        """Calculate SHA-256 hash of a GCS blob.

        Args:
            blob_name: GCS blob name

        Returns:
            SHA-256 hash hex string
        """
        _, bucket = self._get_client()

        # Stream blob and calculate hash
        hasher = hashlib.sha256()

        blob = bucket.blob(blob_name)
        for chunk in blob.download_as_bytes(chunk_size=8192):
            hasher.update(chunk)

        return hasher.hexdigest()


# Factory function to create appropriate scanner
def create_cloud_scanner(location: StorageLocation):
    """Create appropriate cloud scanner for storage location.

    Args:
        location: Storage location configuration

    Returns:
        Cloud scanner instance

    Raises:
        ValueError: If storage type is not supported
    """
    if location.type == StorageType.S3:
        return S3Scanner(location)
    elif location.type == StorageType.GCS:
        return GCSScanner(location)
    else:
        raise ValueError(f"Unsupported cloud storage type: {location.type}")
