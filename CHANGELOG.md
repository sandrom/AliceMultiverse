# Changelog

All notable changes to AliceMultiverse will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (2025-06-05) - Code Cleanup Sprint
- **Repository Cleanup**: Reduced clutter and improved maintainability
  - Updated ROADMAP.md with focused priorities
  - Removed performance testing from immediate priorities (focus on smaller subsets first)
  - Added detailed implementation plans for next focus areas

### Removed (2025-06-05)
- Removed `alice_interface_v2.py` - incomplete compatibility layer that was never used
- Removed `redis_event_migration.py` example - migration to optional Redis completed

### Added (2025-06-04) - Cost Tracking & CLI Improvements
- **Cost Tracking System**: Monitor and control AI API spending
  - Real-time cost tracking per provider and category
  - Budget management with daily/monthly limits
  - Cost warnings before expensive operations
  - CLI commands: `alice cost report/set-budget/providers`
  - Free tier awareness (Google AI 50/day)
  
- **CLI Enhancements**:
  - Added `-u/--understand` flag to enable AI understanding
  - Added `--providers` flag to specify which AI providers to use
  - Improved first-run setup wizard with cost comparisons
  - Better provider recommendations (Google first as it's free)

- **File-Based Event System**: Redis now optional
  - Created `FileBasedEventSystem` in `events/file_events.py`
  - Events stored as daily JSON logs in `~/.alice/events/`
  - Redis can be enabled with `USE_REDIS_EVENTS=true`
  - Separated Redis requirements to `requirements-redis.txt`

### Changed
- **Documentation**: Updated to clarify personal tool nature
  - README.md now states "Sandro's Personal AI Creative Tool"
  - Added warnings about lack of product support
  - Emphasized AI-native usage over CLI

### Fixed
- Fixed missing `--understand` CLI flag
- Improved error handling in first-run setup
- Made Redis dependency optional (was required)

### Removed
- Removed PostgreSQL event migration code (`events/migration.py`)
- Removed redundant `settings.yaml.multipath.example`
- Removed tracked DuckDB files from git
- Removed empty MagicMock test directory

### Added (2025-06-03) - Multi-Path Storage Enhancements
- **Progress Tracking**: Visual feedback for long operations
  - Added `tqdm` progress bars to file scanning and discovery
  - Progress callbacks for external monitoring integration
  - `--no-progress` flag for all storage commands
  - Progress shown by default in `discover`, `scan`, and `consolidate`
  
- **Cloud Storage Support**: S3 and GCS integration
  - `S3Scanner` with full upload/download capabilities
  - `GCSScanner` for Google Cloud Storage
  - Automatic content hash calculation for cloud files
  - Configurable credentials (environment or config)
  - Cloud file transfer in `_transfer_file` method
  
- **Auto-Migration System**: Rule-based lifecycle management
  - `AutoMigrationService` analyzes files against storage rules
  - Automatically moves/copies files to appropriate locations
  - Dry-run mode for safe previewing
  - Concurrent transfer operations with semaphore control
  - `MigrationScheduler` for periodic background runs
  - CLI: `alice storage migrate [--dry-run] [--move]`
  
- **Sync Tracking & Versioning**: Consistency across locations
  - `SyncTracker` detects conflicts across storage locations
  - Multiple resolution strategies:
    - Newest wins (most recent modification)
    - Largest wins (highest quality assumed)
    - Primary wins (highest priority location)
    - Manual (user intervention required)
  - Sync queue for batch processing pending operations
  - `VersionTracker` maintains file version history
  - CLI commands:
    - `alice storage sync-status`: Check conflicts
    - `alice storage resolve-conflict <hash> --strategy <strategy>`
    - `alice storage sync-process`: Process sync queue
  
- **New CLI Commands**:
  - `alice storage consolidate <project> <location>`: Consolidate project assets
  - All commands support `--no-progress` flag
  
- **Documentation & Examples**:
  - Comprehensive multi-path storage guide: `docs/user-guide/multi-path-storage-guide.md`
  - Cloud storage configuration: `examples/cloud_storage_config.yaml`
  - Demo scripts:
    - `storage_progress_demo.py`: Progress tracking demonstration
    - `auto_migration_demo.py`: Lifecycle management example
    - `sync_tracking_demo.py`: Conflict detection and resolution

### Fixed (2025-06-03)
- DuckDB foreign key constraints (removed unsupported CASCADE)
- Array query compatibility in DuckDB
- Test stability with separated scan operations

### Added (2025-01-06) - Multi-Path Storage Architecture
- **Multi-Path Storage System**: Store and manage assets across multiple locations
  - `LocationRegistry` class with DuckDB backend for tracking files across locations
  - Support for local, S3, GCS, and network storage types
  - Storage rules for automatic file placement based on:
    - Age (max_age_days, min_age_days)
    - Quality (min_quality_stars, max_quality_stars)
    - Type (include_types, exclude_types)
    - Size (min_size_bytes, max_size_bytes)
    - Tags (require_tags, exclude_tags)
  - Priority-based location selection for new files
  - Content-addressed tracking with SHA-256 hashes
  - `MultiPathScanner` for project-aware file discovery
  - Project consolidation features
- **Storage CLI Commands**: Full command-line interface
  - `alice storage init`: Initialize storage registry
  - `alice storage add`: Add new storage location
  - `alice storage list`: List all locations
  - `alice storage scan`: Scan specific location
  - `alice storage discover`: Discover all assets
  - `alice storage stats`: View storage statistics
  - `alice storage find-project`: Find project assets
  - `alice storage update`: Update location settings
  - `alice storage from-config`: Load from configuration
- **Configuration Support**: Enhanced settings for multi-path
  - New `storage.locations` array in settings.yaml
  - Example: settings.yaml.multipath.example
  - Backward compatibility with legacy inbox/organized paths
- **Documentation**: Complete migration guide
  - docs/user-guide/multi-path-storage-migration.md
  - Storage rule examples and best practices
  - Troubleshooting guide

### Added (2025-01-06) - Better First-Run Experience
- **Interactive Setup Wizard**: Comprehensive first-time setup
  - New `alice setup` command launches interactive wizard
  - Auto-detects first run and prompts for configuration
  - System requirements checking (Python version, dependencies, disk space)
  - Step-by-step API key setup with provider recommendations
  - Directory configuration with sensible defaults
  - Test organization to verify everything works
  - Shows next steps and quick start commands
- **Welcome Messages**: Friendly guidance for new users
  - `welcome.py` module provides context-aware messages
  - Shows setup status and warnings
  - Quick command reference for common tasks
  - Explains AI-native usage through Claude Desktop
- **Configuration Template**: Added `settings.yaml.example`
  - Fully documented configuration options
  - Cost management settings
  - Provider preferences with pricing notes
- **First-Run Detection**: Automatic setup prompt
  - Checks for existing configuration and API keys
  - Offers to run wizard or shows quick start guide
  - Can be skipped and run later with `alice setup`

### Added (2025-01-06) - Improved Error Messages
- **User-Friendly Error Handling**: Created comprehensive error handling system
  - New `error_handling.py` module with context-aware error messages
  - Provides actionable suggestions for common issues:
    - API key errors: Shows how to run `alice keys setup`
    - File path errors: Suggests checking permissions and using absolute paths
    - Cost limit errors: Shows current spending and how to increase limits
    - Dependency errors: Provides specific install commands
  - Error categories: API_KEY, FILE_PATH, PERMISSION, DEPENDENCY, CONFIGURATION, NETWORK, COST_LIMIT, DATABASE, PROVIDER
  - Integrated into main CLI with formatted output
  - Shows technical details only with --debug flag

### Added (2025-01-06) - Auto-Indexing During Organization
- **Auto-indexing to DuckDB**: Files are now automatically indexed during organization
  - MediaOrganizer calls `_update_search_index` after file operations
  - PipelineOrganizer calls `_auto_index_to_search` after metadata caching
  - Extracts tags from understanding data (v4.0 cache format)
  - Automatically calculates and stores perceptual hashes for images
  - Only runs when understanding is enabled in configuration
  - Handles both flat tag lists and categorized tag dictionaries
- **Improved Search Population**: Search index stays up-to-date as files are processed
  - No need to manually rebuild index after organization
  - New files immediately searchable by tags and similarity
  - Perceptual hashes enable "find similar" functionality

### Added (2025-01-06) - Video Creation Workflow
- **Video Creation Workflow**: Complete system for turning images into videos
  - `VideoCreationWorkflow` class analyzes images for video potential
  - Generates storyboards with shot descriptions and transitions
  - Creates Kling-ready prompts with camera movements (11 types)
  - Prepares enhanced keyframes using Flux Kontext
  - Exports transition guides for video editing
- **MCP Tools for Video**:
  - `analyze_for_video`: Analyze images for video generation potential
  - `generate_video_storyboard`: Create complete storyboards from selections
  - `create_kling_prompts`: Generate formatted prompts for Kling
  - `prepare_flux_keyframes`: Create enhanced keyframes with Flux
  - `create_transition_guide`: Generate video editing guides
- **Video Styles**: 5 predefined styles (cinematic, documentary, music_video, narrative, abstract)
- **Camera Motion Analysis**: Intelligent camera movement suggestions based on image composition
- **Storyboard Persistence**: JSON format for saving and loading video projects
- **Documentation**: Comprehensive video-creation-workflow-guide.md
- **Demo Script**: examples/advanced/video_creation_demo.py

### Fixed (2025-01-06) - Part 2
- **Understanding System Integration**: Fixed multiple issues preventing AI analysis
  - API keys now loaded from keychain automatically via APIKeyManager
  - Fixed ImageAnalysisResult attribute errors (positive_prompt → generated_prompt, removed timestamp/processing_time)
  - Fixed JSON serialization of MediaType enums with custom encoder
  - Fixed MetadataCacheAdapter missing enable_understanding attribute
  - Fixed ProcessingConfig.get() error (using dataclass attribute access)
  - Fixed quality_stars KeyError in statistics update
- **Import Issues**: Fixed scoped import conflict in main_cli.py causing UnboundLocalError
- **Understanding Provider**: Defaults to 'anthropic' when API key is available
- **Perceptual Hashing Integration**: Fixed perceptual hash computation
  - Fixed missing content_hash in AnalysisResult causing database constraint error
  - Fixed MediaType enum comparison in search index update
  - Perceptual hashes (pHash, dHash, aHash) now computed and stored during organization
  - Added proper error handling and logging for hash computation

### Fixed (2025-01-06)
- **Removed Hardcoded Paths**: Fixed all hardcoded test_data/ references
  - FileProjectService now uses config.storage.project_paths
  - SearchHandler uses config.storage.search_db
  - Comparison system uses config.paths.organized
  - All paths now configurable via settings.yaml
  - Added test_path_configuration.py to verify fixes
- **Production Ready**: System can now be deployed with custom paths

### Added (2025-01-06)
- **Understanding Integration**: Connected AI understanding to caching and search
  - UnifiedCache runs understanding analysis when enabled
  - Tags stored in v4.0 cache format with structured categories
  - Search index builder extracts semantic tags from cache
  - DuckDB search supports tag-based queries and facets
  - Understanding enabled by default in settings
  - Provider selection configurable (deepseek default for cost)
- **Lazy Loading**: Fixed circular imports with lazy module loading
- **Auto-indexing**: Files automatically indexed in DuckDB during organization
  - Metadata and tags indexed when files are processed
  - Understanding data flows through to search index
- **Exclusion Lists**: Scanner skips 'sorted-out' folders
  - Prevents re-processing of rejected files
  - Supports 'sorted-out' and 'sorted_out' variants
  - Also excludes .metadata and .alice folders
- **Similarity Search**: Implemented perceptual hashing
  - Three hash types: pHash (DCT), dHash (difference), aHash (average)
  - Hamming distance calculation for similarity matching
  - DuckDB table and indexes for perceptual hashes
  - find_similar_by_phash method with configurable threshold
  - Automatic hash calculation during organization and indexing

### Breaking Changes (2025-06-01)
- **Removed PostgreSQL Integration**: Complete removal of PostgreSQL dependency
  - Deleted alembic/ directory and all migrations
  - Removed SQLAlchemy models and repository classes
  - Updated all modules to work without database
  - Search functionality temporarily disabled (will use DuckDB)
  - Project management temporarily non-functional
  - Asset discovery limited to filesystem operations
- **Simplified Deployment**: No database server required
- **Reduced Dependencies**: Removed SQLAlchemy, Alembic, psycopg2
- **File-First Architecture**: All metadata stored in files, not database

### Architecture Simplification (2025-01-29)
- **Simplified Event System**: Replaced 2,600 lines across 5 implementations with 300-line PostgreSQL-native solution
- **Unified Provider Base**: Reduced 4 abstraction layers to 1 unified base class
- **Fixed Exception Handling**: Replaced all bare except blocks with specific error handling
- **Video Content Hashing**: Implemented ffmpeg-based keyframe extraction for videos
- **Configuration Management**: Moved all hardcoded values to settings.yaml
- **Input Validation**: Added comprehensive validation for all API endpoints
- **Rate Limiting**: Implemented configurable rate limits with burst allowance
- **File Cleanup**: Removed 79 unused files and 6,500+ lines of code
- **Type Hints**: Added comprehensive type annotations throughout codebase
- **AI-Native Documentation**: Updated all docs to reflect AI-first architecture

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