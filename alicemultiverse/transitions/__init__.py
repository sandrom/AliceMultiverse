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
    'export_analysis_for_editor'
]