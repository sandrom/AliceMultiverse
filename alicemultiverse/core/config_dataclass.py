"""Configuration using dataclasses instead of OmegaConf."""

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import yaml

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
    understanding: bool = True  # Image understanding enabled by default
    watch: bool = False
    watch_interval: int = 5
    dry_run: bool = False
    # Pipeline has been removed - use understanding directly
    # API keys (can be set via CLI)
    sightengine_user: str | None = None
    sightengine_secret: str | None = None
    claude_api_key: str | None = None


@dataclass
class QualityThreshold:
    """Quality threshold range."""

    min: float
    max: float


@dataclass
class QualityConfig:
    """Quality assessment configuration."""

    thresholds: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "5_star": {"min": 0, "max": 25},
            "4_star": {"min": 25, "max": 45},
            "3_star": {"min": 45, "max": 65},
            "2_star": {"min": 65, "max": 80},
            "1_star": {"min": 80, "max": 100},
        }
    )
    max_dimension: int = 2048
    enabled: bool = False  # Alias for processing.quality


@dataclass
class AIGeneratorsConfig:
    """AI generator configuration."""

    image: list[str] = field(
        default_factory=lambda: ["stablediffusion", "midjourney", "dalle", "comfyui", "flux"]
    )
    video: list[str] = field(
        default_factory=lambda: ["runway", "kling", "pika", "stable-video", "animatediff"]
    )


@dataclass
class MetadataConfig:
    """Metadata configuration."""

    cache_version: str = "3.0.0"
    folder_name: str = ".metadata"


@dataclass
class StorageLocationConfig:
    """Configuration for a storage location."""

    name: str
    type: str = "local"  # local, s3, gcs, network
    path: str = ""
    priority: int = 0
    rules: list[dict] = field(default_factory=list)
    config: dict = field(default_factory=dict)


@dataclass
class StorageConfig:
    """Storage configuration."""

    search_db: str = "data/search.duckdb"
    location_registry_db: str = "data/locations.duckdb"
    project_paths: list[str] = field(default_factory=lambda: ["projects"])
    asset_paths: list[str] = field(default_factory=lambda: ["organized", "inbox"])
    sorted_out_path: str = "sorted-out"

    # New: Multiple storage locations
    locations: list[dict] = field(default_factory=list)

    # Legacy paths for backward compatibility
    use_legacy_paths: bool = True


@dataclass
class FileTypesConfig:
    """File types configuration."""

    image_extensions: list[str] = field(
        default_factory=lambda: [".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"]
    )
    video_extensions: list[str] = field(default_factory=lambda: [".mp4", ".mov"])


@dataclass
class PipelineConfig:
    """Pipeline configuration."""

    mode: str | None = None
    stages: list[str] = field(default_factory=list)
    cost_limit: float | None = None
    configurations: dict[str, dict[str, list[str]]] = field(
        default_factory=lambda: {
            "basic": {"stages": ["brisque"]},
            "standard": {"stages": ["brisque", "sightengine"]},
            "premium": {"stages": ["brisque", "sightengine", "claude"]},
        }
    )
    thresholds: dict[str, Any] = field(
        default_factory=lambda: {
            "brisque_min_stars": 3,
            "sightengine_min_stars": 4,
            "sightengine_min_quality": 0.7,
        }
    )
    scoring_weights: dict[str, dict[str, float]] = field(
        default_factory=lambda: {
            "standard": {"brisque": 0.6, "sightengine": 0.4},
            "premium": {"brisque": 0.4, "sightengine": 0.3, "claude": 0.3},
        }
    )
    star_thresholds: dict[str, float] = field(
        default_factory=lambda: {"5_star": 0.80, "4_star": 0.65}
    )
    cost_limits: dict[str, float] = field(
        default_factory=lambda: {"sightengine": 5.0, "claude": 10.0, "total": 20.0}
    )
    batch_sizes: dict[str, int] = field(
        default_factory=lambda: {"sightengine": 128, "claude": 10, "gpt4v": 10}
    )
    # Allow extra fields for backward compatibility
    extra_fields: dict[str, Any] = field(default_factory=dict)


