"""Advanced image understanding and analysis module."""

# TODO: Fix missing imports - classes are commented out
# from .advanced_tagger import AdvancedTagger, ProjectTagVocabulary, TagVocabulary
from .analyzer import ImageAnalyzer
from .batch_analyzer import BatchAnalysisRequest, BatchAnalyzer, BatchProgress
# TODO: Fix missing imports - classes are commented out in custom_instructions.py
# from .custom_instructions import CustomInstructionManager, InstructionTemplate, ProjectInstructions
from .custom_instructions import InstructionTemplate

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
    # "AdvancedTagger",
    # "TagVocabulary",
    # "ProjectTagVocabulary",

    # Custom instructions
    # "CustomInstructionManager",  # Class is commented out
    "InstructionTemplate",
    # "ProjectInstructions",  # Class is commented out

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
