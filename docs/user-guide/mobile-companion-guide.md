# Mobile Companion App Guide

Control Alice timelines remotely from your phone or tablet with the mobile companion app.

## Overview

The Alice Mobile Companion lets you:
- View and edit timelines from your mobile device
- Drag-and-drop to reorder clips
- Real-time synchronization with desktop
- Touch-optimized interface
- Secure token-based access

## Quick Start

### 1. Start the Mobile Server

On your computer running Alice:

```bash
alice mobile server
```

You'll see output like:
```
🚀 Starting Alice Mobile Companion Server
==================================================
Local access: http://localhost:8080
Mobile access: http://192.168.1.100:8080

Generate access token with: alice mobile token generate
==================================================
```

### 2. Generate Access Token

```bash
alice mobile token generate --qr
```

This will:
- Generate a secure access token
- Display a QR code you can scan
- Show the token for manual entry

### 3. Connect from Mobile

1. Open your mobile browser
2. Navigate to the URL shown (e.g., `http://192.168.1.100:8080`)
3. Enter your access token
4. Start controlling timelines!

## Features

### Timeline Management

- **View Timelines**: See all available timelines with duration and clip count
- **Edit Timelines**: Tap a timeline to open the editor
- **Reorder Clips**: Drag clips up/down to change order
- **Save Changes**: Changes sync automatically or tap "Save Order"

### Touch Gestures

- **Tap**: Select timeline or clip
- **Long Press & Drag**: Reorder clips
- **Swipe**: Navigate between screens
- **Pinch**: Zoom timeline (coming soon)

### Real-time Sync

- WebSocket connection for instant updates
- See changes from desktop immediately
- Multiple devices can connect simultaneously
- Connection status indicator

## Security

### Token Management

List all tokens:
```bash
alice mobile token list
```

Revoke a token:
```bash
alice mobile token revoke <token-prefix>
```

Clean up expired tokens:
```bash
alice mobile token cleanup
```

### Best Practices

1. **Use HTTPS**: For production, set up HTTPS with certificates
2. **Limited Token Lifetime**: Tokens expire after 24 hours by default
3. **Network Security**: Only use on trusted networks
4. **IP Whitelisting**: Configure firewall rules if needed

## Advanced Usage

### Custom Configuration

Start with custom settings:
```bash
alice mobile server --host 0.0.0.0 --port 9090 --media-dir /path/to/media
```

### Multiple Tokens

Generate tokens for different users/devices:
```bash
alice mobile token generate --name "iPad" --expires 48
alice mobile token generate --name "Phone" --expires 12
```

### AI Integration

Use with Claude Desktop:
```claude
Start the mobile server and generate a token for me
```

Response:
```json
{
  "status": "started",
  "local_url": "http://localhost:8080",
  "mobile_url": "http://192.168.1.100:8080",
  "access_token": "xK3n9Lp2Qr5Tz8..."
}
```

## Troubleshooting

### Can't Connect from Mobile

1. Check both devices are on same network
2. Verify firewall allows port 8080
3. Try using IP address instead of hostname
4. Test with `alice mobile test`

### Token Issues

- Tokens are case-sensitive
- Check token hasn't expired
- Generate new token if needed

### Performance

- Keep timeline clips under 100 for best performance
- Use smaller thumbnails for faster loading
- Close other apps to free memory

## Progressive Web App

The mobile companion can be installed as a PWA:

1. Open in Safari (iOS) or Chrome (Android)
2. Tap Share → Add to Home Screen
3. Launch from home screen for full-screen experience

## Network Requirements

- **Same Network**: Desktop and mobile must be on same network
- **Port Access**: Port 8080 (default) must be accessible
- **Bandwidth**: ~1-5 Mbps for smooth operation
- **Latency**: < 100ms recommended

## Future Features

Coming soon:
- Video preview in timeline
- Multi-select operations  
- Cloud sync support
- Native mobile apps
- Collaborative editing

## Examples

### Basic Workflow

1. Start server and generate token:
```bash
alice mobile server
alice mobile token generate --qr
```

2. Scan QR code with phone

3. Edit timeline on mobile

4. Changes appear instantly on desktop

### Team Collaboration

1. Generate tokens for team:
```bash
alice mobile token generate --name "Editor1" --expires 8
alice mobile token generate --name "Editor2" --expires 8
```

2. Share tokens securely

3. Multiple editors can work simultaneously

### Automation

Create timeline and add to mobile:
```python
# Through MCP
timeline_id = await add_timeline_to_mobile(
    timeline_name="Project Timeline",
    clip_paths=[
        "/path/to/clip1.mp4",
        "/path/to/clip2.mp4"
    ],
    clip_durations=[3.0, 5.0]
)
```

## Tips

- **Battery**: Plug in device for long editing sessions
- **Orientation**: Landscape mode shows more timeline detail
- **Shortcuts**: Double-tap clip for properties (coming soon)
- **Backup**: Desktop auto-saves all changes