@dataclass
class AnthropicConfig:
    """Anthropic provider configuration."""
    models: dict = field(default_factory=dict)
    default_model: str = "claude-opus-4-20250115"
    max_retries: int = 3
    timeout: int = 30


@dataclass
class DatabaseConfig:
    """Database configuration."""
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    pool_pre_ping: bool = True
    pool_echo: bool = False


@dataclass
class EventsConfig:
    """Events configuration."""
    channel_prefix: str = "alice_events"
    cleanup_interval: int = 3600
    retention_days: int = 7


@dataclass
class ProvidersConfig:
    """Provider configuration."""
    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    events: EventsConfig = field(default_factory=EventsConfig)


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
    providers: ProvidersConfig = field(default_factory=ProvidersConfig)
    storage: StorageConfig = field(default_factory=StorageConfig)

    def __post_init__(self) -> None:
        """Post-initialization processing."""
        # Sync quality.enabled with processing.quality
        self.quality.enabled = self.processing.quality

    def get(self, key: str, default: Any = None) -> Any:
        """Get attribute with dot notation support."""
        # TODO: Review unreachable code - try:
        parts = key.split(".")
        obj = self
        for part in parts:
            obj = getattr(obj, part)
        return obj
        # TODO: Review unreachable code - except AttributeError:
        # TODO: Review unreachable code - return default

    def set(self, key: str, value: Any) -> None:
        """Set attribute with dot notation support."""
        parts = key.split(".")
        obj = self
        for part in parts[:-1]:
            obj = getattr(obj, part)
        setattr(obj, parts[-1], value)

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    # TODO: Review unreachable code - def __contains__(self, key: str) -> bool:
    # TODO: Review unreachable code - """Support 'in' operator for checking if attribute exists."""
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - self.get(key)
    # TODO: Review unreachable code - return True
    # TODO: Review unreachable code - except AttributeError:
    # TODO: Review unreachable code - return False

    # TODO: Review unreachable code - @classmethod
    # TODO: Review unreachable code - def from_dict(cls, data: dict[str, Any]) -> "Config":
    # TODO: Review unreachable code - """Create from dictionary."""
    # TODO: Review unreachable code - config = cls()

    # TODO: Review unreachable code - # Update paths
    # TODO: Review unreachable code - if data is not None and "paths" in data:
    # TODO: Review unreachable code - config.paths = PathsConfig(**data["paths"])

    # TODO: Review unreachable code - # Update processing
    # TODO: Review unreachable code - if data is not None and "processing" in data:
    # TODO: Review unreachable code - config.processing = ProcessingConfig(**data["processing"])

    # TODO: Review unreachable code - # Update storage
    # TODO: Review unreachable code - if data is not None and "storage" in data:
    # TODO: Review unreachable code - config.storage = StorageConfig(**data["storage"])

    # TODO: Review unreachable code - # Update quality
    # TODO: Review unreachable code - if data is not None and "quality" in data:
    # TODO: Review unreachable code - quality_data = data["quality"]
    # TODO: Review unreachable code - config.quality = QualityConfig(**quality_data)

    # TODO: Review unreachable code - # Update other sections
    # TODO: Review unreachable code - if data is not None and "ai_generators" in data:
    # TODO: Review unreachable code - config.ai_generators = AIGeneratorsConfig(**data["ai_generators"])

    # TODO: Review unreachable code - if data is not None and "metadata" in data:
    # TODO: Review unreachable code - config.metadata = MetadataConfig(**data["metadata"])

    # TODO: Review unreachable code - if data is not None and "file_types" in data:
    # TODO: Review unreachable code - config.file_types = FileTypesConfig(**data["file_types"])

    # TODO: Review unreachable code - if data is not None and "providers" in data:
    # TODO: Review unreachable code - providers_data = data["providers"]
    # TODO: Review unreachable code - providers_config = ProvidersConfig()

    # TODO: Review unreachable code - if providers_data is not None and "anthropic" in providers_data:
    # TODO: Review unreachable code - providers_config.anthropic = AnthropicConfig(**providers_data["anthropic"])
    # TODO: Review unreachable code - if providers_data is not None and "database" in providers_data:
    # TODO: Review unreachable code - providers_config.database = DatabaseConfig(**providers_data["database"])
    # TODO: Review unreachable code - if providers_data is not None and "events" in providers_data:
    # TODO: Review unreachable code - providers_config.events = EventsConfig(**providers_data["events"])

    # TODO: Review unreachable code - config.providers = providers_config

    # TODO: Review unreachable code - if data is not None and "pipeline" in data:
    # TODO: Review unreachable code - pipeline_data = data["pipeline"].copy()
    # TODO: Review unreachable code - # Extract known fields
    # TODO: Review unreachable code - known_fields = {
    # TODO: Review unreachable code - "mode",
    # TODO: Review unreachable code - "stages",
    # TODO: Review unreachable code - "cost_limit",
    # TODO: Review unreachable code - "configurations",
    # TODO: Review unreachable code - "thresholds",
    # TODO: Review unreachable code - "scoring_weights",
    # TODO: Review unreachable code - "star_thresholds",
    # TODO: Review unreachable code - "cost_limits",
    # TODO: Review unreachable code - "batch_sizes",
    # TODO: Review unreachable code - }
    # TODO: Review unreachable code - extra = {k: v for k, v in pipeline_data.items() if k not in known_fields}
    # TODO: Review unreachable code - pipeline_args = {k: v for k, v in pipeline_data.items() if k in known_fields}
    # TODO: Review unreachable code - pipeline_args["extra_fields"] = extra
    # TODO: Review unreachable code - config.pipeline = PipelineConfig(**pipeline_args)

    # TODO: Review unreachable code - # Sync quality enabled flag
    # TODO: Review unreachable code - config.quality.enabled = config.processing.quality

    # TODO: Review unreachable code - return config


