"""Configuration using dataclasses instead of OmegaConf."""

from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Optional, List, Dict, Any
import json
import yaml
import logging

logger = logging.getLogger(__name__)


@dataclass
class PathsConfig:
    """Path configuration."""
    inbox: str = "inbox"
    organized: str = "organized"


@dataclass
class ProcessingConfig:
    """Processing configuration."""
    copy_mode: bool = True
    force_reindex: bool = False
    quality: bool = False
    watch: bool = False
    watch_interval: int = 5
    dry_run: bool = False
    pipeline: Optional[str] = None
    # API keys (can be set via CLI)
    sightengine_user: Optional[str] = None
    sightengine_secret: Optional[str] = None
    claude_api_key: Optional[str] = None


@dataclass
class QualityThreshold:
    """Quality threshold range."""
    min: float
    max: float


@dataclass
class QualityConfig:
    """Quality assessment configuration."""
    thresholds: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "5_star": {"min": 0, "max": 25},
        "4_star": {"min": 25, "max": 45},
        "3_star": {"min": 45, "max": 65},
        "2_star": {"min": 65, "max": 80},
        "1_star": {"min": 80, "max": 100}
    })
    max_dimension: int = 2048
    enabled: bool = False  # Alias for processing.quality


@dataclass
class AIGeneratorsConfig:
    """AI generator configuration."""
    image: List[str] = field(default_factory=lambda: [
        "stablediffusion", "midjourney", "dalle", "comfyui", "flux"
    ])
    video: List[str] = field(default_factory=lambda: [
        "runway", "kling", "pika", "stable-video", "animatediff"
    ])


@dataclass
class MetadataConfig:
    """Metadata configuration."""
    cache_version: str = "3.0.0"
    folder_name: str = ".metadata"


@dataclass
class FileTypesConfig:
    """File types configuration."""
    image_extensions: List[str] = field(default_factory=lambda: [
        ".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"
    ])
    video_extensions: List[str] = field(default_factory=lambda: [
        ".mp4", ".mov"
    ])


