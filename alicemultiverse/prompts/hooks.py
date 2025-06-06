"""Hooks for integrating prompt tracking with provider generation."""

from typing import Optional, Dict, Any, Callable
from functools import wraps
import time

from ..core.logging import get_logger
from ..providers.types import GenerationResult
from .integration import PromptProviderIntegration

logger = get_logger(__name__)

# Global integration instance
_prompt_integration: Optional[PromptProviderIntegration] = None


def get_prompt_integration() -> PromptProviderIntegration:
    """Get or create the global prompt integration instance."""
    global _prompt_integration
    if _prompt_integration is None:
        _prompt_integration = PromptProviderIntegration()
    return _prompt_integration


def track_prompt_usage(provider_name: str, project: Optional[str] = None):
    """Decorator to automatically track prompt usage in provider methods.
    
    Usage:
        @track_prompt_usage("midjourney")
        def generate(self, prompt: str, **kwargs) -> GenerationResult:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            result = None
            prompt_text = None
            
            try:
                # Extract prompt from arguments
                # Handle both positional and keyword arguments
                if len(args) > 1 and isinstance(args[1], str):
                    prompt_text = args[1]
                elif "prompt" in kwargs:
                    prompt_text = kwargs["prompt"]
                elif "text" in kwargs:
                    prompt_text = kwargs["text"]
                
                # Call the original function
                result = func(*args, **kwargs)
                
                # Track if we have a prompt and result
                if prompt_text and isinstance(result, GenerationResult):
                    duration = time.time() - start_time
                    integration = get_prompt_integration()
                    
                    # Extract project from kwargs or result metadata
                    actual_project = project
                    if not actual_project:
                        actual_project = kwargs.get("project") or \
                                       result.metadata.get("project")
                    
                    integration.track_generation(
                        provider=provider_name,
                        prompt_text=prompt_text,
                        result=result,
                        cost=result.cost,
                        duration=duration,
                        project=actual_project
                    )
                
                return result
                
            except Exception as e:
                logger.error(f"Error in prompt tracking: {e}")
                # Don't break the original function
                if result is None:
                    result = func(*args, **kwargs)
                return result
        
        return wrapper
    return decorator


def track_prompt_from_metadata(provider_name: str):
    """Decorator for providers that store prompts in metadata.
    
    Usage:
        @track_prompt_from_metadata("leonardo")
        def generate_from_config(self, config: Dict) -> GenerationResult:
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            start_time = time.time()
            
            try:
                # Call the original function
                result = func(*args, **kwargs)
                
                # Track if we have a result with metadata
                if isinstance(result, GenerationResult) and result.metadata:
                    integration = get_prompt_integration()
                    prompt_text = integration.extract_prompt_from_metadata(result.metadata)
                    
                    if prompt_text:
                        duration = time.time() - start_time
                        project = result.metadata.get("project")
                        
                        integration.track_generation(
                            provider=provider_name,
                            prompt_text=prompt_text,
                            result=result,
                            cost=result.cost,
                            duration=duration,
                            project=project
                        )
                
                return result
                
            except Exception as e:
                logger.error(f"Error in metadata prompt tracking: {e}")
                return result if 'result' in locals() else func(*args, **kwargs)
        
        return wrapper
    return decorator


class PromptTrackingMixin:
    """Mixin class for providers to add prompt tracking capabilities."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._prompt_integration = get_prompt_integration()
        self._enable_prompt_tracking = kwargs.get("track_prompts", True)
    
    def track_prompt(self, 
                    prompt: str,
                    result: GenerationResult,
                    provider: Optional[str] = None,
                    **kwargs) -> Optional[str]:
        """Track a prompt usage.
        
        Args:
            prompt: The prompt text
            result: Generation result
            provider: Provider name (defaults to class name)
            **kwargs: Additional tracking parameters
            
        Returns:
            Prompt ID if tracked
        """
        if not self._enable_prompt_tracking:
            return None
        
        try:
            provider_name = provider or self.__class__.__name__.replace("Provider", "").lower()
            
            return self._prompt_integration.track_generation(
                provider=provider_name,
                prompt_text=prompt,
                result=result,
                cost=kwargs.get("cost", result.cost),
                duration=kwargs.get("duration"),
                project=kwargs.get("project")
            )
        except Exception as e:
            logger.error(f"Failed to track prompt: {e}")
            return None


# Convenience function for manual tracking
def track_prompt_manually(
    provider: str,
    prompt: str,
    result: GenerationResult,
    **kwargs
) -> Optional[str]:
    """Manually track a prompt usage.
    
    Args:
        provider: Provider name
        prompt: Prompt text
        result: Generation result
        **kwargs: Additional parameters (cost, duration, project)
        
    Returns:
        Prompt ID if tracked
    """
    integration = get_prompt_integration()
    return integration.track_generation(
        provider=provider,
        prompt_text=prompt,
        result=result,
        **kwargs
    )