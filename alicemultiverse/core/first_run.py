"""First-run experience and setup wizard for AliceMultiverse.

This module provides a friendly first-run experience that:
1. Checks system requirements
2. Sets up API keys
3. Creates initial configuration
4. Runs a test organization
5. Provides next steps
"""

import os
import sys
import json
import shutil
import logging
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime

from .config import load_config
from .keys import APIKeyManager
from .structured_logging import get_logger

logger = get_logger(__name__)


class FirstRunWizard:
    """Interactive setup wizard for first-time users."""
    
    # Supported providers with friendly names
    PROVIDERS = {
        "anthropic": {
            "name": "Anthropic (Claude)",
            "required_for": "Advanced image understanding",
            "signup_url": "https://console.anthropic.com/",
            "free_tier": False,
            "recommended": True
        },
        "openai": {
            "name": "OpenAI (GPT-4)",
            "required_for": "Image analysis",
            "signup_url": "https://platform.openai.com/",
            "free_tier": False,
            "recommended": False
        },
        "google": {
            "name": "Google AI (Gemini)",
            "required_for": "Free image understanding (50/day)",
            "signup_url": "https://makersuite.google.com/app/apikey",
            "free_tier": True,
            "recommended": True
        },
        "deepseek": {
            "name": "DeepSeek",
            "required_for": "Cost-effective understanding",
            "signup_url": "https://platform.deepseek.com/",
            "free_tier": False,
            "recommended": True
        }
    }
    
    def __init__(self):
        """Initialize the wizard."""
        self.key_manager = APIKeyManager()
        self.config_path = Path("settings.yaml")
        self.config = None
        self.has_any_key = False
        
    def run(self) -> bool:
        """Run the first-run wizard.
        
        Returns:
            True if setup completed successfully
        """
        try:
            self._print_welcome()
            
            # Check if already configured
            if self._is_already_configured():
                return self._handle_existing_setup()
            
            # System checks
            if not self._check_system_requirements():
                return False
            
            # API key setup
            self._setup_api_keys()
            
            # Directory setup
            self._setup_directories()
            
            # Create initial configuration
            self._create_initial_config()
            
            # Run test if possible
            if self.has_any_key:
                self._run_test_organization()
            
            # Show next steps
            self._show_next_steps()
            
            return True
            
        except KeyboardInterrupt:
            print("\n\n❌ Setup cancelled by user")
            return False
        except Exception as e:
            logger.error(f"Setup failed: {e}")
            print(f"\n❌ Setup failed: {e}")
            return False
    
    def _print_welcome(self):
        """Print welcome message."""
        print("""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║               Welcome to AliceMultiverse! 🎨                  ║
║                                                               ║
║     Sandro's Personal Tool for AI Image Organization          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

Hi! I'm the setup wizard. I'll help you:
  ✓ Set up API keys (with cost info)
  ✓ Configure your directories
  ✓ Test that everything works

This takes about 2 minutes. Let's start!
""")
    
    def _is_already_configured(self) -> bool:
        """Check if AliceMultiverse is already configured."""
        # Check for existing config
        if self.config_path.exists():
            try:
                self.config = load_config(str(self.config_path))
                return True
            except:
                pass
        
        # Check for API keys
        for provider in self.PROVIDERS:
            if self.key_manager.get_api_key(provider):
                return True
                
        return False
    
    def _handle_existing_setup(self) -> bool:
        """Handle case where setup already exists."""
        print("✅ AliceMultiverse appears to be already configured!")
        print("\nCurrent setup:")
        
        # Show API keys status
        print("\n📑 API Keys:")
        for provider, info in self.PROVIDERS.items():
            key = self.key_manager.get_api_key(provider)
            if key:
                print(f"  ✓ {info['name']}: Configured")
            else:
                print(f"  ✗ {info['name']}: Not configured")
        
        # Show directories
        if self.config:
            print(f"\n📁 Directories:")
            print(f"  • Inbox: {self.config.paths.inbox}")
            print(f"  • Organized: {self.config.paths.organized}")
        
        print("\nOptions:")
        print("1. Run setup again (reconfigure)")
        print("2. Add missing API keys")
        print("3. Exit (keep current setup)")
        
        choice = input("\nYour choice (1-3): ").strip()
        
        if choice == "1":
            return self._run_full_setup()
        elif choice == "2":
            self._setup_api_keys(missing_only=True)
            return True
        else:
            print("\n✅ Keeping existing setup")
            return True
    
    def _check_system_requirements(self) -> bool:
        """Check system requirements."""
        print("\n🔍 Checking system requirements...")
        
        issues = []
        
        # Check Python version
        if sys.version_info < (3, 9):
            issues.append(f"Python 3.9+ required (you have {sys.version_info.major}.{sys.version_info.minor})")
        
        # Check essential dependencies
        try:
            import PIL
            import cv2
            import numpy
        except ImportError as e:
            issues.append(f"Missing dependency: {e.name}")
        
        # Check optional but recommended
        warnings = []
        try:
            import redis
        except ImportError:
            warnings.append("Redis not installed (optional - file-based events will be used)")
        
        # Check disk space
        home = Path.home()
        if hasattr(shutil, 'disk_usage'):
            usage = shutil.disk_usage(home)
            free_gb = usage.free / (1024**3)
            if free_gb < 1:
                issues.append(f"Low disk space: {free_gb:.1f}GB free")
            elif free_gb < 5:
                warnings.append(f"Limited disk space: {free_gb:.1f}GB free")
        
        # Report results
        if issues:
            print("\n❌ System requirements not met:")
            for issue in issues:
                print(f"  • {issue}")
            return False
        
        print("  ✓ Python version OK")
        print("  ✓ Essential dependencies OK")
        print("  ✓ Disk space OK")
        
        if warnings:
            print("\n⚠️  Warnings:")
            for warning in warnings:
                print(f"  • {warning}")
        
        print("\n✅ System requirements met!")
        return True
    
    def _setup_api_keys(self, missing_only: bool = False):
        """Set up API keys interactively."""
        print("\n🔑 API Key Setup")
        print("=" * 50)
        
        if not missing_only:
            print("""
AliceMultiverse uses AI providers to understand your images.
You can start with just one provider and add more later.

💰 COST COMPARISON:
  • Google AI:    FREE (50 images/day) ⭐ BEST FOR BEGINNERS
  • DeepSeek:     ~$0.0002/image (~$0.10 for 500 images)
  • Anthropic:    ~$0.0025/image (~$1.25 for 500 images)
  • OpenAI:       ~$0.0050/image (~$2.50 for 500 images)

💡 TIP: Start with Google AI's free tier, add others if needed.
""")
        
        # Check existing keys
        existing_keys = {}
        for provider in self.PROVIDERS:
            key = self.key_manager.get_api_key(provider)
            if key:
                existing_keys[provider] = True
                self.has_any_key = True
        
        # Ask about each provider in recommended order
        provider_order = ["google", "deepseek", "anthropic", "openai"]
        for provider in provider_order:
            if provider not in self.PROVIDERS:
                continue
            info = self.PROVIDERS[provider]
            if missing_only and provider in existing_keys:
                continue
                
            print(f"\n{info['name']}:")
            print(f"  • Used for: {info['required_for']}")
            if info['free_tier']:
                print(f"  • ✨ FREE TIER AVAILABLE")
            if info['recommended']:
                print(f"  • 👍 RECOMMENDED")
            print(f"  • Sign up: {info['signup_url']}")
            
            if provider in existing_keys:
                print("  • ✓ Already configured")
                change = input("  Change key? (y/N): ").strip().lower()
                if change != 'y':
                    continue
            
            # Ask if they want to set up this provider
            setup_provider = input(f"\nSet up {info['name']}? (y/N): ").strip().lower()
            if setup_provider != 'y':
                print(f"  Skipped {info['name']}")
                continue
            
            print(f"\n  📝 Get your API key from: {info['signup_url']}")
            
            while True:
                key = input(f"  Enter {provider} API key: ").strip()
                
                if not key:
                    skip = input("  Skip this provider? (Y/n): ").strip().lower()
                    if skip != 'n':
                        print(f"  Skipped {info['name']}")
                        break
                    continue
                
                # Validate key format
                if self._validate_api_key(provider, key):
                    try:
                        self.key_manager.store_api_key(provider, key)
                        print(f"  ✓ {info['name']} key saved securely")
                        self.has_any_key = True
                        break
                    except Exception as e:
                        print(f"  ❌ Failed to save key: {e}")
                else:
                    print(f"  ❌ Invalid key format for {provider}")
                    retry = input("  Try again? (Y/n): ").strip().lower()
                    if retry == 'n':
                        break
        
        if not self.has_any_key:
            print("\n⚠️  No API keys configured!")
            print("You can add keys later with: alice keys setup")
    
    def _validate_api_key(self, provider: str, key: str) -> bool:
        """Validate API key format."""
        validations = {
            "anthropic": lambda k: k.startswith("sk-ant-"),
            "openai": lambda k: k.startswith("sk-") and len(k) > 20,
            "google": lambda k: len(k) > 20,
            "deepseek": lambda k: len(k) > 20,
        }
        
        validator = validations.get(provider, lambda k: len(k) > 10)
        return validator(key)
    
    def _setup_directories(self):
        """Set up directory structure."""
        print("\n📁 Directory Setup")
        print("=" * 50)
        
        # Default directories
        default_inbox = Path.home() / "Downloads" / "ai-images"
        default_organized = Path.home() / "Pictures" / "AI-Organized"
        
        print("""
Alice needs two directories:
1. INBOX: Where you save new AI-generated images
2. ORGANIZED: Where Alice will organize them by date/project/source
""")
        
        print("📥 INBOX - Where do you save AI-generated images?")
        print(f"   Default: {default_inbox}")
        print("   (This is where you download from Midjourney, DALL-E, etc.)")
        inbox_input = input("\nInbox path (Enter for default): ").strip()
        inbox = Path(inbox_input) if inbox_input else default_inbox
        
        print("\n📂 ORGANIZED - Where should Alice organize your images?")
        print(f"   Default: {default_organized}")
        print("   (Alice will create dated folders here)")
        organized_input = input("\nOrganized path (Enter for default): ").strip()
        organized = Path(organized_input) if organized_input else default_organized
        
        # Create directories
        try:
            inbox.mkdir(parents=True, exist_ok=True)
            organized.mkdir(parents=True, exist_ok=True)
            print(f"\n✓ Created inbox: {inbox}")
            print(f"✓ Created organized: {organized}")
        except Exception as e:
            print(f"\n❌ Failed to create directories: {e}")
            raise
        
        self.inbox_path = inbox
        self.organized_path = organized
    
    def _create_initial_config(self):
        """Create initial configuration file."""
        print("\n⚙️  Creating Configuration")
        print("=" * 50)
        
        config = {
            "paths": {
                "inbox": str(self.inbox_path),
                "organized": str(self.organized_path)
            },
            "processing": {
                "understanding": self.has_any_key,  # Enable if we have keys
                "copy_mode": True,  # Safe default
                "watch": False,
                "dry_run": False,
                "force_reindex": False
            },
            "storage": {
                "search_db": "data/search.duckdb",
                "project_paths": [str(Path.home() / "Pictures" / "AI-Projects")],
                "asset_paths": [str(self.organized_path)]
            }
        }
        
        # Add provider configuration if we have keys
        if self.has_any_key:
            providers = []
            for provider in ["google", "deepseek", "anthropic", "openai"]:
                if self.key_manager.get_api_key(provider):
                    providers.append(provider)
            
            config["understanding"] = {
                "providers": providers,
                "preferred_provider": providers[0] if providers else None
            }
        
        # Save configuration
        config_path = Path("settings.yaml")
        try:
            import yaml
            with open(config_path, 'w') as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            print(f"\n✓ Configuration saved to: {config_path}")
        except Exception as e:
            print(f"\n❌ Failed to save configuration: {e}")
            raise
    
    def _run_test_organization(self):
        """Run a test organization if possible."""
        print("\n🧪 Test Run")
        print("=" * 50)
        
        # Check if there are any test images
        test_images = []
        for ext in ['.png', '.jpg', '.jpeg', '.webp']:
            test_images.extend(self.inbox_path.glob(f"*{ext}"))
        
        if not test_images:
            print("\nNo images found in inbox for test run.")
            print("Add some AI-generated images to:")
            print(f"  {self.inbox_path}")
            return
        
        print(f"\nFound {len(test_images)} images in inbox.")
        run_test = input("Run test organization? (Y/n): ").strip().lower()
        
        if run_test != 'n':
            print("\nRunning test organization...")
            try:
                # Run alice with dry-run
                import subprocess
                result = subprocess.run(
                    ["alice", "--dry-run", "--understand"],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    print("\n✅ Test run successful!")
                    print("Images would be organized without --dry-run")
                else:
                    print(f"\n⚠️  Test run encountered issues:")
                    print(result.stderr[:500])
                    
            except Exception as e:
                print(f"\n❌ Test run failed: {e}")
    
    def _show_next_steps(self):
        """Show next steps to the user."""
        print("\n🎉 Setup Complete!")
        print("=" * 50)
        
        print("\n📋 Quick Start Commands:")
        
        if self.has_any_key:
            # Show provider-specific costs
            providers_configured = []
            for provider in ["google", "deepseek", "anthropic", "openai"]:
                if self.key_manager.get_api_key(provider):
                    providers_configured.append(provider)
            
            print("\n💰 Your Configured Providers:")
            for provider in providers_configured:
                if provider == "google":
                    print("  • Google AI: FREE (50 images/day)")
                elif provider == "deepseek":
                    print("  • DeepSeek: ~$0.0002/image")
                elif provider == "anthropic":
                    print("  • Anthropic: ~$0.0025/image")
                elif provider == "openai":
                    print("  • OpenAI: ~$0.0050/image")
            
            print("""
1. Test with dry run (no cost, no changes):
   alice --dry-run

2. Organize with understanding (uses cheapest provider):
   alice

3. Monitor costs:
   alice cost report
   alice cost set-budget --daily 1.00
""")
        else:
            print("""
1. Basic organization (no AI):
   alice

2. Add API keys for AI features:
   alice keys setup

3. Preview without making changes:
   alice --dry-run
""")
        
        print("\n🤖 Using with Claude Desktop:")
        print("""
Add to ~/Library/Application Support/Claude/claude_desktop_config.json:
{
  "mcpServers": {
    "alice": {
      "command": "alice",
      "args": ["mcp-server"]
    }
  }
}

Then ask Claude: "Help me organize my AI images"
""")
        
        print("\n📚 Learn More:")
        print("  • Full guide: https://github.com/Kael1991/AliceMultiverse")
        print("  • Quick start: alice --help")
        print("  • Cost control: alice set-budget --help")
        
        if not self.has_any_key:
            print("\n⚠️  Remember to add API keys for AI features:")
            print("     alice keys setup")
    
    def _run_full_setup(self) -> bool:
        """Run full setup, overwriting existing configuration."""
        confirm = input("\n⚠️  This will overwrite existing configuration. Continue? (y/N): ").strip().lower()
        if confirm != 'y':
            return False
            
        # Clear existing setup
        self.has_any_key = False
        
        # Continue with normal setup
        return True


def check_first_run() -> bool:
    """Check if this is the first run and launch wizard if needed.
    
    Returns:
        True if setup is complete (or was already done)
    """
    from .welcome import show_first_run_prompt
    
    # Check if already configured
    config_exists = Path("settings.yaml").exists()
    keys_exist = False
    
    try:
        key_manager = APIKeyManager()
        for provider in ["anthropic", "openai", "google", "deepseek"]:
            if key_manager.get_api_key(provider):
                keys_exist = True
                break
    except:
        pass
    
    # If nothing is configured, this is first run
    if not config_exists and not keys_exist:
        # Show welcome and prompt
        if show_first_run_prompt():
            wizard = FirstRunWizard()
            return wizard.run()
        else:
            print("\nYou can run setup anytime with: alice setup")
            return True
    else:
        # Show quick start for existing users
        from .welcome import show_quick_start
        show_quick_start()
    
    return True


def run_setup_command():
    """Run the setup wizard (can be called explicitly via CLI)."""
    wizard = FirstRunWizard()
    success = wizard.run()
    return 0 if success else 1