"""Built-in plugins that come with AliceMultiverse."""

from .upscale_effect import UpscaleEffectPlugin
from .style_transfer_effect import StyleTransferEffectPlugin
from .filter_effect import FilterEffectPlugin
from .watermark_effect import WatermarkEffectPlugin
from .custom_provider_example import CustomProviderPlugin
from .style_consistency_analyzer import StyleConsistencyAnalyzerPlugin
from .batch_enhancement_workflow import BatchEnhancementWorkflowPlugin

__all__ = [
    "UpscaleEffectPlugin",
    "StyleTransferEffectPlugin", 
    "FilterEffectPlugin",
    "WatermarkEffectPlugin",
    "CustomProviderPlugin",
    "StyleConsistencyAnalyzerPlugin",
    "BatchEnhancementWorkflowPlugin"
]