@dataclass
class PipelineConfig:
    """Pipeline configuration."""
    mode: Optional[str] = None
    stages: List[str] = field(default_factory=list)
    cost_limit: Optional[float] = None
    configurations: Dict[str, Dict[str, List[str]]] = field(default_factory=lambda: {
        "basic": {"stages": ["brisque"]},
        "standard": {"stages": ["brisque", "sightengine"]},
        "premium": {"stages": ["brisque", "sightengine", "claude"]}
    })
    thresholds: Dict[str, Any] = field(default_factory=lambda: {
        "brisque_min_stars": 3,
        "sightengine_min_stars": 4,
        "sightengine_min_quality": 0.7
    })
    scoring_weights: Dict[str, Dict[str, float]] = field(default_factory=lambda: {
        "standard": {"brisque": 0.6, "sightengine": 0.4},
        "premium": {"brisque": 0.4, "sightengine": 0.3, "claude": 0.3}
    })
    star_thresholds: Dict[str, float] = field(default_factory=lambda: {
        "5_star": 0.80,
        "4_star": 0.65
    })
    cost_limits: Dict[str, float] = field(default_factory=lambda: {
        "sightengine": 5.0,
        "claude": 10.0,
        "total": 20.0
    })
    batch_sizes: Dict[str, int] = field(default_factory=lambda: {
        "sightengine": 128,
        "claude": 10,
        "gpt4v": 10
    })
    # Allow extra fields for backward compatibility
    extra_fields: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Config:
    """Main configuration class."""
    paths: PathsConfig = field(default_factory=PathsConfig)
    processing: ProcessingConfig = field(default_factory=ProcessingConfig)
    quality: QualityConfig = field(default_factory=QualityConfig)
    ai_generators: AIGeneratorsConfig = field(default_factory=AIGeneratorsConfig)
    metadata: MetadataConfig = field(default_factory=MetadataConfig)
    file_types: FileTypesConfig = field(default_factory=FileTypesConfig)
    pipeline: PipelineConfig = field(default_factory=PipelineConfig)
    
    def __post_init__(self):
        """Post-initialization processing."""
        # Sync quality.enabled with processing.quality
        self.quality.enabled = self.processing.quality
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get attribute with dot notation support."""
        try:
            parts = key.split('.')
            obj = self
            for part in parts:
                obj = getattr(obj, part)
            return obj
        except AttributeError:
            return default
    
    def set(self, key: str, value: Any) -> None:
        """Set attribute with dot notation support."""
        parts = key.split('.')
        obj = self
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    def __contains__(self, key: str) -> bool:
        """Support 'in' operator for checking if attribute exists."""
        try:
            self.get(key)
            return True
        except AttributeError:
            return False
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Config':
        """Create from dictionary."""
        config = cls()
        
        # Update paths
        if 'paths' in data:
            config.paths = PathsConfig(**data['paths'])
        
        # Update processing
        if 'processing' in data:
            config.processing = ProcessingConfig(**data['processing'])
        
        # Update quality
        if 'quality' in data:
            quality_data = data['quality']
            config.quality = QualityConfig(**quality_data)
        
        # Update other sections
        if 'ai_generators' in data:
            config.ai_generators = AIGeneratorsConfig(**data['ai_generators'])
        
        if 'metadata' in data:
            config.metadata = MetadataConfig(**data['metadata'])
        
        if 'file_types' in data:
            config.file_types = FileTypesConfig(**data['file_types'])
        
        if 'pipeline' in data:
            pipeline_data = data['pipeline'].copy()
            # Extract known fields
            known_fields = {
                'mode', 'stages', 'cost_limit', 'configurations', 
                'thresholds', 'scoring_weights', 'star_thresholds', 
                'cost_limits', 'batch_sizes'
            }
            extra = {k: v for k, v in pipeline_data.items() if k not in known_fields}
            pipeline_args = {k: v for k, v in pipeline_data.items() if k in known_fields}
            pipeline_args['extra_fields'] = extra
            config.pipeline = PipelineConfig(**pipeline_args)
        
        # Sync quality enabled flag
        config.quality.enabled = config.processing.quality
        
        return config


def load_config(
    config_path: Optional[Path] = None,
    cli_overrides: Optional[List[str]] = None
) -> Config:
    """Load configuration from YAML file and apply CLI overrides.
    
    Args:
        config_path: Path to the configuration file. If None, uses default.
        cli_overrides: List of CLI overrides in format ["key=value", ...]
        
    Returns:
        Configuration object
        
    Raises:
        FileNotFoundError: If config file doesn't exist
        ValueError: If config file is invalid
    """
    # Default config path
    if config_path is None:
        config_path = Path(__file__).parent.parent.parent / "settings.yaml"
    
    # Start with default config
    config = Config()
    
    # Load from file if it exists
    if config_path and config_path.exists():
        try:
            with open(config_path) as f:
                if config_path.suffix in ['.yaml', '.yml']:
                    data = yaml.safe_load(f)
                elif config_path.suffix == '.json':
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_path.suffix}")
            
            if data:
                config = Config.from_dict(data)
                logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            from ..core.exceptions import ConfigurationError
            raise ConfigurationError(f"Failed to load configuration: {e}")
    elif config_path and not config_path.exists():
        logger.warning(f"Config file not found: {config_path}, using defaults")
    
    # Apply CLI overrides
    if cli_overrides:
        for override in cli_overrides:
            try:
                key, value = override.split('=', 1)
                
                # Convert string values to appropriate types
                if value.lower() in ['true', 'false']:
                    value = value.lower() == 'true'
                elif value.isdigit():
                    value = int(value)
                elif '.' in value and all(p.isdigit() for p in value.split('.', 1)):
                    value = float(value)
                
                config.set(key, value)
                logger.debug(f"Applied override: {key}={value}")
            except Exception as e:
                logger.warning(f"Failed to apply override '{override}': {e}")
    
    return config


def get_default_config() -> Config:
    """Get default configuration."""
    return Config()


# Backward compatibility for OmegaConf style access
class DictConfig(Config):
    """Wrapper to provide OmegaConf-like interface."""
    
    def __getitem__(self, key: str) -> Any:
        """Allow dictionary-style access."""
        return self.get(key)
    
    def __setitem__(self, key: str, value: Any) -> None:
        """Allow dictionary-style setting."""
        self.set(key, value)