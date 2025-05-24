"""Backward compatibility layer for events.

This module maintains compatibility while transitioning to the shared alice-events package.
New code should import from alice_events directly.
"""

import warnings

# Try to import from the new location
try:
    from alice_events import *
    warnings.warn(
        "Importing from alicemultiverse.events is deprecated. "
        "Please import from alice_events instead.",
        DeprecationWarning,
        stacklevel=2
    )
except ImportError:
    # Fall back to local imports if alice_events not installed
    from .base import *
    from .asset_events import *
    from .creative_events import *
    from .workflow_events import *
    
    try:
        from .persistence import *
        from .base_persistence import *
    except ImportError:
        pass