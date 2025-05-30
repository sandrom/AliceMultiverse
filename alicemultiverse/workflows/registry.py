"""Registry for workflow templates."""

import logging
from typing import Dict, List, Optional, Type

from .base import WorkflowTemplate

logger = logging.getLogger(__name__)


class WorkflowRegistry:
    """Registry for discovering and managing workflow templates."""
    
    def __init__(self):
        """Initialize workflow registry."""
        self._workflows: Dict[str, Type[WorkflowTemplate]] = {}
        self._register_builtin_workflows()
    
    def _register_builtin_workflows(self):
        """Register built-in workflow templates."""
        # Import here to avoid circular imports
        try:
            from .templates.image_enhancement import ImageEnhancementWorkflow
            from .templates.video_pipeline import VideoProductionWorkflow
            from .templates.style_transfer import StyleTransferWorkflow
            
            self.register("image_enhancement", ImageEnhancementWorkflow)
            self.register("video_production", VideoProductionWorkflow)
            self.register("style_transfer", StyleTransferWorkflow)
            
            # Aliases for convenience
            self.register("enhance", ImageEnhancementWorkflow)
            self.register("upscale", ImageEnhancementWorkflow)
            self.register("video", VideoProductionWorkflow)
            
        except ImportError as e:
            logger.warning(f"Could not import built-in workflows: {e}")
    
    def register(self, name: str, workflow_class: Type[WorkflowTemplate]):
        """Register a workflow template.
        
        Args:
            name: Workflow name
            workflow_class: Workflow template class
        """
        self._workflows[name.lower()] = workflow_class
        logger.info(f"Registered workflow: {name}")
    
    def get(self, name: str) -> Optional[Type[WorkflowTemplate]]:
        """Get a workflow template by name.
        
        Args:
            name: Workflow name
            
        Returns:
            Workflow template class or None
        """
        return self._workflows.get(name.lower())
    
    def list(self) -> List[str]:
        """List available workflow names.
        
        Returns:
            List of workflow names
        """
        return list(self._workflows.keys())
    
    def get_info(self, name: str) -> Optional[Dict[str, any]]:
        """Get information about a workflow.
        
        Args:
            name: Workflow name
            
        Returns:
            Workflow information or None
        """
        workflow_class = self.get(name)
        if not workflow_class:
            return None
            
        # Create a temporary instance to get info
        workflow = workflow_class()
        
        return {
            "name": workflow.name,
            "description": workflow.get_description(),
            "required_providers": workflow.get_required_providers(),
            "class": workflow_class.__name__,
            "module": workflow_class.__module__,
        }


# Global registry instance
_registry = WorkflowRegistry()


def get_workflow(name: str) -> Optional[WorkflowTemplate]:
    """Get a workflow template instance by name.
    
    Args:
        name: Workflow name
        
    Returns:
        Workflow template instance or None
    """
    workflow_class = _registry.get(name)
    if workflow_class:
        return workflow_class()
    return None


def list_workflows() -> List[str]:
    """List available workflow names.
    
    Returns:
        List of workflow names
    """
    return _registry.list()


def register_workflow(name: str, workflow_class: Type[WorkflowTemplate]):
    """Register a custom workflow template.
    
    Args:
        name: Workflow name
        workflow_class: Workflow template class
    """
    _registry.register(name, workflow_class)


def get_workflow_info(name: str) -> Optional[Dict[str, any]]:
    """Get information about a workflow.
    
    Args:
        name: Workflow name
        
    Returns:
        Workflow information or None
    """
    return _registry.get_info(name)