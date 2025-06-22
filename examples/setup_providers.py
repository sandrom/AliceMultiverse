#!/usr/bin/env python3
"""Setup AI providers for enhanced understanding."""

from alicemultiverse.core.keys.manager import KeyManager

def setup_providers():
    """Interactive setup for AI providers."""
    manager = KeyManager()
    
    print("🔑 AI Provider Setup")
    print("=" * 50)
    print("\nConfigure API keys for AI understanding:")
    print("1. OpenAI - Best for object detection")
    print("2. Anthropic - Best for artistic analysis") 
    print("3. Google AI - Best for technical details")
    print("4. DeepSeek - Cost-effective alternative")
    
    providers = {
        '1': ('openai_api_key', 'OpenAI'),
        '2': ('anthropic_api_key', 'Anthropic'),
        '3': ('google_ai_api_key', 'Google AI'),
        '4': ('deepseek_api_key', 'DeepSeek')
    }
    
    while True:
        choice = input("\nSelect provider to configure (1-4, or 'q' to quit): ")
        if choice == 'q':
            break
            
        if choice in providers:
            key_name, provider_name = providers[choice]
            
            # Check if already configured
            current = manager.get_key(key_name)
            if current:
                print(f"✅ {provider_name} is already configured")
                update = input("Update the key? (y/n): ")
                if update.lower() != 'y':
                    continue
            
            # Get the API key
            print(f"\n📝 Enter your {provider_name} API key")
            print(f"   (Get one from {get_provider_url(provider_name)})")
            api_key = input("API Key: ").strip()
            
            if api_key:
                success = manager.set_key(key_name, api_key)
                if success:
                    print(f"✅ {provider_name} API key saved successfully!")
                else:
                    print(f"❌ Failed to save {provider_name} API key")
    
    # Show configured providers
    print("\n📋 Configured Providers:")
    for key_name, provider_name in providers.values():
        if manager.get_key(key_name):
            print(f"  ✅ {provider_name}")
        else:
            print(f"  ❌ {provider_name} (not configured)")

def get_provider_url(provider):
    """Get the URL to obtain API keys."""
    urls = {
        'OpenAI': 'https://platform.openai.com/api-keys',
        'Anthropic': 'https://console.anthropic.com/settings/keys',
        'Google AI': 'https://makersuite.google.com/app/apikey',
        'DeepSeek': 'https://platform.deepseek.com/api_keys'
    }
    return urls.get(provider, 'provider website')

if __name__ == "__main__":
    setup_providers()