# AliceMultiverse MCP Tools Reference
Version: 1.7.1 | Tools: 106 | Generated: January 17, 2025

## Overview

AliceMultiverse provides 106 Model Context Protocol (MCP) tools organized into functional categories. These tools enable AI assistants like Claude to perform complex creative workflows.

## Tool Categories

### 🔍 Search & Discovery (6 tools)

#### `search_assets`
Search for AI-generated assets using natural language or structured queries.
- **Parameters**: description, style_tags, mood_tags, subject_tags, time_reference, min_quality_stars, media_type, ai_source, limit
- **Returns**: List of matching assets with metadata

#### `find_similar_assets`
Find visually similar assets using perceptual hashing.
- **Parameters**: asset_id, threshold, limit
- **Returns**: Similar assets ranked by similarity score

#### `search_by_project`
Search assets within a specific project context.
- **Parameters**: project_name, query, limit
- **Returns**: Project-specific results

#### `advanced_search`
Complex search with multiple criteria and filters.
- **Parameters**: Multiple filter options, sorting, grouping
- **Returns**: Grouped and sorted results

#### `search_by_generation_params`
Find assets by their generation parameters.
- **Parameters**: provider, model, parameters
- **Returns**: Assets with matching generation data

#### `get_search_suggestions`
Get search suggestions based on current context.
- **Parameters**: partial_query, context
- **Returns**: Suggested queries and filters

### 📁 Organization & Management (8 tools)

#### `organize_media`
Organize AI-generated media into structured folders.
- **Parameters**: source_path, quality_assessment, understanding
- **Returns**: Organization statistics

#### `scan_for_new_media`
Scan directories for new AI-generated content.
- **Parameters**: paths, recursive
- **Returns**: List of discovered media

#### `get_organization_stats`
Get statistics about organized media.
- **Parameters**: date_range, group_by
- **Returns**: Detailed statistics

#### `reorganize_by_criteria`
Reorganize existing media by new criteria.
- **Parameters**: criteria, source_path
- **Returns**: Reorganization results

#### `create_collection`
Create a named collection of assets.
- **Parameters**: name, asset_ids, description
- **Returns**: Collection ID

#### `manage_collections`
List, update, or delete collections.
- **Parameters**: operation, collection_id
- **Returns**: Operation result

#### `export_collection`
Export a collection with assets and metadata.
- **Parameters**: collection_id, format, include_assets
- **Returns**: Export path

#### `import_collection`
Import a previously exported collection.
- **Parameters**: import_path, merge_strategy
- **Returns**: Import statistics

### 🏷️ Tagging & Metadata (7 tools)

#### `update_tags`
Update tags for one or more assets.
- **Parameters**: asset_ids, add_tags, remove_tags, set_tags
- **Returns**: Update status

#### `batch_tag_by_criteria`
Apply tags to multiple assets matching criteria.
- **Parameters**: criteria, tags_to_add
- **Returns**: Number of assets tagged

#### `suggest_tags`
Get AI-powered tag suggestions for assets.
- **Parameters**: asset_ids, context
- **Returns**: Suggested tags with confidence

#### `create_tag_hierarchy`
Create hierarchical tag relationships.
- **Parameters**: parent_tag, child_tags
- **Returns**: Hierarchy created

#### `analyze_tag_distribution`
Analyze tag usage across assets.
- **Parameters**: tag_category, date_range
- **Returns**: Distribution statistics

#### `merge_duplicate_tags`
Find and merge similar/duplicate tags.
- **Parameters**: similarity_threshold
- **Returns**: Merge operations performed

#### `export_tag_taxonomy`
Export complete tag taxonomy.
- **Parameters**: format, include_stats
- **Returns**: Export path

### 🎨 Style & Analysis (12 tools)

#### `analyze_style`
Extract style DNA from images.
- **Parameters**: asset_ids, detailed
- **Returns**: Style vectors and characteristics

