# Changelog

All notable changes to AliceMultiverse will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added (2025-06-18) - Configuration Validation

#### Configuration Validation System
- **Comprehensive Validation**: Validate all configuration settings
  - Path validation with permission checks
  - Performance settings validation
  - Storage configuration checks
  - API key presence verification
  - Understanding settings validation
  
- **System Resource Detection**: Automatic system capability detection
  - CPU count and architecture
  - Available memory detection
  - Disk space monitoring
  - GPU availability check
  - Runtime resource monitoring
  
- **Smart Configuration Builder**: Optimize settings for your system
  - Performance profile recommendations
  - Use-case specific optimization
  - Collection size optimization
  - Resource-based adjustments
  - Automatic constraint application
  
- **Startup Validation**: Pre-flight checks before processing
  - Configuration validation on startup
  - Runtime compatibility checks
  - Auto-fix capability for common issues
  - Interactive setup wizard
  - Visual validation results

#### Validated Media Organizer
- **ValidatedMediaOrganizer**: Enhanced organizer with validation
  - Startup validation integration
  - Auto-optimization based on system
  - Runtime validation checks
  - Dynamic collection size optimization
  - Validation report generation

#### Configuration CLI Commands
- **Config Management**: New CLI commands for configuration
  - `alice --debug debug config validate` - Validate configuration
  - `alice --debug debug config show` - Display current config
  - `alice --debug debug config optimize` - Generate optimized config
  - `alice --debug debug config setup` - Interactive setup wizard
  - `alice --debug debug config check` - Quick configuration check
  - `alice --debug debug config set` - Set configuration values
  - `alice --debug debug config get` - Get configuration values

### Added (2025-06-18) - Error Recovery & Resilience

#### Comprehensive Error Handling
- **Extended Exception Hierarchy**: Categorized errors for better handling
  - `RecoverableError` vs `FatalError` distinction
  - Specific error types: FileOperationError, DatabaseError, ProcessingError, etc.
  - Rich error context with recovery hints
  - Partial batch failure tracking
  
- **Retry Logic with Exponential Backoff**: Automatic retry for transient failures
  - Configurable retry strategies per operation type
  - API-specific retry with rate limit awareness
  - Database transaction retry with rollback
  - File operation retry with alternative strategies
  - Jitter to prevent thundering herd
  
- **Circuit Breaker Pattern**: Prevent cascading failures
  - Automatic circuit opening after failure threshold
  - Half-open state for recovery testing
  - Manual reset capability
  - Per-component circuit breakers
  
- **Dead Letter Queue**: Handle permanently failed items
  - Track items that failed all retries
  - Save failed items for manual inspection
  - Retry capability with degraded settings
  - JSON export for debugging

#### Graceful Degradation System
- **Progressive Degradation Levels**: Maintain functionality under failures
  - `normal`: Full functionality
  - `reduced_parallel`: Limited parallel processing
  - `sequential_only`: No parallel processing
  - `basic_only`: Core features only
  - `safe_mode`: Dry-run mode for safety
  
- **Feature Toggle Management**: Disable problematic features dynamically
  - Automatic feature disabling based on failures
  - Component health tracking
  - Recovery attempts after sustained success
  - Degradation history tracking
  
- **Adaptive Processing**: Dynamic strategy adjustment
  - Automatic worker count reduction
  - Batch size adjustment
  - Fallback to sequential processing
  - Success-based recovery attempts

#### Resilient Media Organizer
- **ResilientMediaOrganizer**: Enhanced organizer with full error recovery
  - Pre-flight checks (disk space, database, config)
  - Component health monitoring
  - Automatic degradation on failures
  - Dead letter queue integration
  - State persistence on critical failures
  
- **Enhanced File Processing**: Robust file operations
  - File validation before processing
  - Fallback destination strategies
  - Alternative operation methods (hardlinks)
  - Existing file conflict resolution
  - Recovery metadata tracking

