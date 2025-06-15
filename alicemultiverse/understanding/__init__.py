"""Advanced image understanding and analysis module."""

from .advanced_tagger import AdvancedTagger, ProjectTagVocabulary, TagVocabulary
from .analyzer import ImageAnalyzer
from .batch_analyzer import BatchAnalysisRequest, BatchAnalyzer, BatchProgress
from .custom_instructions import CustomInstructionManager, InstructionTemplate, ProjectInstructions
from .pipeline_stages import (
    AdvancedBatchUnderstandingStage,
    ImageUnderstandingStage,
    MultiProviderUnderstandingStage,
)
from .provider_optimizer import BudgetManager, ProviderMetrics, ProviderOptimizer
from .providers import (
    AnthropicImageAnalyzer,
    DeepSeekImageAnalyzer,
    GoogleAIImageAnalyzer,
    OpenAIImageAnalyzer,
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

    # Provider optimization
    "ProviderOptimizer",
    "BudgetManager",
    "ProviderMetrics",

    # Pipeline stages
    "ImageUnderstandingStage",
    "MultiProviderUnderstandingStage",
    "AdvancedBatchUnderstandingStage",
]
