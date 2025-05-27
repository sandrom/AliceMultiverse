# API Keys Management

AliceMultiverse uses API keys for advanced quality assessment features. This document explains how to set up and manage these keys securely.

## Quick Setup

Run the interactive setup wizard:

```bash
alice keys setup
```

This will guide you through setting up API keys for:
- **SightEngine** - Professional image quality analysis ($0.001/image)
- **Anthropic Claude** - AI defect detection (~$0.002/image with Haiku model)

Keys are stored securely in macOS Keychain by default.

## Storage Methods

### 1. macOS Keychain (Recommended) 🔐

The default secure storage method - keys are encrypted by the operating system.

```bash
# Interactive setup
alice keys setup

# List configured keys
alice keys list

# Set individual keys
alice keys set sightengine_user
alice keys set sightengine_secret
alice keys set anthropic_api_key
```

### 2. Environment Variables 🐳

For containerized environments or CI/CD:

```bash
export SIGHTENGINE_API_USER="your-user"
export SIGHTENGINE_API_SECRET="your-secret"
export ANTHROPIC_API_KEY="sk-ant-..."
```

### 3. Command Line

Provide keys directly (useful for one-off runs):

```bash
alice --pipeline standard --sightengine-key "user,secret"
alice --pipeline premium --anthropic-key "sk-ant-..."
```

## Getting API Keys

### SightEngine
1. Sign up at [sightengine.com](https://sightengine.com)
2. Go to Dashboard → API Credentials
3. Copy your User and Secret

### Anthropic Claude
1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Go to API Keys
3. Create a new key (format: `sk-ant-...`)

## Security Best Practices

1. **Never commit keys** - Add `.env`, `config.json` to `.gitignore`
2. **Use appropriate storage** - Keychain for personal use, env vars for containers
3. **Rotate regularly** - Change keys every 90 days
4. **Use minimal scopes** - Service-specific keys when possible

## Cost Management

```bash
# Preview costs without processing
alice --pipeline premium --dry-run

# Set spending limit
alice --pipeline premium --cost-limit 10.00

# Use cheaper pipelines
alice --pipeline basic      # Free (BRISQUE only)
alice --pipeline standard   # ~$0.001/image
alice --pipeline premium    # ~$0.003/image
```

## Troubleshooting

See the [API Keys Guide](docs/user-guide/api-keys.md) for detailed troubleshooting steps.