### Added (2025-06-18) - Performance Monitoring & Metrics

#### Performance Monitoring System
- **Real-time Metrics Collection**: Track all aspects of system performance
  - Files processed per second with per-file-type breakdown
  - Processing time tracking (min/max/average)
  - Memory usage monitoring with peak detection
  - CPU usage percentage tracking
  - Cache hit/miss rates with automatic calculation
  - Database operation timing and overhead analysis
  - Worker thread utilization and queue depths
  - Error rate tracking and reporting
  
- **Performance Dashboard**: Rich terminal UI for real-time monitoring
  - Live updating metrics display
  - File type processing statistics
  - Operation timing breakdowns
  - System resource visualization
  - Export metrics to JSON for analysis
  - CLI command: `alice --debug debug performance monitor`
  
- **Performance Tracking Integration**:
  - Automatic tracking in MediaOrganizer
  - Cache operation monitoring
  - Database operation timing
  - Context managers for custom tracking
  - Decorators for method-level timing
  - Thread-safe metrics collection
  
- **CLI Commands**:
  - `alice --debug debug performance monitor` - Real-time dashboard
  - `alice --debug debug performance report` - Show current metrics
  - `alice --debug debug performance export <path>` - Export to JSON
  - `alice --debug debug performance reset` - Reset all metrics

### Added (2025-06-18) - Performance Enhancements & Architecture Improvements

#### Performance Enhancements
- **Parallel Processing**: Process multiple files concurrently for large collections
  - Automatic switching between sequential and parallel based on batch size
  - Configurable worker threads (default: 8, max: 16)
  - Progress tracking for long-running operations
  - ParallelProcessor and ParallelBatchProcessor classes
  
- **Batch Database Operations**: 15x faster database operations
  - BatchOperationsMixin for bulk inserts/updates
  - Transaction management with automatic rollback
  - Configurable batch sizes (default: 100 files)
  - Batch upsert for assets, tags, and understanding data
  
- **Performance Profiles**: Pre-configured settings for different use cases
  - `default`: Balanced performance (8 workers, 100 file batches)
  - `fast`: Maximum performance (16 workers, 200 file batches)
  - `memory_constrained`: For limited RAM (4 workers, 50 file batches)
  - `large_collection`: Bulk processing (12 workers, 500 file batches)
  - Environment variable support: `export ALICE_PERFORMANCE=fast`

#### Architecture Improvements
- **Protocol Interfaces**: Type-safe interfaces for better code organization
  - `HasConfig`, `HasStats`, `HasSearchDB`, `HasOrganizer`
  - Enables better type checking with mypy (reduced errors from 1499 to 1400)
  - Supports mixin-based architecture with proper typing
  
- **Mixin Architecture**: Modular component design
  - Clear separation of concerns across 8+ mixins
  - Each mixin handles specific functionality (file ops, media analysis, etc.)
  - Protocol interfaces ensure type safety
  
- **Performance Configuration**: Flexible performance tuning
  - `PerformanceConfig` dataclass with all performance settings
  - `get_performance_config()` for profile-based configuration
  - Custom configuration support via settings.yaml

### Fixed (2025-06-18)
- **Import Errors**: Fixed 35+ test file import errors
- **Type Errors**: Resolved 99 mypy errors through Protocol interfaces
- **Test Suite**: Fixed all test collection errors
- **EDL/XML Export**: Implemented missing timeline export functionality
- **Storage Scanning**: Implemented location scanning for local/S3/GCS
- **Exception Handling**: Replaced all bare except statements with specific types

### Changed (2025-06-18)
- **Organizer Architecture**: Consolidated multiple organizer classes into single configurable `MediaOrganizer`
- **Performance Defaults**: Optimized default settings for better out-of-box performance
- **Error Messages**: More specific error handling throughout codebase

