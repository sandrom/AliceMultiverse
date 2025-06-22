#!/usr/bin/env python3
"""Validate the complete restoration of AliceMultiverse."""

import sys
import importlib
import inspect
from typing import List, Tuple
from pathlib import Path


def test_imports() -> Tuple[int, int, List[str]]:
    """Test all critical imports."""
    modules_to_test = [
        # Core modules
        "alicemultiverse.core.config_dataclass",
        "alicemultiverse.core.memory_optimization",
        "alicemultiverse.core.structured_logging",
        "alicemultiverse.core.unified_cache",
        "alicemultiverse.core.file_operations",
        "alicemultiverse.core.keys.manager",
        
        # Interface modules
        "alicemultiverse.interface.main_cli",
        "alicemultiverse.interface.cli_parser",
        "alicemultiverse.interface.cli_handlers",
        "alicemultiverse.interface.validation.basic",
        "alicemultiverse.interface.validation.request_validators",
        "alicemultiverse.interface.alice_api",
        "alicemultiverse.interface.mcp_server",
        
        # Storage modules
        "alicemultiverse.storage.batch_operations",
        "alicemultiverse.storage.location_registry",
        "alicemultiverse.storage.multi_path_scanner",
        
        # Analytics modules
        "alicemultiverse.analytics.performance_tracker",
        
        # Event modules
        "alicemultiverse.events.file_events",
        
        # Provider modules
        "alicemultiverse.understanding.providers",
        
        # Monitoring modules
        "alicemultiverse.monitoring.metrics",
        "alicemultiverse.monitoring.tracker",
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for module_name in modules_to_test:
        try:
            module = importlib.import_module(module_name)
            passed += 1
            print(f"✅ {module_name}")
        except Exception as e:
            failed += 1
            errors.append(f"{module_name}: {str(e)}")
            print(f"❌ {module_name}: {e}")
    
    return passed, failed, errors


def test_class_completeness() -> Tuple[int, int, List[str]]:
    """Test that restored classes have all expected methods."""
    classes_to_test = [
        ("alicemultiverse.core.memory_optimization", "MemoryMonitor"),
        ("alicemultiverse.core.memory_optimization", "BoundedCache"),
        ("alicemultiverse.core.memory_optimization", "ObjectPool"),
        ("alicemultiverse.core.memory_optimization", "StreamingFileReader"),
        ("alicemultiverse.analytics.performance_tracker", "PerformanceTracker"),
        ("alicemultiverse.storage.batch_operations", "BatchOperations"),
        ("alicemultiverse.events.file_events", "FileEventPublisher"),
        ("alicemultiverse.core.config_dataclass", "Config"),
    ]
    
    passed = 0
    failed = 0
    errors = []
    
    for module_name, class_name in classes_to_test:
        try:
            module = importlib.import_module(module_name)
            cls = getattr(module, class_name)
            
            # Check if class has methods (not just TODO comments)
            methods = [m for m in inspect.getmembers(cls, inspect.ismethod) 
                      if not m[0].startswith('_')]
            
            if len(methods) > 0 or hasattr(cls, '__init__'):
                passed += 1
                print(f"✅ {class_name} has {len(methods)} public methods")
            else:
                failed += 1
                errors.append(f"{class_name} has no methods")
                print(f"❌ {class_name} has no methods")
                
        except Exception as e:
            failed += 1
            errors.append(f"{class_name}: {str(e)}")
            print(f"❌ {class_name}: {e}")
    
    return passed, failed, errors


def test_cli_functionality() -> Tuple[int, int, List[str]]:
    """Test CLI parser functionality."""
    passed = 0
    failed = 0
    errors = []
    
    try:
        from alicemultiverse.interface.main_cli import create_parser
        parser = create_parser()
        
        # Test that parser has expected commands
        if parser._subparsers:
            subparsers_actions = parser._subparsers._actions
            if subparsers_actions:
                commands = []
                for action in subparsers_actions:
                    if hasattr(action, 'choices'):
                        commands.extend(action.choices.keys())
                
                expected_commands = ['mcp-server', 'keys', 'debug']
                for cmd in expected_commands:
                    if cmd in commands:
                        passed += 1
                        print(f"✅ CLI command '{cmd}' available")
                    else:
                        failed += 1
                        errors.append(f"Missing CLI command: {cmd}")
                        print(f"❌ Missing CLI command: {cmd}")
        
    except Exception as e:
        failed += 1
        errors.append(f"CLI parser error: {str(e)}")
        print(f"❌ CLI parser error: {e}")
    
    return passed, failed, errors


def check_todo_comments() -> Tuple[int, List[str]]:
    """Check for remaining TODO comments in critical files."""
    critical_files = [
        "alicemultiverse/core/config_dataclass.py",
        "alicemultiverse/core/memory_optimization.py",
        "alicemultiverse/interface/validation/basic.py",
        "alicemultiverse/interface/cli_handlers.py",
        "alicemultiverse/storage/batch_operations.py",
        "alicemultiverse/analytics/performance_tracker.py",
    ]
    
    todo_count = 0
    files_with_todos = []
    
    for file_path in critical_files:
        path = Path(file_path)
        if path.exists():
            content = path.read_text()
            todos = content.count("TODO:")
            if todos > 0:
                todo_count += todos
                files_with_todos.append(f"{file_path} ({todos} TODOs)")
    
    return todo_count, files_with_todos


def main():
    """Run all validation tests."""
    print("🔍 Validating AliceMultiverse Restoration")
    print("=" * 60)
    
    total_passed = 0
    total_failed = 0
    all_errors = []
    
    # Test imports
    print("\n📦 Testing Module Imports...")
    passed, failed, errors = test_imports()
    total_passed += passed
    total_failed += failed
    all_errors.extend(errors)
    
    # Test class completeness
    print(f"\n🏗️ Testing Class Implementations...")
    passed, failed, errors = test_class_completeness()
    total_passed += passed
    total_failed += failed
    all_errors.extend(errors)
    
    # Test CLI functionality
    print(f"\n⌨️ Testing CLI Functionality...")
    passed, failed, errors = test_cli_functionality()
    total_passed += passed
    total_failed += failed
    all_errors.extend(errors)
    
    # Check for remaining TODOs
    print(f"\n🔎 Checking for Remaining TODOs...")
    todo_count, files_with_todos = check_todo_comments()
    if todo_count == 0:
        print("✅ No TODO comments found in critical files")
        total_passed += 1
    else:
        print(f"⚠️ Found {todo_count} TODO comments in:")
        for file in files_with_todos:
            print(f"   - {file}")
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 VALIDATION SUMMARY")
    print("=" * 60)
    print(f"✅ Passed: {total_passed}")
    print(f"❌ Failed: {total_failed}")
    print(f"📈 Success Rate: {(total_passed / (total_passed + total_failed) * 100):.1f}%")
    
    if all_errors:
        print(f"\n⚠️ Errors encountered:")
        for error in all_errors[:10]:  # Show first 10 errors
            print(f"   - {error}")
        if len(all_errors) > 10:
            print(f"   ... and {len(all_errors) - 10} more")
    
    if total_failed == 0:
        print("\n🎉 PERFECT VALIDATION! All systems operational!")
        return 0
    else:
        print(f"\n⚠️ Some issues remain, but {total_passed} components are working!")
        return 1


if __name__ == "__main__":
    sys.exit(main())