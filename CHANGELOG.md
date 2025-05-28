# Changelog

All notable changes to AliceMultiverse will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Enhanced provider interface with BaseProvider abstract class
- Cost estimation with detailed breakdowns (CostEstimate type)
- Budget validation and BudgetExceededError for cost control
- Provider interface documentation for implementing new providers
- GenerationStartedEvent for tracking generation lifecycle
- Enhanced provider registry with comprehensive cost tracking
- Global and per-request budget management
- Provider selection based on cost and capabilities
- CLI commands for provider management (list, cost, enable/disable, budget)
- Cost reporting by provider, project, and daily aggregation
- Provider health monitoring and automatic disabling
- Event-driven architecture foundation with AsyncAPI documentation
- Content-addressed database system using SQLAlchemy
- Asset discovery system for finding moved files
- Event monitoring tools for real-time observation
- Comprehensive roadmap and vision documentation
- WebP and HEIC/HEIF format support with metadata embedding
- fal.ai provider integration with FLUX Pro and Kling models
- Support for video generation (Kling v1 and v2, including elements and lipsync)
- Comprehensive test suite for providers
- Detailed documentation for fal.ai provider usage

### Changed
- Extracted provider types into separate types.py module
- Enhanced ProviderCapabilities with streaming and batch support flags
- Improved provider event publishing with ProviderEventMixin
- Updated all documentation to reflect evolution toward creative workflow hub
- Unified all cache implementations into single UnifiedCache class
- Migrated from OmegaConf to dataclasses for configuration (with backward compatibility)
- Reorganized module structure for better maintainability

### Architecture
- Separated provider interface into base_provider.py (new) and base.py (deprecated)
- Implemented event publishing for all major operations
- Created event bus with middleware support
- Added AsyncAPI 3.0 specifications for all events
- Prepared foundation for service extraction

## [1.4.0] - 2024-01-14

### Added
- Unified command-line interface with `alice` command
- Multi-stage quality pipeline with configurable modes
- Watch mode for continuous file monitoring
- Cost optimization features for API usage

### Changed
- Consolidated all scripts into single entry point
- Improved metadata caching with content-based hashing
- Enhanced quality assessment with multiple providers

## [1.3.0] - 2023-12-20

### Added
- BRISQUE quality assessment integration
- SightEngine API support
- Claude API integration for defect detection
- Star rating system (1-5 stars)

### Changed
- Restructured output folders by quality rating
- Improved AI source detection patterns
- Enhanced metadata extraction

## [1.2.0] - 2023-11-15

### Added
- Support for 15+ AI generation tools
- Metadata caching system
- Project-based organization

### Changed
- Improved file naming with sequence numbers
- Better duplicate detection
- Performance optimizations

## [1.1.0] - 2023-10-01

### Added
- Basic media organization by date and project
- AI source detection from filenames
- Simple quality assessment

## [1.0.0] - 2023-09-01

### Added
- Initial release
- Basic file organization functionality
- Support for images and videos