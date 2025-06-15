"""Advanced image understanding and analysis module."""

from .advanced_tagger import AdvancedTagger, ProjectTagVocabulary, TagVocabulary
from .analyzer import ImageAnalyzer
from .batch_analyzer import BatchAnalysisRequest, BatchAnalyzer, BatchProgress
from .custom_instructions import CustomInstructionManager, InstructionTemplate, ProjectInstructions
# Pipeline stages have been removed - use simple_analysis functions instead
# Provider optimizer removed - simple cost tracking in results is sufficient
from .providers import (
    AnthropicImageAnalyzer,
    DeepSeekImageAnalyzer,
    GoogleAIImageAnalyzer,
    OpenAIImageAnalyzer,
)
# Simple functions for direct use
from .simple_analysis import (
    analyze_image,
    analyze_images_batch,
    estimate_analysis_cost,
    should_analyze_image,
)

__all__ = [
    # Core analyzer
    "ImageAnalyzer",

    # Provider implementations
    "AnthropicImageAnalyzer",
    "OpenAIImageAnalyzer",
    "GoogleAIImageAnalyzer",
    "DeepSeekImageAnalyzer",

    # Advanced tagging system
    "AdvancedTagger",
    "TagVocabulary",
    "ProjectTagVocabulary",

    # Custom instructions
    "CustomInstructionManager",
    "InstructionTemplate",
    "ProjectInstructions",

    # Batch processing
    "BatchAnalyzer",
    "BatchAnalysisRequest",
    "BatchProgress",


    
    # Simple functions
    "analyze_image",
    "analyze_images_batch",
    "estimate_analysis_cost",
    "should_analyze_image",
]
