"""
Advanced scene transition analysis for smooth visual flow.
"""

from .motion_analyzer import MotionAnalyzer
from .transition_matcher import TransitionMatcher
from .models import TransitionSuggestion, MotionVector, SceneCompatibility
from .morphing import (
    SubjectMorpher, 
    MorphingTransitionMatcher,
    SubjectRegion,
    MorphKeyframe,
    MorphTransition
)
from .color_flow import (
    ColorFlowAnalyzer,
    ColorPalette,
    LightingInfo,
    GradientTransition,
    ColorFlowAnalysis,
    analyze_sequence,
    export_analysis_for_editor
)
from .match_cuts import (
    MatchCutDetector,
    MatchCutAnalysis,
    find_match_cuts,
    export_match_cuts,
    MotionVector as MatchMotionVector,
    ShapeMatch
)
from .portal_effects import (
    PortalDetector,
    PortalEffectGenerator,
    PortalEffectAnalysis,
    Portal,
    PortalMatch,
    export_portal_effect
)
from .visual_rhythm import (
    VisualRhythmAnalyzer,
    RhythmAnalysis,
    VisualComplexity,
    EnergyProfile,
    PacingSuggestion,
    match_rhythm_to_music,
    export_rhythm_analysis
)

__all__ = [
    'MotionAnalyzer',
    'TransitionMatcher', 
    'TransitionSuggestion',
    'MotionVector',
    'SceneCompatibility',
    'SubjectMorpher',
    'MorphingTransitionMatcher',
    'SubjectRegion',
    'MorphKeyframe',
    'MorphTransition',
    'ColorFlowAnalyzer',
    'ColorPalette',
    'LightingInfo',
    'GradientTransition',
    'ColorFlowAnalysis',
    'analyze_sequence',
    'export_analysis_for_editor',
    'MatchCutDetector',
    'MatchCutAnalysis',
    'find_match_cuts',
    'export_match_cuts',
    'MatchMotionVector',
    'ShapeMatch',
    'PortalDetector',
    'PortalEffectGenerator',
    'PortalEffectAnalysis',
    'Portal',
    'PortalMatch',
    'export_portal_effect',
    'VisualRhythmAnalyzer',
    'RhythmAnalysis',
    'VisualComplexity',
    'EnergyProfile',
    'PacingSuggestion',
    'match_rhythm_to_music',
    'export_rhythm_analysis'
]