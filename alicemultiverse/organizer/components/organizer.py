"""Media organizer implementation combining all mixins."""

from .base import MediaOrganizerBase
from .file_operations import FileOperationsMixin
from .media_analysis import MediaAnalysisMixin
from .organization_logic import OrganizationLogicMixin
from .process_file import ProcessFileMixin
from .search_operations import SearchOperationsMixin
from .statistics import StatisticsMixin
from .watch_mode import WatchModeMixin


class MediaOrganizer(
    MediaOrganizerBase,
    FileOperationsMixin,
    MediaAnalysisMixin,
    OrganizationLogicMixin,
    ProcessFileMixin,
    SearchOperationsMixin,
    StatisticsMixin,
    WatchModeMixin,
):
    """Main class for organizing AI-generated media files.
    
    This class combines all the functionality from various mixins to provide
    a complete media organization solution. It handles:
    
    - Finding and analyzing media files
    - Detecting AI generation sources
    - Organizing files by date/project/source
    - Quality assessment and rating
    - Understanding (semantic tagging)
    - Search indexing with perceptual hashing
    - Duplicate detection and cleanup
    - Watch mode for continuous monitoring
    - Comprehensive statistics tracking
    """

    pass  # All functionality comes from mixins
