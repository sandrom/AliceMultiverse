#!/usr/bin/env python3
"""
Configuration Validation Demo

This script demonstrates the configuration validation features:
1. System resource detection
2. Configuration validation
3. Smart configuration building
4. Runtime compatibility checks
"""

from pathlib import Path
import tempfile

from alicemultiverse.core.config_validation import (
    ConfigValidator,
    SmartConfigBuilder,
    SystemResources
)
from alicemultiverse.core.startup_validation import StartupValidator


def demonstrate_system_detection():
    """Demonstrate system resource detection."""
    print("\n=== System Resource Detection ===")
    
    resources = SystemResources.detect()
    
    print(f"CPU Count: {resources.cpu_count}")
    print(f"Memory: {resources.memory_mb:,} MB")
    print(f"Available Disk: {resources.available_disk_mb:,} MB")
    print(f"GPU Available: {resources.has_gpu}")


def demonstrate_config_validation():
    """Demonstrate configuration validation."""
    print("\n=== Configuration Validation ===")
    
    validator = ConfigValidator()
    
    # Create test configuration
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        inbox = tmppath / "inbox"
        inbox.mkdir()
        
        config = {
            "paths": {
                "inbox": str(inbox),
                "organized": str(tmppath / "organized")  # Will be created
            },
            "performance": {
                "max_workers": 100,  # Excessive
                "batch_size": 50,
                "profile": "fast"
            },
            "storage": {
                "search_db": str(tmppath / "search.db"),
                "cache_size_mb": 10000  # Very large
            },
            "understanding": {
                "enabled": True,
                "providers": ["openai"],
                "cost_limit": 10.0
            }
        }
        
        # Validate
        result = validator.validate_config(config)
        
        print(f"\nValidation Result: {'VALID' if result.is_valid else 'INVALID'}")
        
        if result.errors:
            print("\nErrors:")
            for field, error in result.errors.items():
                print(f"  ✗ {field}: {error}")
        
        if result.warnings:
            print("\nWarnings:")
            for field, warning in result.warnings.items():
                print(f"  ⚠ {field}: {warning}")
        
        if result.recommendations:
            print("\nRecommendations:")
            for rec in result.recommendations:
                print(f"  → {rec}")


def demonstrate_smart_config_builder():
    """Demonstrate smart configuration building."""
    print("\n=== Smart Configuration Builder ===")
    
    builder = SmartConfigBuilder()
    
    # Show recommended profile
    profile, settings = builder.validator.recommend_performance_profile()
    
    print(f"\nRecommended Profile: {profile}")
    print("Settings:")
    for key, value in settings.items():
        print(f"  {key}: {value}")
    
    # Build configs for different use cases
    use_cases = ["quick_scan", "full_analysis", "bulk_import"]
    
    print("\n--- Use Case Optimizations ---")
    for use_case in use_cases:
        config = builder.build_config({}, use_case)
        perf = config.get("performance", {})
        print(f"\n{use_case}:")
        print(f"  Workers: {perf.get('max_workers')}")
        print(f"  Batch Size: {perf.get('batch_size')}")
        if 'enable_understanding' in perf:
            print(f"  Understanding: {perf.get('enable_understanding')}")


def demonstrate_collection_optimization():
    """Demonstrate collection size optimization."""
    print("\n=== Collection Size Optimization ===")
    
    builder = SmartConfigBuilder()
    
    sizes = [50, 500, 5000, 50000]
    
    for size in sizes:
        config = builder.optimize_for_collection_size(
            {"performance": {}},
            size
        )
        
        perf = config["performance"]
        print(f"\n{size:,} files:")
        print(f"  Workers: {perf.get('max_workers')}")
        print(f"  Batch Size: {perf.get('batch_size')}")
        if perf.get('enable_batch_operations'):
            print(f"  Batch Operations: Enabled")


def demonstrate_runtime_validation():
    """Demonstrate runtime compatibility checks."""
    print("\n=== Runtime Compatibility ===")
    
    validator = ConfigValidator()
    
    # Test with current system state
    config = {
        "performance": {
            "batch_size": 500,
            "max_workers": 16
        }
    }
    
    result = validator.validate_runtime_compatibility(config)
    
    print(f"\nRuntime Check: {'OK' if result.is_valid else 'WARNINGS'}")
    
    if result.warnings:
        print("\nWarnings:")
        for field, warning in result.warnings.items():
            print(f"  ⚠ {warning}")
    
    if result.recommendations:
        print("\nRecommendations:")
        for rec in result.recommendations:
            print(f"  → {rec}")


def demonstrate_startup_validation():
    """Demonstrate startup validation process."""
    print("\n=== Startup Validation ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create test config file
        import yaml
        config_path = tmppath / "test_config.yaml"
        
        config = {
            "paths": {
                "inbox": str(tmppath / "inbox"),
                "organized": str(tmppath / "organized")
            },
            "performance": {
                "max_workers": 8,
                "batch_size": 100
            }
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f)
        
        # Run startup validation
        validator = StartupValidator(config_path)
        
        print("\nRunning startup validation...")
        
        # This would normally show rich console output
        # For demo, we'll just check if it passes
        try:
            if validator.validate_startup(auto_fix=True):
                print("✓ Startup validation passed!")
                
                # Check that directories were created
                if (tmppath / "inbox").exists():
                    print("✓ Inbox directory created")
                if (tmppath / "organized").exists():
                    print("✓ Organized directory created")
        except Exception as e:
            print(f"✗ Validation failed: {e}")


def demonstrate_validation_fixing():
    """Demonstrate automatic fixing of issues."""
    print("\n=== Automatic Issue Fixing ===")
    
    with tempfile.TemporaryDirectory() as tmpdir:
        tmppath = Path(tmpdir)
        
        # Create config with issues
        config = {
            "paths": {
                "inbox": str(tmppath / "nonexistent_inbox"),
                "organized": str(tmppath / "nonexistent_organized")
            },
            "performance": {
                "profile": "invalid_profile"  # Invalid
            }
        }
        
        validator = ConfigValidator()
        
        # Initial validation
        result = validator.validate_config(config)
        print(f"\nBefore Fix - Valid: {result.is_valid}")
        print(f"Errors: {len(result.errors)}")
        
        # Apply fixes
        print("\nApplying automatic fixes...")
        
        # Create missing directories
        (tmppath / "nonexistent_inbox").mkdir()
        
        # Fix invalid profile
        profile, settings = validator.recommend_performance_profile()
        config["performance"] = settings
        config["performance"]["profile"] = profile
        
        # Re-validate
        result = validator.validate_config(config)
        print(f"\nAfter Fix - Valid: {result.is_valid}")
        print(f"Errors: {len(result.errors)}")


def main():
    """Run all demonstrations."""
    print("AliceMultiverse Configuration Validation Demo")
    print("=" * 50)
    
    demonstrate_system_detection()
    demonstrate_config_validation()
    demonstrate_smart_config_builder()
    demonstrate_collection_optimization()
    demonstrate_runtime_validation()
    demonstrate_startup_validation()
    demonstrate_validation_fixing()
    
    print("\n" + "=" * 50)
    print("Demo completed!")


if __name__ == "__main__":
    main()