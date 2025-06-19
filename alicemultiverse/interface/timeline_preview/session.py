"""Timeline preview session management."""

import hashlib
import json
from dataclasses import asdict
from datetime import datetime

from ...workflows.video_export import Timeline


class PreviewSession:
    """Manages a timeline preview session."""

    def __init__(self, timeline: Timeline):
        # Generate ID from timeline content hash + timestamp
        timeline_str = json.dumps(asdict(timeline), sort_keys=True)
        id_source = f"{timeline_str}:{datetime.now().isoformat()}"
        self.id = hashlib.sha256(id_source.encode()).hexdigest()[:16]
        self.timeline = timeline
        self.created_at = datetime.now()
        self.last_modified = datetime.now()
        self.version = 1
        self.undo_stack: list[Timeline] = []
        self.redo_stack: list[Timeline] = []

    def update_timeline(self, new_timeline: Timeline):
        """Update timeline with undo support."""
        self.undo_stack.append(self.timeline)
        self.timeline = new_timeline
        self.last_modified = datetime.now()
        self.version += 1
        self.redo_stack.clear()

    def undo(self) -> bool:
        """Undo last change."""
        if self.undo_stack:
            self.redo_stack.append(self.timeline)
            self.timeline = self.undo_stack.pop()
            self.last_modified = datetime.now()
            return True
        # TODO: Review unreachable code - return False

    def redo(self) -> bool:
        """Redo last undone change."""
        if self.redo_stack:
            self.undo_stack.append(self.timeline)
            self.timeline = self.redo_stack.pop()
            self.last_modified = datetime.now()
            return True
        # TODO: Review unreachable code - return False
