# Alice Mobile Companion

A mobile-friendly web interface for controlling Alice timelines and previewing content remotely.

## Features

- **Remote Timeline Control**: Drag-and-drop timeline editing from your phone
- **Live Preview**: Real-time preview of timeline changes
- **Touch-Optimized**: Designed for mobile devices with touch gestures
- **WebSocket Sync**: Instant synchronization between devices
- **Secure Access**: Token-based authentication for remote access

## Architecture

The mobile companion consists of:
1. **API Server**: FastAPI backend with WebSocket support
2. **Mobile Web App**: Progressive Web App (PWA) for mobile devices
3. **Authentication**: Secure token-based access control
4. **Real-time Sync**: WebSocket connections for live updates

## Usage

1. Start the mobile server:
   ```bash
   alice mobile-server --host 0.0.0.0 --port 8080
   ```

2. Get your access token:
   ```bash
   alice mobile-token generate
   ```

3. Access from your mobile device:
   - Navigate to `http://your-computer-ip:8080`
   - Enter your access token
   - Start controlling timelines!

## Security

- Token-based authentication
- HTTPS support with self-signed certificates
- Session timeout for inactive connections
- IP whitelist options available