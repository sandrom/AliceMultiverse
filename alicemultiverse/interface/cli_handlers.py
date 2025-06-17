"""Command handlers for AliceMultiverse CLI."""

import logging
from pathlib import Path

from omegaconf import DictConfig

from ..core.keys.manager import APIKeyManager
from ..organizer import media_organizer as create_organizer

logger = logging.getLogger(__name__)


def handle_keys_command(args, config: DictConfig) -> int:
    """Handle keys management commands."""
    key_manager = APIKeyManager()

    if args.keys_command == "set":
        import getpass
        value = getpass.getpass(f"Enter value for {args.key_name}: ")
        if key_manager.set_api_key(args.key_name, value, method=args.method):
            print(f"✓ {args.key_name} saved to {args.method}")
            return 0
        else:
            print(f"✗ Failed to save {args.key_name}")
            return 1

    elif args.keys_command == "get":
        value = key_manager.get_api_key(args.key_name)
        if value:
            print(f"{args.key_name}: {'*' * 10}{value[-4:]}")
            return 0
        else:
            print(f"{args.key_name}: Not found")
            return 1

    elif args.keys_command == "delete":
        if key_manager.delete_api_key(args.key_name):
            print(f"✓ {args.key_name} deleted")
            return 0
        else:
            print(f"✗ Failed to delete {args.key_name}")
            return 1

    elif args.keys_command == "list":
        keys = key_manager.list_api_keys()
        if keys:
            print("Stored API keys:")
            for key in keys:
                print(f"  - {key}")
        else:
            print("No API keys stored")
        return 0

    elif args.keys_command == "setup":
        from ..core.keys.setup_wizard import run_setup_wizard
        return run_setup_wizard()

    return 0


def handle_setup_command(args, config: DictConfig) -> int:
    """Handle setup wizard command."""
    from ..core.setup import run_first_time_setup

    # Check if already configured
    settings_path = Path.home() / ".alice" / "settings.yaml"
    if settings_path.exists() and not args.reconfigure:
        print("Alice is already configured. Use --reconfigure to run setup again.")
        return 0

    return run_first_time_setup()


def handle_recreate_command(args, config: DictConfig) -> int:
    """Handle recreation commands."""
    from ..recreation import RecreationManager

    manager = RecreationManager(config)

    if args.recreate_command == "inspect":
        metadata = manager.inspect_generation(Path(args.file))
        if metadata:
            import json
            print(json.dumps(metadata, indent=2))
            return 0
        else:
            print("No generation metadata found")
            return 1

    elif args.recreate_command == "recreate":
        results = manager.recreate_generation(
            Path(args.file),
            provider=args.provider,
            output_dir=Path(args.output) if args.output else None,
            variations=args.variations
        )
        print(f"Created {len(results)} variations")
        return 0

    elif args.recreate_command == "catalog":
        catalog = manager.catalog_generations(Path(args.directory))
        if args.output:
            import json
            with open(args.output, "w") as f:
                json.dump(catalog, f, indent=2)
            print(f"Catalog saved to {args.output}")
        else:
            import json
            print(json.dumps(catalog, indent=2))
        return 0

    return 0


def handle_interface_command(args, config: DictConfig) -> int:
    """Handle interface server command."""
    from ..interface.server import run_server

    print(f"Starting Alice interface on http://{args.host}:{args.port}")
    print("This is the AI-native service mode - use with AI assistants")

    return run_server(host=args.host, port=args.port, config=config)


def handle_mcp_command(args, config: DictConfig) -> int:
    """Handle MCP server command."""
    from ..interface.mcp_server import run_mcp_server

    # Set up logging for MCP mode
    logging.getLogger().setLevel(logging.WARNING)

    # Run MCP server
    return run_mcp_server(
        transport=args.transport,
        host=args.host,
        port=args.port,
        config=config
    )


def handle_migrate_command(args, config: DictConfig) -> int:
    """Handle migration commands."""
    from ..migration import MigrationManager

    manager = MigrationManager(config)

    if args.migrate_command == "from-legacy":
        stats = manager.migrate_from_legacy(
            source=Path(args.source),
            target=Path(args.target),
            dry_run=args.dry_run
        )

        print(f"Migration {'(dry run) ' if args.dry_run else ''}complete:")
        print(f"  Files processed: {stats['processed']}")
        print(f"  Files migrated: {stats['migrated']}")
        print(f"  Errors: {stats['errors']}")

        return 0

    return 0


def handle_monitor_command(args, config: DictConfig) -> int:
    """Handle monitoring commands."""
    if args.monitor_command == "events":
        from ..monitoring.event_monitor import monitor_events

        return monitor_events(
            follow=args.follow,
            filter_type=args.filter,
            format=args.format
        )

    elif args.monitor_command == "metrics":
        from ..monitoring.metrics_monitor import monitor_metrics

        return monitor_metrics(interval=args.interval)

    return 0