def load_config(config_path: Path | None = None, cli_overrides: list[str] | None = None) -> Config:
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
                if config_path.suffix in [".yaml", ".yml"]:
                    data = yaml.safe_load(f)
                elif config_path.suffix == ".json":
                    data = json.load(f)
                else:
                    raise ValueError(f"Unsupported config format: {config_path.suffix}")

            # TODO: Review unreachable code - if data:
            # TODO: Review unreachable code - config = Config.from_dict(data)
            # TODO: Review unreachable code - logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            from ..core.exceptions import ConfigurationError

            raise ConfigurationError(f"Failed to load configuration: {e}")
    # TODO: Review unreachable code - elif config_path and not config_path.exists():
    # TODO: Review unreachable code - logger.warning(f"Config file not found: {config_path}, using defaults")

    # TODO: Review unreachable code - # Apply CLI overrides
    # TODO: Review unreachable code - if cli_overrides:
    # TODO: Review unreachable code - for override in cli_overrides:
    # TODO: Review unreachable code - try:
    # TODO: Review unreachable code - key, value = override.split("=", 1)

    # TODO: Review unreachable code - # Convert string values to appropriate types
    # TODO: Review unreachable code - if value.lower() in ["true", "false"]:
    # TODO: Review unreachable code - value = value.lower() == "true"
    # TODO: Review unreachable code - elif value.isdigit():
    # TODO: Review unreachable code - value = int(value)
    # TODO: Review unreachable code - elif "." in value and all(p.isdigit() for p in value.split(".", 1)):
    # TODO: Review unreachable code - value = float(value)

    # TODO: Review unreachable code - config.set(key, value)
    # TODO: Review unreachable code - logger.debug(f"Applied override: {key}={value}")
    # TODO: Review unreachable code - except Exception as e:
    # TODO: Review unreachable code - logger.warning(f"Failed to apply override '{override}': {e}")

    # TODO: Review unreachable code - return config


def get_default_config() -> Config:
    """Get default configuration."""
    return Config()


# TODO: Review unreachable code - # Backward compatibility for OmegaConf style access
# TODO: Review unreachable code - class DictConfig(Config):
# TODO: Review unreachable code - """Wrapper to provide OmegaConf-like interface."""

# TODO: Review unreachable code - def __getitem__(self, key: str) -> Any:
# TODO: Review unreachable code - """Allow dictionary-style access."""
# TODO: Review unreachable code - return self.get(key) or 0

# TODO: Review unreachable code - def __setitem__(self, key: str, value: Any) -> None:
# TODO: Review unreachable code - """Allow dictionary-style setting."""
# TODO: Review unreachable code - self.set(key, value)