#### `find_style_matches`
Find assets with similar artistic style.
- **Parameters**: reference_asset_id, threshold
- **Returns**: Style-matched assets

#### `create_style_cluster`
Group assets by visual style similarity.
- **Parameters**: asset_ids, num_clusters
- **Returns**: Style clusters

#### `generate_style_report`
Create detailed style analysis report.
- **Parameters**: asset_ids, include_recommendations
- **Returns**: Comprehensive style report

#### `track_style_evolution`
Analyze style changes over time.
- **Parameters**: date_range, style_attributes
- **Returns**: Evolution timeline

#### `compare_styles`
Compare styles between assets or groups.
- **Parameters**: asset_ids_a, asset_ids_b
- **Returns**: Style comparison metrics

#### `extract_color_palette`
Extract dominant colors and palettes.
- **Parameters**: asset_id, num_colors
- **Returns**: Color palette with weights

#### `analyze_composition`
Analyze visual composition elements.
- **Parameters**: asset_id, include_suggestions
- **Returns**: Composition analysis

#### `detect_visual_themes`
Identify recurring visual themes.
- **Parameters**: asset_ids, min_occurrence
- **Returns**: Detected themes

#### `create_mood_board`
Generate mood board from assets.
- **Parameters**: theme, num_assets, layout
- **Returns**: Mood board configuration

#### `analyze_artistic_influences`
Detect artistic style influences.
- **Parameters**: asset_id, reference_database
- **Returns**: Detected influences

#### `generate_style_guide`
Create style guide documentation.
- **Parameters**: project_id, format
- **Returns**: Style guide document

### 🎬 Video Generation (8 tools)

#### `generate_video`
Generate video using any supported provider.
- **Parameters**: prompt, provider, duration, aspect_ratio, options
- **Returns**: Generation ID and status

#### `check_video_status`
Check video generation status.
- **Parameters**: generation_id, provider
- **Returns**: Current status and preview

#### `list_video_providers`
List available video generation providers.
- **Returns**: Provider capabilities and pricing

#### `estimate_video_cost`
Estimate cost before generation.
- **Parameters**: prompt, provider, duration, options
- **Returns**: Cost breakdown

#### `batch_generate_videos`
Generate multiple videos efficiently.
- **Parameters**: prompts, provider, shared_options
- **Returns**: Batch ID and individual statuses

#### `create_video_variations`
Generate variations of existing video.
- **Parameters**: source_video_id, variation_prompts
- **Returns**: Variation IDs

#### `analyze_video_content`
Analyze generated video content.
- **Parameters**: video_id, analysis_types
- **Returns**: Content analysis

#### `optimize_video_settings`
Get optimal settings for provider/style.
- **Parameters**: prompt, target_style, budget
- **Returns**: Recommended settings

### 🎞️ Timeline & Editing (11 tools)

#### `create_timeline`
Create video timeline from assets.
- **Parameters**: asset_ids, duration, transitions
- **Returns**: Timeline object

#### `preview_timeline`
Generate timeline preview.
- **Parameters**: timeline_id, format, resolution
- **Returns**: Preview URL

#### `export_timeline`
Export timeline to editing software.
- **Parameters**: timeline_id, format (EDL/XML/JSON)
- **Returns**: Export file path

#### `add_timeline_markers`
Add markers for beats, sections, cues.
- **Parameters**: timeline_id, markers
- **Returns**: Updated timeline

#### `apply_timeline_effects`
Apply effects to timeline segments.
- **Parameters**: timeline_id, effects
- **Returns**: Effect application status

#### `optimize_timeline_pacing`
Analyze and optimize pacing.
- **Parameters**: timeline_id, target_energy
- **Returns**: Pacing suggestions

#### `sync_to_music`
Synchronize timeline to audio.
- **Parameters**: timeline_id, audio_file, sync_mode
- **Returns**: Synced timeline

