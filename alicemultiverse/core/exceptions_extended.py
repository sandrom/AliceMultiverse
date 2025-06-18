"""Extended exception hierarchy for better error categorization and handling."""

from typing import Optional, Dict, Any, List
from pathlib import Path

from .exceptions import AliceMultiverseError


class RecoverableError(AliceMultiverseError):
    """Base class for errors that can be recovered from."""
    
    def __init__(self, message: str, recovery_hint: Optional[str] = None):
        super().__init__(message)
        self.recovery_hint = recovery_hint


class FatalError(AliceMultiverseError):
    """Base class for errors that cannot be recovered from."""
    pass


# File Operation Errors
class FileOperationError(RecoverableError):
    """Base class for file operation errors."""
    
    def __init__(self, 
                 message: str, 
                 file_path: Optional[Path] = None,
                 operation: Optional[str] = None,
                 recovery_hint: Optional[str] = None):
        super().__init__(message, recovery_hint)
        self.file_path = file_path
        self.operation = operation


class FileReadError(FileOperationError):
    """Error reading a file."""
    
    def __init__(self, file_path: Path, original_error: Exception):
        super().__init__(
            f"Failed to read file: {file_path}",
            file_path=file_path,
            operation="read",
            recovery_hint="Check file permissions and ensure file exists"
        )
        self.original_error = original_error


class FileWriteError(FileOperationError):
    """Error writing a file."""
    
    def __init__(self, file_path: Path, original_error: Exception):
        super().__init__(
            f"Failed to write file: {file_path}",
            file_path=file_path,
            operation="write",
            recovery_hint="Check disk space and write permissions"
        )
        self.original_error = original_error


class FileMoveError(FileOperationError):
    """Error moving a file."""
    
    def __init__(self, source: Path, destination: Path, original_error: Exception):
        super().__init__(
            f"Failed to move file from {source} to {destination}",
            file_path=source,
            operation="move",
            recovery_hint="Check source exists and destination is writable"
        )
        self.source = source
        self.destination = destination
        self.original_error = original_error


# Database Errors
class DatabaseError(RecoverableError):
    """Base class for database-related errors."""
    
    def __init__(self, 
                 message: str,
                 query: Optional[str] = None,
                 recovery_hint: Optional[str] = None):
        super().__init__(message, recovery_hint)
        self.query = query


class DatabaseConnectionError(DatabaseError):
    """Database connection failed."""
    
    def __init__(self, database_path: Path, original_error: Exception):
        super().__init__(
            f"Failed to connect to database: {database_path}",
            recovery_hint="Check database file exists and is not corrupted"
        )
        self.database_path = database_path
        self.original_error = original_error


class DatabaseTransactionError(DatabaseError):
    """Database transaction failed."""
    
    def __init__(self, operation: str, original_error: Exception):
        super().__init__(
            f"Database transaction failed during: {operation}",
            recovery_hint="Transaction rolled back, operation can be retried"
        )
        self.operation = operation
        self.original_error = original_error


# Processing Errors
class ProcessingError(RecoverableError):
    """Base class for processing errors."""
    
    def __init__(self,
                 message: str,
                 item: Optional[Any] = None,
                 stage: Optional[str] = None,
                 recovery_hint: Optional[str] = None):
        super().__init__(message, recovery_hint)
        self.item = item
        self.stage = stage


class MediaAnalysisError(ProcessingError):
    """Error analyzing media file."""
    
    def __init__(self, file_path: Path, stage: str, original_error: Exception):
        super().__init__(
            f"Failed to analyze media file: {file_path}",
            item=file_path,
            stage=stage,
            recovery_hint="File may be corrupted or in unsupported format"
        )
        self.file_path = file_path
        self.original_error = original_error


class MetadataExtractionError(ProcessingError):
    """Error extracting metadata."""
    
    def __init__(self, file_path: Path, original_error: Exception):
        super().__init__(
            f"Failed to extract metadata from: {file_path}",
            item=file_path,
            stage="metadata_extraction",
            recovery_hint="File may lack metadata or be in unsupported format"
        )
        self.file_path = file_path
        self.original_error = original_error


