"""Custom exceptions for AliceMultiverse."""


class AliceMultiverseError(Exception):
    """Base exception for all AliceMultiverse errors."""
    pass


class ConfigurationError(AliceMultiverseError):
    """Raised when there's a configuration problem."""
    pass


class MediaAnalysisError(AliceMultiverseError):
    """Raised when media analysis fails."""
    pass


class QualityAssessmentError(AliceMultiverseError):
    """Raised when quality assessment fails."""
    pass


class CacheError(AliceMultiverseError):
    """Raised when cache operations fail."""
    pass


class APIError(AliceMultiverseError):
    """Raised when external API calls fail."""
    pass


class FileOperationError(AliceMultiverseError):
    """Raised when file operations fail."""
    pass