#### `detect_timeline_issues`
Find potential editing issues.
- **Parameters**: timeline_id, check_types
- **Returns**: Detected issues

#### `create_rough_cut`
Auto-generate rough cut from assets.
- **Parameters**: asset_ids, target_duration, style
- **Returns**: Rough cut timeline

#### `render_timeline_preview`
Render low-res preview video.
- **Parameters**: timeline_id, quality, watermark
- **Returns**: Preview video path

#### `analyze_timeline_flow`
Analyze narrative and visual flow.
- **Parameters**: timeline_id, flow_aspects
- **Returns**: Flow analysis report

### 🎵 Music & Audio (6 tools)

#### `analyze_music`
Analyze music for video sync.
- **Parameters**: audio_file, analysis_depth
- **Returns**: BPM, beats, structure, mood

#### `detect_music_sections`
Identify intro, verse, chorus, etc.
- **Parameters**: audio_file, genre_hint
- **Returns**: Section timecodes

#### `generate_beat_markers`
Create beat-aligned markers.
- **Parameters**: audio_file, marker_density
- **Returns**: Beat marker list

#### `match_music_mood`
Find music matching visual mood.
- **Parameters**: asset_ids, music_library
- **Returns**: Matched music suggestions

#### `create_audio_reactive_timeline`
Generate timeline reacting to audio.
- **Parameters**: audio_file, visual_assets, reactivity
- **Returns**: Audio-reactive timeline

#### `extract_audio_features`
Extract detailed audio features.
- **Parameters**: audio_file, feature_types
- **Returns**: Audio feature data

### 🔄 Transitions & Effects (10 tools)

#### `analyze_transitions`
Analyze transition opportunities.
- **Parameters**: asset_sequence, transition_style
- **Returns**: Transition suggestions

#### `create_morphing_transition`
Create subject morphing effect.
- **Parameters**: source_asset, target_asset, duration
- **Returns**: Morph configuration

#### `generate_color_flow`
Create color-based transitions.
- **Parameters**: assets, flow_type, duration
- **Returns**: Color flow data

#### `detect_match_cuts`
Find match cut opportunities.
- **Parameters**: asset_sequence, threshold
- **Returns**: Match cut points

#### `create_portal_transition`
Design portal-based transition.
- **Parameters**: source, target, portal_shape
- **Returns**: Portal effect data

#### `analyze_visual_rhythm`
Analyze rhythm for transitions.
- **Parameters**: asset_sequence, target_rhythm
- **Returns**: Rhythm analysis

#### `generate_transition_pack`
Create transition preset pack.
- **Parameters**: style, num_transitions
- **Returns**: Transition pack

#### `preview_transition`
Preview transition effect.
- **Parameters**: transition_data, preview_quality
- **Returns**: Preview file

#### `optimize_transition_timing`
Optimize transition durations.
- **Parameters**: timeline_id, target_feel
- **Returns**: Timing adjustments

#### `export_transition_data`
Export for editing software.
- **Parameters**: transition_ids, target_software
- **Returns**: Export files

### 🎯 Prompts & Generation (7 tools)

#### `find_effective_prompts`
Find prompts that worked well.
- **Parameters**: criteria, provider, limit
- **Returns**: Effective prompts with stats

#### `analyze_prompt_effectiveness`
Analyze prompt performance.
- **Parameters**: prompt_ids, metrics
- **Returns**: Effectiveness report

#### `create_prompt_template`
Create reusable prompt template.
- **Parameters**: base_prompt, variables, description
- **Returns**: Template ID

#### `suggest_prompt_improvements`
Get AI suggestions for prompts.
- **Parameters**: prompt, target_outcome
- **Returns**: Improvement suggestions

#### `track_prompt_usage`
Track prompt usage and results.
- **Parameters**: prompt_id, result_id, rating
- **Returns**: Tracking confirmation