# API/Provider Errors
class ProviderError(RecoverableError):
    """Base class for provider-related errors."""
    
    def __init__(self,
                 message: str,
                 provider: Optional[str] = None,
                 recovery_hint: Optional[str] = None):
        super().__init__(message, recovery_hint)
        self.provider = provider


class APIRateLimitError(ProviderError):
    """API rate limit exceeded."""
    
    def __init__(self, provider: str, retry_after: Optional[int] = None):
        super().__init__(
            f"Rate limit exceeded for {provider}",
            provider=provider,
            recovery_hint=f"Retry after {retry_after} seconds" if retry_after else "Wait before retrying"
        )
        self.retry_after = retry_after


class APIAuthenticationError(ProviderError):
    """API authentication failed."""
    
    def __init__(self, provider: str):
        super().__init__(
            f"Authentication failed for {provider}",
            provider=provider,
            recovery_hint="Check API key configuration"
        )


class APITimeoutError(ProviderError):
    """API request timed out."""
    
    def __init__(self, provider: str, timeout: float):
        super().__init__(
            f"Request to {provider} timed out after {timeout}s",
            provider=provider,
            recovery_hint="Retry with longer timeout or check network connection"
        )
        self.timeout = timeout


# Batch Processing Errors
class BatchProcessingError(RecoverableError):
    """Error during batch processing."""
    
    def __init__(self,
                 message: str,
                 batch_size: int,
                 failed_items: List[Any],
                 successful_items: List[Any],
                 recovery_hint: Optional[str] = None):
        super().__init__(message, recovery_hint)
        self.batch_size = batch_size
        self.failed_items = failed_items
        self.successful_items = successful_items
        self.failure_rate = len(failed_items) / batch_size if batch_size > 0 else 0


class PartialBatchFailure(BatchProcessingError):
    """Some items in batch failed."""
    
    def __init__(self, 
                 batch_size: int,
                 failed_items: List[Any],
                 successful_items: List[Any]):
        super().__init__(
            f"Partial batch failure: {len(failed_items)} of {batch_size} items failed",
            batch_size=batch_size,
            failed_items=failed_items,
            successful_items=successful_items,
            recovery_hint="Failed items can be retried individually"
        )


# Resource Errors
class ResourceError(RecoverableError):
    """Base class for resource-related errors."""
    pass


class InsufficientDiskSpaceError(ResourceError):
    """Not enough disk space."""
    
    def __init__(self, required_bytes: int, available_bytes: int):
        required_mb = required_bytes / 1024 / 1024
        available_mb = available_bytes / 1024 / 1024
        super().__init__(
            f"Insufficient disk space: need {required_mb:.1f}MB, have {available_mb:.1f}MB",
            recovery_hint="Free up disk space or change output location"
        )
        self.required_bytes = required_bytes
        self.available_bytes = available_bytes


class MemoryError(ResourceError):
    """Out of memory."""
    
    def __init__(self, operation: str):
        super().__init__(
            f"Out of memory during: {operation}",
            recovery_hint="Reduce batch size or enable memory-constrained mode"
        )
        self.operation = operation


# Configuration Errors
class ConfigurationValidationError(FatalError):
    """Configuration validation failed."""
    
    def __init__(self, errors: Dict[str, str]):
        message = "Configuration validation failed:\n"
        for field, error in errors.items():
            message += f"  - {field}: {error}\n"
        super().__init__(message)
        self.errors = errors


# Cache Errors
class CacheError(RecoverableError):
    """Base class for cache-related errors."""
    pass


class CacheCorruptionError(CacheError):
    """Cache is corrupted."""
    
    def __init__(self, cache_path: Path):
        super().__init__(
            f"Cache corrupted at: {cache_path}",
            recovery_hint="Delete cache file and it will be regenerated"
        )
        self.cache_path = cache_path


class CacheVersionMismatchError(CacheError):
    """Cache version mismatch."""
    
    def __init__(self, expected_version: str, found_version: str):
        super().__init__(
            f"Cache version mismatch: expected {expected_version}, found {found_version}",
            recovery_hint="Cache will be regenerated with current version"
        )
        self.expected_version = expected_version
        self.found_version = found_version