"""Custom exceptions for AliceMultiverse."""


class AliceMultiverseError(Exception):
    """Base exception for all AliceMultiverse errors."""



class ConfigurationError(AliceMultiverseError):
    """Raised when there's a configuration problem."""



class MediaAnalysisError(AliceMultiverseError):
    """Raised when media analysis fails."""



class QualityAssessmentError(AliceMultiverseError):
    """Raised when quality assessment fails."""



class CacheError(AliceMultiverseError):
    """Raised when cache operations fail."""



class APIError(AliceMultiverseError):
    """Raised when external API calls fail."""



class FileOperationError(AliceMultiverseError):
    """Raised when file operations fail."""



class ValidationError(AliceMultiverseError):
    """Raised when input validation fails."""