#### `batch_test_prompts`
Test prompt variations.
- **Parameters**: base_prompt, variations, provider
- **Returns**: Test results

#### `export_prompt_library`
Export successful prompts.
- **Parameters**: criteria, format
- **Returns**: Export file

### 🎪 Advanced Workflows (10 tools)

#### `create_video_storyboard`
Design video storyboard.
- **Parameters**: concept, num_shots, style
- **Returns**: Storyboard with shots

#### `generate_b_roll_suggestions`
Suggest B-roll for main content.
- **Parameters**: main_content_id, context, num_suggestions
- **Returns**: B-roll suggestions

#### `create_style_variations`
Generate style variations.
- **Parameters**: source_asset, variation_styles
- **Returns**: Variation IDs

#### `build_narrative_sequence`
Create narrative-driven sequence.
- **Parameters**: story_beats, visual_assets
- **Returns**: Narrative timeline

#### `optimize_creative_workflow`
Analyze and optimize workflow.
- **Parameters**: workflow_data, goals
- **Returns**: Optimization suggestions

#### `generate_content_calendar`
Create content generation calendar.
- **Parameters**: themes, frequency, duration
- **Returns**: Content calendar

#### `analyze_audience_engagement`
Predict engagement levels.
- **Parameters**: asset_ids, target_audience
- **Returns**: Engagement predictions

#### `create_multi_platform_campaign`
Design cross-platform campaign.
- **Parameters**: concept, platforms, duration
- **Returns**: Campaign plan

#### `generate_creative_brief`
Create detailed creative brief.
- **Parameters**: project_type, requirements
- **Returns**: Creative brief document

#### `simulate_workflow_outcomes`
Simulate workflow results.
- **Parameters**: workflow_steps, parameters
- **Returns**: Simulation results

### 🔍 Deduplication (5 tools)

#### `find_duplicates`
Find duplicate assets.
- **Parameters**: scan_paths, threshold, hash_types
- **Returns**: Duplicate groups

#### `preview_deduplication`
Preview what would be removed.
- **Parameters**: duplicate_groups, strategy
- **Returns**: Preview report

#### `deduplicate_assets`
Remove duplicates with strategy.
- **Parameters**: duplicate_groups, strategy, use_hardlinks
- **Returns**: Deduplication results

#### `analyze_similarity_clusters`
Find similar (not duplicate) assets.
- **Parameters**: assets, similarity_threshold
- **Returns**: Similarity clusters

#### `restore_deduplicated`
Restore previously removed duplicates.
- **Parameters**: dedup_report_id
- **Returns**: Restoration status

### 📊 Analytics & Insights (8 tools)

#### `generate_usage_report`
Create comprehensive usage analytics.
- **Parameters**: date_range, report_type
- **Returns**: Usage report

#### `analyze_generation_costs`
Analyze costs by provider/project.
- **Parameters**: date_range, group_by
- **Returns**: Cost analysis

#### `track_creative_performance`
Track which creations perform well.
- **Parameters**: asset_ids, performance_metrics
- **Returns**: Performance data

#### `predict_generation_success`
Predict prompt success likelihood.
- **Parameters**: prompt, provider, historical_data
- **Returns**: Success prediction

#### `analyze_workflow_efficiency`
Measure workflow performance.
- **Parameters**: workflow_ids, metrics
- **Returns**: Efficiency report

#### `generate_insights_dashboard`
Create insights dashboard data.
- **Parameters**: dashboard_type, date_range
- **Returns**: Dashboard data

#### `export_analytics_data`
Export analytics for external tools.
- **Parameters**: data_types, format, date_range
- **Returns**: Export files

#### `schedule_recurring_reports`
Set up automated reporting.
- **Parameters**: report_config, schedule
- **Returns**: Schedule confirmation

### 🛠️ System & Maintenance (8 tools)

#### `check_system_health`
Check system components health.
- **Returns**: Health status report