### Documentation (2025-06-18)
- **Performance Guide** (`docs/PERFORMANCE_GUIDE.md`): Comprehensive guide for performance optimization
- **Development Guide** (`docs/DEVELOPMENT_GUIDE.md`): Protocol interfaces and mixin patterns
- **Architecture Docs**: Updated with performance architecture details
- **README**: Added performance section and new features

### Tests (2025-06-18)
- Added comprehensive test suite for new functionality:
  - `test_enhanced_media_organizer.py`: 13 tests for parallel processing
  - `test_batch_operations.py`: Tests for batch database operations
  - `test_parallel_processor.py`: Tests for parallel processing infrastructure
  - `test_performance_config.py`: Tests for configuration system
  - `test_protocol_interfaces.py`: Tests for type-safe protocols
  - `test_storage_location_scanning.py`: Tests for storage scanning

## [Unreleased]

### Added (2025-01-08) - Template Workflows
- **Story Arc Templates**: Narrative-driven video creation
  - StoryArcTemplate with 5 classic structures (3-act, 5-act, hero's journey, kishoten, circular)
  - Narrative content analysis and emotional mapping
  - Story beat distribution with appropriate pacing
  - Narrative-appropriate transitions and timing
  - Chapter markers and voiceover support
  - DocumentaryStoryTemplate for information delivery
  - EmotionalJourneyTemplate for mood-based narratives
  
- **Social Media Templates**: Platform-optimized workflows
  - SocialMediaTemplate base with platform detection
  - Platform specifications for 9+ social networks
  - Instagram Reel template with music sync and effects
  - TikTok template with trend integration
  - LinkedIn video template for professional content
  - Automatic aspect ratio and duration optimization
  - Safe zone management for UI elements
  - Platform-specific engagement features
  
- **MCP Tools for Templates**:
  - `create_story_arc_video`: Create narrative videos
  - `create_documentary_video`: Documentary style
  - `create_social_media_video`: Platform optimization
  - `create_instagram_reel`: Instagram-specific
  - `create_tiktok_video`: TikTok with trends
  - `get_platform_specifications`: Platform info
  - `suggest_story_structure`: Content analysis
  
- **Template Features**:
  - Hook optimization for engagement
  - Caption and hashtag integration
  - Platform-specific filters and effects
  - Trending element detection
  - Export optimization per platform

### Added (2025-01-08) - Style Memory & Learning
- **Comprehensive Style Preference System**: Learn and adapt to personal creative style
  - StyleMemory class for persistent preference storage
  - Tracks 10 preference types (color, composition, lighting, mood, etc.)
  - Usage statistics and success tracking per preference
  - Time-based pattern detection
  - Project-specific style profiles
  
- **Real-time Workflow Tracking**:
  - PreferenceTracker monitors choices during workflows
  - Tracks adjustments, iterations, and outcomes
  - Identifies improvement areas from usage patterns
  - Session-based learning with quality metrics
  
- **Intelligent Learning Engine**:
  - Pattern detection (co-occurrence, temporal, evolution)
  - Actionable insights with priority levels
  - Predictive preference suggestions
  - Confidence scoring for recommendations
  
- **Personalized Recommendations**:
  - 4 recommendation types: preset, variation, exploration, trending
  - Context-aware suggestions (time, project, current state)
  - Style fusion for creative combinations
  - Next action guidance during workflows
  
- **MCP Tools for Style Management**:
  - `track_style_preference`: Record style choices
  - `get_style_recommendations`: Get personalized suggestions
  - `analyze_style_patterns`: Discover usage patterns
  - `start/end_style_workflow`: Track workflow success
  - `get_style_evolution`: View style changes over time
  - `suggest_next_style_action`: Get workflow guidance
  - `export/import_style_profile`: Backup and share profiles
  
- **Documentation**:
  - Comprehensive Style Memory Guide
  - Integration examples with other features
  - Best practices for effective learning

### Added (2025-01-08) - Performance Analytics
- **Comprehensive Performance Tracking**: Monitor workflow efficiency and success
  - Session-based analytics with start/end tracking
  - Workflow metrics (duration, success rate, resource usage)
  - Export pattern analysis by format and platform
  - User behavior tracking (adjustments, previews, iterations)
  
- **Export Analytics Engine**:
  - Format preferences and usage patterns
  - Platform compatibility scoring
  - Quality trends over time
  - Time-to-final tracking
  
- **AI-Powered Improvements**:
  - Automated suggestion engine
  - Prioritized by impact and effort
  - Categories: workflow, performance, quality, efficiency
  - Actionable implementation steps
  
- **MCP Tools for Analytics**:
  - `start_analytics_session`: Begin performance tracking
  - `end_analytics_session`: Get session summary
  - `get_performance_insights`: View stats and improvements
  - `get_export_analytics`: Analyze export patterns
  - `get_improvement_suggestions`: Get optimization tips
  - `track_user_action`: Record behavior patterns
  
- **Documentation**:
  - Comprehensive Performance Analytics Guide
  - Metrics explanation and best practices
  - Integration examples with other features

### Added (2025-01-08) - Multi-Version Export
- **Platform-Specific Timeline Adaptations**: Export to 8 social media platforms
  - Automatic aspect ratio conversion (16:9 → 9:16, 1:1, etc.)
  - Smart cropping with AI subject detection
  - Duration constraints (trim/extend to platform limits)
  - Platform-specific pacing optimization
  
- **Supported Platforms**:
  - Instagram (Reel, Story, Post)
  - TikTok (up to 3 minutes)
  - YouTube (Shorts, Horizontal)
  - Twitter/X (quick view optimized)
  - Master (4K archival)
  
- **Intelligent Features**:
  - Music sync preservation during adaptation
  - Loop-friendly transitions for Instagram
  - Trend sync points for TikTok
  - Safe zone management for UI elements
  - Hook optimization for engagement
  
- **MCP Tools for Multi-Version Export**:
  - `export_for_platforms`: Create platform versions
  - `check_platform_compatibility`: Get recommendations
  - `export_all_platforms`: Batch export workflow
  - `get_platform_specs`: Platform specifications
  
- **Documentation**:
  - Comprehensive Multi-Version Export Guide
  - Platform feature comparison
  - Workflow examples and best practices

### Added (2025-01-08) - Natural Language Timeline Editing
- **Natural Language Command Processing**: Edit timelines with conversational commands
  - 9 edit intent types: pace changes, pauses, sync, energy, transitions, etc.
  - Intelligent section detection (intro, outro, chorus, bridge, drop)
  - Confidence scoring for command interpretation
  - Batch command processing for complex edits
  
- **AI-Powered Timeline Suggestions**:
  - Automatic timeline analysis (pace, rhythm, energy flow)
  - Context-aware improvement suggestions
  - Example commands by category
  
- **MCP Tools for Natural Language Editing**:
  - `edit_timeline_naturally`: Process single commands
  - `suggest_timeline_improvements`: Get AI suggestions
  - `apply_timeline_commands`: Batch multiple edits
  - `get_timeline_edit_examples`: Browse command examples
  
- **Documentation**:
  - Comprehensive Natural Language Editing Guide
  - Command examples by workflow type
  - Integration with timeline preview

### Added (2025-01-08) - Web Timeline Preview Interface
- **Interactive Timeline Preview**: Web-based interface for video timeline editing
  - FastAPI server with real-time WebSocket updates
  - Drag-and-drop clip reordering with visual feedback
  - Timeline visualization with clips, transitions, and markers
  - Undo/redo support for all operations
  - Session-based editing with unique URLs
  - Export to EDL, XML, or JSON formats
  
- **MCP Tools for Timeline Preview**:
  - `preview_video_timeline`: Open timeline in web browser
  - `update_preview_timeline`: Modify clips (reorder, trim, transitions)
  - `export_preview_timeline`: Export to various formats
  - `get_timeline_preview_status`: Check server status
  
- **Documentation**:
  - Comprehensive Timeline Preview Guide
  - Integration examples and workflow tips
  - Troubleshooting section

### Added (2025-01-08) - Project Cleanup
- **Root Directory Organization**: Reduced clutter from 18+ to 6 essential files
  - Moved 10 documentation files to appropriate `/docs/` subdirectories
  - Archived temporary reports and status files
  - Created cleanup scripts for future maintenance
  - Removed 2,350 Python cache files
  
- **New Cleanup Tools**:
  - `scripts/cleanup_unnecessary_files.py`: Remove cache and temp files
  - `scripts/reorganize_root_files.py`: Organize documentation files
  - Both scripts support dry-run mode for safety

### Added (2025-01-07) - Google Veo 3 Integration
- **Google Veo 3 Support**: Added state-of-the-art video generation
  - Integrated via fal.ai provider with model ID `veo-3`
  - Added to Google AI provider for future Vertex AI access
  - Native audio generation with ambient sounds and music
  - Speech capabilities with accurate lip sync
  - Improved physics simulation and realism
  - 5-8 second video generation
  - Pricing: $0.50/second (no audio) or $0.75/second (with audio)
  - Created comprehensive Veo 3 guide and examples
  - Added unit tests for both providers

### Added (2025-01-07) - Advanced Transition Effects
- **Match Cut Detection**: Find seamless transitions where motion/shapes align
  - Motion vector analysis for movement continuity
  - Shape matching for circles, rectangles, lines
  - Action continuity scoring
  - Export to EDL format with annotations
  - CLI: `alice transitions matchcuts`
  
- **Portal Effects**: "Through the looking glass" transitions
  - Detect circles, rectangles, arches as portals
  - Quality scoring based on darkness, edges, size
  - Portal matching between shots
  - After Effects script export
  - CLI: `alice transitions portal`
  
- **Visual Rhythm Engine**: Intelligent pacing suggestions
  - Visual complexity analysis (edges, color, texture)
  - Energy profiling (brightness, motion, emotion)
  - Automatic duration suggestions
  - BPM synchronization support
  - Balance scoring for variety
  - CSV export for timing sheets
  - CLI: `alice transitions rhythm`

### Added (2025-01-06) - Color Flow Transitions
- **Color Flow Transitions**: Advanced color-based transition analysis
  - Added `ColorFlowAnalyzer` class for analyzing color palettes between shots
  - Extracts dominant colors using K-means clustering
  - Analyzes lighting direction and intensity using gradient detection
  - Creates gradient transitions (linear, radial, diagonal) based on shot properties
  - Calculates compatibility scores for smooth visual flow
  - Suggests transition effects based on color and lighting differences
  - Exports editor-specific formats:
    - DaVinci Resolve: JSON + color matching LUTs
    - Adobe Premiere: Keyframe data for color effects
    - Final Cut Pro X: Motion template parameters
    - Blackmagic Fusion: Node-based compositions
  - Added CLI commands:
    - `alice transitions colorflow` - Analyze color flow in image sequences
    - `alice transitions colorpair` - Detailed analysis of a single transition
  - Created comprehensive test suite and demo script

### Added (2025-06-05) - Code Cleanup Sprint, Workflow Polish & Deep Cleanup
- **Repository Cleanup**: Reduced clutter and improved maintainability
  - Updated ROADMAP.md with focused priorities
  - Removed performance testing from immediate priorities (focus on smaller subsets first)
  - Added detailed implementation plans for next focus areas
  - Identified overlapping DuckDB implementations for future consolidation:
    - DuckDBSearchCache (primary, used by MCP server)
    - DuckDBSearch (legacy/specialized, used by search handler)
  - Verified Claude MCP integration is working properly

- **Project Management via MCP**: Streamlined project creation workflow
  - Added `create_project` tool - Create projects with creative context
  - Added `list_projects` tool - View all projects with budget status
  - Added `get_project_context` tool - Get project details and statistics
  - Added `update_project_context` tool - Update creative parameters
  - Projects now fully accessible through AI assistant interface

- **Duplicate Detection via MCP**: Better duplicate management
  - Added `find_duplicates` tool - Find exact duplicate files
  - Shows duplicate groups sorted by wasted space
  - Calculates total wasted storage from duplicates
  - Foundation for future perceptual similarity detection

- **Deep Cleanup**: Addressed future cleanup opportunities
  - Analyzed DuckDB implementations merge strategy (complex, postponed)
  - Cleaned up PostgreSQL references in comments throughout codebase
  - Created v3-cleanup-plan.md documenting deprecated cache modules
  - Identified that DuckDB merge would be significant undertaking

- **Quick Selection Workflow**: Fast favorites marking system
  - Added `quick_mark` tool - Instantly mark as favorite/hero/maybe/review
  - Added `list_quick_marks` tool - View recent quick selections
  - Added `export_quick_marks` tool - Export marked assets to folders
  - Auto-creates daily collections by mark type
  - Integrates with comprehensive selection service for persistence
  - Created quick-selection-guide.md with workflow examples

- **Batch Analysis Optimization**: Smart cost reduction for image analysis
  - Added `analyze_images_optimized` tool with similarity detection
  - Added `estimate_analysis_cost` tool for cost comparison
  - Groups similar images using perceptual hashing
  - Analyzes one representative per group (20-40% cost savings)
  - Progressive provider strategy (free → cheap → premium)
  - Created optimized_batch_analyzer.py module
  - Created batch-analysis-optimization.md guide

- **Local Vision Models Integration**: Free, private image analysis with Ollama
  - Created `ollama_provider.py` with OllamaImageAnalyzer class
  - Support for multiple vision models (LLaVA, BakLLaVA, Phi3)
  - Integrated Ollama into main analyzer with automatic detection
  - Added `check_ollama_status` tool - Check local model availability
  - Added `analyze_with_local` tool - Hybrid local/cloud analysis
  - Added `pull_ollama_model` tool - Download vision models
  - Cost tracking shows $0 for local analysis
  - Created local-vision-models-guide.md documentation
  - Fallback to cloud providers when local unavailable

- **Intelligent Tag Hierarchies**: Semantic tag organization and clustering
  - Created `tag_hierarchy.py` with hierarchical tag relationships
  - Created `tag_clustering.py` for automatic tag grouping
  - Created `taxonomy_manager.py` for personal organization schemes
  - Created `enhanced_analyzer.py` integrating all tag intelligence
  - Default hierarchies for art styles, subjects, moods, lighting, colors
  - Tag aliasing and normalization (b&w → black_and_white)
  - Co-occurrence tracking for pattern detection
  - DBSCAN clustering for similarity grouping
  - Project-specific tag collections
  - Mood board support with tags, colors, and images
  - Export/import custom taxonomies
  - Added 5 MCP tools for tag management
  - Created intelligent-tag-hierarchies-guide.md documentation

- **Style Similarity Clusters**: Visual style analysis and clustering
  - Created `style_analyzer.py` for extracting visual DNA
  - Created `style_clustering.py` for style-based grouping
  - Color palette extraction using KMeans (dominant colors, temperature, harmony)
  - Composition analysis (rule of thirds, symmetry, balance, focal points)
  - Lighting analysis (mood, direction, contrast, time of day detection)
  - Texture analysis (smoothness, patterns, grain, detail density)
  - Style fingerprint vectors for mathematical similarity comparison
  - "More like this" style-based image search
  - Automatic style collections ("Warm Dramatic", "Cool Minimalist")
  - Style transfer hint extraction with reusable prompt fragments
  - Style compatibility checking for coherent sets
  - Success rate estimation for style transfers
  - Added 5 MCP tools for style analysis
  - Created style-similarity-clusters-guide.md documentation

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