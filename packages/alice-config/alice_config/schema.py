"""Configuration schema definitions."""

from typing import Any

from pydantic import BaseModel, Field


class PathsConfig(BaseModel):
    """Paths configuration."""

    inbox: str = Field(default="./inbox", description="Inbox directory")
    organized: str = Field(default="./organized", description="Organized output directory")
    cache: str = Field(default="~/.alicemultiverse/cache", description="Cache directory")
    logs: str = Field(default="./logs", description="Logs directory")


class ServiceConfigBase(BaseModel):
    """Base service configuration."""

    host: str = Field(default="0.0.0.0", description="Service host")
    port: int = Field(description="Service port")
    workers: int = Field(default=1, description="Number of workers")
    log_level: str = Field(default="INFO", description="Logging level")


class AliceInterfaceConfig(ServiceConfigBase):
    """Alice Interface service configuration."""

    port: int = 8000
    anthropic_api_key: str | None = None
    openai_api_key: str | None = None


class AssetProcessorConfig(ServiceConfigBase):
    """Asset Processor service configuration."""

    port: int = 8001
    batch_size: int = Field(default=100, description="Processing batch size")
    concurrent_tasks: int = Field(default=4, description="Concurrent processing tasks")


class QualityAnalyzerConfig(ServiceConfigBase):
    """Quality Analyzer service configuration."""

    port: int = 8002
    pipeline_mode: str = Field(default="basic", description="Pipeline mode")
    thresholds: dict[str, float] = Field(
        default_factory=lambda: {"5_star": 0.80, "4_star": 0.65, "3_star": 0.50}
    )


class MetadataExtractorConfig(ServiceConfigBase):
    """Metadata Extractor service configuration."""

    port: int = 8003
    extract_ai_params: bool = Field(default=True, description="Extract AI generation parameters")
    extract_exif: bool = Field(default=True, description="Extract EXIF data")


class ServiceConfigs(BaseModel):
    """All service configurations."""

    alice_interface: AliceInterfaceConfig = Field(default_factory=AliceInterfaceConfig)
    asset_processor: AssetProcessorConfig = Field(default_factory=AssetProcessorConfig)
    quality_analyzer: QualityAnalyzerConfig = Field(default_factory=QualityAnalyzerConfig)
    metadata_extractor: MetadataExtractorConfig = Field(default_factory=MetadataExtractorConfig)


class FeaturesConfig(BaseModel):
    """Feature flags configuration."""

    quality_assessment: bool = Field(default=True, description="Enable quality assessment")
    event_persistence: bool = Field(default=True, description="Enable event persistence")
    metadata_embedding: bool = Field(default=True, description="Embed metadata in files")
    watch_mode: bool = Field(default=False, description="Enable watch mode by default")


class RedisConfig(BaseModel):
    """Redis configuration."""

    url: str = Field(default="redis://localhost:6379", description="Redis URL")
    stream_prefix: str = Field(default="alice:events:", description="Event stream prefix")
    consumer_group: str = Field(default="alice-main", description="Consumer group name")
    max_stream_length: int = Field(default=100000, description="Maximum events per stream")


class ConfigSchema(BaseModel):
    """Complete configuration schema."""

    paths: PathsConfig = Field(default_factory=PathsConfig)
    services: ServiceConfigs = Field(default_factory=ServiceConfigs)
    features: FeaturesConfig = Field(default_factory=FeaturesConfig)
    redis: RedisConfig = Field(default_factory=RedisConfig)

    # Additional custom configuration
    custom: dict[str, Any] = Field(default_factory=dict)