#### `optimize_storage`
Optimize storage usage.
- **Parameters**: optimization_level
- **Returns**: Optimization results

#### `rebuild_search_index`
Rebuild search indices.
- **Parameters**: index_types, force
- **Returns**: Rebuild status

#### `backup_metadata`
Backup all metadata.
- **Parameters**: backup_location, include_cache
- **Returns**: Backup confirmation

#### `restore_from_backup`
Restore from backup.
- **Parameters**: backup_path, restore_options
- **Returns**: Restore status

#### `clean_temporary_files`
Clean up temporary files.
- **Parameters**: age_days, dry_run
- **Returns**: Cleanup report

#### `update_file_locations`
Update file location tracking.
- **Parameters**: scan_paths, update_missing
- **Returns**: Update results

#### `generate_diagnostic_report`
Create system diagnostic report.
- **Returns**: Diagnostic data

### 🤝 Integration Tools (8 tools)

#### `export_to_creative_suite`
Export for Adobe/DaVinci/etc.
- **Parameters**: asset_ids, target_app, project_settings
- **Returns**: Export package

#### `import_from_external`
Import from other tools.
- **Parameters**: source_path, source_type
- **Returns**: Import results

#### `sync_with_cloud`
Sync with cloud storage.
- **Parameters**: cloud_provider, sync_direction
- **Returns**: Sync status

#### `generate_api_schema`
Generate API schema docs.
- **Parameters**: format, include_examples
- **Returns**: Schema documentation

#### `create_webhook`
Set up webhook notifications.
- **Parameters**: event_types, endpoint
- **Returns**: Webhook ID

#### `test_integration`
Test external integration.
- **Parameters**: integration_type, config
- **Returns**: Test results

#### `map_external_metadata`
Map external metadata formats.
- **Parameters**: source_format, mapping_rules
- **Returns**: Mapping configuration

#### `validate_export_compatibility`
Check export compatibility.
- **Parameters**: export_data, target_system
- **Returns**: Compatibility report

## Usage Examples

### Basic Search and Organization
```
# Find cyberpunk portraits
await search_assets(
    description="cyberpunk portrait",
    style_tags=["digital_art", "neon"],
    limit=20
)

# Organize new downloads
await organize_media(
    source_path="/Users/me/Downloads/AI",
    understanding=True
)
```

### Video Creation Workflow
```
# Generate video
result = await generate_video(
    prompt="Cyberpunk city at night, neon lights",
    provider="runway",
    duration=5,
    aspect_ratio="16:9"
)

# Check status
status = await check_video_status(
    generation_id=result["generation_id"],
    provider="runway"
)
```

### Timeline Creation
```
# Create timeline from images
timeline = await create_timeline(
    asset_ids=["hash1", "hash2", "hash3"],
    duration=30,
    transitions="smooth"
)

# Export for DaVinci Resolve
await export_timeline(
    timeline_id=timeline["id"],
    format="xml"
)
```

## Best Practices

1. **Batch Operations**: Use batch tools when processing multiple items
2. **Cost Awareness**: Always check costs before generation operations
3. **Caching**: Results are cached automatically for efficiency
4. **Error Handling**: All tools return structured error responses
5. **Async Operations**: Long-running operations return IDs for status checking

## Integration Notes

- All tools follow MCP (Model Context Protocol) standards
- Authentication is handled by the MCP server
- File paths should be absolute
- Large results are automatically paginated
- Rate limits are respected automatically

## Version History

- v1.7.1: Added style memory and learning tools
- v1.7.0: Added deduplication and B-roll suggestions
- v1.6.0: Enhanced video providers (7 total)
- v1.5.0: Timeline preview and natural language editing
- v1.4.0: Advanced transitions and effects
- v1.3.0: Prompt management system
- v1.2.0: Multi-version export
- v1.1.0: Performance analytics
- v1.0.0: Initial 60 core tools