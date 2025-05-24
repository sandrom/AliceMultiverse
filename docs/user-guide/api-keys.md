# API Keys Management

AliceMultiverse provides secure storage for API keys using macOS Keychain, with environment variables as an alternative for containerized environments.

## Quick Setup

The easiest way to configure your API keys is using the interactive setup wizard:

```bash
alice keys setup
```

This will guide you through setting up API keys for:
- SightEngine (quality assessment)
- Anthropic Claude (AI defect detection)

All keys are stored securely in macOS Keychain.

## Storage Methods

### 1. macOS Keychain (Default) 🔐

The only supported method for interactive storage - keys are encrypted by the operating system.

```bash
# Store individual keys
# Set keys individually (prompts for value)
alice keys set sightengine_user
alice keys set sightengine_secret
alice keys set anthropic_api_key

# Keys are automatically retrieved when needed
alice organize inbox/ --pipeline brisque-sightengine-claude
```

**Benefits:**
- Encrypted storage
- No plain text files
- Survives system updates
- Per-application access control

### 2. Environment Variables (For Containers) 🐳

The only alternative to Keychain, suitable for containerized environments:

```bash
# Set in Docker container or CI/CD
export SIGHTENGINE_API_USER="your-user"
export SIGHTENGINE_API_SECRET="your-secret"
export ANTHROPIC_API_KEY="sk-ant-..."
```

**Benefits:**
- Works in containers
- CI/CD compatible
- No file management
- Platform agnostic

**Note:** Environment variables are only checked if keys are not found in Keychain.

## API Key Commands

### Interactive Setup
```bash
alice keys setup
```

### Individual Key Management
```bash
# Interactive setup (recommended)
alice keys setup

# List all stored keys
alice keys list

# Keys can also be provided at runtime:
alice --pipeline brisque-sightengine --sightengine-key "user,secret"
alice --pipeline brisque-claude --anthropic-key "sk-ant-..."
# Output:
# Configured API keys:
# • sightengine_user (keychain)
# • sightengine_secret (keychain)  
# • anthropic_api_key (keychain)
```

## Priority Order

When AliceMultiverse needs an API key, it checks in this order:

1. **Command line** - Direct argument (highest priority)
2. **macOS Keychain** - Default secure storage
3. **Environment variable** - For containerized environments only

Example:
```bash
# Command line override (highest priority)
alice organize --pipeline standard --sightengine-key "user,secret"

# Uses keychain (normal usage)
alice organize --pipeline premium

# Environment variable (in Docker container)
docker run -e ANTHROPIC_API_KEY="sk-ant-..." alice organize --pipeline premium
```

## API Services

### SightEngine

Professional image analysis API for quality metrics and AI detection.

**Required Keys:**
- `sightengine_user` - Your API user ID
- `sightengine_secret` - Your API secret

**Getting Keys:**
1. Sign up at [sightengine.com](https://sightengine.com)
2. Go to Dashboard → API Credentials
3. Copy your User and Secret

**Usage:**
```bash
alice keys setup --sightengine-key "user,secret"
```

### Anthropic Claude

Advanced AI for defect detection in images.

**Required Keys:**
- `anthropic_api_key` - Your Anthropic API key (format: `sk-ant-...`)

**Getting Keys:**
1. Sign up at [console.anthropic.com](https://console.anthropic.com)
2. Go to API Keys
3. Create a new key

**Usage:**
```bash
alice keys setup --anthropic-key "sk-ant-..."
```

## Security Best Practices

### 1. Never Commit Keys
```bash
# Add to .gitignore
echo ".env" >> .gitignore
echo "config.json" >> .gitignore
echo "*.key" >> .gitignore
```

### 2. Use Appropriate Storage
- **Development**: Config file or .env
- **Production**: Environment variables
- **Personal**: macOS Keychain
- **CI/CD**: Secure secrets manager

### 3. Restrict Permissions
```bash
# Config file
chmod 600 ~/.alicemultiverse/config.json

# .env file
chmod 600 .env
```

### 4. Rotate Regularly
- Change keys every 90 days
- Immediately if exposed
- After team member leaves

### 5. Use Minimal Scopes
- Read-only keys when possible
- Service-specific keys
- Separate dev/prod keys

## Troubleshooting

### "API key not found"

1. Check key name spelling:
   ```bash
   alice keys setup --list
   ```

2. Verify environment variables:
   ```bash
   env | grep -E "(SIGHTENGINE|ANTHROPIC|OPENAI)"
   ```

3. Check keychain (macOS):
   ```bash
   security find-generic-password -s AliceMultiverse
   ```

### "Permission denied"

Fix file permissions:
```bash
chmod 600 ~/.alicemultiverse/config.json
ls -la ~/.alicemultiverse/
```

### "Invalid API key"

1. Check for extra spaces or quotes
2. Verify key format:
   - Claude: `sk-ant-...`
   - OpenAI: `sk-...`
   - SightEngine: Two separate values

3. Test with curl:
   ```bash
   # Test SightEngine
   curl https://api.sightengine.com/1.0/check.json \
     -F "api_user=YOUR_USER" \
     -F "api_secret=YOUR_SECRET" \
     -F "models=genai" \
     -F "url=https://example.com/image.jpg"
   ```

### Environment Variables Not Working

1. Ensure shell configuration is sourced:
   ```bash
   source ~/.zshrc  # or ~/.bashrc
   ```

2. Check variable names (exact match required):
   - `SIGHTENGINE_API_USER` (not SIGHTENGINE_USER)
   - `SIGHTENGINE_API_SECRET` (not SIGHTENGINE_KEY)
   - `ANTHROPIC_API_KEY` (not CLAUDE_API_KEY)

## Cost Management

Monitor your API usage to control costs:

```bash
# Dry run to see what would be processed
alice organize inbox/ --pipeline premium --dry-run

# Set cost limit
alice organize inbox/ --pipeline premium --cost-limit 10.00

# Use progressive pipeline to reduce costs
alice organize inbox/ --pipeline standard  # Cheaper than premium
```

## Example Workflows

### First Time Setup
```bash
# 1. Run setup wizard
alice keys setup

# 2. Choose keychain (option 1)
# 3. Enter your API credentials when prompted
# 4. Verify setup
alice keys setup --list

# 5. Test with a single image
alice test-image.jpg --pipeline standard
```

### CI/CD Setup
```yaml
# GitHub Actions example
env:
  SIGHTENGINE_API_USER: ${{ secrets.SIGHTENGINE_USER }}
  SIGHTENGINE_API_SECRET: ${{ secrets.SIGHTENGINE_SECRET }}
  ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_KEY }}

steps:
  - name: Run AliceMultiverse
    run: |
      alice organize ./media --pipeline standard
```

### Team Setup
```bash
# 1. Create shared config
cat > team-config.json << EOF
{
  "sightengine_user": "team-user",
  "sightengine_secret": "team-secret"
}
EOF

# 2. Encrypt and share securely
# 3. Team members install:
mkdir -p ~/.alicemultiverse
cp team-config.json ~/.alicemultiverse/config.json
chmod 600 ~/.alicemultiverse/config.json
```