def handle_storage_command(args, config: DictConfig) -> int:
    """Handle storage commands."""
    from ..storage import StorageManager

    manager = StorageManager(config)

    if args.storage_command == "scan":
        for directory in args.directories:
            print(f"Scanning {directory}...")
            stats = manager.scan_directory(
                Path(directory),
                recursive=args.recursive
            )
            print(f"  Found {stats['files']} files")
            print(f"  Total size: {stats['size_mb']:.1f} MB")

    elif args.storage_command == "index":
        if args.action == "rebuild":
            print("Rebuilding search index...")
            manager.rebuild_index()
            print("Index rebuilt successfully")
        elif args.action == "update":
            print("Updating search index...")
            manager.update_index()
            print("Index updated successfully")
        elif args.action == "optimize":
            print("Optimizing search index...")
            manager.optimize_index()
            print("Index optimized successfully")

    return 0


def handle_scenes_command(args, config: DictConfig) -> int:
    """Handle scene detection commands."""
    from ..scene_detection import SceneDetector

    detector = SceneDetector(config)

    if args.scenes_command == "detect":
        print(f"Detecting scenes in {args.video}...")
        scenes = detector.detect_scenes(
            Path(args.video),
            threshold=args.threshold
        )

        if args.output:
            import json
            with open(args.output, "w") as f:
                json.dump(scenes, f, indent=2)
            print(f"Found {len(scenes)} scenes, saved to {args.output}")
        else:
            print(f"Found {len(scenes)} scenes")
            for i, scene in enumerate(scenes):
                print(f"  Scene {i+1}: {scene['start']:.2f}s - {scene['end']:.2f}s")

    elif args.scenes_command == "shotlist":
        import json

        from ..scene_detection import generate_shotlist
        with open(args.scenes_file) as f:
            scenes = json.load(f)

        shotlist = generate_shotlist(
            scenes,
            format=args.format,
            project_name=getattr(args, 'project_name', 'Untitled'),
            style=getattr(args, 'style', 'cinematic')
        )

        with open(args.output, "w") as f:
            if args.format == "json":
                json.dump(shotlist, f, indent=2)
            else:
                f.write(shotlist)

        print(f"Shot list saved to {args.output}")

    elif args.scenes_command == "extract":
        print(f"Extracting frames from {args.video}...")

        if args.scenes_file:
            import json
            with open(args.scenes_file) as f:
                scenes = json.load(f)
        else:
            scenes = detector.detect_scenes(Path(args.video))

        output_dir = Path(args.output) if args.output else Path("frames")
        detector.extract_frames(
            Path(args.video),
            scenes,
            output_dir,
            format=getattr(args, 'format', 'jpg')
        )

        print(f"Extracted frames to {output_dir}")

    return 0


def handle_dedup_command(args, config: DictConfig) -> int:
    """Handle deduplication commands."""
    from ..assets.deduplication import DeduplicationEngine

    engine = DeduplicationEngine(config)

    if args.dedup_command == "find":
        print(f"Scanning {args.directory} for duplicates...")
        report = engine.find_duplicates(
            Path(args.directory),
            threshold=args.threshold,
            recursive=getattr(args, 'recursive', True),
            include_similar=getattr(args, 'include_similar', True)
        )

        print(f"Found {len(report['duplicates'])} duplicate groups")
        print(f"Total space that could be saved: {report['potential_savings_mb']:.1f} MB")

        if getattr(args, 'output', None):
            import json
            with open(args.output, "w") as f:
                json.dump(report, f, indent=2)
            print(f"Report saved to {args.output}")

    elif args.dedup_command == "remove":
        import json
        with open(args.report) as f:
            report = json.load(f)

        if getattr(args, 'dry_run', True):
            print("DRY RUN - no files will be deleted")

        stats = engine.remove_duplicates(
            report,
            strategy=args.strategy,
            backup_dir=Path(args.backup) if getattr(args, 'backup', None) else None,
            dry_run=getattr(args, 'dry_run', True)
        )

        print(f"Removed {stats['removed']} files")
        print(f"Freed {stats['space_freed_mb']:.1f} MB")

    return 0


def handle_prompts_command(args, config: DictConfig) -> int:
    """Handle prompts management commands."""
    from ..prompts import PromptManager

    manager = PromptManager(config)

    if args.prompts_command == "add":
        prompt_id = manager.add_prompt(
            text=args.text,
            category=args.category,
            providers=getattr(args, 'providers', []),
            tags=getattr(args, 'tags', []),
            project=getattr(args, 'project', None),
            style=getattr(args, 'style', None),
            description=getattr(args, 'description', None),
            notes=getattr(args, 'notes', None),
            keywords=getattr(args, 'keywords', [])
        )
        print(f"Added prompt: {prompt_id}")

    elif args.prompts_command == "search":
        results = manager.search_prompts(
            query=args.query,
            category=getattr(args, 'category', None),
            provider=getattr(args, 'provider', None),
            tags=getattr(args, 'tag', []),
            project=getattr(args, 'project', None),
            style=getattr(args, 'style', None),
            min_effectiveness=getattr(args, 'min_effectiveness', None),
            min_success_rate=getattr(args, 'min_success_rate', None),
            effective_only=getattr(args, 'effective', False),
            limit=getattr(args, 'limit', 20)
        )

        print(f"Found {len(results)} prompts")
        for prompt in results:
            print(f"\n[{prompt['id']}] {prompt['category']} - {', '.join(prompt['providers'])}")
            print(f"  {prompt['text'][:100]}...")
            if prompt.get('effectiveness'):
                print(f"  Effectiveness: {prompt['effectiveness']:.2f}")

        if getattr(args, 'export', None):
            import json
            with open(args.export, "w") as f:
                json.dump(results, f, indent=2)
            print(f"\nExported to {args.export}")

    return 0


