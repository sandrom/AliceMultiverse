"""
Advanced scene transition analysis for smooth visual flow.
"""

from .color_flow import (
    ColorFlowAnalysis,
    ColorFlowAnalyzer,
    ColorPalette,
    GradientTransition,
    LightingInfo,
    analyze_sequence,
    export_analysis_for_editor,
)
from .match_cuts import (
    MatchCutAnalysis,
    MatchCutDetector,
    ShapeMatch,
    export_match_cuts,
    find_match_cuts,
)
from .match_cuts import MotionVector as MatchMotionVector
from .models import MotionVector, SceneCompatibility, TransitionSuggestion
from .morphing import (
    MorphingTransitionMatcher,
    MorphKeyframe,
    MorphTransition,
    SubjectMorpher,
    SubjectRegion,
)
from .motion_analyzer import MotionAnalyzer
from .portal_effects import (
    Portal,
    PortalDetector,
    PortalEffectAnalysis,
    PortalEffectGenerator,
    PortalMatch,
    export_portal_effect,
)
from .transition_matcher import TransitionMatcher
from .visual_rhythm import (
    EnergyProfile,
    PacingSuggestion,
    RhythmAnalysis,
    VisualComplexity,
    VisualRhythmAnalyzer,
    export_rhythm_analysis,
    match_rhythm_to_music,
)

__all__ = [
    'ColorFlowAnalysis',
    'ColorFlowAnalyzer',
    'ColorPalette',
    'EnergyProfile',
    'GradientTransition',
    'LightingInfo',
    'MatchCutAnalysis',
    'MatchCutDetector',
    'MatchMotionVector',
    'MorphKeyframe',
    'MorphTransition',
    'MorphingTransitionMatcher',
    'MotionAnalyzer',
    'MotionVector',
    'PacingSuggestion',
    'Portal',
    'PortalDetector',
    'PortalEffectAnalysis',
    'PortalEffectGenerator',
    'PortalMatch',
    'RhythmAnalysis',
    'SceneCompatibility',
    'ShapeMatch',
    'SubjectMorpher',
    'SubjectRegion',
    'TransitionMatcher',
    'TransitionSuggestion',
    'VisualComplexity',
    'VisualRhythmAnalyzer',
    'analyze_sequence',
    'export_analysis_for_editor',
    'export_match_cuts',
    'export_portal_effect',
    'export_rhythm_analysis',
    'find_match_cuts',
    'match_rhythm_to_music'
]
