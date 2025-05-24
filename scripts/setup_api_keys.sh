#!/bin/bash
# Setup script for AliceMultiverse API keys

echo "🔐 AliceMultiverse API Key Setup"
echo "================================"
echo ""
echo "This script will help you securely store your API keys."
echo "Choose your preferred storage method:"
echo ""
echo "1. macOS Keychain (Most Secure - Recommended)"
echo "2. Config File (~/.alicemultiverse/config.json)"
echo "3. Environment Variables (.zshrc/.bashrc)"
echo ""
read -p "Select method (1-3): " method

case $method in
    1)
        storage="keychain"
        echo "Using macOS Keychain (encrypted storage)"
        ;;
    2)
        storage="config"
        echo "Using config file (will be chmod 600)"
        ;;
    3)
        storage="env"
        echo "Using environment variables"
        ;;
    *)
        echo "Invalid selection"
        exit 1
        ;;
esac

echo ""
echo "Which API keys would you like to configure?"
echo "1. SightEngine only"
echo "2. Claude only"
echo "3. Both SightEngine and Claude"
echo "4. All (including GPT-4V)"
echo ""
read -p "Select keys to configure (1-4): " keys

# Function to setup a key
setup_key() {
    local key_name=$1
    local prompt=$2
    
    echo ""
    echo "Setting up $key_name..."
    python3 api_key_manager.py set $key_name --method $storage
}

case $keys in
    1)
        setup_key "sightengine" "SightEngine API"
        ;;
    2)
        setup_key "claude" "Claude API"
        ;;
    3)
        setup_key "sightengine" "SightEngine API"
        setup_key "claude" "Claude API"
        ;;
    4)
        setup_key "sightengine" "SightEngine API"
        setup_key "claude" "Claude API"
        setup_key "gpt4v" "GPT-4V API"
        ;;
    *)
        echo "Invalid selection"
        exit 1
        ;;
esac

echo ""
echo "✅ API keys configured!"
echo ""
echo "To verify your keys, run:"
echo "  python3 api_key_manager.py list"
echo ""
echo "To test with organizer:"
echo "  python3 organizer.py inbox --pipeline standard --dry-run"
echo ""

# Make script executable
chmod +x setup_api_keys.sh