def handle_organize_command(args, config: DictConfig) -> int:
    """Handle the default organize command."""
    # Validate paths
    inbox_path = Path(config.paths.inbox)
    organized_path = Path(config.paths.organized)

    if not inbox_path.exists():
        logger.error(f"Inbox directory does not exist: {inbox_path}")
        return 1

    # Create organizer
    organizer = create_organizer(config)

    # Run organization
    if config.watch.enabled:
        print(f"Watching {inbox_path} for new media...")
        print("Press Ctrl+C to stop")

        try:
            from ..monitoring import WatchMode
            watcher = WatchMode(organizer, config)
            watcher.run()
        except KeyboardInterrupt:
            print("\nStopping watch mode...")

    else:
        # Single run
        stats = organizer.organize()

        # Print summary
        print("\nOrganization complete:")
        print(f"  Files processed: {stats['processed']}")
        print(f"  Files organized: {stats['organized']}")
        print(f"  Files skipped: {stats['skipped']}")
        print(f"  Errors: {stats['errors']}")

        if config.understanding.enabled:
            print(f"  Understanding cost: ${stats.get('understanding_cost', 0):.4f}")

    return 0


def handle_index_command(args, config: DictConfig) -> int:
    """Handle index management commands."""
    from ..storage.index_builder import SearchIndexBuilder

    # Get DB path from config
    db_path = None
    if hasattr(config, 'storage') and hasattr(config.storage, 'search_db'):
        db_path = config.storage.search_db

    builder = SearchIndexBuilder(db_path)

    if args.index_command == "rebuild":
        print(f"Rebuilding search index from {len(args.paths)} paths...")
        count = builder.rebuild_from_paths(
            args.paths,
            show_progress=not args.no_progress
        )
        print(f"\nSuccessfully indexed {count} assets")
        return 0

    elif args.index_command == "update":
        print(f"Updating search index from {args.path}...")
        count = builder.update_from_path(args.path)
        print(f"Updated {count} assets in index")
        return 0

    elif args.index_command == "verify":
        print("Verifying search index...")
        results = builder.verify_index()
        print("\nIndex verification results:")
        print(f"  Total indexed: {results['total_indexed']}")
        print(f"  Valid files: {results['valid_files']}")
        print(f"  Missing files: {results['missing_files']}")
        if results['missing_files'] > 0 and results['missing_file_paths']:
            print("\nFirst few missing files:")
            for path in results['missing_file_paths'][:10]:
                print(f"  - {path}")
        return 0

    elif args.index_command == "stats":
        print("Search index statistics:")
        stats = builder.search_db.get_statistics()
        print(f"  Total assets: {stats.get('total_assets', 0)}")
        print(f"  Unique tags: {stats.get('unique_tags', 0)}")
        print(f"  Storage size: {stats.get('storage_size_mb', 0):.1f} MB")
        return 0

    return 0


def handle_comparison_command(args, config: DictConfig) -> int:
    """Handle comparison commands."""
    if args.comparison_command == "server":
        import os

        from ..comparison.web_server import run_server

        if args.populate_test_data:
            os.environ["ALICE_ENV"] = "development"

        run_server(host=args.host, port=args.port)
        return 0
    else:
        # Handle other comparison commands
        from ..comparison.cli import cli as comparison_cli

        # Build command line args for click
        click_args = [args.comparison_command]

        if args.comparison_command == "populate":
            click_args.append(args.directory)
            if args.recursive:
                click_args.append("--recursive")
            if args.limit:
                click_args.extend(["--limit", str(args.limit)])
        elif args.comparison_command == "populate-default":
            if hasattr(args, "limit") and args.limit:
                click_args.extend(["--limit", str(args.limit)])
        # stats and reset don't need additional args

        comparison_cli(click_args)
        return 0


def handle_transitions_command(args, config: DictConfig) -> int:
    """Handle transitions commands."""
    from ..workflows.transitions.cli import transitions as transitions_cli

    # Build command line args for click
    click_args = [args.transitions_command]

    if args.transitions_command == "analyze":
        click_args.extend(args.images)
        if hasattr(args, "output") and args.output:
            click_args.extend(["-o", args.output])
        if hasattr(args, "verbose") and args.verbose:
            click_args.append("-v")
    elif args.transitions_command == "motion":
        click_args.append(args.image)
        if hasattr(args, "verbose") and args.verbose:
            click_args.append("-v")

    transitions_cli(click_args)
    return 0
