"""Base plugin classes and interfaces."""

import logging
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Types of plugins supported."""
    PROVIDER = "provider"
    EFFECT = "effect"
    ANALYZER = "analyzer"
    EXPORTER = "exporter"
    WORKFLOW = "workflow"


@dataclass
class PluginMetadata:
    """Plugin metadata and configuration."""
    name: str
    version: str
    type: PluginType
    description: str
    author: str
    email: Optional[str] = None
    url: Optional[str] = None
    dependencies: List[str] = None
    config_schema: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.config_schema is None:
            self.config_schema = {}


class Plugin(ABC):
    """Base class for all plugins."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize plugin with configuration.
        
        Args:
            config: Plugin-specific configuration
        """
        self.config = config or {}
        self._initialized = False
    
    @property
    @abstractmethod
    def metadata(self) -> PluginMetadata:
        """Return plugin metadata."""
        pass
    
    @abstractmethod
    async def initialize(self) -> bool:
        """
        Initialize the plugin.
        
        Returns:
            True if initialization successful
        """
        pass
    
    @abstractmethod
    async def cleanup(self):
        """Clean up plugin resources."""
        pass
    
    def validate_config(self) -> bool:
        """
        Validate plugin configuration against schema.
        
        Returns:
            True if configuration is valid
        """
        # TODO: Implement JSON schema validation
        return True


class ProviderPlugin(Plugin):
    """Base class for provider plugins."""
    
    @abstractmethod
    async def generate(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate content based on request.
        
        Args:
            request: Generation request
            
        Returns:
            Generation result
        """
        pass
    
    @abstractmethod
    def get_supported_models(self) -> List[str]:
        """Return list of supported models."""
        pass
    
    @abstractmethod
    def estimate_cost(self, request: Dict[str, Any]) -> float:
        """Estimate cost for generation request."""
        pass


class EffectPlugin(Plugin):
    """Base class for effect plugins."""
    
    @abstractmethod
    async def apply(self, input_path: Path, output_path: Path, parameters: Dict[str, Any]) -> Path:
        """
        Apply effect to input file.
        
        Args:
            input_path: Input file path
            output_path: Output file path
            parameters: Effect parameters
            
        Returns:
            Path to processed file
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported file formats."""
        pass


class AnalyzerPlugin(Plugin):
    """Base class for analyzer plugins."""
    
    @abstractmethod
    async def analyze(self, input_path: Path) -> Dict[str, Any]:
        """
        Analyze input file.
        
        Args:
            input_path: File to analyze
            
        Returns:
            Analysis results
        """
        pass
    
    @abstractmethod
    def get_analysis_types(self) -> List[str]:
        """Return list of analysis types provided."""
        pass


class ExporterPlugin(Plugin):
    """Base class for exporter plugins."""
    
    @abstractmethod
    async def export(self, data: Dict[str, Any], output_path: Path, format: str) -> Path:
        """
        Export data to specified format.
        
        Args:
            data: Data to export
            output_path: Output file path
            format: Export format
            
        Returns:
            Path to exported file
        """
        pass
    
    @abstractmethod
    def get_supported_formats(self) -> List[str]:
        """Return list of supported export formats."""
        pass


class WorkflowPlugin(Plugin):
    """Base class for workflow plugins."""
    
    @abstractmethod
    async def execute(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute workflow.
        
        Args:
            inputs: Workflow inputs
            
        Returns:
            Workflow outputs
        """
        pass
    
    @abstractmethod
    def get_workflow_schema(self) -> Dict[str, Any]:
        """Return workflow input/output schema."""
        pass